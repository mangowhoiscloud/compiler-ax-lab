## 문제와 변경

- 목적 / issue / 재현 조건:
- 관측에서 선택한 수정과 버린 대안:
- 보존할 동작 / 의도적으로 바뀌는 동작:
- 허용 범위 / 제외 범위:

## Revision

- Baseline SHA:
- PR head SHA:
- PR base SHA:
- 실제 검사 checkout SHA (head와 test merge를 구분):

## 검증

| 명령 / 검사 | 결과 (PASS / FAIL / INVALID / NOT_RUN) | 실행 수·범위 | Run / artifact / revision |
|---|---|---|---|
| `node scripts/check.mjs` | | | |
| 변경에 필요한 추가 검사 | | | |

- 미실행·예외·남은 위험과 결정자:
- 실패한 검사가 실제 결함을 구별하는 근거:
- 보호 검사 결과는 공개 가능한 요약·제한된 locator만 기록합니다. 원문·정답·개별 로그를 붙이지 않습니다.

## 사람 검토

- AI 보조 범위 / 사람이 직접 확인한 코드·근거:
- [ ] 구조·API·테스트 의미·관련 문서를 확인했습니다.
- [ ] 기준 완화·검사 삭제·결과 무시로 통과시키지 않았습니다.
- [ ] 새 파일을 포함한 diff에 개인 정보·키·로컬 자료가 없습니다.
- [ ] 현재 head/base의 필수 검사가 실제 success이며 누락·생략·취소가 없습니다.
- 검토자 / 판단 / 잔여 조건:

## 병합 이후

- `main` post-merge run (병합 후 기록):
- 회귀 시 수정 / revert 경로:
- 릴리스·유료 실행·Furiosa upstream 제출 승인: 별도이며 이 PR 승인에서 추론하지 않습니다.
