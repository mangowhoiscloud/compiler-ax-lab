# PR과 병합

이 규약은 문서·로컬 실행기·Rust 사례의 변경을 검토할 때 적용합니다. 실행 범위와 결과는 [README](../README.md#검증-상태), Rust의 판정 의무는 [품질 계약](quality.md)에 둡니다. CI·사람 채택·병합은 별도 상태입니다.

## 브랜치와 검토 상태

경로는 feature branch → `dev` → `main`입니다. 현재 `codex/executable-loop-skill`은 feature branch 역할을 합니다. feature→dev는 squash PR, dev→main은 별도 merge-commit PR로 올립니다. 장수 dev를 main에 반복 squash하면 공통 조상이 갱신되지 않아 다음 승격에 과거 변경이 다시 나타날 수 있으므로, 승격은 ancestry를 보존합니다.

`dev`와 `main`은 최신 base의 `lab-ci` 필수, 관리자 포함 보호, 대화 해결 요구, force push·삭제 금지를 적용합니다. merge commit을 허용하므로 선형 이력은 강제하지 않습니다. 독립 리뷰어 승인 수는 0명입니다. 이 규약과 실제 서버 설정을 매 병합 전에 대조하고, 사용자 요청 없이 필수 검사를 해제하거나 관리자 우회하지 않습니다. 다음 작업 주기에서는 새 feature를 dev에 넣기 전에 main→dev 동기화 PR을 merge commit으로 반영해 최신 base 조건을 맞춥니다. 이미 squash된 feature를 재사용하지 않고 동기화된 dev에서 새 작업을 시작합니다. 직접 reset하지 않습니다.

Draft는 구현이나 필수 검사가 남아 있는 작업 상태입니다. 검토 가능한 diff는 Ready for review로 전환합니다. Draft 해제·검사 성공·실험 결과 채택·저장소 병합은 서로 다릅니다. 사용자가 순차 병합을 명시적으로 요청한 범위에서는 매 단계의 현재 revision과 검사를 확인한 뒤 실행할 수 있지만, 이를 사람이 모든 실험 결과를 직접 검토했다는 기록으로 바꾸지 않습니다.

## 변경에서 병합까지

1. **범위를 정합니다.** 문제·재현 조건·보존할 동작·허용 파일·필수 검사를 고정합니다. 판정기나 품질 기준 변경은 평가받는 후보와 분리합니다.
2. **기존 branch를 확인합니다.** 한 가설에 필요한 코드·회귀 검사만 변경합니다. 현재 diff와 소유권을 읽고 무관한 리팩터링·history rewrite를 하지 않습니다.
3. **로컬에서 검사합니다.** `node scripts/check.mjs`와 [변경 언어의 정적 검사·회귀 검사](quality.md#언어별-정적-검사와-ci-분기)를 수행합니다. 적용하지 않는 검사는 선택 계획의 이유를, 미실행은 `NOT_RUN`을 남깁니다.
4. **feature→dev PR을 갱신합니다.** 기존 PR이 있으면 재사용합니다. [템플릿](../.github/pull_request_template.md)에 현재 base 대비 전체 diff와 실제 증거를 설명합니다. 공개 가능한 정확한 파일만 stage해 논리적 변경별 commit으로 push합니다. 진행 중이라면 기준 시각과 남은 절차를 적습니다.
5. **현재 CI를 확인합니다.** push 뒤 원격 head·PR head·base·실제 checkout SHA를 대조합니다. `pull_request` CI의 test merge SHA는 head SHA와 구분합니다. 둘 중 하나가 바뀌면 이전 검사 성공을 재사용하지 않습니다.
6. **검토와 권한을 확인합니다.** 구조·API 의미·테스트 판별력·미실행 위험을 검토하고 남은 사람 판단을 적습니다. AI 검토는 승인 권한이 아니며 사람 체크박스를 대신 채우지 않습니다. 구현·필수 검사가 끝난 PR을 Ready for review로 전환합니다.
7. **요청된 순서로 병합합니다.** 명시적 병합 요청, 현재 head/base, 필수 job의 정확한 success를 다시 확인해 feature→dev를 squash합니다. dev의 post-merge CI가 통과하면 그 SHA를 head로 dev→main PR을 생성합니다. 해당 PR의 현재 CI를 다시 확인한 뒤 merge commit으로 병합합니다. 자동 병합 예약이나 직접 push로 우회하지 않습니다.
8. **병합 후 확인합니다.** 새 main SHA의 post-merge CI와 승격한 dev의 tree 일치를 확인합니다. 실패하면 회귀 issue와 최소 수정 또는 해당 변경의 revert PR을 만듭니다. 릴리스·유료 실행·upstream 제출은 별도 승인입니다.

## 필수 CI와 기록

[quality.yml](../.github/workflows/quality.yml)의 `lab-system`은 항상 공개 경계·링크·CI 규약과 actionlint를 실행합니다. 변경 경로에 따라 `lab-python`, `lab-javascript`, `lab-rust`를 선택합니다. `lab-ci`는 `if: always()`로 실행해 선택된 job의 정확한 `success`를 요구하며 계획에서 제외한 언어 job의 `skipped`만 허용합니다. 계획 누락·예상하지 않은 생략·취소·neutral은 실패입니다. Python/Rust 테스트는 0개 실행이나 skip/ignore도 거절합니다. 이 CI는 독립 Rust reference를 검사하지만 SDK 전체·NPU·A/B를 실행하지 않습니다.

PR 기록에는 요청, baseline/head/base/실제 checkout SHA, 명령, 실제 테스트 수, 결과, 공개 가능한 근거 locator, 예외, 결정자가 필요합니다. 의도 오류 검출은 컴파일 성공 뒤 지정 assertion 실패여야 하며 환경 실패와 구분합니다. 중단 기록도 보존하고 수거·자원 회수를 확인합니다.

보호 원문·정답·계정·개인 절대경로는 게시하지 않습니다. 공개 요약에서 비공개 원문에 없는 수치나 성공을 만들지 않습니다. 템플릿과 CI 자체도 수정 가능한 코드이므로 검토 대상이며, 악의적 코드로부터 평가를 격리하는 보안 장벽으로 과장하지 않습니다.
