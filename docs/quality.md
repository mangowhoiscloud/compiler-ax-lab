# 품질 계약: 통과한 검사가 무엇을 보장하는가

**[추론: 파일럿 적용 기준]** 첫 과제는 double-buffering의 테스트 보강이다. 제품 구현을 임의로 바꾸거나 새 품질 프레임워크를 만드는 과제가 아니다. 기존 코드 관례·명령을 재사용하되, 실행 누락과 잘못된 판정 때문에 정상처럼 보이는 변경을 구별한다. 근거는 [Furiosa·Dioxus·Rust 원문 대장](sources.md)에 있다. 아래 기준은 설계에 반영했으며 Rust 검사·CI 구현은 아직 실행하지 않았다.

### 컨벤션은 기존 구조를 보존하고 변경 이유를 드러내야 한다

- **읽기와 수정 범위:** 작업할 crate의 구현·직접 호출자·기존 테스트·관련 문서를 먼저 확인한다. 첫 과제의 허용 파일은 새 테스트와 필요한 테스트 helper·설명으로 고정한다. kernel·runtime·macro·build script·dependency·평가 코드 변경이 필요하면 중단해 재합의한다. 다른 기능 정리와 대규모 리팩터링을 함께 넣지 않는다.
- **Rust 관례:** 기존 이름·module 경계·오류 타입·helper를 재사용한다. 테스트 이름은 조건과 관측할 동작이 읽히게 쓰고, assertion 실패에는 variant·그룹·출력 위치·expected/actual을 남긴다. 독립 기대값은 검증 대상 kernel이나 동일 helper를 다시 호출해 만들지 않는다.
- **포맷과 lint:** nightly-2026-05-01과 120자 폭, 기존 Clippy 예외를 유지한다. 검사에는 check-only 명령을 사용하고 `--fix`는 후보 수정 단계에서만 허용한다. 전역 pedantic/restriction이나 테스트의 `unwrap` 금지를 새로 강제하지 않는다. 새 blanket allow, warning cap, `#[ignore]`, test 삭제, assertion·오차 완화는 허용하지 않는다. 필요한 예외는 범위·근거·검사 담당자·재검토 조건을 별도 승인한다.
- **버전·의존성:** source pin·Cargo.lock·실제 rustc/Clippy·host triple·GLIBC·native library tag/hash를 함께 기록한다. LOCAL_PREBUILT도 준비 담당자가 출처와 checksum을 확인한다. checksum 일치와 출처 인증은 구분한다. 기존 lockfile은 평가 중 변경하지 않는다.
- **위험한 변경:** 첫 과제에서 새 unsafe·FFI·API 변경은 범위 확대다. 이후 허용하면 소유권·aliasing·수명·정렬·동시성·실패 시 부수효과 중 해당 의무와 표적 검사를 선정한다. `Safety` 주석이나 Miri 통과를 NPU·외부 FFI 안전성의 증명으로 쓰지 않는다.
- **문서·인계:** 변경 목적·보존 동작·버린 대안·검사 결과·미실행 범위를 짧게 남긴다. API가 바뀌면 Errors/Panics/Safety·예제·변경 이력을 맞춘다. 테스트 보강만으로 무관한 changelog나 패키지 버전을 수정하지 않는다.

### 품질 검사 순서와 실패 뒤 행동

아래는 **A/B에 동일하게 고정할 수용 기준**이다. A에도 같은 공개 요구·기존 지침·도구를 제공한다. B에만 조사→변경→검사 근거 정리의 절차 안내를 추가한다. 품질 문턱이나 보호 정답의 차이를 B의 효과로 세지 않는다. [추론]

| 단계 | 검사·증거 | 실패 또는 누락 시 행동 |
|---|---|---|
| Q0 계약·환경 | pin/lock/toolchain/native artifact, 허용 파일·금지 효과, 자원·시간 상한. 무변경 baseline에서 필요한 명령과 테스트 목록 확인 | 준비 실패면 E0/E1 시작 금지. 기존 warning·flaky failure도 사전 기록하며 후보가 숨기지 못하게 한다. |
| Q1 범위·기계 품질 | diff와 새 파일까지 확인; `make fmt`; 표적 cargo check/clippy. 안정 후보에서 `make check`, `make clippy`, `cargo machete` | 원문 diagnostic으로 수정하거나 이관한다. suppression·test 삭제로 통과시키지 않는다. |
| Q2 실제 동작 | release 표적 테스트의 이름·실행 수·seed·입력·expected/actual·exit code. 세 variant의 그룹별 값을 별도 기대값과 비교 | 출력 오류는 반례. 0 tests·조건부 조기 return·누락 로그는 성공에서 제외한다. timeout/OOM의 원인과 비용을 남긴다. |
| Q3 통합·문서 | 안정 revision에서 기존 `make test`. 문서 변경 시 `make mdbook-build`와 해당 예제 실행/`make mdbook-test`; 생성물은 재생성 diff 확인 | workspace 결과와 제외/ignored/NPU 미실행을 분리한다. docs build·파일 생성만으로 실행 성공을 주장하지 않는다. |
| Q4 독립 최종 확인 | 공개 수정 종료 후 snapshot 고정. 보호 정상/의도 오류 구현에서 생성 테스트를 1회 평가; reference·parser·오차는 후보 밖에서 관리 | 정상 오탐/오류 누락/검사 무효를 분리한다. 실패 뒤 수정은 새 실험이다. 보호 로그를 같은 후보의 repair에 반환하지 않는다. |
| Q5 사람의 채택 | 목적·구조·API·테스트 의미·잔여 위험 검토. 필수 검사 목록과 실제 receipt를 같은 candidate revision에 결속 | required check가 없거나 skipped/cancelled이면 완료 불가. 담당자가 이유와 함께 기각/보류한다. PR·병합·릴리스는 별도 승인이다. |

