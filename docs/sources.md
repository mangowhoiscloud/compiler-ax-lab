# Compiler AX 품질 기준: 원문 확인 대장

MD 지침과 실행·평가 코드를 분리한 사례의 실제 경로와 판본은 [원문 폴더 구조 대장](../references/source-layouts.md)에 따로 둔다. 실행 지침은 [program.md](../program.md)이며, 참고 사례의 이름이나 성과를 실행 규칙 대신 사용하지 않는다.

2026-09-14에 Furiosa와 Dioxus의 공개 코드 및 Rust 공식 지침을 직접 읽었다. 이 문서는 원문 사본이 아닌 판본·읽은 범위·설계 결정의 기록이다. 유지할 기준은 [품질 계약](quality.md)의 품질 계약에 종합한다. 저장소·문서 조회만 수행했으며 빌드, 테스트, 퍼징, NPU 실행은 하지 않았다.

## Furiosa: 기존 규칙을 출발점으로 고정

이번 확인 대상은 공개 `furiosa-ai/furiosa-opt`의 고정 commit `9b9cf0fdc78df00cdc430eae725a5ad9084a735e`, release 0.8.1이다. 이후 이동하는 `main`을 자동으로 추종하지 않는다. 다음은 해당 commit의 직접 확인 범위다. `[실측: 소스]`는 명령 실행 성공을 뜻하지 않는다.

