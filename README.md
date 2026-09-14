# Compiler AX Lab

프론티어 코딩 에이전트가 만든 변경을 컴파일러 개발자가 검토하고 유지할 수 있는 형태로 만드는 실험입니다. 생성량보다 **정확한 변경을 검토하는 데 든 사람 작업시간과 재작업**을 봅니다.

공개 `furiosa-opt`의 Rust 예제를 대상으로 실험을 설계했습니다. FuriosaAI와 무관한 개인 연구이며, 내부 컴파일러·CI·승인 체계를 재현한 프로젝트가 아닙니다. **현재는 실험 설계와 로컬 변경 루프 데모 단계입니다. Rust 빌드, 클라우드 실험, NPU 측정은 아직 수행하지 않았습니다.**

**로컬 구현·회귀 검사를 재개했습니다.** 원격·모델 비교 실험은 [남은 재개 조건](docs/experiment.md#시행-보류와-재개-조건)을 확인한 뒤 승인된 범위에서 진행합니다. [보고서와 실험의 대응](docs/context.md#보고서에서-이번-실험으로-옮긴-범위), [입력·수치 계약](docs/quality.md#입력과-수치-계약), [원격 환경·기록 명세](docs/architecture/02-REMOTE-EXECUTION.md)에 정렬 기준을 남겼습니다.

## 먼저 읽을 것

전체 경로는 [Architecture 인덱스](docs/architecture/00-OVERVIEW.md)에서 고릅니다. 현재 폴더 트리, 구성요소별 책임, 로컬 실행기의 스펙과 계획된 원격 환경을 나눠 설명합니다.

1. [실험 계획](docs/experiment.md): 검사 병렬도 보정, 에이전트 작업 절차 비교, 별도 후속 단일 요인 비교.
2. [품질 계약](docs/quality.md): 기존 컨벤션, 검사별 보장 범위, 품질 검사·채택 절차.
3. [기존 시행도](report/assets/compiler-ax-experiment-approval.html): 로컬 브라우저로 열 수 있는 단일 HTML. 최신 Nebius CI·종료 절차는 실험 계획을 따릅니다.
4. [PR·병합 절차](docs/merge.md): 검사한 revision, 사람 판단, 병합 후 확인.
5. [판단 컨텍스트](docs/context.md)와 [1차 출처](docs/sources.md): 채택 이유와 읽은 범위. skill·링크형 wiki 선택과 KG 엔진 보류 이유도 기록합니다.
6. [원문 사례의 폴더 구조](references/source-layouts.md): 고정 commit의 실제 경로와 공개 범위.

![기존 실험 시행도: 최신 환경·CI 개정은 MD 참조](report/assets/compiler-ax-experiment-approval-3.png)

## 지금 재현할 수 있는 검사

Node.js 22 이상과 Unix 계열 Python 3.9 이상을 사용합니다. 추가 패키지는 필요하지 않습니다.

```bash
node scripts/check.mjs
python3 -m unittest discover -s tests -v
```

첫 명령은 문서 링크·공개 파일 경계·품질 단계·PR 필드 및 512개 산술 조합을 검사합니다. 두 번째는 의도 오류 후보로 로컬 실행기의 판정·중단 동작을 시험합니다. 컴파일러의 정확성이나 생산성 효과를 검사하는 명령은 아닙니다. GitHub Actions도 같은 명령을 PR과 `main`에서 실행합니다.

선택적 그림 재검수는 이미 설치된 Playwright와 Chromium을 사용합니다. 설치나 브라우저 다운로드를 자동 수행하지 않습니다.

```bash
PLAYWRIGHT_PACKAGE=/absolute/path/to/playwright/package.json \
CHROMIUM_EXECUTABLE=/absolute/path/to/chromium \
node report/render-experiment-approval.mjs
```

## MD가 작업을 안내하고 스크립트가 상태를 결정한다

[현재 폴더·책임 지도](docs/architecture/00-OVERVIEW.md#3-현재-폴더와-책임)와 [로컬 실행기 상세 명세](docs/architecture/01-LOCAL-TRIAL.md)는 실제 파일·함수·CLI 한도·기록 필드를 연결합니다. [원격 명세](docs/architecture/02-REMOTE-EXECUTION.md)는 구현 전 스펙·권한·회수 절차를 별도로 정의합니다.

[스킬](.agents/skills/run-bounded-change-loop/SKILL.md)은 [program.md](program.md)를 읽어 실행합니다. 에이전트가 baseline의 실제 차이를 진단하고 후보 하나를 수정하면, 실행기가 고정 검사기·유한 시도·시간 상한 아래에서 다시 검사합니다. 결과는 `REVISE`, `READY_FOR_REVIEW`, `STOP`으로 다음 행동을 제한합니다. 모델 호출이나 자동 패치 생성기는 추가하지 않았습니다. 기존 코딩 에이전트가 진단과 구현을 맡습니다.

실행기는 명령·후보 사본·원문 출력·테스트 수·결과를 같은 attempt 아래에 남깁니다. 검사 통과는 사람 검토로 넘어갈 조건이며 자동 병합 권한이 아닙니다. MD와 같은 계정의 프로세스 분리는 보안 격리가 아닙니다. 공개 seed에는 실제 벤더에서 찾은 결함이나 보호 검사 문제가 포함되지 않습니다.

## 작업공간과 공개 범위

이 저장소는 **실험 설계·운영용**입니다. A/B 후보는 별도 clean checkout에서 동일한 공개 요구·도구를 받습니다. B에만 추가 절차를 제공하며, 이 저장소의 설계 컨텍스트 전체를 후보에게 주입하지 않습니다.

기존 개인 작업공간의 원고와 이력은 보존했습니다. 선택한 로컬 참고 자료는 Git에서 제외한 `.local/context/`에 있습니다. 원문 전사·논문 사본·지원 자료·계정 기록·보호 검사 입력·실제 실행 로그는 공개하지 않습니다. `.gitignore`는 접근 통제 수단이 아니므로 보호 검사는 후보와 별도 권한의 실행 환경에 둡니다.

공개 저장소 생성과 문서 게시가 실험 실행이나 Furiosa upstream PR 승인까지 의미하지는 않습니다. 비용·접근·예산·검토자와 보호 기준을 고정한 후 첫 CPU smoke를 승인받는 것이 다음 단계입니다.
