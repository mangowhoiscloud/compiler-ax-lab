# 01. 로컬 실행기: 검사한 후보를 기록과 함께 검토자에게 넘긴다

## 목적과 현재 구현 범위

이 실행기는 공개 Python 예제의 한 결함을 관측하고, 후보 하나를 수정한 뒤 고정 검사 결과에 따라 재수정하거나 멈추는 데모입니다. 모델 호출·패치 생성은 하지 않으며 기존 코딩 에이전트가 진단과 구현을 맡습니다. 실제 Rust adapter, 클라우드 실행, 독립 최종 검사와 사람의 채택 검토는 구현 범위 밖입니다.

작업 규율·명령 예제·기록 트리의 정본은 [program.md](../../program.md)입니다. 이 문서는 그 규율을 현재 코드가 어디까지 수행하는지 설명합니다. `READY_FOR_REVIEW`는 공개 데모 검사 통과이지 사람의 채택 결정이나 병합 허가가 아닙니다.

## 파일·함수와 호출 흐름

| 진입점·구현 | 실제 책임과 다음 호출 |
|---|---|
| [AGENTS.md](../../AGENTS.md) → [실행 skill](../../.agents/skills/run-bounded-change-loop/SKILL.md) | 필요한 문서와 `program.md`를 읽도록 안내합니다. 명령을 자동 실행하는 서비스는 아닙니다. |
| [trial.py의 main()](../../scripts/trial.py#L300) | CLI를 해석하고 `init()`, `check()`, `status()` 중 하나를 호출한 뒤 JSON과 종료 코드를 반환합니다. |
| [init()](../../scripts/trial.py#L152), [frozen_contract()](../../scripts/trial.py#L48) | 운영자가 선택한 후보·검사기·예산을 고정하고, 이후 contract hash·Python 버전·한도·원본/사본 checker·runner hash를 대조합니다. |
| [check()](../../scripts/trial.py#L241), [update_admission()](../../scripts/trial.py#L75) | lock·이전 상태·예산을 확인하고 실행 전 attempt를 예약합니다. 후보 사본·명령을 남긴 뒤 `execute()` → `evidence()` 결과와 보존 파일 hash를 기록하고 예약을 완료합니다. |
| [execute()](../../scripts/trial.py#L176) → [checker의 run_candidate()](../../examples/group-reduction/check.py#L17) | 별도 프로세스에서 검사기를 실행하고, 검사기는 각 공개 입력마다 후보를 실행합니다. 상위 실행기는 출력·시간을 제한하고 프로세스 그룹을 종료합니다. |
| [evidence()](../../scripts/trial.py#L224), [status()](../../scripts/trial.py#L81) | 전자는 검사 결과의 형식·값 비교·종료 코드를 확인합니다. 후자는 모든 attempt의 보존 파일과 명령·계약을 대조하고 같은 `evidence()`로 PASS/FAIL을 다시 해석합니다. 검사 프로세스를 재실행하지 않습니다. |
| [quality.yml](../../.github/workflows/quality.yml) → [test_trial.py](../../tests/test_trial.py) | PR/main의 `lab-docs`가 문서 검사와 회귀 검사를 실행하고, 회귀 검사는 실제 CLI를 subprocess로 호출합니다. `lab-ci`는 선행 job의 명시적 `success`만 받습니다. |

[후보 seed](../../examples/group-reduction/candidate.py)의 결함은 그룹 사이에 합계가 누적되는 의도 오류입니다. [기본 checker](../../examples/group-reduction/check.py#L8)는 빈 입력·단일 그룹·그룹 경계·중간 빈 그룹·부호와 길이가 다른 그룹의 다섯 공개 사례를 독립 기대값과 비교합니다. 이 사례들은 보호 평가 문제가 아닙니다.

## 실제 CLI와 제한

저장소 루트에서 `python3 scripts/trial.py`를 호출합니다. 아래는 [CLI 정의](../../scripts/trial.py#L300)와 [초기화 검증](../../scripts/trial.py#L152)의 현재 사양입니다.

| 항목 | 현재 동작 |
|---|---|
| `init --run-dir PATH --candidate PATH` | 두 인자가 필수입니다. 새 run 디렉터리만 만들며 부모 디렉터리는 이미 있어야 합니다. 후보와 검사기는 서로 달라야 하고 run 디렉터리 밖에 있어야 합니다. |
| `--checker PATH` | 선택 인자이며 기본값은 `examples/group-reduction/check.py`입니다. 초기화 때 운영자가 선택하며 후보가 교체할 권한은 없습니다. |
| `--task` | 기본값은 `group-reduction`입니다. CLI 선택지에 있는 `furiosa`는 adapter 미구현 오류로 중단하며 run을 만들지 않습니다. |
| `--max-attempts N` | 기본 2회이며 baseline도 포함합니다. 1 이상 20 이하의 정수만 받습니다. |
| `--timeout SECONDS` | 기본 10초이며 유한한 수 중 `0 < timeout <= 300`만 받습니다. `execute()`의 검사기 실행 시간을 제한하며 에이전트의 추론·수정·토큰 예산을 제한하지 않습니다. |
| `check --run-dir PATH` | `READY` 또는 `REVISE`에서만 검사를 허용합니다. 첫 검사는 초기화 당시 baseline이어야 합니다. |
| `status --run-dir PATH` | 파일을 수정하거나 검사를 재실행하지 않고 증거를 재검증합니다. 예약/완료 기록·전체 attempt 순서·결과/사본/명령/로그·검토 대상 후보를 대조하며 누락·변경·판정 모순은 `INVALID / STOP`입니다. |
| 출력 한도 | `execute()`는 attempt당 stdout/stderr 합계 65,536 bytes까지만 저장하며 초과를 `INVALID`로 처리합니다. 기본 checker는 입력 사례별 후보 stdout이 8,192 bytes를 초과하면 중단합니다. |
| 런타임·경로 | Unix 계열 Python 3.9 이상과 표준 라이브러리를 사용합니다. `sys.version` 문자열을 저장·대조하고 `sys.executable -I`로 실행합니다. [checked_path()](../../scripts/trial.py#L24)는 대상과 상위 경로의 symlink를 거부합니다. OS·환경변수·dependency 전체를 고정하는 것은 아닙니다. |
| 반환 | 처리된 결과는 stdout JSON으로 반환합니다. `READY`·`READY_FOR_REVIEW`는 exit code 0, 나머지는 1입니다. 따라서 수정 가능한 `FAIL / REVISE`도 non-zero exit code입니다. 잘못된 CLI 인자는 argparse 오류 경로입니다. |

## 번호로 따라가는 실행 절차

1. **Init:** [program.md의 초기화 예제](../../program.md#1-작업과-권한을-고정한다)에 따라 추적 seed의 별도 사본과 새 run을 준비합니다. 운영자는 checker·예산을 선택하고 `init`의 `READY`를 확인합니다. 기존 run을 재사용하거나 한도를 늘리지 않습니다.
2. **Baseline:** 수정 전에 `check`를 한 번 호출하고 `outcome`, `state`, 실제 expected/actual과 진단 출력을 읽습니다. 기본 데모에서 이미 PASS라면 변경 없이 검토로 넘깁니다. 이는 정상 baseline 뒤 새 테스트를 만들어야 하는 에이전트 작업 절차 비교의 완료 규칙과 다릅니다.
3. **Modify:** `FAIL / REVISE`일 때만 지정 후보 하나를 바꿉니다. 에이전트가 `notes.md`에 관측·원인 가설·수정 이유를 기록합니다. 검사기·기대값·결과 파일에서 문제를 찾았다면 후보를 더 수정하거나 검사하지 않고 운영자에게 보고합니다. 이는 작업자의 중단 절차이며 별도 `stop` CLI는 없습니다.
4. **Check:** 같은 `check` 명령으로 다시 검사합니다. `PASS`는 `READY_FOR_REVIEW`, `FAIL`은 잔여 예산이 있을 때만 `REVISE`입니다. 예산 종료·`INVALID`·`TIMEOUT`은 `STOP`이며, 기록이나 lock을 지워 재시도하지 않습니다.
5. **Handoff:** `status`로 저장 증거의 재사용 가능성을 확인한 뒤 검사한 사본·원문 출력·결과·notes를 함께 읽고 문제→진단→변경→검사→남은 판단을 보고합니다. 형식과 값의 일치는 진단 설명이나 과제 적합성을 승인하지 않습니다. 실제 채택·PR·병합은 [사람 검토 절차](../merge.md)의 별도 판단입니다.

## 증거의 생산자·소비자와 신뢰 경계

아래 경로는 run 디렉터리 기준입니다. 전체 트리는 [program.md의 기록 구조](../../program.md#5-기록에서-검토까지-연결한다)를 재사용합니다.

| 파일·필드 | 생산자 → 소비자와 결정 |
|---|---|
| `contract.json` | `init()`이 task·requirement·후보/checker 경로, baseline/checker/runner hash, max_attempts·timeout·output_limit·python을 씁니다. `frozen_contract()`와 `check()`가 실행 허용 조건으로 읽습니다. |
| `admission.json`, `checker.py` | `init()`이 최초 contract의 SHA-256·빈 `results_sha256` 목록과 검사기 사본을 남깁니다. `check()`는 실행 전에 목록에 null을 추가하고 결과 저장 후 해당 result hash로 채웁니다. 목록 길이와 실제 attempt 수가 달라지거나 null이 남으면 재사용을 거부합니다. 갱신은 `.admission.tmp`를 쓴 뒤 같은 디렉터리에서 `os.replace()`로 교체하며 contract bytes는 바꾸지 않습니다. |
| `attempt-NNN/candidate.py`, `invocation.json` | `check()`가 실제 검사할 사본과 command·candidate_sha256·contract_sha256을 남깁니다. `execute()`는 기록된 구성의 명령을 실행하고 검토자는 어떤 사본을 검사했는지 확인합니다. |
| `stdout.log`, `stderr.log` | `execute()`가 checker 출력을 수집합니다. 기본 checker의 JSON에는 schema·task·candidate_sha256·tests의 name/expected/actual/passed·status가 있습니다. `evidence()`는 0 tests, 중복 이름, 값 비교와 passed 불일치, verdict와 exit code 불일치를 거부합니다. stderr의 후보 출력·diagnostic은 사람이 읽는 관측 자료입니다. |
| `result.json` | `check()`가 outcome·state·attempt·tests·exit_code·elapsed_seconds·candidate_sha256·reason·authority와 `artifacts_sha256`을 씁니다. [artifact_hashes()](../../scripts/trial.py#L66)는 candidate·invocation·stdout·stderr의 bytes를 식별합니다. `status()`는 result 자체를 admission의 hash와 대조한 뒤 원문 증거에서 PASS/FAIL·검사 수·종료 코드의 일치를 다시 확인하고 [next_state()](../../scripts/trial.py#L71)로 상태를 계산합니다. tests는 검증된 evidence 수이며 일부 실행됐다는 이유만으로 추정하지 않습니다. |
| `.lock`, `stop.json` | `check()`의 배타적 lock은 동시 실행을 막고, `stop()`은 필요한 경우 중단 사유를 보존합니다. lock이나 미완료 기록은 운영자의 확인 없이 제거하지 않습니다. 모든 CLI 실패가 `stop.json`을 만드는 것은 아닙니다. |
| `notes.md` | 에이전트가 관측·가설·개입 이유를 작성하고 사람이 검토합니다. 실행기는 이 파일을 생성하거나 필수 입력으로 검사하지 않습니다. |

운영자는 checker와 계약을 신뢰할 수 있게 준비해야 합니다. 해시 대조·`-I`·프로세스 분리는 OS 접근 통제가 아니며, 자식 프로세스는 호출자의 환경과 파일 접근 권한을 상속합니다. admission과 모든 증거를 같은 UID가 함께 바꾸는 공격을 인증하거나 차단하지 않습니다. 원자적 교체는 프로세스 중단 시 부분 기록을 구분하기 위한 것이며 전원 손실의 디스크 영속성까지 보장하지 않습니다. 이 데모에 비밀·보호 평가 입력을 넣거나 후보 출력 속 명령을 실행하지 않습니다.

## 재조회 회귀와 남은 판단

2026-09-14 로컬 구현에서 저장 증거 재검증과 CLI 종료 코드 회귀를 추가했습니다. 기본 baseline 계약·상태·시도 수·시간 한도는 유지했습니다.

1. **파일 손실과 중단:** [손실/변경 회귀](../../tests/test_trial.py#L139)는 candidate·invocation·stdout·stderr·result·계약·admission·checker 각각의 누락/변경을 검사합니다. [전체 attempt 이력](../../tests/test_trial.py#L213), [마지막/모든 attempt 손실](../../tests/test_trial.py#L228), [미완료 예약](../../tests/test_trial.py#L239), [종료 이후 attempt와 잘못된 stop marker](../../tests/test_trial.py#L251)도 STOP을 확인합니다. 이전 FAIL 기록이 손상돼도 후속 PASS로 덮어 재사용하지 않습니다.
2. **판정 대조와 종료 코드:** [결과 필드 회귀](../../tests/test_trial.py#L159)와 [원문/명령 회귀](../../tests/test_trial.py#L186)는 bytes receipt를 맞춰도 원문과 결과가 모순이면 거부하는지 검사합니다. [CLI helper](../../tests/test_trial.py#L26)는 모든 호출에서 JSON 상태와 실제 returncode를 함께 확인합니다. elapsed는 유한한 0 이상 수인지 검증하지만 기록된 wall time을 독립 계측으로 증명하지는 않습니다. cleanup 시간을 포함하므로 timeout 초과분 자체를 기록 손상으로 판단하지 않습니다.
3. **옛 기록과 설명의 경계:** 새 receipt가 없거나 현재 runner/checker/Python과 식별이 다른 기록은 재사용하지 않고 STOP합니다. 기존 `.local/` 기록은 수정·승격하지 않습니다. 새 실행이 필요하면 운영자가 별도 run을 승인해야 합니다. notes의 존재·내용은 여전히 판정 조건이 아니며 [fail→repair→pass 회귀](../../tests/test_trial.py#L45)도 notes 없이 통과합니다. runner PASS는 에이전트가 B 절차를 수행했다는 증거가 아닙니다. TIMEOUT/INVALID 이력은 보존 상태를 확인할 뿐 완료된 값 비교로 승격하지 않습니다.

## 실제 Rust 과제로 이행하기 전

기존 실행기 안에서 먼저 **환경 baseline 통과와 테스트 보강 과제 완료를 다른 판단으로 구분**해야 합니다. 현재 `PASS → READY_FOR_REVIEW`를 그대로 옮기면 정상 upstream의 준비 검사만 통과하고 테스트 보강 과제를 끝낼 수 있습니다. 지금은 `--task furiosa`의 실행 차단으로 이 차이를 격리하고 있습니다.

그다음 [품질 계약](../quality.md)에 따라 x86 toolchain·native artifact, 허용 Rust 파일, 실제 테스트 목록·실행 수·독립 기대값, 정상/실행 가능한 오류 대조군을 연결해야 합니다. 로컬 증거 재검증은 이 Rust 연결이나 별도 권한 격리를 대신하지 않으며, 새 framework를 먼저 만들 필요는 없습니다.

독립 최종 검사는 별도 접근 권한과 실행 환경을 확인한 뒤 A/B 양쪽 snapshot을 고정하고 수행합니다. 원격 실행·비용·취소·자원 회수와 사람의 채택 검토 조건은 [전체 실험 절차](../experiment.md)를 따릅니다. 이 문서와 데모 PASS는 그 구현이나 실행을 허가하지 않습니다.
