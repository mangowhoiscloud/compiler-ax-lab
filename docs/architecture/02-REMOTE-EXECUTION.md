# Remote execution: 승인된 후보만 검사하고 자원 회수까지 확인한다

## 1. 목적과 구현 상태

**AWS 단일 무변경 CPU smoke·파일 수거·재검증·자원 삭제 완료. Nebius CI·A/B 연결은 설계 단계다.** 원격 환경은 고정된 Rust 후보를 x86-64에서 빌드·검사하는 worker다. Codex가 후보를 만드는 세션과 cloud 자원을 관리하는 controller를 worker에 합치지 않는다. 현재 [quality.yml](../../.github/workflows/quality.yml)은 GitHub-hosted 문서·데모 검사만 수행한다. [이번 AWS 실행 결과](../experiment.md#무변경-cpu-smoke-실행-결과)는 로컬 CLI/SSH로 얻었으며 원격 PR CI의 성공이 아니다.

후속 double-buffering 정상 SDK 검사와 공개 오류 대조군 검출은 [로컬 Docker amd64/Rosetta](../kernels/double-buffering.md#8-로컬-docker-실행-결과)에서 완료했다. 아래 원격 CI 설계나 Nebius 할당을 실행한 결과는 아니다.

실험 방법·환경 선택은 [experiment.md](../experiment.md), Rust 컨벤션과 품질 검사·채택 절차는 [quality.md](../quality.md)가 정본이다. 아래는 이 결정을 구현할 때 필요한 입출력·권한·실패 처리의 상세 명세다. 공급사 근거는 [공식 출처 대장](../sources.md)에 둔다.

## 2. 환경 스펙과 확정 시점

2026-09-14 후속 승인: 첫 smoke를 AWS 서울 `m7i.large`(2 vCPU·8 GiB), 20 GiB gp3, 최대 2시간·예산 1 USD 범위에서 완료했다. 운영자 CLI/SSH, 고정 Ubuntu 24.04 x86-64 AMI와 build jobs=1을 사용했고 [실험 계약](../experiment.md#작업과-환경)과 [기록 규약](../quality.md#cpu-smoke의-관측성과-기록-규격)을 적용했다. 아래 표와 main controller·컨테이너 절차는 **Nebius AI Cloud 및 향후 CI 설계**이며 이번 단일 CPU smoke의 실제 구현으로 읽지 않는다. Token Factory beta는 접근 승인을 기다린다.

| 계층 | 현재 선택 또는 요구 | 실행 전 남길 증거 |
|---|---|---|
| CPU worker | Nebius `cpu-d3`, `8vcpu-32gb`의 8 vCPU·32 GiB, x86-64, 초기 1 VM을 계획한다. | 실제 region·zone·preset·할당 CPU/RAM·VM ID와 빌드·검사 중 최대 메모리 사용량을 기록한다. 할당 완료나 자원 충분성을 실측한 상태가 아니다. |
| OS | Ubuntu 24.04 host와 digest를 고정한 Ubuntu 24.04 amd64 빌드 컨테이너를 선정한다. 아래 pin의 Dockerfile을 참고한 선택이다. | host image ID·container digest·kernel·GLIBC·host triple을 고정한다. 컨테이너는 host kernel을 공유하며 호환성 smoke는 아직 실행하지 않았다. |
| Rust 대상 | `furiosa-opt` 0.8.1, `9b9cf0fdc78df00cdc430eae725a5ad9084a735e`, `nightly-2026-05-01` | checkout SHA·Cargo.lock hash·rustc/Clippy 버전을 기록한다. upstream Dockerfile의 `dist` 입력인 실행 바이너리·native library도 출처·release/tag·target·전체 SHA-256을 고정해야 한다. |
| 저장장치 | VM-managed disk를 우선한다. | 종류·용량·상한·정확한 ID·삭제 책임을 승인 전에 고정한다. 별도 disk/IP도 추적한다. |
| 검사 병렬도 | 검사 병렬도 보정에서 한 VM 내부 슬롯 1/2를 비교한다. 에이전트 작업 절차 비교의 두 세션은 순차 실행한다. | Cargo jobs·test threads·내부 thread pool·작업별 CPU/RAM·cache 상태를 고정한다. |
| 생성 모델 | 기존 Codex 구독 세션을 사용한다. | 실제 model ID·effort·공개 컨텍스트·관측 가능한 사용량·중단 한도를 기록한다. worker에는 개인 인증정보를 전달하지 않는다. |
| 시간·비용 | 아직 실행 수치를 승인하지 않았다. | 준비/smoke/trial timeout·출력/디스크 상한·총비용·모델 한도·만료시각을 먼저 정한다. 데모의 10초를 Rust에 복사하지 않는다. |
| 자원 권한 | VM 할당과 실행은 별도 승인이 필요하다. | 실제 AI Cloud 이용 권한·결제/크레딧 적용·단가를 확인한다. Token Factory 크레딧으로 대체하지 않는다. |

값이 비어 있으면 사전 승인 단계에서 멈춘다. 문서 작성자가 임의의 default를 채워 유료 실행을 허가하지 않는다. CPU host 값 검사·정적 compiler 검사·NPU 실측은 별개이며 이 환경에 NPU나 cycle-accurate simulator가 있다고 가정하지 않는다.

## 3. 구성요소와 데이터 접근

### 3.1 제어와 실행을 나눈다

```text
소유자 → 승인된 main controller → VM 생성 / 명령 전달 / 기록 수집 / 삭제·재조회
                                  ↓
                            CPU worker
                     고정 toolchain + 후보 사본
                                  ↓
                         원문 로그·종료 코드
                                  ↓
                       신뢰된 판정기 → PR 검토

별도 Codex A/B 세션 → 각각의 후보 snapshot
양쪽 공개 작업 종료 → 별도 권한의 독립 최종 검사 → 집계 결과 → 사람의 채택 검토
```

1. **Controller:** 보호된 `main` workflow에서만 동작한다. 전용 service account의 authorized key를 secret으로 관리하고 프로젝트 범위 권한을 제한한다. PR 입력은 명령 문자열이 아니라 검증할 revision·식별자 데이터로 취급한다.
2. **Worker:** GitHub runner를 설치하지 않는다. 관리 키·GitHub write token·Codex 인증정보·SSH agent forwarding을 받지 않는다. 후보는 비특권 컨테이너에서 실행하며 host socket과 보호 자료를 mount하지 않는다.
3. **판정기:** worker 산출물을 실행하지 않고 제한된 데이터로 읽는다. revision·실제 테스트 수·명령·exit code·값 비교를 확인한다. JSON의 `PASS` 필드만 신뢰하지 않는다.
4. **독립 최종 검사 환경:** 공개 worker의 숨김 폴더가 아니다. 후보 세션과 생성 테스트 코드는 보호 fixture 저장소·정답 파일·구현 정상/오류 label·판정기·다른 후보 결과에 접근할 수 없다. 신뢰된 실행기가 필요한 입력 값만 고정 인터페이스로 테스트에 공급하고, 생성 세션에는 개별 입력·로그·판정을 돌려주지 않는다. 실행 중 테스트가 처리하는 값 자체까지 숨긴다고 가정하지 않는다. 공급 방식·파일/네트워크 제한을 실제로 확인하지 못하면 에이전트 작업 절차 비교를 시작하지 않는다.

### 3.2 후보 프롬프트에 넣을 것

| 공통 A/B 입력 | B에만 추가할 절차 | 후보에게 제공하지 않을 운영 정보 |
|---|---|---|
| 공개 과제·upstream 지침·동일 source pin·허용 파일·검사·예산 | 관측 → 원인 가설 → 최소 개입 → 공개 검사 근거 정리 | 전체 lab AGENTS/위키·보호 입력/변이·최종 판정기·다른 후보의 대화/patch/결과·cloud secret |

공개 요구와 품질 문턱은 양쪽에 같다. [커널 계약](../kernels/double-buffering.md)에서 입력·의미·허용 파일·공개 검사 요구만 추출해 같은 판본으로 제공한다. 운영자용 실행 분기·전체 조사 경로는 후보에게 주입하지 않는다. B의 차이는 정답 정보나 더 강한 도구가 아니라 안내 절차다. B의 기록·정리 시간도 비용에 포함한다. 자연어 절차 준수와 스크립트 PASS는 별도로 검토한다.

## 4. 실행과 회수 절차

### 4.1 승인에서 공개 CPU receipt까지

1. **계약을 고정한다.** 요청·실험 ID, 작업 범위, head/base/test-merge SHA, controller/image/checker identity, 모든 상한과 담당자를 기록한다. smoke 허가와 검사 병렬도 보정·에이전트 작업 절차 비교의 허가를 구분한다.
2. **권한을 점검한다.** dispatch branch와 secret environment가 정확히 `main`만 허용하는지 확인한다. 비승인 요청은 VM 생성 전에 거부한다. GitHub→Nebius OIDC가 구성됐다고 가정하지 않는다.
3. **VM을 만들고 소유 기록을 남긴다.** 반환된 정확한 VM/disk ID·run ID·만료시각을 저장한다. 생성 응답이 불명확하면 기존 자원을 재조회한 뒤 판단하며 중복 생성하지 않는다.
4. **환경을 준비한다.** 고정 dependency를 준비하고 baseline 테스트의 목록·실행 수·결과를 확인한다. 이 PASS는 기존 코드를 검사할 준비가 됐다는 뜻이며 새 테스트 보강 과제의 완료가 아니다. 준비 단계도 timeout과 비용에 포함한다. 이후 후보의 네트워크·metadata 접근 제한을 확인한다.
5. **후보를 검사한다.** 후보별 새 checkout·컨테이너·쓰기 cache를 사용한다. 정해진 public command와 상한으로 검사하며 0 tests, timeout, OOM, 형식 오류를 성공으로 바꾸지 않는다.
6. **증거를 수집하고 재검증한다.** 후보 사본·명령·환경·stdout/stderr·실제 값·테스트 수·종료 상태를 함께 보존한다. 수집 뒤 원본 식별자·bytes·명령·revision의 대응과 접근 가능성을 다시 확인한다. 필수 판정 증거의 누락·손상·출력 잘림은 최종 통과와 인계를 보류한다. 부가 trajectory만 누락됐다면 해당 변경 과정·비용 설명을 제한하고 누락 범위를 밝힌다.
7. **Revision을 다시 확인한다.** 최초 CPU receipt는 소유자가 PR에서 검토한다. 현재 head/base와 다르면 stale 결과다. `main` dispatch의 성공을 PR required check로 자동 간주하지 않는다.

### 4.2 실패·취소도 자원 회수로 끝낸다

1. 실행을 중단할 때 후보 프로세스·임시 파일·남은 자원을 확인한다. 원인과 원래 종료 코드를 보존한다.
2. 수집 가능한 증거를 제한된 시간 안에 보존하고, 이 run이 소유한 정확한 VM·disk·별도 IP·임시 인증자료를 회수한다. 운영용 service account 자체를 임의로 삭제하지 않는다.
3. 삭제 요청 뒤 API로 잔존 여부를 재조회한다. 재조회 실패는 `회수 미확인`이며 완료가 아니다. 운영자 확인 전 새 run을 보류한다.
4. controller 중단에 대비한 별도 정리 작업은 기록된 owner/run/만료시각이 맞는 자원만 처리한다. cloud 전체 목록에 무차별 삭제를 적용하지 않는다.

`finally`나 CI 취소 처리만으로 모든 자원 회수를 보장할 수 없다. 승인 시 회수 담당자와 재조회 방법을 지정한다. VM stop은 디스크 삭제가 아니며 예산 알림도 자동 과금 차단 장치가 아니다.

## 5. 기록의 상세 규격

### 5.1 내용과 식별자를 함께 보존한다

새 DB를 만들지 않고 기존 Git·Codex 기록·파일 묶음을 사용한다. 다음은 **향후 원격 기록의 최소 필드**이며 현재 `trial.py`의 구현 필드라고 해석하지 않는다.

| 기록 | 필수 내용 | 작성자 → 읽는 주체·결정 |
|---|---|---|
| 실행 계약 | 요청, 허용 파일, source/head/base/checkout SHA, toolchain/image/checker, 명령, 상한 | 운영자 → controller: 실행 허용 여부 |
| 자원 기록 | run/owner, VM/disk/IP 식별자, 생성·만료·삭제·재조회 결과 | controller → 회수 담당자: 중복 생성 방지·잔존 자원 처리 |
| 산출물 목록 | artifact 유형·경로/locator·byte 크기·전체 SHA-256, 접근 주체·접근 가능 여부, 보존 위치·기간·현재 보존 상태, 필수 판정 증거/부가 기록 구분 | 수집 담당자 → 판정기·검토자: 원본 식별·재검증 가능 여부 |
| 검사 기록 | 후보 hash+경로, 명령/cwd, 원래 측정값·단위·집계/변환 규칙, 실제 test 이름/수, expected/actual, 로그, exit code | worker → 판정기: pass/반례/무효/미완료 구분 |
| 생성·개입 기록 | 원본 Codex 기록 locator와 native event ID 또는 고정 구간, attempt ID·parent revision, 후보 diff, 관측·가설·개입, 원래 사용량·시간·단위·집계/변환 규칙, 수집 불가 항목 | 세션 운영자 → 검토자: 변경 근거·재작업 비용 판단 |
| 채택 기록 | snapshot, 후보 테스트 묶음·구현 ID별 판정과 독립 최종 검사 집계, 사람의 채택 결정/이유, PR 상태, 회수 상태 | 검토자 → 실험 보고: 완료·미완료와 다음 조치 |

Hash는 원본 bytes의 식별자다. 입력·단위·명령·실패 원인을 대신하지 않는다. 원래 측정값을 보존하고 변환하지 않았으면 그 사실을 적는다. 로그를 일부만 보존했다면 잘린 범위와 상한을 남긴다. 비공개 원본과 공개 집계본은 접근·보존 범위를 구분한다.

필수 판정 증거는 실행 계약에서 먼저 정한다. 이 증거를 사후에 재검증할 수 없으면 인계를 보류한다. 입력 case·assertion 기록을 별도 점수로 늘리지 않고 [실험 계약의 판정 단위](../experiment.md#결함-검출의-판정-단위)로 집계한다. 부가 trajectory 누락은 관련 설명의 한계로 남기며, 별도로 재검증된 정확성 결과까지 자동으로 무효화하지 않는다. AWS smoke의 계약·원문·수거 대조·CPU 판정·회수 기록은 구현해 실행했다. 생성·개입 trajectory와 A/B·CI 자동 연결은 아직 구현하지 않았다.

### 5.2 향후 실행 산출물의 논리 트리

아래는 A/B용 파일 묶음의 **제안 구조**다. 실제 AWS smoke 기록은 비공개 `.local/aws-cpu-smoke-20260914-h9bE3zWX/`에 별도로 생성했다. 아래 보호 평가 디렉터리는 아직 없으며 경로 분리만으로 보호되지는 않는다.

```text
운영자 전용 run 디렉터리/
├── contract.json                 승인된 실행 계약
├── resources.json                생성 식별자·회수 재조회 기록
├── baseline/                     환경 smoke의 실제 증거
├── candidate-A/                  diff·원본 기록 locator·공개 검사
├── candidate-B/                  다른 세션·checkout·cache의 증거
└── review.md                     독립 최종 검사 집계·채택 판단·미완료 사유

별도 권한의 평가 저장소/
└── 실험별 보호 입력·대조군·판정기·원본 결과
```

## 6. 구현 순서와 완료 검사

1. **Rust 연결:** [로컬 실행기](01-LOCAL-TRIAL.md)의 저장 증거 재검증을 출발점으로 삼되 무조건 범용화하지 않는다. 실제 Rust 명령·결과 형식에 필요한 최소 연결만 만든다. 무변경 baseline의 명령·실행 수·exit·원격 산출물 수거/재검증은 AWS에서 완료했다. 새 테스트 보강과 오류 대조군을 실행기에 연결하는 작업은 남아 있다. CPU 명령과 실제 관측 범위는 [품질 계약](../quality.md#실제-명령과-아직-없는-테스트를-구분한다)을 따른다. 데모의 `READY_FOR_REVIEW`를 Rust 과제 완료나 사람의 채택으로 읽지 않는다.
2. **무변경 원격 smoke:** 승인된 환경에서 기존 테스트를 실행하고 0 tests·timeout·출력 누락·취소·회수 실패의 처리까지 확인한다. 단순한 문서 PASS로 대체하지 않는다.
3. **PR 연결:** 신뢰된 workflow, revision 고정, 결과 누락·stale 결과 거부를 확인한다. 환경 보호 설정과 실제 실행 receipt를 함께 남긴다.
4. **보호 접근 검사:** 평가 자료의 파일·네트워크 접근을 후보 세션과 생성 코드 양쪽에서 확인한다. 접근 차단과 평가 가능성이 입증된 뒤 검사 병렬도 보정과 에이전트 작업 절차 비교를 승인받는다.
5. **비교 실험과 인계:** 검사 병렬도를 보정한 뒤 에이전트 작업 절차를 비교한다. 양쪽 공개 작업 종료 → snapshot 고정 → 후보별 독립 최종 검사 한 번 → 사람의 채택 검토 순서를 지킨다. 정상 assertion 실패/오류 통과와 runner 실패는 [실험 계약의 판정 기준](../experiment.md)에 따라 구분한다.

이 절차의 완료 근거는 고정된 코드와 실제 실행·회수 기록이다. 독립한 모델 개선 효과나 NPU 성능 주장은 여기서 생성하지 않는다.