| 원문 | 확인한 내용 | 설계에서 바뀌는 판단 |
|---|---|---|
| [README의 host·도구 요구](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/README.md#L23-L56) | 모든 backend의 지원 host는 `x86_64-unknown-linux-gnu`다. 배포 바이너리는 GLIBC 2.34 이상이 필요하고 Ubuntu 22.04는 최소 지원 버전이다. Ubuntu 24.04도 지원하며 nightly-2026-05-01과 driver ABI가 결합된다. `build-essential`·`libclang-dev`는 공통, AArch64 cross compiler는 NPU 빌드용이다. | `[설계]` CPU host와 NPU target을 구분한다. 22.04만 필수라고 해석하지 않으며, 문서에 없는 AVX 계열 요구나 실제 VM의 ISA 노출을 추정하지 않는다. |
| [Dockerfile](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/Dockerfile) | `FROM ubuntu:24.04`이며 `dist`의 실행 바이너리·driver·native library를 복사하고 local prebuilt 경로를 지정한다. source만으로 완결되는 빌드 파일은 아니다. 기본 `ENTRYPOINT`는 `cargo furiosa-opt`다. | `[설계]` 24.04 amd64 빌드 컨테이너를 선택한다. host image·container digest와 `dist`의 출처·release/tag·target·전체 SHA-256을 고정한다. CPU smoke는 entrypoint를 명시적으로 바꿔 plain Cargo로 실행한다. 아직 빌드·실행하지 않았다. |
| [Makefile](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/Makefile#L24-L67) | check/clippy는 workspace·all-targets, fmt는 check-only, test는 release다. `clippy-npu`, mdbook build/test가 별도다. | `[추론]` 기존 target을 재사용하고 검사와 수정, CPU와 NPU, 문서 렌더와 예제 실행을 분리한다. |
| [build.yml](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/.github/workflows/build.yml) | Ubuntu 22.04, 고정 nightly, prebuilt 경로, check/fmt/clippy/machete/test 순서가 있다. | `[추론]` 내부 CI 표준으로 일반화하지 않는다. 첫 CPU 체크포인트에서 공개 검사 묶음을 확인한다. |
| [rust-toolchain.toml](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/rust-toolchain.toml), [rustfmt.toml](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/rustfmt.toml), [clippy.toml](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/clippy.toml) | nightly-2026-05-01, rustfmt/clippy, max_width=120, allow-dbg-in-tests=true, too-many-lines-threshold=1150. | `[추론]` 임의의 80자·전역 pedantic·unwrap 금지 규칙을 덧씌우지 않는다. |
| [Cargo.toml](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/Cargo.toml), [Cargo.lock](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/Cargo.lock) | 현재 workspace와 기대 cfg, 추적된 lockfile이 존재한다. `--all-features`는 공개 Makefile의 공통 명령이 아니다. | `[추론]` 지원 backend/feature를 명시하고 lockfile을 보존한다. `--locked` 추가는 파일럿의 재현 정책이며 기존 Makefile 옵션으로 쓰지 않는다. |
| [prebuilt 다운로드](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/.github/actions/download-released-libraries/action.yml), [mapping build.rs](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-mapping/build.rs#L28-L75) | CI는 SHA256SUMS를 검사한다. build.rs의 LOCAL_PREBUILT 경로는 파일을 복사하며, 일반 다운로드는 checksum 확인과 선택적 attestation 경로가 있다. | `[추론]` 로컬 prebuilt를 쓰더라도 출처·tag·target·전체 SHA를 준비 담당자가 검증한다. checksum 일치를 출처 인증으로 부르지 않는다. |
| [binary_add_tests.rs](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/tests/binary_add_tests.rs#L6-L28), [kernel-validation.md](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/docs/src/quick-start/kernel-validation.md) | 실제 `test_binary_add_2048`는 고정 seed와 별도 host 덧셈 결과를 `assert_eq!`로 비교하며 성공한 값 전체를 출력하지 않는다. 검증 문서는 정적 compile, CPU 값, NPU 실행, schedule을 구분한다. | `[추론]` 무변경 smoke는 테스트 소스·hash와 libtest의 이름·실행 수·verdict·exit로 assertion 통과를 연결한다. 관측하지 않은 출력값은 만들지 않는다. 조사 후 추가·실행한 double-buffering 검사는 [별도 실행 근거](kernels/double-buffering.md#8-로컬-docker-실행-결과)로 구분한다. |
| [double_buffering.rs의 축](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering.rs#L13), [rolled_kernel의 입출력](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/rolled_kernel.rs#L9), [cast.rs](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-std/src/cast.rs#L385) | `Tok=16, Red=64, Out=8, Group=20, Pairs=10`. 세 변형의 activation·weight·output은 각각 `bf16`의 `[16,64]`, `[20,8,64]`, `[16,20,8]`이며 contraction 결과 형식은 `f32`다. | `[계산]` 논리 입출력 원자료는 2+20+5=27 KiB다. 빌드 메모리·host 복사본·oracle 메모리를 포함한 실측치가 아니다. 입력 값·seed·독립 기대값·허용 오차는 실행 전에 별도로 고정해야 한다. |
| [runtime.rs](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-std/src/runtime.rs#L225), [CPU backend](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-std/src/backend/cpu.rs#L14) | 일반 Cargo 실행은 CPU에서 원래 함수 본문을 실행한다. CPU backend는 host buffer를 사용하며 NPU 실행과 경로가 다르다. | `[설계]` 이번 테스트 보강은 CPU 값과 오류 검출을 평가한다. 정적 kernel compile을 새 필수 후보 검사로 확대하거나 NPU 정확성·성능이 확인됐다고 쓰지 않는다. |

과거 SWMAP의 0.4.0 workspace 수·backend 명칭은 날짜가 다른 기록이다. 이번 명령의 근거는 위 0.8.1 pin이다. 공개 driver stub을 내부 Compiler 소스로 해석하지 않는다.

## 공개 Agent 지침과 리뷰에서 채택한 규칙

확인일은 2026-09-14입니다. 아래 공개 지침·리뷰·소스와 이 lab의 적용 결정을 구분합니다. 운영 절차는 [AGENTS.md](../AGENTS.md#3-코드와-커밋의-컨벤션)에 두고 외부 prompt나 명령을 자동 실행하지 않습니다.

| 원문과 판본 | 확인 범위 | 적용과 한계 |
|---|---|---|
| [torch-fx-rs AGENTS.md, 3024d6d](https://github.com/furiosa-ai/torch-fx-rs/blob/3024d6d157732e51b02ef67b808131bec4d652ef/AGENTS.md) | 전체 문서. 목적·구현 위치·기존 helper·작은 PR·표적 테스트·API 문서와 수명 규칙을 명시합니다. | 읽기 경로, 의미 보존, 작은 diff와 근거 인계를 채택합니다. PyO3/GIL·Python 3.10·구체 wrapper 구조는 해당 repo 규칙이며 lab 공통 규칙으로 복사하지 않습니다. |
| [agent_skills AGENTS.md, d5fc482](https://github.com/furiosa-ai/agent_skills/blob/d5fc482fdca0af78aada5d1e183b4aad18ffbfc7/AGENTS.md) | 전체 문서. 최종 diff 기반 설명·원자적 커밋·사람 확인을 명시합니다. 같은 pin의 tree에는 진입점이 가리키는 `git-commit-helper/SKILL.md`가 없고 현재 이름은 `pr-restructure`입니다. | 의미 단위 변경과 현재 diff 확인을 채택합니다. 오래된 경로·명령 이름·복구용 destructive command를 복사하지 않습니다. prefix 금지는 lab의 기존 커밋 형식과 달라 이식하지 않습니다. |
| [validator #34, 2026-06-25 리뷰](https://github.com/furiosa-ai/furiosa-rngd-validator/pull/34#discussion_r3472422897), [07-01 승인](https://github.com/furiosa-ai/furiosa-rngd-validator/pull/34#pullrequestreview-4608023875) | 실행 파일 부재를 활성화 파일만으로 놓쳐 기본 30분 polling까지 지연시키는 경로, 상태 의미와 README 정합성을 지적했습니다. | 긴 작업 전에 실제 실행 파일·환경을 확인합니다. 30분은 코드·리뷰의 지연 경로이며 이번 실측 시간이 아닙니다. 외부 skip/unknown을 lab PASS로 흡수하지 않습니다. |
| [validator #48, 2026-07-24 재리뷰](https://github.com/furiosa-ai/furiosa-rngd-validator/pull/48#pullrequestreview-4774195374), [복구 파일 지적](https://github.com/furiosa-ai/furiosa-rngd-validator/pull/48#discussion_r3712120903), [최종 수정 ee270ad](https://github.com/furiosa-ai/furiosa-rngd-validator/commit/ee270ad60446a6b8c442df857477dcd8537f8b12) | 일부 ACS 적용 실패의 복원과 컨테이너 종료 후 복구 자료 보존을 확인했습니다. 최종 diff는 복원 실패 종료·상태 파일 보존·회귀 테스트를 포함합니다. | 실패 후 실제 상태·복구 결과·원문 증거를 보존합니다. NPU 검증 도구 사례이며 컴파일러 내부 병목이나 실제 장치 재실행 근거로 쓰지 않습니다. |
| [코멘트 수집 코드, d5fc482](https://github.com/furiosa-ai/agent_skills/blob/d5fc482fdca0af78aada5d1e183b4aad18ffbfc7/scripts/fetch_pr_comments.py) | unresolved만 남기며 처음 100개 thread·50개 comment를 조회합니다. | 리뷰 학습에는 resolved 대화·일반 댓글·판정·후속 commit도 필요합니다. 같은 GitHub API를 쓰되 페이지 끝과 수집 실패를 기록합니다. 별도 엔진은 추가하지 않습니다. |
| [mapping 문법](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-mapping-macro/src/parser/parser.lalrpop), [진단 테스트](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-mapping-macro/src/parser/diagnostic.rs) | Extent 문법의 네 형태와 `A /` 오류 위치·안내 테스트를 확인했습니다. | 조사 후 추가한 두 진입점의 AST·span 검사는 [parser 계약과 실행 상태](quality.md#mapping-parser)에 둡니다. 공개 예시를 보호 평가로 재사용하지 않습니다. |

`furiosa-opt`의 [PR #2 병합 commit](https://github.com/furiosa-ai/furiosa-opt/commit/a889fe762bbc1b7605b0ad630729ff1142e99475)과 [Copybara import](https://github.com/furiosa-ai/furiosa-opt/commit/06dda288eb450b97f702fc5b69dfb1777cfa9072)는 확인되지만 해당 PR 대화는 당시 공개 조회에서 확인되지 않았습니다. PR이 없었다거나 내부 리뷰가 느리다는 결론으로 바꾸지 않습니다. 지침은 선언된 기준이고, 공개 리뷰는 해당 변경의 판단 근거입니다. 조직 전체의 채택률·리뷰 시간은 별도 증거가 필요합니다.

## Dioxus: 전사에서 제기한 문제를 저장소의 검사로 대조

[Jonathan Kelley, Building ambitious software](https://www.youtube.com/watch?v=H7vFrcNWXzs)의 보존 원어 자동 자막 중 05:30부터 종료까지를 이번에 다시 읽었다. 비어 있지 않은 이벤트 총 485개와 원본 SHA `fa27b1c4a4376ad1399e6f6bb3578d7d492300b54efcba5166be440634382538`를 확인했다. 원문 전사는 로컬에만 보존하며 이 공개 저장소에는 재배포하지 않는다. 웹 watch 페이지는 이번에도 throttled였으며 새 전사나 원음 검수를 했다고 쓰지 않는다.

- `[주장: 발표]` [06:18–06:53](https://www.youtube.com/watch?v=H7vFrcNWXzs&t=378s): 많은 생성 변경이 병합 품질을 넘지 못했다. `[추론]` 생성량이 아닌 검토가 끝난 변경을 완료 단위로 둔다.
- `[주장: 발표]` [10:46–11:14](https://www.youtube.com/watch?v=H7vFrcNWXzs&t=646s): 플러그인의 빠른 구현 뒤 시험 조건과 실장치 확인에 시간을 썼다. `[추론]` host 성공 뒤 필요한 target 확인을 별도로 남긴다. 이 기간을 독립 생산성 측정으로 쓰지 않는다.
- `[주장: 발표]` [13:04–15:59](https://www.youtube.com/watch?v=H7vFrcNWXzs&t=784s): 코드·문서·예제·릴리스 품질, 사람이 정하는 테스트 조건과 runner, agent의 fuzzing harness 보조를 설명한다.
- `[주장: 발표]` [16:03–18:08](https://www.youtube.com/watch?v=H7vFrcNWXzs&t=963s): 과도한 구조 변경의 위험과 사람의 줄 단위 PR 검토를 설명한다. 모든 과거/현재 PR에 실제 적용됐다는 감사 결과는 아니다.

현재 공개 main은 `ada3b67c73c1c5484dd2e8408cb21c470b200423`으로 고정했다. 발표에서 언급한 특정 작업과 이 commit의 인과적 동일성은 주장하지 않는다.

| 원문 | 직접 확인한 작동 방식 | Compiler AX에 옮길 범위 |
|---|---|---|
| [AGENTS.md](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/AGENTS.md) | 작업 대상에 따라 crate·아키텍처 문서를 안내한다. | `[추론]` 후보가 바꿀 모듈과 호출자·테스트를 먼저 읽도록 한다. 문서를 모두 prompt에 넣지 않는다. |
| [CI main.yml](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/.github/workflows/main.yml#L35-L190) | Rust 경로 필터, fmt/clippy, schema 재생성 diff, docs build와 doctest를 분리한다. 파일 필터에는 Cargo.lock/rustfmt.toml이 명시되지 않는다. | `[추론]` CI 존재만으로 해당 변경의 검사 완료를 가정하지 않는다. 필수 검사 목록과 실제 run/skip을 대조한다. Dioxus의 전체 feature/플랫폼 조합은 복사하지 않는다. |
| [fuzz README](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/packages/fuzz/README.md), [src/lib.rs](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/packages/fuzz/src/lib.rs#L17-L21) | 구조화된 동작을 incremental/fresh 결과로 비교한다. 일반 CI용 재사용 하네스와 별도 libFuzzer 실행을 나눈다. | `[추론]` 첫 파일럿은 고정 경계 입력·독립 기대값으로 시작한다. 탐색에서 얻은 반례는 축소해 일반 회귀 검사로 남긴다. |
| [targeted.rs](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/packages/fuzz/src/targeted.rs#L21-L108) | 축소된 byte 입력은 strict 검사로 재실행한다. 전체 corpus coverage 재생은 `run_case` 결과를 의도적으로 버린다. corpus 쓰기는 별도 환경변수로 제어한다. | `[추론]` coverage 통과를 correctness로 사용하지 않는다. 검사 중 fixture 갱신·결과 무시를 차단한다. 변수는 문서의 `=1` 표현과 달리 코드가 존재 여부를 검사하므로 임의의 0 값도 비활성화라고 가정하지 않는다. |

CI 파일은 검사 의도를 입증하며, 실제 완료 run이나 branch protection의 강제 여부를 대신하지 않는다. 이번 정책은 모든 required check의 같은 revision 결과를 요구하는 자체 제안이다. Dioxus 또는 Furiosa가 동일하게 강제한다는 주장은 하지 않는다.

## Rust 공식 지침에서 채택한 최소 기준

- [Clippy usage](https://doc.rust-lang.org/clippy/usage.html): 기본 lint와 `-D warnings`를 사용한다. pedantic은 의도적 오탐 가능성이 있고 restriction 전체 사용은 권장되지 않는다. `[추론]` 후보가 임의로 allow 범위를 넓히지 못하게 하되, 오탐은 사유·범위·담당자 결정으로 처리한다.
- [Cargo test](https://doc.rust-lang.org/cargo/commands/cargo-test.html): `--no-run`은 실행이 아니며 `--all-targets`에 doctest는 포함되지 않는다. build jobs와 test threads, package/target/feature를 따로 고정한다. `[추론]` 목록·선택된 테스트·실제 실행 수를 보존하고 0건 통과를 배제한다.
- [Rust API Guidelines: documentation](https://rust-lang.github.io/api-guidelines/documentation.html): 예제의 사용 목적, Errors/Panics/Safety 조건과 릴리스 변경을 문서화한다. `[추론]` unsafe/FFI/API가 실제 변경될 때 필요한 계약과 검사를 확장하며 처음부터 모든 도구를 강제하지 않는다.

## 이번 반영의 경계

이 기록은 2026-09-14 품질 기준 조사 범위다. 이후 이 lab 저장소에 추가한 문서 CI와 구분한다. Rust CI 실행, compiler checkout 변경, dependency 설치, cloud 호출, Furiosa upstream PR/병합은 수행하지 않았다. Miri·sanitizer·cargo-fuzz·보안 공급망 도구의 전면 도입은 첫 CPU 테스트 보강 과제의 선행 조건으로 두지 않는다. 해결할 위험과 실행 가능한 범위가 확인된 뒤 별도 검사로 추가한다.

## 계획·실행·검토: 원논문의 방법과 이 실험의 선택

2026-09-14에 보존된 강의 프레임·자동 자막을 원논문과 대조했다. 확인 구간은 [Learning from Feedback with Tools/Code 05:00–08:00](https://www.youtube.com/watch?v=Lxh9RF5S-K0&t=300s), [Planning and Multi-Step Reasoning 07:00–13:00·19:00 및 25:00–33:00](https://www.youtube.com/watch?v=Ml_fp9XkB8Y&t=420s)다. 강의가 여러 연구를 설명한다는 점은 [공식 일정](https://cs329a.stanford.edu/)으로 확인했다. 영상 watch 페이지의 재조회는 실패해 원음을 새로 청취하지 않았으며, 자동 자막은 직접 인용문으로 사용하지 않는다. 기관·강의명은 이 확인 경로에만 남긴다.

| 원저작물·확인 위치 | 원문이 다루는 동작 | 이 실험에서 사용하는 범위 |
|---|---|---|
| Yao et al., [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629), 초록·강의 06:00 도식 | 추론과 행동을 번갈아 수행하고 환경 관측을 다음 선택의 문맥에 넣는다. | 명령 출력은 관측으로, 원인 가설은 해석으로 구분한다. 검사 통과나 변경 채택은 별도 판단이다. |
| Zhou et al., [Language Agent Tree Search Unifies Reasoning, Acting, and Planning in Language Models](https://arxiv.org/html/2310.04406v3), v3 §4.2·6·Appendix B | **Language Agent Tree Search(LATS)**는 MCTS로 행동 후보를 탐색한다. **Backpropagation**은 탐색 트리의 값 갱신이며 모델 가중치 학습이 아니다. 이전 환경 상태로 돌아갈 수 있다는 가정이 있다. | 대안 비교 전 상태 복원 조건을 확인한다. 파일 사본만으로 프로세스·외부 부수효과까지 복원된다고 가정하지 않는다. 이번 파일럿은 LATS 구현이 아니다. |
| Biju et al., [Sprint: Enabling Interleaved Planning and Parallelized Execution in Reasoning Models](https://arxiv.org/html/2506.05745v2), v2 §3.1–3.2·Fig. 1 | **Planning → Parallel executions → Syncing**을 반복한다. 같은 단계의 독립 하위 과제에 대한 모델 출력을 누적 문맥에 합친다. 데이터의 의존 DAG 구성과 모델 미세조정은 별도 학습 과정이다. | 독립성 확인과 결과 수집을 참고한다. 원문의 executor는 하위 문제를 푸는 모델이며 CPU 검사기가 아니다. VM 슬롯 보정은 자체 실행 설계이고, 결과 동기화는 독립 평가가 아니다. |
| Mishra·Rajeev·Chakraborty, [Tree-of-Concerns: Hierarchical Multi-Agent Debate for Unstated-Limitation Extraction in Scientific Critique](https://arxiv.org/html/2608.20777v1), v1 §3.3–3.5 | 논문에 명시되지 않은 한계를 찾기 위해 관점별로 쟁점을 제기하고 반박·재검토·판정을 거친다. 생성 중에는 분기 사이의 통신을 막는다. | 필요할 때 고정 후보의 쟁점별 검토에 참고한다. 코드 위치·반례·검사 명령을 요구하는 세 관점은 자체 제안이며, 모델의 판정은 컴파일러 정확성 증거가 아니다. |

과거 강의 요약의 “evaluator가 결과를 통합한다”는 표현은 Sprint의 **Syncing**으로 바로잡는다. 또한 [RLEF: Grounding Code LLMs in Execution Feedback with Reinforcement Learning](https://arxiv.org/html/2410.02089v2) v2 Fig. 2·§2에서는 private tests도 PPO 학습 보상에 쓰인다. 이를 이 실험의 후보 고정 후 독립 최종 검사와 같은 역할로 옮기지 않는다. 위 구분은 참고 스킬의 해당 요약에도 반영했다.

## 실험·PR 설계의 추가 원문

- [DoRA v2 §3.2·4](https://arxiv.org/html/2402.09353v2): 문단 전개를 참고하며 학습 방법의 이식은 아니다.
- [Nebius VM 종류](https://docs.nebius.com/compute/virtual-machines/types), [Sandbox overview](https://docs.tokenfactory.nebius.com/sandboxes/overview): 제품 안내이며 실제 할당·계정 접근의 증거는 아니다.
- [GitHub branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches): required check가 skipped/neutral도 허용한다는 점, strict up-to-date와 stale approval 처리. 저장소의 실제 설정은 API 응답으로 별도 확인한다.
- [GitHub pull_request event](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request): 기본 test merge checkout과 head/base revision을 구분한다.

## 2026-09-14 Nebius CI 계획의 원문과 선택

아래는 공개 문서를 확인한 설계 근거다. 계정의 VM 사용권·잔액·실제 자원 할당이나 이 repo의 CI 구현 결과가 아니다. 운영 절차의 정본은 [실험 계획](experiment.md)이다.

| 원문 | 확인한 내용과 적용 |
|---|---|
| [VM 플랫폼](https://docs.nebius.com/compute/virtual-machines/types) | `cpu-d3`는 AMD EPYC 9654 기반이며 `8vcpu-32gb` preset은 8 vCPU·32 GiB다. 초기 후보로 정하되 실제 지역·할당 가능 여부는 실행 전에 확인한다. 32 GiB가 빌드·검사에 충분하다는 실측 결과는 없다. |
| [부팅 이미지](https://docs.nebius.com/compute/storage/boot-disk-images) | non-GPU 기본 이미지가 Ubuntu 24.04이며 `ubuntu22.04-driverless`로 새 디스크를 만드는 경로는 deprecated다. `[설계]` 24.04 host와 위 pin의 Dockerfile을 참고한 24.04 amd64 빌드 컨테이너를 선택한다. 정확한 image ID·digest와 userspace·native dependency 호환성은 아직 고정·실행 검증하지 않았다. |
| [브라우저 없는 CLI 인증](https://docs.nebius.com/cli/no-browser) | service account의 authorized key를 CI secret에서 주입하는 경로가 문서화돼 있다. `[설계]` 권한 있는 controller만 이 키를 사용하고 후보 worker에 전달하지 않는다. private key가 있으므로 secretless 인증이라고 부르지 않는다. |
| [VM 삭제](https://docs.nebius.com/compute/virtual-machines/delete), [과금](https://docs.nebius.com/compute/resources/pricing), [예산](https://docs.nebius.com/signup-billing/budgets) | VM 삭제는 VM-managed disk도 삭제하며 별도 volume은 따로 정리해야 한다. stop 이후에도 storage 비용이 남고 예산 알림은 자동 지출 차단이 아니다. `[설계]` 한 대로 시작하고 정확한 자원 식별자를 기록해 종료·취소 뒤 삭제 및 재조회를 수행한다. 잔존 자원 정리는 자체 구현 계획이지 Nebius 기본 TTL 기능이 아니다. |
| [GitHub 보안](https://docs.github.com/en/actions/reference/security/secure-use), [environment 제한](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments) | 공개 PR 코드와 secret을 가진 실행 경로를 분리한다. `[설계]` GitHub-hosted 기본 CI를 유지하고 신뢰된 main의 승인형 controller만 VM을 관리한다. environment 승인이나 workflow 이름만으로 후보 코드가 신뢰되는 것은 아니다. |

KG 엔진 보류는 외부 연구가 입증한 우열이 아니라 현재 작업의 미구현 지점과 읽기 경로를 바탕으로 한 선택이다. [판단 기록](context.md)에 기준선·재검토 조건을 남긴다.

외부 소스·논문·전사 전체를 vendoring하지 않는다. 이 저장소의 자체 서술과 코드는 개인 연구이며 FuriosaAI나 Dioxus의 공식 정책을 대변하지 않는다.
