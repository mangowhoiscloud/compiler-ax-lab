# Double-buffering 테스트 계약: 그룹별 출력과 경계를 구별한다

이 문서는 공개 테스트 예제의 허용 변경·수치 의무·재현 절차를 정합니다. 실행 결과와 미완료 상태는 [README의 검증 상태](../../README.md#검증-상태)에 모읍니다. 이 예제의 통과를 별도 A/B·NPU·사람 채택 결과로 사용하지 않으며, 문서 정리는 동결된 실험 요구를 변경하지 않습니다.

## 1. 목적과 허용 변경

고정 `rolled`, `software_pipelined`, `unrolled`가 같은 입력에서 그룹별 기대 출력을 만드는지 검사합니다. 제품 결함 수정이나 kernel 최적화가 아니라 정상 구현과 공개 의도 오류를 구별하는 host 테스트 보강입니다. 허용 변경은 다음 두 새 파일입니다.

- `furiosa-opt-examples/tests/double_buffering_tests.rs` ← [SDK 테스트](../../examples/furiosa-double-buffering/tests/double_buffering_tests.rs)
- `furiosa-opt-examples/tests/support/double_buffering_reference.rs` ← [입력·독립 oracle·판정기 검사](../../examples/furiosa-double-buffering/tests/support/double_buffering_reference.rs)

kernel·runtime·macro·build script·dependency·lock·unsafe·FFI·API 변경이 필요하면 중단하고 범위를 재합의합니다. 세 구현과 현재 shape를 유지하며 홀수 Group 지원을 추가하지 않습니다. 오류 patch는 별도 checkout에서만 적용합니다. 공개 oracle와 출력 수준 판정기는 독립 최종 평가의 보호 판정기가 아닙니다. [품질 계약](../quality.md), [작업 권한](../../AGENTS.md)

## 2. 고정 소스와 입출력

대상은 `furiosa-opt` v0.8.1, commit `9b9cf0fdc78df00cdc430eae725a5ad9084a735e`, `nightly-2026-05-01`입니다. [고정 README](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/README.md)의 x86-64 Linux host·호환 GLIBC·native 의존성을 준비하고 source/lock/toolchain/native tag·hash·라이선스를 기록합니다.

[공통 정의](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering.rs#L5-L13)는 `Tok=16, Red=64, Out=8, Group=20, Pairs=10`입니다. 세 함수의 논리 입출력 타입은 같습니다.

| 데이터 | 타입·shape | 원자료 크기 |
|---|---|---:|
| activation | `bf16[16,64]` | 2 KiB |
| weight | `bf16[20,8,64]` | 20 KiB |
| output | `bf16[16,20,8]` | 5 KiB |

원소당 2바이트인 원자료 합계는 27 KiB입니다. layout·정렬·중간 버퍼·host 복사·oracle·빌드 메모리는 제외하므로 VM 요구량이나 최대 RSS가 아닙니다. 출력 flatten 인덱스는 `(t*20+g)*8+o`이며 `out[t,g,o] = sum_r A[t,r]*W[g,o,r]`를 요구합니다.

## 3. 데이터 이동과 구현별 의무

| 구현·고정 원문 | 소스상의 그룹 처리 | 확인할 의무 |
|---|---|---|
| [rolled](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/rolled_kernel.rs#L19-L43) | 그룹 `g`의 weight를 TRF에 적재하고 같은 output view에 기록 | 모든 입력·출력 그룹 대응 |
| [software_pipelined](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/software_pipelined_kernel.rs#L19-L64) | `first=pair*2`, `second=first+1`을 각각 적재·계산·기록 | 쌍 내부·쌍 사이·마지막 그룹 대응 |
| [unrolled](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/unrolled_kernel.rs#L19-L44) | `#[unroll]` 그룹 반복으로 각 output view에 기록 | 반복을 펼쳐도 같은 그룹별 값 유지 |

함수는 HBM activation·weight를 `device.tdma`의 `to_dm`으로 옮깁니다. `device.sub`가 그룹 weight를 `begin → fetch → collect → to_trf`로 적재하고, `device.main`이 `contract_outer → contract_packet → contract_time → contract_lane`으로 축약합니다. `cast::<bf16>`·`commit_trim`·`commit_view`를 거쳐 output DM에 기록한 뒤 `to_hbm_view`로 반환합니다. host 테스트가 이를 회수해 독립 기대값과 비교합니다.

mapping은 `Chip=m![1]`, `Cluster=m![Tok / 8 % 2]`, `Slice=m![Tok % 8 # 256]`을 유지합니다. [mapping·DM 이동](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/rolled_kernel.rs#L4-L17)의 소스 관계이지 관측된 NPU 시각·물리 버퍼 배치가 아닙니다. CPU 값 검사는 consumer 완료 전 덮어쓰기나 실제 중첩 성능을 입증하지 않습니다.

## 4. 유한 정수 fixture와 독립 oracle

기대값은 SDK contraction·cast·kernel을 재호출하지 않는 scalar i32 합으로 계산합니다. 입력은 결정적이며 seed가 없습니다. `h(k,r)=(-1)^popcount(k & r)`, `c=8g+o+1`, `k=2o+(g mod 2)`로 둡니다.

| case | 입력 생성식 | 닫힌 기대값·검사 목적 |
|---|---|---|
| `Basis(q)`, q=0,1,2,3 | `A[t,r]=1` iff `r=16q+t`, 나머지 0; `W[g,o,r]=1+((8g+o+17r) mod 251)` | 선택한 weight인 1부터 251까지의 정수; 64개 reduction 위치와 그룹·출력 구별 |
| `SignedDense` | `A[t,r]=h(t,r)`; `W[g,o,r]=(-1)^o*c*h(k,r)` | `t=k`이면 `(-1)^o*64c`, 아니면 0; 부호·축약·상쇄 검사 |
| `Zero` | A는 모두 0, W는 Basis와 같음 | 전체 0; 같은 Device에서 nonzero case 뒤에 실행 |

고정 SDK는 [bf16 피연산자를 f32로 확장](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-std/src/cast.rs#L335-L386)해 축약하고 최종 bf16으로 변환합니다. 일반 실수에는 [합산 순서 차이](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-std/src/backend/mod.rs#L178-L181)가 있으므로 무조건 exact 비교를 적용하지 않습니다. 이 fixture의 Dense 곱과 어떤 순서의 부분합도 정수이고 절댓값은 `64*160=10,240` 이하라 f32에서 정확합니다. 최종 `64c`는 `c≤160`이므로 bf16에서도 정확하며 Basis·Zero도 정확한 범위에 있습니다.

helper는 입력·기대값의 bf16 표현 가능성과 닫힌 식을 따로 대조합니다. SDK 테스트는 축 크기를 확인한 뒤 `HostTensor<bf16>`로 변환하고, 각 variant 안의 같은 Device에서 6개 case를 순서대로 실행합니다. host 결과를 `[Tok,Group,Out]`로 회수해 2,560개 길이를 확인하고 모든 값을 수치적 동등 비교합니다. 유한 기대값에 대한 NaN/Inf는 거부하고 +0/-0은 동등합니다. 일반 실수·NaN 입력·subnormal·반올림 경계·다른 shape는 범위 밖입니다.

`CASE_RESULT`는 variant·case·전체 expected/actual을 출력하고 `CASE_PASS`는 비교 성공 뒤에만 출력합니다. 실패에는 `(t,g,o)`와 두 값을 남깁니다. `--nocapture` 원문과 case별 배열을 보존하며 출력 누락을 성공으로 세지 않습니다. 이 공개 예제의 검사 규모는 세 variant×6 case×2,560개 값이며, 재시도 합산이나 다른 후보에 대한 보편 테스트 수로 사용하지 않습니다.

## 5. 공개 대조군과 실패 판정

helper의 출력 수준 대조군은 그룹 순환·홀수 그룹 누락·group/output 전치·길이 부족·NaN/Inf를 판정기에 직접 넣습니다. 이는 실제 오류 SDK를 실행한 근거가 아닙니다. 정상 구현끼리의 비교나 전체 합계만으로 독립 oracle를 대신하지 않습니다.

[reuse-first-trf.patch](../../examples/furiosa-double-buffering/controls/reuse-first-trf.patch)는 별도 사본의 `software_pipelined`에서 두 번째 그룹이 `second_trf` 대신 `first_trf`를 읽게 하는 공개 의도 오류입니다. 컴파일과 실제 1개 테스트 실행을 확인한 후 `Basis(0), t=0/g=1/o=0`, expected=9·actual=1의 예정된 assertion 실패를 검출로 판정합니다. command exit 101만으로 판정하지 않습니다.

대조군의 revision·위반 요구·독립 확인 근거를 남깁니다. compile error·OOM·runner crash·0 tests·수거 실패는 결함 검출이 아니며, timeout은 미완료입니다. 정상 baseline의 expected를 관측 결과에 맞춰 바꾸지 않습니다. 공개 대조군은 upstream 결함·미지 결함 검출률·에이전트 우월성의 증거가 아니며 보호 평가에 재사용하지 않습니다.

## 6. 재현 절차

1. 호환 환경과 실행 권한을 확인합니다. pin·lock·native를 검증한 정상 checkout에 위 두 파일만 같은 상대경로로 복사하고, jobs=1·테스트 스레드=1·내부 thread 한도·전용 target/cache·시간/출력/자원 상한·회수 담당자를 기록합니다. 기존 `test_binary_add_2048`로 worker 준비를 확인합니다.
2. 아래 명령은 고정 upstream checkout에서 plain Cargo로 실행합니다. 의존성을 미리 준비해야 `--offline`을 사용할 수 있습니다. `--list`도 빌드하며, 목록은 SDK 3개와 helper 2개여야 합니다. 정상·오류 target을 분리하고 source hash·재컴파일 로그·실행 바이너리를 연결해 stale binary를 제외합니다.

```bash
cargo +nightly-2026-05-01 fmt --all -- --check
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-opt-examples --test double_buffering_tests --release -- --list
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-opt-examples --test double_buffering_tests --release -- --nocapture --test-threads=1
cargo +nightly-2026-05-01 clippy --offline --locked -p furiosa-opt-examples --test double_buffering_tests --release -- -D warnings
```

3. SDK 이름은 `test_double_buffering_rolled`, `test_double_buffering_software_pipelined`, `test_double_buffering_unrolled`입니다. helper의 `fixtures_match_closed_forms_and_are_exact_bf16_values`와 `comparison_rejects_wrong_groups_missing_outputs_and_nonfinite_values`는 별도로 집계합니다. 이름·case·전체 값·command/capture exit·source/binary hash가 연결돼야 합니다.
4. 오류 checkout에만 같은 테스트와 공개 patch를 적용하고 위 test 명령에 `test_double_buffering_software_pipelined --exact --nocapture --test-threads=1`을 지정합니다. 정상 컴파일·실제 1개 실행·예정된 값 assertion 실패를 모두 확인합니다. 정상 소스와 lock은 그대로 보존합니다.
5. [공통 필수 검사](../quality.md#품질-검사-순서와-실패-뒤-행동)를 안정 revision에 적용하고, 타겟별 목록과 실행을 대조합니다. 원문·최종 소스·바이너리를 수거해 대조한 뒤 생성 자원만 회수하고 잔존 여부를 확인합니다. 중단 기록과 다른 작업 자료는 보존합니다.

helper만 검사하려면 lab 루트에서 아래 명령을 사용합니다. SDK 의존성이 없는 두 검사이며 host에서의 성공은 SDK API 컴파일·NPU 검증을 뜻하지 않습니다.

```bash
mkdir -p .local/checks
rustc --edition 2024 -D warnings --test examples/furiosa-double-buffering/tests/support/double_buffering_reference.rs -o .local/checks/double-buffering-reference
.local/checks/double-buffering-reference --nocapture
```

## 7. 채택과 해석의 경계

[Python 데모](../../program.md)는 Rust 실행기가 아닙니다. 기존 Cargo·기록·수거 경로를 사용하고, 검사한 revision·실제 명령·실행 수·원문·미완료 사유를 [병합 규약](../merge.md)에 따라 사람이 검토합니다. 통과·사람 채택·PR·병합·릴리스·추가 유료 실행은 별도 상태와 권한입니다.

이 테스트 보강에는 `cargo furiosa-opt compile`, NPU ELF 생성·실장치 실행·schedule 최적화를 자동 추가하지 않습니다. [공식 Kernel Validation](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/docs/src/quick-start/kernel-validation.md#L3-L14)에 맞춰 정적 compile은 번역·mapping/shape, CPU는 실행한 입력의 값, schedule은 계획, NPU는 기록된 장치 조건의 관측으로 구분합니다. target 변경이 필요하면 허용 범위와 검사를 다시 합의합니다.
