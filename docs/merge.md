# PR과 병합: 검사한 변경과 받아들인 변경을 연결한다

## 현재 구현과 제안의 경계

이 lab에는 [PR 템플릿](../.github/pull_request_template.md), [CI](../.github/workflows/quality.yml), [CODEOWNERS](../.github/CODEOWNERS)가 있습니다. CI는 문서·공개 파일·산술과 로컬 변경 루프 실행기의 회귀 검사를 수행합니다. 실제 Rust·NPU 검사는 아직 실행하지 않았으며 이 CI가 대신하지 않습니다.

기존 Furiosa 작업에는 head/base/통합 revision → 재검사 → 사람 병합 → post-merge CI → 별도 릴리스라는 도식이 있었지만 실제 PR 템플릿·원격 저장소·workflow는 없었습니다. 이번에는 같은 절차를 lab 운영에 연결합니다. Furiosa upstream에 PR을 올리는 일은 별도 승인입니다.

## 변경에서 병합까지

1. **범위 합의:** 문제·재현 조건·보존할 동작·허용 파일·필수 검사를 정합니다. 보호 판정기나 품질 기준 변경은 평가받는 후보와 별도 PR로 검토합니다.
2. **작은 branch:** `codex/<bounded-change>`에서 한 가설만 바꿉니다. 기존 patch가 있으면 재생성하지 않습니다. 먼저 로컬 검사와 staged diff를 봅니다.
3. **Draft PR:** 템플릿에 변경 이유·버린 대안·baseline/head/base와 검사 기록을 남깁니다. AI 보조 범위와 사람이 확인하지 않은 부분을 밝힙니다.
4. **통합 상태 검사:** PR CI의 실제 checkout SHA를 head SHA와 별도로 기록합니다. 기본 `pull_request` checkout은 test merge commit입니다. base나 head가 바뀌면 현재 조합에서 다시 검사합니다.
5. **사람 검토:** 구조·API·테스트가 주장하는 성질·문서·미실행 위험을 확인합니다. Agent 리뷰는 지적 후보이며 승인 권한이 아닙니다. 검사 통과가 인간 판단을 자동으로 대신하지 않습니다.
6. **병합:** 현재 head/base와 필수 검사의 명시적 success를 대조한 뒤 소유자가 병합합니다. push 이후 diff가 바뀌면 이전 검토가 그대로 유효한지 다시 판단합니다. auto-merge는 사용하지 않습니다.
7. **병합 후:** `main`의 새 commit에서 같은 CI가 다시 통과하는지 확인합니다. 실패하면 해당 변경의 완료 처리를 보류하고 회귀 issue와 수정 또는 revert PR을 만듭니다. 공유 branch를 reset하거나 force push하지 않습니다. 릴리스·배포는 별도 승인입니다.

```text
계약 → 작은 diff → 로컬 검사 → Draft PR
                              ↓
                    현재 head + base의 통합 검사
                              ↓ 실패: 같은 공개 계약 안에서 수정
                         사람 검토·판단
                              ↓
                          병합 commit
                              ↓
                         post-merge CI
                              ↓ 실패: issue → 수정/revert PR
                      완료 기록 · 릴리스는 별도
```

## 필수 검사와 실제 강제 수준

`lab-docs`는 path filter나 조건부 생략 없이 문서·산술·로컬 실행기 검사를 실행합니다. `lab-ci`는 `if: always()`로 실행되어 앞 job 결과가 정확히 `success`인지 확인합니다. GitHub required checks가 skipped/neutral도 허용하므로 단순히 초록색 badge만 보고 Q5를 통과시키지 않습니다. 둘 중 하나가 사라졌거나 취소·생략되면 병합하지 않습니다.

공개 후 `main`에 PR 경유, `lab-ci` 필수, 최신 base 반영, 대화 해결, force push·삭제 금지를 설정하고 API 응답으로 확인합니다. 관리자의 우회도 허용하지 않는 설정을 사용합니다. 실제 적용 결과는 공개 완료 보고에서 따로 기록합니다. 이 파일의 존재만으로 서버 설정이 적용됐다고 판단하지 않습니다.

현재 확인된 운영자는 개인 저장소 소유자 한 명입니다. 독립 리뷰어가 지정되지 않았으므로 GitHub 승인 리뷰 1개를 강제해 본인 PR을 막지는 않습니다. CODEOWNERS는 검토 요청의 대상이며 독립 리뷰를 보장하지 않습니다. 별도 리뷰어를 확보하면 required approval 1개·code owner review를 추가합니다. 그 전에는 **소유자의 수동 검토**이며 독립 동료 리뷰로 보고하지 않습니다.

처음 공개하는 bootstrap commit은 원격 규칙이 생기기 전에 올립니다. 이를 이후의 main 직접 push 관례로 사용하지 않습니다. 실제 보호 검사는 별도 실행 권한으로 두며 공개 PR 본문에 원문·정답·개별 로그를 넣지 않습니다.

## 기록의 최소 단위

PR에는 요청/issue, baseline, head, base, 실제 검사 SHA, 명령과 필수 검사 결과, 실행 수, run/artifact 위치, 예외·미실행 이유, 결정자를 남깁니다. 장치 검사가 필요한 변경은 host 결과만으로 완료시키지 않습니다. 예상 시간과 실측, 의도 오류 주입과 실제 발견 버그를 구분합니다.

템플릿 체크박스와 CI도 수정 가능한 코드입니다. 관련 변경은 diff와 소유자 리뷰를 거쳐야 하며 악의적 후보로부터 평가 기준을 격리하는 보안 장벽으로 과장하지 않습니다. 현재 규모에는 merge queue·외부 승인 서비스·새 이력 DB를 추가하지 않습니다.

GitHub 설정의 근거는 [1차 출처](sources.md)에 있습니다.
