# Compiler AX Lab

코딩 에이전트의 초안을 **컴파일러 개발자가 검토할 수 있는 변경**으로 만드는 실험입니다. 코드 생성량보다 무엇을 고쳤고, 어떤 검사가 그 변경을 실제로 확인했는지를 다룹니다.

컴파일 성공만으로 출력의 의미가 보존되지는 않습니다. 값이 맞아도 이전 바이너리를 실행했을 수 있고, 실패한 검사가 의도한 결함이 아니라 환경 문제를 잡았을 수도 있습니다. 이 저장소는 변경 범위를 먼저 정하고, 독립 기대값·정상/오류 대조군·소스와 바이너리의 연결로 그 차이를 확인합니다.

```text
문제·보존할 동작 → 원인 가설 → 한정된 변경 → 고정 검사
                                             ↓
                          소스·명령·실제 값·종료 상태 대조
                                             ↓
                                   사람 검토 → 별도 병합
```

FuriosaAI와 무관한 개인 연구입니다. 공개 `furiosa-opt`의 Rust 예제를 사용하며 내부 production compiler나 NPU를 재현한 시스템은 아닙니다.

## 공개된 시스템

| 구성 | 역할 | 진입점 |
|---|---|---|
| 작업 규율 | 요청 범위·컨벤션·Git 경로·공개 경계를 정합니다. | [AGENTS.md](AGENTS.md) |
| 실행 스킬 | 별도 후보 사본에서 진단·수정·검사를 제한된 횟수로 수행합니다. | [run-bounded-change-loop](.agents/skills/run-bounded-change-loop/SKILL.md), [program.md](program.md) |
| 로컬 실행기 | 계약과 검사기를 고정하고 시도 예약·원문·사본·결과를 재검증합니다. | [trial.py](scripts/trial.py), [회귀 검사](tests/test_trial.py) |
| Rust 테스트 사례 | 세 커널의 수치 의미와 parser의 문법·AST·진단 위치를 검사합니다. | [double-buffering](docs/kernels/double-buffering.md), [mapping parser](docs/quality.md#mapping-parser) |
| 검토·PR 스킬 | 현재 diff와 실제 검사 revision을 연결해 기존 PR을 갱신합니다. | [review-to-verified-pr](.agents/skills/review-to-verified-pr/SKILL.md), [병합 규약](docs/merge.md) |

공개 실행기는 표준 라이브러리 기반 Python 데모입니다. Rust 사례는 호환 x86-64 환경에서 Cargo로 재현하는 테스트·patch이며, `trial.py --task furiosa`로 실행할 수 없습니다. A/B의 운영자 실행기·계정 기록·보호 입력·원문은 로컬에만 보존합니다.

## 빠르게 확인하기

Git으로 clone한 저장소 루트에서 실행합니다. Git, Node.js 22 이상, Unix 계열 Python 3.9 이상이면 추가 패키지 없이 공개 시스템을 검사할 수 있습니다.

```bash
node scripts/check.mjs
python3 -m unittest discover -s tests -v
```

첫 명령은 공개 파일·민감정보·읽기 경로·PR/CI 규약을 검사합니다. 두 번째는 실행기의 정상·실패·중단 및 저장 증거 검증을 확인합니다. 둘 다 Rust나 NPU 검사는 아닙니다.

변경을 제출할 때는 [언어별 품질 검사](docs/quality.md#언어별-정적-검사와-ci-분기)도 실행합니다. CI는 항상 공개/문서·workflow를 확인하고, 변경 경로에 따라 Python의 Ruff·mypy·회귀, JavaScript의 Biome, Rust의 포맷·독립 reference Clippy/테스트·patch 검사를 나눕니다. `lab-ci`는 선택된 job의 실패·취소·누락을 거절합니다. 검사 도구만 개발 의존성으로 추가되며 데모 실행에는 필요하지 않습니다.

실제 수정 데모는 [program.md](program.md)의 순서로 진행합니다. seed에는 의도적인 결함이 있으므로 사본만 수정합니다. 기본 예산은 baseline을 포함한 검사 2회, 호출당 10초입니다. `REVISE`에서만 수정하며 `READY_FOR_REVIEW`는 사람에게 넘길 상태이지 자동 승인이 아닙니다. 누락·시간 초과·한도 종료는 `STOP`으로 남습니다.

## Rust 사례를 재현하려면

기준은 `furiosa-opt` v0.8.1, commit `9b9cf0fdc78df00cdc430eae725a5ad9084a735e`, `nightly-2026-05-01`입니다. SDK에 맞는 x86-64 Linux와 native dependency를 준비한 뒤, [품질 계약](docs/quality.md)에 따라 lock·도구·명령과 한도를 기록합니다. CI의 Rust job은 SDK native 환경을 설치하지 않고 독립 reference와 patch 적용 가능성까지만 검사합니다.

- **Double-buffering:** [SDK 테스트](examples/furiosa-double-buffering/tests/double_buffering_tests.rs)와 [독립 scalar reference](examples/furiosa-double-buffering/tests/support/double_buffering_reference.rs)를 고정 checkout에 적용합니다. [입력·수치 계약과 명령](docs/kernels/double-buffering.md)에 따라 세 구현의 모든 출력 좌표를 대조합니다.
- **Mapping parser:** [테스트 patch](examples/furiosa-mapping-parser/tests.patch)를 적용해 두 parser 진입점의 AST·오류 문구·byte range를 함께 확인합니다. [적용 범위와 명령](docs/quality.md#mapping-parser)을 따릅니다.
- 공개 오류 patch는 별도 사본에서 검사기의 판별력을 확인하는 용도입니다. upstream에서 발견한 버그나 A/B의 보호 평가 정답으로 취급하지 않습니다.

## 검증 상태

다음은 서로 다른 실행의 근거입니다. 테스트 수, 원소 비교 수, A/B 평가 단위를 합산하지 않습니다.

| 실행 | 확인한 결과 | 해석 범위 |
|---|---|---|
| AWS 무변경 CPU smoke | 지정 assertion 1개 통과, 파일 94개 수거·대조와 생성 자원 회수 | native x86 환경 준비; 새 후보의 성과가 아님 |
| 공개 double-buffering 보강 | SDK 3개·18개 입력 실행·46,080개 값 일치, helper 2개 통과. 공개 오류 사본은 컴파일 후 지정 수치 assertion 실패 | 고정 shape·정확히 표현 가능한 bf16 입력의 CPU 검사 |
| 공개 mapping parser 보강 | 기존 6개에서 12개 검사로 확장해 통과. 공개 오류 사본의 잘못된 수용을 지정 검사에서 검출 | 두 진입점의 AST·진단. 오류 사본은 mapping assertion에서 먼저 실패 |
| 두 변경의 CPU workspace 통합 | 일반 검사 720개·doctest 55개·전체 대상 release Clippy 통과 | 기본 feature. ignored 17개 제외; doctest 55개 중 44개는 `compile_fail` |
| 로컬 실행기 | 회귀 검사 16개 통과 | Python 데모·증거 처리; compiler 정확성과 별개 |

로컬 CPU 실험은 Ubuntu 24.04 amd64/Rosetta, 2 CPU·6 GiB, Cargo jobs=1 환경입니다. 원격 무변경 smoke는 별도 AWS x86 실행입니다. NPU timing·overlap·성능, 비기본 feature 전체, 사람의 채택은 확인 범위에 포함하지 않습니다.

### 진행 중인 A/B 파일럿

**기준 시각: 2026-09-15 17:30 KST.** 같은 상세 과제만 받은 A와, 같은 과제에 조사·진단·변경·검증 절차를 추가한 B를 비교합니다. 한 과제·한 쌍이며 순서는 B 다음 A로 고정했습니다.

| 항목 | A: 공통 과제 | B: 절차 안내 추가 |
|---|---|---|
| 생성 | 초안 완료 | 초안 완료 |
| 공개 검사 | 디스크 하한·사용자 중단 기록을 보존하고 같은 소스로 재개. 원래 종료 시각 유지; 수정 기회 1회 미사용 | 수정 1회 후 fmt·컴파일·SDK 3개와 helper 1개·Clippy 통과 |
| 소스 동결 | 대기 | 완료 |
| 최종 정상/오류 비교 | 4개 단위 미실행 | 4개 단위 미실행 |
| 사람 작업시간·채택 | PENDING | PENDING |

두 후보가 모두 동결된 뒤 최종 8개 단위를 검사하며, 보호 결과는 후보 수정에 돌려주지 않습니다. 생성 전 고정한 예산을 유지하고 중단·재개는 별도 기록합니다. 사용자 승인으로 구독 계정이 바뀌었고 실행 중 호스트 캐시 정리도 있었으므로, 단일 요인을 엄밀히 통제한 생산성 실험으로 해석하지 않습니다. 사람 작업시간은 모델의 실행 시간으로 대신하지 않습니다.

## 변경과 공개

Git 경로는 feature branch → `dev` → `main`입니다. 현재 `codex/executable-loop-skill`이 feature branch 역할을 합니다. feature 변경은 `dev` PR에서 squash하고, 검증한 `dev`는 별도 PR의 merge commit으로 `main`에 올려 다음 승격에서도 공통 조상을 보존합니다. 두 단계 모두 현재 head/base의 필수 CI와 명시적 병합 요청을 확인합니다. [병합 규약](docs/merge.md), [PR 템플릿](.github/pull_request_template.md)

Draft는 구현·필수 검사가 남았을 때만 사용합니다. 검토 가능한 변경은 Ready for review로 전환하며, Draft 자체를 검토나 병합 승인 대신 사용하지 않습니다. 브랜치 직접 push로 병합을 우회하거나 history rewrite를 하지 않습니다. 실행 결과에 대한 사람 채택과 저장소 변경 병합은 구분합니다.

공개 트리에는 실행 코드·테스트·스킬·필수 계약만 둡니다. 조사 원문·설계 이력·발표 자료·실험 로그·보호 평가·인증정보는 Git에서 제외한 로컬 자료입니다. 공개 스냅샷은 실시간 상태판이 아니며 다음 검사 완료 시 갱신합니다. 이전 공개 자료는 Git 이력에 남아 있습니다.

## 설계에 참고한 원문

- [autoresearch의 작업 절차](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/program.md): 수정 파일·고정 평가·실행 기록을 분리하는 구성. 이 lab에서는 무한 탐색 대신 유한 시도와 사람 검토로 종료합니다.
- [Dioxus Agent Guide](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/AGENTS.md): 작업에 필요한 구조만 읽고 실제 구현으로 이동하는 진입 방식.
- [Furiosa torch-fx-rs 지침](https://github.com/furiosa-ai/torch-fx-rs/blob/3024d6d157732e51b02ef67b808131bec4d652ef/AGENTS.md), [Agent Skills](https://github.com/furiosa-ai/agent_skills/blob/d5fc482fdca0af78aada5d1e183b4aad18ffbfc7/AGENTS.md): 기존 API 의미·작은 변경·표적 검사와 최종 diff 기반 PR 설명.
- [Furiosa Kernel Validation](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/docs/src/quick-start/kernel-validation.md): CPU 값 검사와 타깃 검증의 구분.
- [Furiosa CI](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/.github/workflows/build.yml), [Dioxus CI](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/.github/workflows/main.yml): 언어 도구·표적 검사·문서 검사를 실제 job에 연결하는 구조. 이 lab의 규모와 공개 코드에 필요한 검사만 적용합니다.
- [GEODE 운영 원칙](https://github.com/mangowhoiscloud/geode/blob/c221191bd9f90fd4a1df116f45371ec08797c2dd/GEODE.md): 허용 범위 안의 지속성, 확인한 근거에 따른 판단, 실패를 보존한 제한적 복구. GEODE runtime 기능이나 권한 tier를 이 lab에 구현된 것으로 옮기지 않습니다.
- [Trajectory publication contract](https://github.com/mangowhoiscloud/geode-eval-artifacts/blob/d277607f3a179f191ad24b1497c0934beb9d2470/TRAJECTORIES.md): 원본·파생 요약·점수 receipt의 구분, 순서·짝·출처·불완전성 보존. 기존 run 기록을 사용하며 새 schema나 저장 엔진을 추가하지 않습니다.
- [OpenAI Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering), [Claude Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices): 목적·제약·예시·참고 문맥을 분리하고 완료 조건을 명시하는 방식. 2026-09-16 본문을 확인했으며 모델별 권고를 보편 규칙으로 적용하지 않습니다. 지침 효과는 별도 평가 대상입니다.

외부 지침의 프로젝트별 명령·강제 조건을 그대로 복사하지 않습니다. 이 lab의 작업 규칙은 [AGENTS.md](AGENTS.md), 실행 순서는 [program.md](program.md), 판정 의무는 [품질 계약](docs/quality.md)에 있습니다.
