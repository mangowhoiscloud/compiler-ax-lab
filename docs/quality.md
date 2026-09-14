# 품질 계약: 통과한 검사가 무엇을 보장하는가

**[추론: 파일럿 적용 기준]** 이 문서는 과제에 공통으로 적용할 코드 관례·검사·채택 기준을 정한다. 기존 명령을 재사용하되 실행 누락과 잘못된 판정 때문에 정상처럼 보이는 변경을 구별한다. 첫 과제의 동작·허용 변경·소스·실행 분기는 [double-buffering 테스트 계약](kernels/double-buffering.md)에 둔다. 근거는 [Furiosa·Dioxus·Rust 원문 대장](sources.md)에 있다. 2026-09-14 무변경 Rust CPU smoke는 완료했으며, 아래 전체 품질 검사·원격 PR CI·A/B는 아직 실행하지 않았다. [실행 결과](experiment.md#무변경-cpu-smoke-실행-결과)

### 입력과 수치 계약

커널별 shape·dtype·계산식·공개 경계 입력과 독립 oracle의 미확정 조건은 [double-buffering 테스트 계약](kernels/double-buffering.md)에 옮겼습니다. 기존 링크는 이 절을 계속 사용할 수 있습니다. 공통 원칙은 입력·수치 비교를 검사 전에 고정하고, 미정값이나 host 검사 결과를 임의의 성공·NPU 근거로 채우지 않는 것입니다.

### 컨벤션은 기존 구조를 보존하고 변경 이유를 드러내야 한다

- **읽기와 수정 범위:** 작업할 crate의 구현·직접 호출자·기존 테스트·관련 문서를 먼저 확인한다. 허용 파일과 보존할 동작은 해당 과제 계약으로 고정하며 범위 확대가 필요하면 중단해 재합의한다. 다른 기능 정리와 대규모 리팩터링을 함께 넣지 않는다.
- **Rust 관례:** 기존 이름·module 경계·오류 타입·helper를 재사용한다. 테스트 이름은 조건과 관측할 동작이 읽히게 쓰고, assertion 실패에는 입력·위치·expected/actual 또는 원문 diagnostic을 남긴다. 독립 기대값은 검증 대상 kernel이나 동일 helper를 다시 호출해 만들지 않는다.
- **포맷과 lint:** nightly-2026-05-01과 120자 폭, 기존 Clippy 예외를 유지한다. 검사에는 check-only 명령을 사용하고 `--fix`는 후보 수정 단계에서만 허용한다. 전역 pedantic/restriction이나 테스트의 `unwrap` 금지를 새로 강제하지 않는다. 새 blanket allow, warning cap, `#[ignore]`, test 삭제, assertion·오차 완화는 허용하지 않는다. 필요한 예외는 범위·근거·검사 담당자·재검토 조건을 별도 승인한다.
- **버전·의존성:** source pin·Cargo.lock·실제 rustc/Clippy·host triple·GLIBC·native library tag/hash를 함께 기록한다. LOCAL_PREBUILT도 준비 담당자가 출처와 checksum을 확인한다. checksum 일치와 출처 인증은 구분한다. 기존 lockfile은 평가 중 변경하지 않는다.
- **위험한 변경:** unsafe·FFI·API 변경을 허용하는 과제에서는 소유권·aliasing·수명·정렬·동시성·실패 시 부수효과 중 해당 의무와 표적 검사를 선정한다. `Safety` 주석이나 Miri 통과를 NPU·외부 FFI 안전성의 증명으로 쓰지 않는다.
- **문서·인계:** 변경 목적·보존 동작·버린 대안·검사 결과·미실행 범위를 짧게 남긴다. API가 바뀌면 Errors/Panics/Safety·예제·변경 이력을 맞춘다. 테스트 보강만으로 무관한 changelog나 패키지 버전을 수정하지 않는다.

### 품질 검사 순서와 실패 뒤 행동

아래는 **A/B에 동일하게 고정할 수용 기준**이다. A에도 같은 공개 요구·기존 지침·도구를 제공한다. B에만 조사→변경→검사 근거 정리의 절차 안내를 추가한다. 품질 문턱이나 보호 정답의 차이를 B의 효과로 세지 않는다. [추론]

| 단계 | 검사·증거 | 실패 또는 누락 시 행동 |
|---|---|---|
| 계약·환경 확인 | pin/lock/toolchain/native artifact, 허용 파일·금지 효과, 자원·시간 상한. 무변경 baseline에서 필요한 명령과 테스트 목록 확인 | 준비 실패면 검사 병렬도 보정과 에이전트 작업 절차 비교를 시작하지 않는다. 기존 warning·flaky failure도 사전 기록하며 후보가 숨기지 못하게 한다. |
| 범위·코드 품질 검사 | diff와 새 파일까지 확인; `make fmt`; 표적 cargo check/clippy. 안정 후보에서 `make check`, `make clippy`, `cargo machete` | 원문 diagnostic으로 수정하거나 이관한다. suppression·test 삭제로 통과시키지 않는다. |
| 출력 동작 검사 | release 표적 테스트의 이름·실행 수·seed·입력·expected/actual·exit code. 해당 과제의 동작을 독립 기대값과 비교 | 출력 오류는 반례. 0 tests·조건부 조기 return·누락 로그는 성공에서 제외한다. timeout/OOM의 원인과 비용을 남긴다. |
| 통합·문서 검사 | 안정 revision에서 기존 `make test`. 문서 변경 시 `make mdbook-build`와 해당 예제 실행/`make mdbook-test`; 생성물은 재생성 diff 확인 | workspace 결과와 제외/ignored/NPU 미실행을 분리한다. docs build·파일 생성만으로 실행 성공을 주장하지 않는다. |
| 독립 최종 검사 | 공개 수정 종료 후 snapshot 고정. 보호 정상/의도 오류 구현에서 생성 테스트를 1회 평가; reference·parser·오차는 후보 밖에서 관리 | 정상 오탐/오류 누락/검사 무효를 분리한다. 실패 뒤 수정은 새 실험이다. 보호 로그를 같은 후보의 repair에 반환하지 않는다. |
| 사람의 채택 검토 | 목적·구조·API·테스트 의미·잔여 위험 검토. 필수 검사 목록과 실제 receipt를 같은 candidate revision에 연결 | required check가 없거나 skipped/cancelled이면 완료 불가. 담당자가 이유와 함께 기각/보류한다. PR·병합·릴리스는 별도 승인이다. |

`PASS`, `FAIL`, `INVALID`, `NOT_RUN`을 검사별로 보존하고 timeout은 미완료 사유로 남긴다. 적용하지 않는 검사는 실행 전에 담당자가 근거와 함께 제외한다. 사후 N/A로 바꿔 통과율을 높이지 않는다. 기준 수정은 별도 변경이며 영향받은 A/B 결과를 다시 평가한다. 기존 실패는 baseline 문제부터 해소하거나 사전 예외를 합의한다. [추론]

### CPU smoke의 관측성과 기록 규격

2026-09-14 실행 전 점검에서 터미널 끝 30줄만 출력하던 경로, 실패 뒤 자원 기록 부재, 프로세스 RSS와 VM 전체 메모리의 혼동 가능성을 확인했습니다. 기존 worker에 원문 스트림 보존·수거 확인을 더했고, 공개 Rust 테스트와 oracle은 바꾸지 않았습니다. 정상 종료·명령 실패·timeout·자식이 pipe를 잡고 있는 네 경우를 실제 Linux에서 검사한 뒤 smoke를 실행했습니다. 아래는 이번 lab의 기록 규약이며 공급사의 내부 규격이 아닙니다.

| 기록 | 생산자와 필드 | 읽는 주체와 판단 |
|---|---|---|
| `contract.json` | 운영자: format version, run ID, 승인 범위, source/lock/toolchain/native pin, 명령 argv·cwd, seed·shape·dtype·oracle, 시간·자원 한도 | 실행 담당자: 조건 일치 여부. 계정·자원 ID는 비공개 디렉터리에만 보존합니다. |
| 단계별 원문 | worker: stdout/stderr, 실제 명령, `time -v`, 원래 exit code, 로그 수집 exit code. `stages.tsv`는 UTC 시작/종료와 단계 이름을 연결합니다. | 검토자: 실패한 명령·panic·실행 수 확인. PTY는 재생용이며 원문 파일이나 stdout/stderr 사이의 전역 발생 순서를 대신하지 않습니다. |
| 자원 기록 | worker: 환경·cgroup 한도·thread 설정, 5초 간격 `vmstat`, 실행 전후 `df`·`du`와 단위 | 운영자: 관측된 메모리·디스크 압력 판단. `vmstat` 첫 CPU 행은 부팅 이후 평균이며 나머지는 표본입니다. `time -v`의 최대 RSS는 동시 프로세스 RSS 합이나 VM 전체 peak가 아닙니다. |
| `artifacts.json` | 수거 담당자: 상대경로, 역할, bytes, 전체 SHA-256, 필수 여부, `present/missing/partial`, 원격 원본과 로컬 대조 결과 | 판정 담당자: 필요한 증거를 실제로 읽을 수 있는지 확인. hash는 원본 식별자이며 의미·순서·결과를 압축하지 않습니다. |
| 판정·회수 기록 | 운영자: 테스트 PASS/FAIL/INVALID/NOT_RUN, 실제 passed/failed/ignored/filtered 수, 중단 원인, 수거 결과, 생성한 instance·disk·임시 key/보안그룹의 삭제 및 재조회 | 사용자: 검사 결과와 운영 종료를 별도로 확인. 필수 증거가 없으면 완전한 통과로 인계하지 않습니다. |

1. **실행 전:** 기존 `test_binary_add_2048`의 seed는 42, 두 입력은 각각 `[2048]` i8, 출력은 `[2048]` i32입니다. oracle은 호스트에서 i32로 변환한 입력의 원소별 덧셈입니다. source·lock·실제 Rust 버전과 native 파일·라이선스·출처를 보존합니다. 성공 배열 전체는 `NOT_EMITTED`로 두며 로그에 없는 값을 만들지 않습니다. [고정 테스트](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/tests/binary_add_tests.rs)
2. **실행 중:** 전체 stdout/stderr를 파일과 터미널에 함께 남깁니다. 출력 수집에도 유한 대기를 적용하고, 명령이 끝나도 자식 프로세스가 pipe를 잡고 있으면 기록 불완전으로 종료합니다. 사전 점검·설치 실패는 controller 원문에 남기며 worker가 시작하지 않았다는 사실을 구별합니다.
3. **실행 후:** 명령 exit=0만 보지 않고 정확한 테스트 이름, 1 passed·0 failed·0 ignored·1 filtered out, lockfile 무변경, 수집·파일 대조 결과를 확인합니다. timeout·OOM·취소·수거 실패는 각각 원래 상태를 보존합니다. OOM은 137만으로 단정하지 않고 kernel diagnostic 등 추가 근거를 찾습니다.
4. **유실의 경계:** 실행 중에는 원문 파일을 수시로 수거하고 최종 묶음을 삭제 전에 다시 대조합니다. 네트워크 단절과 강제 종료 사이의 미수거 구간은 `partial`로 남깁니다. 전원 손실까지 무손실이라고 보장하지 않습니다. 이번에는 후보 코드 생성이 없으므로 모델 토큰 사용량·내부 추론 trajectory를 CPU 실행 데이터로 채우지 않습니다.

Dioxus에서 참고한 것은 [실패 입력·step·원문 오류](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/packages/fuzz/src/case.rs#L119), [예상/실제 snapshot 진단](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/packages/fuzz/src/harness.rs#L224), [사용자 출력과 파일 로그의 분리](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/packages/cli/src/logging.rs#L244)입니다. 같은 코드의 쓰기 오류 무시나 CLI 중단의 Success 처리를 lab 판정으로 옮기지 않습니다. 공개 설정을 읽은 근거이며 Dioxus CI가 실제 완료됐다는 기록은 아닙니다. 관측 서비스를 새로 설치하거나 단일 JSON 안에 원문 전체를 넣지 않습니다.

### 실제 명령과 아직 없는 테스트를 구분한다

다음은 공개 소스에서 확인한 **기존 명령·테스트 이름**이다. 2026-09-14 목록·지정 테스트 명령에 고정 toolchain과 `--locked`를 적용해 실제 실행했다. `make fmt`와 전체 workspace 검사는 이번 smoke 범위에 없었다. `--list`도 빌드를 유발하므로 무비용 조회가 아니다. 정확한 argv와 결과는 [실행 기록 요약](experiment.md#무변경-cpu-smoke-실행-결과)에 둔다.

```bash
make fmt
cargo test -p furiosa-opt-examples --release --test binary_add_tests -- --list
cargo test -p furiosa-opt-examples --release --test binary_add_tests -- --exact test_binary_add_2048
```

위 명령은 **plain Cargo CPU 경로**입니다. 고정 upstream Dockerfile의 기본 `ENTRYPOINT`는 `cargo furiosa-opt`이므로, 해당 이미지를 사용할 때는 entrypoint를 `cargo` 또는 명시한 shell로 바꿉니다. 기본 entrypoint에 `test`만 전달해 CPU 검사라고 기록하지 않습니다. [Dockerfile·테스트 원문](sources.md)

기존 `test_binary_add_2048`는 `assert_eq!`로 독립 덧셈 결과를 비교하며 성공한 원소의 expected/actual 전체를 출력하지 않습니다. 이 준비 검사의 receipt에는 고정 테스트 소스·hash, 정확한 테스트 이름·실행 수, libtest 결과·exit code를 연결해 **해당 assertion의 통과**를 기록합니다. 로그에 없는 실제 값은 생성하지 않습니다. [새 커널 테스트](kernels/double-buffering.md)의 입력·수치 증거 계약과 이 무변경 smoke의 관측 범위는 구분합니다.

기존 checkpoint 묶음은 `make check`, `make clippy`, `cargo machete`, `make test`다. 공개 Makefile에는 `--all-features`가 없으며 `make test`는 release profile이다. `clippy-npu`는 별도 target으로 이 CPU 파일럿에 자동 추가하지 않는다. Cargo의 `--all-targets`는 모든 feature 조합이나 doctest 검사를 뜻하지 않는다. [실측]

승인 뒤 `CARGO_BUILD_JOBS`, 테스트 스레드, 전용 `CARGO_TARGET_DIR`, 기타 내부 thread pool 한도와 cache 시작 상태를 고정한다. 직접 Cargo 명령에 `--locked`를 추가하는 재현 정책은 기존 Makefile과 구분한다. Make target을 유지할 경우 전후 lockfile hash도 대조한다. lock 변경이 필요한 준비는 A/B 시작 전에 끝낸다. `make mdbook-test`처럼 내부에서 target directory를 지정하는 명령은 해당 경로까지 후보별로 격리한다. [추론]

복사한 수정 파일이 기존 산출물보다 오래된 mtime을 가지면 Cargo가 이전 바이너리를 재사용할 수 있다. 이번 로컬 실행에서 이 정황을 발견해 해당 결과를 최종 근거에서 제외하고, 변경 파일의 시각을 갱신해 실제 재컴파일한 뒤 재검사했다. warm cache를 사용할 때는 **소스 hash뿐 아니라 복사 방식·빌드 로그·실행 바이너리와 source의 연결**을 확인한다. 불명확하면 해당 변경을 재빌드하거나 새 target을 사용한다. [관측과 조치](kernels/double-buffering.md#8-로컬-docker-실행-결과)

`cargo furiosa-opt compile`은 선택 kernel의 번역·mapping/shape를 확인하는 별도 검사입니다. host 값 검사와 정적 compile·target 산출물·장치 검사 중 무엇이 필요한지는 해당 과제 계약으로 정합니다. CPU smoke에 NPU ELF 생성용 cross toolchain이나 장치 실행을 자동으로 포함하지 않습니다.

### 별도 과제 후보: mapping 문법과 진단의 일치

**상태: 공개 소스 기반 과제 준비이며 미실행입니다.** 기존 double-buffering 과제와 수치·판정 단위를 공유하지 않습니다. 목적은 mapping 문법, 생성된 AST, 오류 위치·안내가 같은 계약을 따르는지 검사하는 것입니다. [고정 문법·진단과 리뷰 근거](sources.md#공개-agent-지침과-리뷰에서-채택한-규칙)

1. **대상:** 같은 `9b9cf0f`의 `furiosa-mapping-macro/src/parser/`를 읽습니다. 허용 변경은 해당 crate의 테스트와 필요한 테스트 helper·설명부터 정합니다. 제품 문법·진단 구현 수정이 필요하면 별도 bug-fix 범위로 합의합니다. 여기서 DSL parser는 검증 대상이며 후보 밖의 보호 판정기가 아닙니다.
2. **정상·오류를 함께 확인:** 개발용 예시 `A / 4`, `A / {N}`, `A / B`, `A / (B, C)`는 parse 성공뿐 아니라 기대 AST를 확인합니다. `A /`, `A / [B]`는 예상 거절 위치와 diagnostic을 대조합니다. 오류 문자열 snapshot 갱신만으로 완료하지 않습니다. 문법상 불법, 적법하지만 미지원, 도구 준비 실패를 구별합니다.
3. **실행 준비:** 표적 명령 후보는 `cargo test -p furiosa-mapping-macro --lib --release`입니다. 실제 test 목록·선택 수·toolchain·lockfile·명령 한도를 고정한 후 호환 환경에서 무변경 baseline부터 확인합니다. macro crate의 직접 의존성만 보고 전체 workspace 또는 ARM host가 검증됐다고 쓰지 않습니다. 이번 문서는 명령 성공을 기록한 receipt가 아닙니다.
4. **판정:** 기대 거절을 검사하는 테스트는 해당 진단·위치 assertion이 통과해야 합니다. 무관한 Cargo build 실패를 거절 성공으로 세지 않습니다. 정상 입력의 잘못된 거절과 불법 입력의 잘못된 수용을 별도로 기록합니다. 정적 device compile·CPU 값·NPU 검사는 이 parser 검사와 합산하지 않습니다.
5. **비교 전 조건:** 공개된 진단 수정과 위 예시는 개발용입니다. 미공개 대조군·입력·판정 단위·평가 개입·담당자를 별도로 고정하고 기존 실험 계약을 개정하기 전에는 A/B를 시작하지 않습니다. 현재 `trial.py --task furiosa`의 중단 경로를 우회하거나 Python 데모 판정을 Rust 결과에 적용하지 않습니다.

### Dioxus에서 옮길 것은 탐색 실패를 작은 회귀 검사로 남기는 방식이다

Dioxus의 현재 코드는 구조화된 동작을 incremental renderer와 fresh rebuild 결과로 비교하고, 축소한 실패 입력을 일반 테스트에서 strict 조건으로 재생한다. 긴 libFuzzer 탐색은 별도 실행이다. 전체 corpus의 coverage 재생은 비교 결과를 의도적으로 버리는 코드가 있어 그 성공을 정확성 통과로 읽을 수 없다. [실측: 위 원문 대장]

첫 파일럿은 고정 경계 입력으로 시작한다. 후속 탐색은 원본 실패→축소 입력→원인 확인→일반 회귀 테스트로 남긴다. 테스트 수·coverage 비율만 목표로 삼지 않는다. 후보가 생성한 expected를 그대로 갱신하거나 검사 중 corpus를 덮어쓰지 않는다. parser/macro 변경에는 적법·부적법 입력과 예상 diagnostic, buffer 변경에는 값·수명·완료 순서의 검사를 선정한다. host에서 확인할 의무와 장치가 필요한 의무는 구분한다. [추론]

Fuzzing, Miri, sanitizer, 광범위 dependency/보안 감사는 해당 위험과 실행 가능성이 확인될 때 추가한다. 첫 과제에는 새 framework·custom lint·CI 서비스가 필요하지 않다. 장기 탐색·공급망 정책·실기기 검증을 에이전트 작업 절차 비교의 효과에 합치지 않는다. [실험 계약](experiment.md), [판단 컨텍스트](context.md)


PR 준비·통합 revision 확인·병합 후 검사 절차는 [병합 규약](merge.md)을 따릅니다. 이 문서의 품질 검사·채택 절차는 컴파일러 실험 기준이며 현재 lab 문서 CI의 PASS와는 별개입니다.
