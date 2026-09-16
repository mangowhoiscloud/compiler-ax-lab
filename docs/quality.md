# 품질 계약: 통과한 검사가 무엇을 보장하는가

이 문서는 이 lab의 코드 관례·검사·채택 기준입니다. 공급사의 내부 정책을 뜻하지 않습니다. 실행 결과 집계는 [README의 검증 상태](../README.md#검증-상태), 작업 권한은 [AGENTS](../AGENTS.md), PR 인계는 [병합 규약](merge.md)을 따릅니다. 문서 정리는 이미 동결한 개별 실행 계약을 변경하지 않습니다.

### 언어별 정적 검사와 CI 분기

실행 코드는 표준 라이브러리를 유지하고 검사 도구만 개발 의존성으로 고정합니다. 검사 중 자동 수정하지 않으며, 포맷 변경도 diff로 검토합니다.

| 대상 | 고정 도구·실행 | 검출 범위와 제외 범위 |
|---|---|---|
| Python 4개 파일 | [pyproject.toml](../pyproject.toml), [requirements-dev.txt](../requirements-dev.txt): Ruff lint/format, mypy; Python 3.9·3.12에서 unittest | 미정의 이름·import·포맷·함수 타입 및 16개 동작 회귀. JSON 경계의 `Any`는 기존 런타임 검증이 담당하며 완전한 schema 타입 증명은 아님 |
| JavaScript·검사 설정 | [Biome](../biome.json), [package lock](../package-lock.json): `npm ci --ignore-scripts`, `npm run check` | 권장 lint·포맷·import 정리. TypeScript 타입 검사나 의미 보존 증명은 아님 |
| Rust 파일·patch | nightly-2026-05-01 rustfmt, 독립 reference의 `clippy-driver --test -D warnings`와 2개 테스트; 고정 upstream에서 `git apply --check` | SDK 테스트 파일의 구문/포맷, 독립 reference의 타입·Clippy·동작, patch 적용 가능성. SDK 통합 타입·링크·parser 실행·NPU 검사는 별도 |
| Markdown·공개 경계 | `node scripts/check.mjs` | allowlist·로컬 링크/anchor·민감정보 패턴·스킬 진입 경로·필수 CI 규약. 외부 URL의 가용성이나 문장의 사실 여부는 별도 검토 |
| GitHub Actions YAML·shell | actionlint v1.7.12; runner의 ShellCheck가 있으면 함께 사용 | YAML·식·job 의존성과 shell 진단. 실제 클라우드 실행 결과를 대신하지 않음 |

Python 검사는 별도 환경에서 다음 명령으로 재현합니다. Python 3.9는 기존 호환성 하한의 회귀 검사이며 새 운영 환경의 권고 버전이 아닙니다.

```bash
python3 -m venv .local/static-env
.local/static-env/bin/python -m pip install -r requirements-dev.txt
.local/static-env/bin/python -m ruff check scripts tests examples/group-reduction
.local/static-env/bin/python -m ruff format --check scripts tests examples/group-reduction
.local/static-env/bin/python -m mypy
.local/static-env/bin/python -m unittest discover -s tests -v
npm ci --ignore-scripts
npm run check
node scripts/check.mjs
```

실제 분기는 [quality.yml](../.github/workflows/quality.yml)이 실행하고 [check.mjs](../scripts/check.mjs)가 선택·집계합니다. `lab-system`은 항상 실행합니다. `.py`는 Python, `.mjs`·npm/Biome 설정은 JavaScript, `.rs`·`.patch`는 Rust 검사를 선택합니다. 공통 지침·품질/CI 설정·알 수 없는 경로는 모두 선택합니다. README·병합 설명·PR 템플릿만 바뀌면 언어 job은 선택하지 않습니다. 삭제·이름 변경은 이전/새 경로를 모두 비교하고, 비교 base를 읽지 못하면 전체 검사를 실행합니다.

필수 check 이름은 기존 `lab-ci`를 유지합니다. 선택된 모든 job은 `success`여야 하며, 계획에서 선택하지 않은 언어 job의 `skipped`만 허용합니다. 필수 job의 실패·취소·예상하지 않은 생략·누락된 계획은 거절합니다. 선택/집계의 정상·거절 사례는 `node scripts/check.mjs --self-test`로 재현합니다. 검사 파일 변경도 전체 job을 실행하며 `continue-on-error`로 실패를 숨기지 않습니다.

새 도구나 규칙은 담당 언어의 코드·설정·CI·이 표를 함께 갱신합니다. CI는 instruction 준수나 모델의 문제 해결 성능을 측정하지 않습니다. SDK 전체 검사는 아래 별도 명령과 환경 계약을 따릅니다.

### 입력과 수치 계약

검사 전에 shape·dtype·계산식·입력 범위·오차·독립 oracle을 고정합니다. [Double-buffering 계약](kernels/double-buffering.md)은 유한 정수 입력의 수치 의무를, [아래 parser 계약](#mapping-parser)은 AST와 오류 위치를 정합니다. 미정값·누락 증거를 성공으로 채우거나 CPU 결과를 NPU 근거로 사용하지 않습니다.

### 컨벤션은 기존 구조를 보존하고 변경 이유를 드러내야 한다

- 해당 crate의 구현·직접 호출자·기존 테스트·문서를 읽고 허용 파일과 보존할 동작을 정합니다. 범위 확대는 중단 후 재합의하며, 무관한 리팩터링을 섞지 않습니다.
- 기존 이름·module·오류 타입·helper를 재사용합니다. 테스트 이름은 조건과 동작을 드러내고, 실패에는 입력·위치·expected/actual 또는 원문 diagnostic을 남깁니다. 기대값을 검증 대상 kernel이나 동일 계산 helper로 만들지 않습니다.
- `nightly-2026-05-01`, 120자 폭과 기존 Clippy 예외를 유지합니다. 검사는 check-only이며 `--fix`는 후보 수정 단계에서만 사용합니다. 전역 pedantic/restriction이나 테스트의 `unwrap` 금지를 추가하지 않습니다.
- 새 blanket allow·warning cap·`#[ignore]`·테스트 삭제·assertion/오차 완화로 통과시키지 않습니다. 예외는 범위·근거·담당자·재검토 조건을 별도 승인합니다.
- source pin·Cargo.lock·실제 rustc/Clippy·host triple·GLIBC·native tag/hash·라이선스를 기록합니다. `LOCAL_PREBUILT`도 출처와 checksum을 확인하며, hash 일치를 출처 인증으로 보지 않습니다. 평가 중 lockfile을 바꾸지 않습니다.
- 허용된 unsafe·FFI·API 변경에만 소유권·aliasing·수명·정렬·동시성·실패 효과의 관련 의무와 검사를 추가합니다. `Safety` 주석이나 Miri 통과는 NPU·외부 FFI 안전성의 증명이 아닙니다.
- 목적·보존 동작·선택 이유·버린 대안·검사 결과·미실행 범위를 인계합니다. API 변경은 Errors/Panics/Safety·예제·변경 이력을 맞추되, 테스트 보강으로 무관한 버전·changelog를 수정하지 않습니다.

### 품질 검사 순서와 실패 뒤 행동

A/B에는 같은 공개 요구·도구·수용 기준을 고정하고 추가 작업 절차만 분리합니다. 보호 정답이나 품질 문턱의 차이를 절차의 효과로 세지 않습니다. 운영자 문서 전체를 후보에게 제공하지 않습니다.

| 단계 | 필요한 검사·증거 | 실패 또는 누락 시 행동 |
|---|---|---|
| 계약·환경 | pin/lock/toolchain/native, 허용 파일·금지 효과, 자원·시간 상한, 무변경 baseline의 명령·테스트 목록 | 준비 실패면 후보 비교를 시작하지 않습니다. 기존 warning·flaky failure도 사전 기록합니다. |
| 범위·코드 품질 | 새 파일까지 diff 확인, `make fmt`, 표적 check/Clippy; 안정 후보의 `make check`, `make clippy`, `cargo machete` | 원문 diagnostic으로 수정하거나 이관하며 suppression으로 숨기지 않습니다. |
| 출력 동작 | release 표적 이름·실행 수·seed·입력·독립 기대값·실제 값·exit | 값 불일치는 반례입니다. 0 tests·조기 return·누락 로그는 성공이 아닙니다. |
| 통합·문서 | 안정 revision의 `make test`; upstream 문서 변경 시 `make mdbook-build`와 해당 예제/`make mdbook-test`; 생성물 재생성 diff | ignored·제외·NPU 미실행을 분리합니다. lab 문서는 `node scripts/check.mjs`로 검사하며 문서 빌드를 실행 성공으로 세지 않습니다. |
| 독립 최종 평가 | 공개 수정 종료와 양쪽 snapshot 고정 후, 동결한 정상/의도 오류 평가를 각 1회 수행; reference·결과 parser·오차는 후보 밖에서 관리 | 정상 오탐·오류 누락·검사 무효를 분리합니다. 보호 로그를 같은 후보의 repair에 반환하지 않으며 이후 수정은 새 실험입니다. |
| 사람의 채택 | 목적·구조·API·테스트 의미·잔여 위험, 같은 candidate revision의 필수 receipt | required check 누락·skipped·cancelled은 완료가 아닙니다. 채택·PR·병합·릴리스는 별도 판단입니다. |

검사별 `PASS / FAIL / INVALID / NOT_RUN`과 중단 원인을 보존합니다. timeout은 미완료이며, 적용 제외는 실행 전에 근거와 담당자를 정합니다. 사후 N/A로 통과율을 높이지 않습니다. baseline 실패는 먼저 해결하거나 사전 예외를 합의하고, 기준 수정은 별도 검토 후 영향을 받은 결과를 재평가합니다.

### CPU smoke의 관측성과 기록 규격

기존 명령·로그·수거 경로를 재사용합니다. 아래 기록명은 운영자 자료의 역할이며, 새 프레임워크나 관측 서비스가 필요하다는 뜻은 아닙니다.

| 기록 | 생산자가 남길 내용 | 검토자가 확인할 것 |
|---|---|---|
| 계약 | version·run ID·승인 범위·source/lock/toolchain/native·argv/cwd·seed/shape/dtype/oracle·상한 | 실제 환경과 조건 일치; 계정·자원 ID는 비공개로 보존 |
| 단계 원문 | stdout/stderr·명령·UTC 시작/종료·`time -v`·원래 command exit·capture exit | 원문 diagnostic과 실행 수; PTY는 재생용이며 원문이나 스트림 간 전역 순서를 대신하지 않음 |
| 자원 | cgroup/VM 한도·thread 설정·5초 `vmstat`·전후 `df/du`와 단위 | 프로세스 최대 RSS와 전체 peak 구분; `vmstat` 첫 CPU 행은 부팅 이후 평균이고 이후는 표본 |
| 수거 목록 | 상대경로·역할·bytes·SHA-256·필수 여부·present/missing/partial·원본 대조 | 필수 증거의 완전성; hash는 바이트 식별이지 의미·순서·정확성 증명이 아님 |
| 판정·회수 | passed/failed/ignored/filtered·STOP 원인·수거 결과·생성 자원 삭제와 재조회 | 검사 종료와 운영 종료를 별도로 확인; 다른 작업의 자원과 기록은 보존 |

출력 수집에도 유한 대기를 적용합니다. 자식이 pipe를 유지하거나 수거가 실패하면 불완전으로 남깁니다. 준비 실패와 worker 미시작도 구분하고, 실행 중 수거본과 삭제 전 최종 원본을 대조합니다. 네트워크 단절·강제 종료 사이의 미수거 구간을 무손실로 주장하지 않습니다. exit 137만으로 OOM을 단정하지 않으며 cgroup·kernel·controller 근거를 함께 봅니다.

[Dioxus의 실패 입력·원문 오류](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/packages/fuzz/src/case.rs#L119)와 [예상/실제 진단](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/packages/fuzz/src/harness.rs#L224)처럼 재현할 증거를 남깁니다. coverage 수나 비교 결과를 버리는 재생을 정확성 통과로 읽지 않고, 검사 중 expected·corpus를 덮어쓰지 않습니다. fuzzing·Miri·sanitizer는 관련 위험과 실행 가능성이 있을 때만 추가합니다.

### 실제 명령과 실행 증거

기록을 인계할 때 run/attempt·후보/부모 후보·실제 command와 결과를 연결합니다. 관측 순서와 tool call/result의 짝은 원본에 있는 식별자로 보존하고, 없는 시각·순서·ID는 추정해 채우지 않습니다. 현재 Python 데모의 attempt 기록은 검사 receipt이며 전체 에이전트 대화 trajectory가 아닙니다. 별도 agent transcript가 있다면 제한된 locator로 연결합니다.

원본은 생산 시스템의 기록이고 정규화본·요약은 파생본입니다. 원문 발생 시각·수집 시각·공개 시각, 범위 완전성과 재생 가능성을 각각 구분합니다. 잘린 출력·누락 pair·확인하지 못한 구간은 명시합니다. 외부 공개용 마스킹은 원본과 별도 digest로 기록하고 비공개 프롬프트·인증정보·숨겨진 reasoning은 공개하지 않습니다. 수거 목록과 hash만 남은 receipt를 원본의 복구 가능한 백업으로 보지 않습니다.

호환 x86-64 Linux에서 [고정 upstream README](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/README.md)의 의존성을 먼저 준비합니다. source pin은 `9b9cf0fdc78df00cdc430eae725a5ad9084a735e`입니다. jobs·테스트/내부 스레드·전용 `CARGO_TARGET_DIR`·cache 시작 상태·시간/출력/자원 상한을 고정합니다. `--list`도 빌드를 유발합니다.

```bash
cargo +nightly-2026-05-01 fmt --all -- --check
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-opt-examples --release --test binary_add_tests -- --list
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-opt-examples --release --test binary_add_tests -- --exact test_binary_add_2048 --test-threads=1
```

[기존 smoke](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/tests/binary_add_tests.rs)는 seed=42, 두 `i8[2048]` 입력과 `i32[2048]` 출력, host i32 원소별 덧셈 oracle을 사용합니다. 정확한 1개 통과·0 failed·0 ignored·1 filtered와 command/capture 성공·lock 무변경을 확인합니다. 성공 배열은 출력하지 않으므로 `NOT_EMITTED`로 두고 없는 값을 생성하지 않습니다.

위 명령은 plain Cargo CPU 경로입니다. [upstream Dockerfile](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/Dockerfile)의 기본 `cargo furiosa-opt` entrypoint에는 단순히 `test`를 붙이지 말고 Cargo 또는 shell을 명시합니다. [Makefile](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/Makefile)의 `make test`는 release 검사이며 `clippy-npu`는 별도입니다. `--all-targets`는 모든 feature 조합·doctest를 뜻하지 않습니다. 직접 명령의 `--locked` 정책과 Makefile을 구분하고, 내부에서 지정한 mdbook target 경로도 격리합니다.

복사한 파일의 오래된 mtime 때문에 이전 바이너리가 재사용될 수 있습니다. 소스 hash·복사 방식·재컴파일 로그·실행한 바이너리를 연결하고, 불명확하면 재빌드하거나 새 target을 사용합니다. 목록과 실행을 타겟별로 대조하며 자식 프로세스의 테스트 요약을 중복 합산하지 않습니다. `compile_fail` doctest의 기대 거절, ignored, CPU에서 0개인 NPU 전용 target도 구별합니다.

### Mapping parser

[테스트 patch](../examples/furiosa-mapping-parser/tests.patch)는 같은 pin의 [문법](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-mapping-macro/src/parser/parser.lalrpop)·[AST/parser](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-mapping-macro/src/parser/mod.rs)·[진단](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-mapping-macro/src/parser/diagnostic.rs)의 계약을 검사합니다. `parse_mapping`과 `parse_index`의 수용 여부뿐 아니라 정확한 AST 또는 오류 문구·byte range를 확인합니다. index 입력에는 `: value`를 붙이며 assignment 1개와 값 토큰 `value`를 보존해야 합니다.

| 공통 입력 | `Stride(Symbol(A), extent)`에서 보존할 extent |
|---|---|
| `A / 4` | `Const(Lit(4))` |
| `A / {N}` | `Const(Const(tokens N))`; 외곽 중괄호 제외 |
| `A / B` | `Axis(B)` |
| `A / (B, C)` | `Mapping(Pair(Symbol(B), Symbol(C)))`; 좌우 순서 유지 |

`[B]`는 두 진입점에서 `Symbol(B)`인 atom이지만 `A / [B]`는 Extent로 허용하지 않습니다. 두 모드 모두 `4..5`의 `[`와 아래 문구를 반환해야 합니다. `A /`의 EOF는 `2..3`의 마지막 `/`를 지목하고 mapping/index 모드를 구분합니다. 범위는 0-based, 끝 미포함 byte range입니다.

```text
unexpected token `[`; expected an axis name, an integer, a braced Rust expression, or `(`
unexpected end of mapping expression; expected an axis name, an integer, a braced Rust expression, or `(`
unexpected end of index expression; expected an axis name, an integer, a braced Rust expression, or `(`
```

변경은 `diagnostic.rs`의 `cfg(test)` 안에 helper 2개·테스트 6개를 추가하는 것으로 제한하며 기존 6개를 유지합니다. 제품 문법·AST·진단·dependency·lock은 바꾸지 않습니다. 정상 baseline 6개와 후보 12개의 목록·실행 수, fmt·표적 release Clippy를 각각 확인합니다.

```bash
git apply --check /path/to/compiler-ax-lab/examples/furiosa-mapping-parser/tests.patch
git apply /path/to/compiler-ax-lab/examples/furiosa-mapping-parser/tests.patch
cargo +nightly-2026-05-01 fmt --all -- --check
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-mapping-macro --lib --release -- --list
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-mapping-macro --lib --release -- --nocapture --test-threads=1
cargo +nightly-2026-05-01 clippy --offline --locked -p furiosa-mapping-macro --all-targets --release -- -D warnings
```

별도 checkout과 target에만 [공개 오류 patch](../examples/furiosa-mapping-parser/controls/accept-bracket-extent.patch)를 추가합니다. 같은 test 명령에 `parser::diagnostic::tests::brackets_are_atoms_not_extents --exact`를 지정하고, 컴파일 성공 후 실제 1개 검사의 예정된 assertion 실패를 확인합니다. 이 대조군은 mapping assertion에서 먼저 실패하므로 index의 독립 오류 검출까지 주장하지 않습니다. compile error·0 tests·OOM·누락 증거는 검출이 아닙니다.

이 사례는 토큰화 가능한 DSL 입력의 AST와 `syn::Error`를 검사합니다. macro 확장 전체·Rust 타입·mapping 실행·NPU lowering의 증명이 아니며, 공개 의도 오류는 upstream 결함이나 보호 평가 자료가 아닙니다. 정적 compile·CPU 값·schedule·장치 측정·사람 채택은 각각의 근거로 판단합니다. [병합 규약](merge.md)