`PASS`, `FAIL`, `INVALID`, `NOT_RUN`을 검사별로 보존하고 timeout은 미완료 사유로 남긴다. 적용하지 않는 검사는 실행 전에 담당자가 근거와 함께 제외한다. 사후 N/A로 바꿔 통과율을 높이지 않는다. 기준 수정은 별도 변경이며 영향받은 A/B 결과를 다시 평가한다. 기존 실패는 baseline 문제부터 해소하거나 사전 예외를 합의한다. [추론]

### 실제 명령과 아직 없는 테스트를 구분한다

다음은 공개 소스에서 확인한 **기존 명령·테스트 이름**이다. 승인된 x86-64 환경과 native dependency 준비 뒤 실행한다. `--list`도 빌드를 유발할 수 있으므로 무비용 조회가 아니다. [실측: 소스·미실행]

```bash
make fmt
cargo test -p furiosa-opt-examples --release --test binary_add_tests -- --list
cargo test -p furiosa-opt-examples --release --test binary_add_tests -- --exact test_binary_add_2048
```

기존 checkpoint 묶음은 `make check`, `make clippy`, `cargo machete`, `make test`다. 공개 Makefile에는 `--all-features`가 없으며 `make test`는 release profile이다. `clippy-npu`는 별도 target으로 이 CPU 파일럿에 자동 추가하지 않는다. Cargo의 `--all-targets`는 모든 feature 조합이나 doctest 검사를 뜻하지 않는다. [실측]

승인 뒤 `CARGO_BUILD_JOBS`, 테스트 스레드, 전용 `CARGO_TARGET_DIR`, 기타 내부 thread pool 한도와 cache 시작 상태를 고정한다. 직접 Cargo 명령에 `--locked`를 추가하는 재현 정책은 기존 Makefile과 구분한다. Make target을 유지할 경우 전후 lockfile hash도 대조한다. lock 변경이 필요한 준비는 A/B 시작 전에 끝낸다. `make mdbook-test`처럼 내부에서 target directory를 지정하는 명령은 해당 경로까지 후보별로 격리한다. [추론]

`double_buffering_tests.rs`는 만들 파일의 **제안명**이다. 실제 생성 뒤 목록에서 발견되고 assertion이 실행되는지 확인한다. 정상 구현에서는 통과하고, 실행 가능한 알려진 오류에서는 의도한 값 비교로 실패해야 한다. compile error나 runner crash는 오류 검출이 아니다. 테스트 보강 과제는 정상 baseline을 깨뜨릴 필요가 없으며, 오류 대조군을 구별하는지가 핵심이다. [추론]

### Dioxus에서 옮길 것은 탐색 실패를 작은 회귀 검사로 남기는 방식이다

Dioxus의 현재 코드는 구조화된 동작을 incremental renderer와 fresh rebuild 결과로 비교하고, 축소한 실패 입력을 일반 테스트에서 strict 조건으로 재생한다. 긴 libFuzzer 탐색은 별도 실행이다. 전체 corpus의 coverage 재생은 비교 결과를 의도적으로 버리는 코드가 있어 그 성공을 정확성 통과로 읽을 수 없다. [실측: 위 원문 대장]

첫 파일럿은 고정 경계 입력으로 시작한다. 후속 탐색은 원본 실패→축소 입력→원인 확인→일반 회귀 테스트로 남긴다. 테스트 수·coverage 비율만 목표로 삼지 않는다. 후보가 생성한 expected를 그대로 갱신하거나 검사 중 corpus를 덮어쓰지 않는다. parser/macro 변경에는 적법·부적법 입력과 예상 diagnostic, buffer 변경에는 값·수명·완료 순서의 검사를 선정한다. host에서 확인할 의무와 장치가 필요한 의무는 구분한다. [추론]

Fuzzing, Miri, sanitizer, 광범위 dependency/보안 감사는 해당 위험과 실행 가능성이 확인될 때 추가한다. 첫 과제에는 새 framework·custom lint·CI 서비스가 필요하지 않다. 장기 탐색·공급망 정책·실기기 검증을 E1의 효과에 합치지 않는다. [실험 계약](experiment.md), [판단 컨텍스트](context.md)


PR 준비·통합 revision 확인·병합 후 검사 절차는 [병합 규약](merge.md)을 따릅니다. 이 문서의 Q0–Q5는 컴파일러 실험 기준이며 현재 lab 문서 CI의 PASS와는 별개입니다.
