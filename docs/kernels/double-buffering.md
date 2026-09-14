# Double-buffering 테스트 계약: 그룹별 출력과 경계를 구별한다

상태: **2026-09-15 KST 로컬 Docker amd64에서 SDK 테스트 3개·18 case·46,080개 값 비교가 통과했고, 공개 오류 대조군 1개는 예상한 수치 assertion으로 검출했습니다. 고정 nightly의 fmt·표적 Clippy도 통과했습니다.** [실행 결과](#8-로컬-docker-실행-결과)를 준비 절차와 구분합니다. 이번 작업은 공개 단일 변경 파일럿이며 A/B 비교나 NPU 측정이 아닙니다. 추가 원격 실행은 [재개 조건](../experiment.md#시행-보류와-재개-조건)과 비용·시간 승인을 별도로 확인합니다.

## 1. 목적과 허용 변경

고정된 `rolled`, `software_pipelined`, `unrolled` 구현이 같은 입력에서 그룹별 기대 출력을 만드는지 검사할 테스트를 보강합니다. 목적은 생성 테스트가 정상 동작과 사전에 확인한 출력 오류를 구별하는지 확인하는 것입니다. 현재 제품 결함을 발견했거나 커널을 최적화한 상태는 아닙니다. [설계]

후보 checkout의 허용 변경은 다음 두 새 파일입니다. lab의 원본을 고정 source에 같은 내용으로 배치했습니다.

- `furiosa-opt-examples/tests/double_buffering_tests.rs` ← [SDK 테스트](../../examples/furiosa-double-buffering/tests/double_buffering_tests.rs)
- `furiosa-opt-examples/tests/support/double_buffering_reference.rs` ← [입력·독립 oracle·판정기 검사](../../examples/furiosa-double-buffering/tests/support/double_buffering_reference.rs)

kernel·runtime·macro·build script·dependency 변경, 새 unsafe·FFI·API 추가가 필요하면 중단하고 범위를 다시 합의합니다. 축과 세 구현은 유지하며 홀수 `Group`이나 다른 shape 지원을 추가하지 않습니다. 오류 대조군 patch는 별도 checkout에서만 적용하며 후보 수정에 포함하지 않습니다. 이번 oracle는 공개 테스트의 일부이고, 독립 최종 평가의 보호 판정기와는 다릅니다.

공통 Rust 관례와 필수 검사는 [품질 계약](../quality.md), A/B 배정·예산·독립 최종 검사는 [실험 계약](../experiment.md)이 정합니다. 후보에게는 같은 동작·입력·수치·검사 요구를 동결해 추출하며, 이 MD 전체나 운영자 절차를 그대로 주입하지 않습니다. B에만 적용할 작업방법을 공통 제품 요구로 섞지 않습니다.

## 2. 고정 소스와 입력·출력

대상은 공개 `furiosa-opt` 0.8.1, commit `9b9cf0fdc78df00cdc430eae725a5ad9084a735e`입니다. `nightly-2026-05-01`과 호환 host·native artifact 준비는 [환경 계약](../experiment.md#작업과-환경)을 따릅니다. 아래는 2026-09-14에 고정 소스를 읽어 확인한 내용이며 실행 결과가 아닙니다. [소스 확인]

| 원문 | 그룹 처리 방식 | 확인할 출력 관계 |
|---|---|---|
| [double_buffering.rs](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering.rs#L5-L13) | 세 구현을 공개하고 `Tok=16, Red=64, Out=8, Group=20, Pairs=10`을 정의합니다. | 세 구현의 논리 입출력 축을 고정합니다. |
| [rolled_kernel.rs](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/rolled_kernel.rs#L19-L43) | `g`마다 weight 한 그룹을 TRF에 적재하고 같은 `g`의 output view에 기록합니다. | 입력 그룹과 출력 그룹의 대응을 확인합니다. |
| [software_pipelined_kernel.rs](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/software_pipelined_kernel.rs#L19-L64) | `first=pair*2`, `second=first+1`의 weight를 각각 적재하고 각각의 output view에 기록합니다. | 쌍 내부·쌍 사이와 마지막 그룹의 대응을 확인합니다. |
| [unrolled_kernel.rs](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/unrolled_kernel.rs#L19-L44) | `#[unroll]`을 붙인 그룹 반복으로 각 output view에 기록합니다. | 반복을 펼쳐도 같은 그룹별 값이 유지되는지 확인합니다. |

| 데이터 | 논리 타입·shape | 원자료 크기 |
|---|---|---:|
| activation | `bf16[16,64]` | 2 KiB |
| weight | `bf16[20,8,64]` | 20 KiB |
| output | `bf16[16,20,8]` | 5 KiB |

bf16 원소당 2바이트로 계산한 합계는 **27 KiB**입니다. 실제 저장 layout·정렬·중간 버퍼·host 복사·oracle·빌드 메모리는 포함하지 않습니다. 세 구현의 입출력 signature는 같은 타입이며, 이 크기를 VM 메모리 요구량이나 최대 RSS로 사용하지 않습니다. [계산]

## 3. 데이터 이동과 값을 기록하는 주체

다음은 세 함수에 공통인 소스상의 처리 관계입니다. `Device`의 필드와 tensor view가 담당하는 동작을 설명하며, NPU에서 관측한 실행 시각·중첩·물리 버퍼 배치를 뜻하지 않습니다. [소스 확인]

| 순서 | 입력과 처리 주체 | 출력·다음 소비자 |
|---|---|---|
| 1 | 함수가 HBM의 activation·weight를 빌리고 `device.tdma`를 사용하는 `to_dm`을 호출합니다. | 함수 안의 DM tensor가 activation과 전체 weight를 보관합니다. |
| 2 | `device.sub`가 선택한 그룹의 weight view를 `begin → fetch → collect → to_trf`로 처리합니다. | 해당 그룹의 `TrfTensor`를 `device.main`의 contraction이 읽습니다. |
| 3 | `device.main`이 activation view를 읽고 `contract_outer → contract_packet → contract_time → contract_lane`으로 축약합니다. | 그룹별 계산 결과를 `cast::<bf16>`와 `commit_trim`에 전달합니다. |
| 4 | `commit_view`가 해당 그룹의 가변 output view에 기록합니다. | 함수가 소유한 output DM tensor에 그룹별 결과가 모입니다. |
| 5 | `to_hbm_view`가 DM 결과를 새 HBM result에 기록합니다. | 함수가 HBM result를 반환하며, 새 host 테스트는 이를 회수해 독립 기대값과 비교해야 합니다. |

실제 mapping은 `Chip=m![1]`, `Cluster=m![Tok / 8 % 2]`, `Slice=m![Tok % 8 # 256]`입니다. 이식할 때 새 배치나 주소를 추정하지 않습니다. [공통 mapping과 DM 이동](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/rolled_kernel.rs#L4-L17), [공식 데이터 이동·contraction 설명](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/docs/src/quick-start/kernel-design.md#L145-L157)

`software_pipelined`가 두 weight 그룹을 노출하는 코드와 장치가 실제로 두 작업을 중첩하는 것은 다른 주장입니다. CPU 값 검사는 잘못된 그룹을 읽거나 기록하는 오류를 확인할 수 있지만, 실제 장치에서 consumer가 끝나기 전 버퍼가 덮이는지와 중첩 성능은 입증하지 않습니다.

## 4. 정수 oracle로 검증할 수 있는 입력을 먼저 고정한다

논리적으로 요구하는 식은 `out[t,g,o] = sum_r activation[t,r] * weight[g,o,r]`입니다. 모든 `t`, `g`, `o`의 값을 검사하며 세 구현끼리만 비교해 같은 오류를 놓치지 않도록 합니다. kernel이나 동일 계산 helper의 재호출로 기대값을 만들지 않습니다. [설계]

고정 SDK는 bf16 피연산자를 f32로 넓혀 contraction하고, 대상 함수는 축약 뒤 bf16으로 변환합니다. CPU 병렬 축약은 합산 순서를 바꿀 수 있으므로 일반 실수에 무조건 exact 비교를 쓰지 않습니다. 이번에는 **입력·곱·중간 합·최종 bf16 변환이 정확한 정수 집합**을 골라 그룹 처리 오류와 반올림 차이를 구분합니다. [ContractionCast](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-std/src/cast.rs#L335-L386), [피연산자 확장](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-std/src/engine/contraction/outer/mod.rs#L151-L159), [합산 순서 주의](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-std/src/backend/mod.rs#L178-L181), [출력 변환](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/rolled_kernel.rs#L28-L39)

생성식은 결정적이며 seed가 없습니다. `h(k,r)=(-1)^popcount(k & r)`, `c=8g+o+1`, `k=2o+(g mod 2)`로 둡니다. [구현·닫힌 식 대조 검사](../../examples/furiosa-double-buffering/tests/support/double_buffering_reference.rs)

| 입력 | 생성식 | 기대 결과·검사 목적 |
|---|---|---|
| `Basis(q)`, `q=0..3` | `A[t,r]=1` iff `r=16q+t`, 나머지 0. `W[g,o,r]=1+((8g+o+17r) mod 251)` | 결과는 선택한 weight이며 1..251입니다. 네 입력이 64개 reduction 위치를 모두 선택하고 그룹·출력 위치를 구별합니다. |
| `SignedDense` | `A[t,r]=h(t,r)`, `W[g,o,r]=(-1)^o*c*h(k,r)` | `t=k`이면 `(-1)^o*64c`, 나머지 0입니다. 부호가 섞인 축약·상쇄를 검사합니다. |
| `Zero` | A는 모두 0, W는 Basis와 같음 | 결과는 모두 0입니다. 동일 Device에서 nonzero 입력 이후 실행합니다. |

Dense의 곱은 정수이고 어떤 순서의 부분합도 절댓값이 `64*160=10,240` 이하이므로 f32에서 정확합니다. 최종 `64c`는 `c≤160`이라 bf16으로도 정확히 표현됩니다. Basis·Zero도 같은 조건을 만족합니다. 독립 oracle는 scalar i32 합으로 계산하며 SDK contraction·cast를 재사용하지 않습니다. 별도 검사에서 생성한 입력과 모든 기대값의 bf16 표현 가능성 및 위 닫힌 식을 대조했습니다. [로컬 검사 통과]

비교는 **2,560개 전체 길이 확인 후 수치적 동등 비교**입니다. 유한 기대값에 대한 NaN/Inf를 거부하고 +0/-0은 동등하게 취급합니다. 일반 실수·NaN 입력·subnormal·반올림 경계와 다른 shape는 이번 입력 범위가 아닙니다. 세 구현×6종×2,560개인 **46,080개 비교를 최종 정상 실행에서 확인했습니다.** 이전 시도와 재검사를 합쳐 비교 수를 늘리지 않습니다.

SDK 테스트는 `CASE_RESULT`에 variant·case·전체 expected/actual을 출력하고, 비교 성공 뒤에만 `CASE_PASS`를 남깁니다. 실패 메시지는 `(t,g,o)`와 두 값을 포함합니다. `--nocapture` 원문을 보존하고 출력 누락을 성공으로 세지 않습니다. 실제 비용·시간·worker 상한은 원격 실행 전에 고정하며 이전 무변경 smoke 승인을 자동 연장하지 않습니다.

## 5. 공개 실패 가설과 최소 확인

다음은 소스의 그룹 처리 방식에서 도출한 **공개 개발용 가설**이며 upstream 결함이 아닙니다. 출력 수준 판정기 검사와 실제 SDK 오류 커널 실행은 별도 근거로 남깁니다. 독립 최종 검사의 비공개 입력·변이·판정 구현은 이 문서에 두지 않습니다.

| 가설 | 필요한 공개 검사 | 놓치지 말아야 할 조건 |
|---|---|---|
| 다른 그룹의 weight 또는 output view를 사용하면 그룹 대응이 바뀔 수 있습니다. | 그룹별로 구별 가능한 입력으로 각 `(t,g,o)`를 독립 기대값과 비교합니다. | 그룹마다 같은 값인 입력이나 전체 합계만 비교해서 순열 오류를 가리지 않습니다. |
| 쌍의 두 번째 처리나 마지막 처리를 빠뜨리면 일부 그룹 결과가 누락될 수 있습니다. | 첫·마지막 그룹, 쌍 내부와 쌍 사이 경계를 포함해 세 variant의 전체 출력을 확인합니다. | 현재 짝수 `Group=20`을 유지하며 홀수 그룹 지원을 새 요구로 추가하지 않습니다. |
| host 측 shape·축 순서 해석이나 bf16 변환을 잘못하면 올바른 kernel을 오탐하거나 오류를 놓칠 수 있습니다. | 입력 생성·출력 인덱싱·oracle를 별도로 검토하고 확정한 수치 계약으로 비교합니다. | 세 kernel끼리 같은 결과를 내는 것만으로 독립 검증을 대신하지 않습니다. |

공개 오류 대조군을 준비할 때는 ID·revision·위반 요구와 독립 확인 근거를 남깁니다. 오류 구현은 컴파일되고 의도한 출력 차이를 만들어야 하며, compile error·OOM·runner crash를 결함 검출로 세지 않습니다. 테스트 보강 과제는 정상 baseline을 깨뜨릴 필요가 없습니다. 정상/오류 구별의 집계 단위는 [실험 계약](../experiment.md#결함-검출의-판정-단위)을 따릅니다.

- **로컬에서 확인:** 정답 출력의 그룹 순환, 홀수 그룹 누락, group/output 축 전치, 길이 부족, NaN/Inf를 판정기가 거부했습니다. 이것은 잘못된 출력 배열을 넣은 검사이며 SDK 커널을 실행한 결과가 아닙니다.
- **실제 SDK에서 검출:** [reuse-first-trf.patch](../../examples/furiosa-double-buffering/controls/reuse-first-trf.patch)는 `software_pipelined`의 두 번째 그룹이 `second_trf` 대신 `first_trf`를 읽게 합니다. 별도 checkout의 컴파일이 성공했고, 정확히 1개 테스트를 실행해 `Basis(0), t=0/g=1/o=0`, expected=9·actual=1에서 실패했습니다. 종료 코드 101만 본 것이 아니라 원문 assertion과 전체 출력도 확인했습니다. 이 공개 patch를 보호 평가용으로 다시 사용하지 않습니다.

## 6. helper 단독 검사와 SDK 실행 절차를 구분한다

### 6.1 로컬에서 실행한 검사

lab 루트에서 실행합니다. 이미 설치된 Rust만 사용하며 결과 바이너리는 Git 제외 경로에 둡니다.

```bash
mkdir -p .local/checks
rustc --edition 2024 -D warnings --test \
  examples/furiosa-double-buffering/tests/support/double_buffering_reference.rs \
  -o .local/checks/double-buffering-reference
.local/checks/double-buffering-reference --nocapture
```

macOS arm64·Homebrew rustc 1.97.0에서 **2 passed / 0 failed**를 확인했습니다. 동일 helper를 SDK integration test에서도 사용하지만 이 단독 실행은 SDK API의 컴파일 호환성을 검사하지 않습니다. native library가 필요한 SDK 실행은 x86-64 Linux에서 진행합니다.

### 6.2 이번 공개 단일 변경에 적용한 실행 절차

1. **정상 checkout을 고정합니다.** pin과 Cargo.lock hash를 확인하고 허용한 두 파일만 복사합니다. toolchain·native artifact·jobs=1·검사 스레드=1·전용 cache·시간/출력/자원 상한과 회수 담당자를 기록합니다. 기존 `test_binary_add_2048`를 다시 실행해 이번 worker의 준비 상태를 확인합니다.
2. **테스트를 발견하고 실행합니다.** 목록은 SDK 테스트 3개(`test_double_buffering_rolled`, `test_double_buffering_software_pipelined`, `test_double_buffering_unrolled`)와 helper 검사 2개입니다. 이번 실행은 아래 명령에 `--offline`, 명시한 출력 형식을 더해 수행했습니다. 실제 목록이 다르거나 0 tests면 중단합니다.

```bash
cargo +nightly-2026-05-01 test --locked -p furiosa-opt-examples \
  --test double_buffering_tests --release -- --list
cargo +nightly-2026-05-01 test --locked -p furiosa-opt-examples \
  --test double_buffering_tests --release -- --nocapture --test-threads=1
```

3. **정상 통과를 해석합니다.** SDK 3개·18 case·46,080개 수치 비교와 helper 2개를 분리해 집계합니다. 전체 출력·assertion·exit code·source hash가 연결돼야 합니다. 정상 구현 실패는 원인을 조사하며 expected를 결과에 맞춰 갱신하지 않습니다.
4. **별도 오류 checkout을 검사합니다.** 동일 두 테스트 파일과 공개 patch만 적용하고 `test_double_buffering_software_pipelined --exact --nocapture --test-threads=1`로 하나를 선택합니다. 정상 컴파일·실제 1개 실행·예정된 값 assertion 실패가 있어야 검출입니다. compile error·OOM·runner 실패는 `INVALID`, timeout은 미완료로 남깁니다. 정상 checkout을 오류 실험에 재사용하지 않습니다.
5. **인계하고 회수합니다.** 정상/오류 checkout의 diff·원문·수거 대조와 [공통 필수 검사](../quality.md#품질-검사-순서와-실패-뒤-행동)를 묶습니다. fmt·Clippy·통합 검사는 실제 실행한 것만 기록하고 사람의 채택을 별도로 받습니다. 생성 자원 삭제·잔존 여부까지 확인합니다.

기존 Python `trial.py`를 Rust 실행기로 포장하지 않습니다. 평범한 Cargo 명령과 기존 기록·수거 경로를 사용합니다. A/B의 배정·보호 입력·독립 평가 접근·비용 계약은 이후 별도 확정하며 이번 공개 변경의 성공으로 대신하지 않습니다.

## 7. 증거가 허용하는 판단

필수 기록은 source·candidate revision, 실제 명령과 환경, variant·case ID·선택/실행된 테스트 수, 수치 비교 근거·원문 diagnostic, 미완료 사유입니다. 기존 로그와 Git diff를 사용하며 실행하지 않은 값이나 로그를 생성하지 않습니다. 검토자는 이 증거와 수정 범위·가독성·유지비를 보고 채택·반려·보류합니다. 검사 통과와 사람 승인, 실제 PR 병합·릴리스는 별도 상태입니다. [품질 계약](../quality.md), [병합 규약](../merge.md)

이번 과제는 kernel을 바꾸지 않는 host 테스트 보강입니다. `cargo furiosa-opt compile`을 새 필수 후보 검사로 추가하지 않으며 NPU ELF 생성·실장치 실행·schedule 최적화도 포함하지 않습니다. 정적 compile은 번역·mapping/shape, CPU 검사는 실행한 host 입력의 값, schedule은 고정 조건의 계획, NPU 실행은 기록된 장치 조건의 관측을 각각 확인합니다. 실제 target 변경이 필요하면 계약과 필요한 검사를 다시 합의합니다. [공식 Kernel Validation](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/docs/src/quick-start/kernel-validation.md#L3-L14)

## 8. 로컬 Docker 실행 결과

run `docker-cpu-validation-20260914-q7dp65jv`의 최종 정상 실행은 2026-09-15 KST에 완료했습니다. Apple Silicon의 Docker Desktop에서 Ubuntu 24.04 amd64를 실행했고, 실행 중인 rustc의 `/proc` 경로로 Rosetta를 확인했습니다. 컨테이너 한도는 2 CPU·6 GiB·추가 swap 없음이며 Cargo jobs=1, Rayon threads=2, test threads=1을 사용했습니다. image digest는 `sha256:224a1869083a311ef3f13648a154ba79832fbef6364d31493642ca03082da254`입니다. 의존성 준비 후 네트워크를 끊고 `--offline --locked`로 검사했습니다. [실행]

| 검사 | 확인한 결과 | 범위 |
|---|---|---|
| 기존 `test_binary_add_2048` | 1 passed, 0 failed, 1 filtered | 이 worker에서 기존 CPU assertion이 동작합니다. |
| 정상 double-buffering | SDK 3개와 helper 2개 통과; 18개 고유 case·46,080개 값 일치 | 원문 expected/actual 전체를 닫힌 식으로 다시 계산해 대조했습니다. |
| 형식·표적 lint | 고정 nightly의 `cargo fmt --all -- --check`, 표적 `cargo clippy ... -- -D warnings` exit 0 | 전체 workspace test·Clippy 완료를 뜻하지 않습니다. |
| 공개 오류 대조군 | 컴파일 성공; 1개 실행·의도한 assertion 실패, 4 filtered; command exit 101·capture exit 0 | `Basis(0)`의 `(t=0,g=1,o=0)`에서 expected=9·actual=1. 출력 2,560개도 오류 가설과 대조했습니다. |

첫 baseline 빌드·목록 명령은 **22분 42.80초**, 최대 RSS는 **3,868,016 KiB**였습니다. 최종 정상 값 검사 명령은 warm cache에서 **18.68초**였으며 Cargo 시작과 출력 기록 시간이 포함됩니다. 프로세스 최대 RSS를 컨테이너 전체 peak로 읽지 않으며, Rosetta 수치를 AWS native x86이나 NPU 성능과 직접 비교하지 않습니다.

과정에서 두 가지를 수정했습니다. 먼저 helper의 짝수 판별을 Clippy가 권하는 `is_multiple_of(2)`로 고쳤고 입력·기대값·오차 기준은 유지했습니다. 이후 `docker cp`가 원래 mtime을 보존해 Cargo가 수정 전 바이너리를 재사용한 정황을 발견했습니다. 값이 일치해도 그 결과를 수정본의 실행 증거로 채택하지 않고 별도 보존했습니다. 변경 파일의 시각을 갱신한 뒤 실제 재컴파일·소스 hash·바이너리 시각을 확인하고 최종 값을 다시 검사했습니다. **출력 일치와 실행한 소스의 일치는 각각 확인해야 합니다.**

오류 checkout은 정상 테스트와 lock을 유지한 채 kernel 한 줄만 바꿨습니다. 컴파일·목록 명령은 9분 14.01초, 실제 오류 검사 명령은 1.73초였습니다. 정상 커널 checkout은 변경되지 않았고, 정상·오류 바이너리를 각각 보존해 SHA-256을 대조했습니다. 알려진 한 오류를 구별한 결과이므로 미지의 결함 검출률이나 에이전트 작업 절차의 우월성을 추정하지 않습니다.

원문 stdout/stderr·단계별 exit/capture exit·GNU time·PTY 재생 기록·최종 소스와 두 바이너리는 Git 제외 실행 폴더에 보존합니다. 검증기는 누락·중복 case, 잘린 배열, 수치 오류, 수집 실패, 컴파일 오류를 거부하는 자체 검사 8개를 통과했습니다. 이 검증기 통과만으로 소스/바이너리 연결이나 사람의 채택을 대신하지 않습니다. 로컬 작업은 container UID 0으로 실행했으며, 보호 평가·악의적 후보 격리가 입증된 환경으로 주장하지 않습니다.

수거한 두 바이너리와 오류 소스의 hash를 원본과 대조한 뒤 이번 worker·probe 컨테이너 3개를 삭제하고 잔존 0개를 확인했습니다. 원문 기록·이미지는 보존했고 기존 Kubernetes 컨테이너 3개는 중지 상태로 유지했습니다. 새 클라우드 자원·유료 API·원격 PR 변경·병합은 수행하지 않았습니다.

## 9. 후속 workspace 검사와 중단 기록

run `compiler-followup-20260915-iGJZ5Q`는 같은 upstream pin·Cargo.lock과 공개 double-buffering 테스트 두 파일을 새 worker에서 검사했습니다. Ubuntu 24.04 amd64/Rosetta·2 CPU·6 GiB·Cargo jobs=1이며 의존성 준비 뒤 네트워크를 끊었습니다. 앞 run의 결과나 cache가 있다는 이유로 전체 검사를 통과 처리하지 않았습니다.

| 명령·단계 | 실제 결과 |
|---|---|
| 기록기 회귀·`cargo fmt --all -- --check` | command/capture exit 0 |
| `cargo check --offline --locked --workspace --all-targets` | PASS, command/capture exit 0; 6분 04초 |
| `cargo clippy --offline --locked --workspace --all-targets -- -D warnings` | PASS, command/capture exit 0; 1분 41초 |
| `cargo test --offline --locked --workspace --release --no-run` | INTERRUPTED: host 여유 공간 6 GiB 하한 도달. 완료 exit/capture receipt 없음 |
| 전체 workspace test | NOT_RUN: release 빌드가 완료되지 않음 |

2026-09-14 16:35:35 UTC에 여유 공간이 6,240,176 KiB로 내려가 감시 스크립트가 이 worker만 중지했습니다. `docker exec`는 137로 끝났지만 Docker `OOMKilled=false`였으며, 이를 컴파일러 오류나 메모리 OOM으로 분류하지 않았습니다. 중단 전 원문과 부분 산출물은 보존했습니다. 전체 빌드를 다시 시작하거나 시간 상한을 늘리지 않고, 이번 worker의 재생성 가능한 SDK cache만 정리한 뒤 같은 한도 안에서 작은 [parser 검사](../quality.md#mapping-parser)를 완료했습니다.

parser의 정상·오류 바이너리와 소스·원문을 대조한 뒤 후속 worker를 중지·삭제했습니다. Kubernetes 노드 세 개는 사용자 확인에 따라 중지하고 restart policy를 `no`로 변경했습니다. 다른 작업의 이미지·volume·소스·채팅과 이전 실행 증거는 삭제하지 않았습니다. lab 원격 PR CI는 [별도 기록](../merge.md#현재-구현과-제안의-경계)이며, Rust 전체 검사·NPU 실행·병합·릴리스 완료를 대신하지 않습니다.
