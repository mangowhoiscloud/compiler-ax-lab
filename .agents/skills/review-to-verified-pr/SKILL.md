---
name: review-to-verified-pr
description: Turn public code reviews into scoped requirements, implement requested Compiler AX Lab changes, and hand off a revision-verified Draft PR when authorized. Use for this repository's review, change and PR workflow, not local trial execution or cloud provisioning.
---

# Review to verified PR

이 저장소의 운영자용 스킬입니다. 기존 Git·검사·PR을 사용하며 별도 실행 엔진을 만들지 않습니다. 조회·진단 요청은 보고에서 끝내고, 변경·push·PR 작성은 사용자가 요청한 범위에서만 수행합니다. 스킬 선택 자체는 실행 권한이 아닙니다.

## 1. 요청한 경로만 읽는다

| 요청 | 필요한 상세 자료 | 여기서 끝낼 조건 |
|---|---|---|
| 공개 리뷰·조직 기준 조사 | [리뷰 근거 수집](references/review-evidence.md) | 확인한 요구·미확인 범위 보고; 구현으로 자동 진행하지 않음 |
| 문서·코드 변경 | [공통 컨벤션](../../../AGENTS.md#3-코드와-커밋의-컨벤션), [검사·인계](../../../AGENTS.md#5-변경을-검사하고-인계한다), 해당 실제 파일 | 요청한 diff와 검사 결과; 원격 반영 요청이 없으면 로컬에서 인계 |
| 원격 반영·PR 검사 | [병합 규약](../../../docs/merge.md), [PR 템플릿](../../../.github/pull_request_template.md), [실제 CI](../../../.github/workflows/quality.yml) | 현재 revision의 원격·검사 상태 보고; 병합은 별도 요청 |

리뷰 근거가 필요한 변경에서만 첫 경로를 함께 읽습니다. 단순 문서 수정이나 기존 PR 동기화에 외부 리서치를 강제하지 않습니다. 로컬 후보 데모 실행은 [run-bounded-change-loop](../run-bounded-change-loop/SKILL.md)로 넘기고, 설계·Rust·원격 환경 요청은 [AGENTS의 해당 경로](../../../AGENTS.md#1-요청에-맞는-경로를-고른다)를 선택합니다. 전체 위키·원문을 선행 로드하지 않습니다.

## 2. 관측에서 변경과 검사로 연결한다

1. 현재 요청이 조사·진단·변경·원격 반영 중 어디까지 허용하는지 정합니다. branch·revision·dirty 상태·다른 작업 소유권을 확인하고, 조사에서는 원문·당시 코드, 변경에서는 실제 구현·직접 호출자·기존 검사를 읽습니다.
2. 관측한 문제와 보존할 동작, 허용 파일, 선택한 수정, 실패를 구별할 검사를 연결합니다. 조사만 요청받았다면 이 판단을 보고하고 끝냅니다. 범위 안의 변경은 기존 helper와 검사 명령을 재사용하며, 원인 수정과 회귀 근거를 함께 남깁니다.
3. 문서·공개 경계는 `node scripts/check.mjs`, 실행기 변경은 `python3 -m unittest discover -s tests -v`로 검사합니다. 원격 lab CI는 두 명령을 모두 실행합니다. Rust가 관련될 때만 [품질 계약](../../../docs/quality.md)의 표적 검사를 고르며, 환경·권한 미확정은 `NOT_RUN`, 불완전 증거는 `INVALID`로 기록합니다. 데모 통과를 Rust·NPU 결과로 쓰지 않습니다.
4. 결과에서 다음 행동을 정합니다. 실패는 원문 diagnostic·실제 남은 상태를 확인한 뒤 허용 범위에서 수정하거나 인계합니다. 요청한 변경 밖의 결함, 보호 검사 변경, 비용·권한 확대는 멈춰 설명합니다. 통과하면 검사한 사본과 남은 위험을 인계하고 원격 요청이 있을 때만 다음 절로 갑니다.

## 3. 승인된 변경만 원격에서 확인한다

1. 원격 URL·소유자·공개 범위와 branch·기존 PR을 조회합니다. 공개 가능한 정확한 파일만 stage하고 staged diff·현재 base 대비 전체 diff를 확인합니다. 기존 branch와 PR을 재사용하되 타 작업을 섞지 않습니다. force push·main 직접 push·중복 PR 생성으로 우회하지 않습니다.
2. 승인된 commit/push 뒤 원격 head와 PR head를 확인합니다. push 응답이 불명확하면 원격 ref부터 다시 읽고 중복 실행을 피합니다. 기존 Draft/검토 상태를 임의로 바꾸지 않습니다.
3. 현재 head/base와 CI의 실제 checkout SHA를 연결합니다. 필수 job이 모두 명시적 `success`인지 확인하고 누락·취소·생략은 통과로 세지 않습니다. CI 실패 시 로그를 조사하고 관련 최소 수정 후 새 SHA에서 검사합니다. base/head 변경 뒤의 오래된 통과 결과는 재사용하지 않습니다.
4. PR 설명을 현재 전체 diff와 검사 기록으로 갱신합니다. AI 검토를 사람 승인으로 표시하지 않고, 미실행·환경·잔여 위험을 템플릿에 남깁니다. 마지막으로 PR·원격 ref·로컬 상태를 다시 읽어 `로컬 변경 / push / CI / 사람 검토 / 병합`을 구분해 보고합니다. 병합·릴리스·유료 실행·Furiosa upstream 제출은 자동 후속 작업이 아닙니다.

이 스킬과 공통 규약은 A/B 후보에게 통째로 주입하지 않습니다. 후보에게 제공할 절차와 같은 공개 요구는 별도 실험 계약에서 정합니다.
