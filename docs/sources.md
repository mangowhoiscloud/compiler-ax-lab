# Compiler AX 품질 기준: 원문 확인 대장

MD 지침과 실행·평가 코드를 분리한 사례의 실제 경로와 판본은 [원문 폴더 구조 대장](../references/source-layouts.md)에 따로 둔다. 실행 지침은 [program.md](../program.md)이며, 참고 사례의 이름이나 성과를 실행 규칙 대신 사용하지 않는다.

2026-09-14에 Furiosa와 Dioxus의 공개 코드 및 Rust 공식 지침을 직접 읽었다. 이 문서는 원문 사본이 아닌 판본·읽은 범위·설계 결정의 기록이다. 유지할 기준은 [품질 계약](quality.md)의 품질 계약에 종합한다. 저장소·문서 조회만 수행했으며 빌드, 테스트, 퍼징, NPU 실행은 하지 않았다.

## Furiosa: 기존 규칙을 출발점으로 고정

공개 `furiosa-ai/furiosa-opt` main은 `9b9cf0fdc78df00cdc430eae725a5ad9084a735e`, release 0.8.1이다. 이번 파일럿의 기존 pin과 같다. 다음은 해당 commit의 직접 확인 범위다. `[실측: 소스]`는 명령 실행 성공을 뜻하지 않는다.

| 원문 | 확인한 내용 | 설계에서 바뀌는 판단 |
|---|---|---|
| [Makefile](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/Makefile#L24-L67) | check/clippy는 workspace·all-targets, fmt는 check-only, test는 release다. `clippy-npu`, mdbook build/test가 별도다. | `[추론]` 기존 target을 재사용하고 검사와 수정, CPU와 NPU, 문서 렌더와 예제 실행을 분리한다. |
| [build.yml](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/.github/workflows/build.yml) | Ubuntu 22.04, 고정 nightly, prebuilt 경로, check/fmt/clippy/machete/test 순서가 있다. | `[추론]` 내부 CI 표준으로 일반화하지 않는다. 첫 CPU 체크포인트에서 공개 검사 묶음을 확인한다. |
| [rust-toolchain.toml](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/rust-toolchain.toml), [rustfmt.toml](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/rustfmt.toml), [clippy.toml](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/clippy.toml) | nightly-2026-05-01, rustfmt/clippy, max_width=120, allow-dbg-in-tests=true, too-many-lines-threshold=1150. | `[추론]` 임의의 80자·전역 pedantic·unwrap 금지 규칙을 덧씌우지 않는다. |
| [Cargo.toml](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/Cargo.toml), [Cargo.lock](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/Cargo.lock) | 현재 workspace와 기대 cfg, 추적된 lockfile이 존재한다. `--all-features`는 공개 Makefile의 공통 명령이 아니다. | `[추론]` 지원 backend/feature를 명시하고 lockfile을 보존한다. `--locked` 추가는 파일럿의 재현 정책이며 기존 Makefile 옵션으로 쓰지 않는다. |
| [prebuilt 다운로드](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/.github/actions/download-released-libraries/action.yml), [mapping build.rs](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-mapping/build.rs#L28-L75) | CI는 SHA256SUMS를 검사한다. build.rs의 LOCAL_PREBUILT 경로는 파일을 복사하며, 일반 다운로드는 checksum 확인과 선택적 attestation 경로가 있다. | `[추론]` 로컬 prebuilt를 쓰더라도 출처·tag·target·전체 SHA를 준비 담당자가 검증한다. checksum 일치를 출처 인증으로 부르지 않는다. |
| [binary_add_tests.rs](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/tests/binary_add_tests.rs#L6-L28), [kernel-validation.md](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/docs/src/quick-start/kernel-validation.md) | 실제 `test_binary_add_2048`는 고정 seed와 별도 host 덧셈 결과를 비교한다. 검증 문서는 정적 compile, CPU 값, NPU 실행, schedule을 구분한다. | `[추론]` 이 검사를 무변경 smoke 후보로 쓴다. double-buffering용 새 테스트는 구현할 산출물이며 기존 실행 결과가 아니다. |

과거 SWMAP의 0.4.0 workspace 수·backend 명칭은 날짜가 다른 기록이다. 이번 명령의 근거는 위 0.8.1 pin이다. 공개 driver stub을 내부 Compiler 소스로 해석하지 않는다.

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

## 실험·PR 설계의 추가 원문

- [SPRINT §3.1](https://arxiv.org/html/2506.05745v2), [LATS](https://arxiv.org/html/2310.04406v3): 작업 의존성·결과 동기화와 상태 복원 조건. 성능 수치를 이 실험에 대입하지 않는다.
- [Tree-of-Concerns](https://arxiv.org/pdf/2608.20777): 논문 비평의 쟁점 분해를 후속 E2 검토에 제한적으로 참고한다.
- [DoRA v2 §3.2·4](https://arxiv.org/html/2402.09353v2): 문단 전개를 참고하며 학습 방법의 이식은 아니다.
- [Nebius VM 종류](https://docs.nebius.com/compute/virtual-machines/types), [Sandbox overview](https://docs.tokenfactory.nebius.com/sandboxes/overview): 제품 안내이며 실제 할당·계정 접근의 증거는 아니다.
- [GitHub branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches): required check가 skipped/neutral도 허용한다는 점, strict up-to-date와 stale approval 처리. 저장소의 실제 설정은 API 응답으로 별도 확인한다.
- [GitHub pull_request event](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request): 기본 test merge checkout과 head/base revision을 구분한다.

외부 소스·논문·전사 전체를 vendoring하지 않는다. 이 저장소의 자체 서술과 코드는 개인 연구이며 FuriosaAI나 Dioxus의 공식 정책을 대변하지 않는다.
