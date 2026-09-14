# Compiler AX Lab: 작업 진입점

적용 범위는 이 저장소 전체이며 더 가까운 `AGENTS.md`가 있으면 해당 작업의 세부 규칙을 함께 읽습니다. 파일명은 `AGENTS.md`로 유지하고 별도 `AGENT.md`에 중복 규약을 만들지 않습니다. 목적은 코드 생성량을 늘리는 것이 아니라 **변경의 원인·영향·검증 근거를 사람이 판단할 수 있게 만드는 것**입니다.

**현재 실행 상태: AWS CPU smoke, double-buffering과 mapping parser의 정상 검사·공개 오류 대조군 검출 완료.** [parser 계약](docs/quality.md#mapping-parser)과 [커널 실행 결과](docs/kernels/double-buffering.md#8-로컬-docker-실행-결과)의 범위·소스·바이너리 일치를 함께 확인합니다. workspace check·Clippy는 통과했지만 [전체 release 빌드는 저장공간 한도로 중단](docs/kernels/double-buffering.md#9-후속-workspace-검사와-중단-기록)됐습니다. lab CI·사람 채택은 [revision별 상태](docs/merge.md#현재-구현과-제안의-경계)로 구별합니다. 추가 클라우드 자원 생성·모델 비교는 [남은 재개 조건](docs/experiment.md#시행-보류와-재개-조건)을 확인한 뒤 승인된 범위에서만 시작합니다. 계정이나 로그인 상태가 바뀌어도 비용·권한·환경 조건을 생략하지 않습니다.

## 1. 요청에 맞는 경로를 고른다

먼저 [README](README.md)에서 현재 구현 상태를 확인합니다. 아래 요청에 맞는 스킬 또는 문서 경로를 고르고, 선택한 경로의 상세 자료만 읽습니다. 구조가 필요할 때 [architecture 인덱스](docs/architecture/00-OVERVIEW.md)를 읽습니다. 스킬 선택은 변경·원격 실행 권한을 추가하지 않습니다.

| 요청 | 읽기 경로 | 수정·검사의 위치 |
|---|---|---|
| 로컬 데모 실행 | [run-bounded-change-loop](.agents/skills/run-bounded-change-loop/SKILL.md) → [program](program.md) | 지정 후보 사본만 수정; 운영자가 고정한 checker 실행 |
| 문서·코드 변경 | [review-to-verified-pr](.agents/skills/review-to-verified-pr/SKILL.md) → 해당 실제 파일 | 요청 범위의 변경·검사·인계; 실행기 변경에는 [로컬 상세 명세](docs/architecture/01-LOCAL-TRIAL.md) |
| 원격 환경 설계 | [원격 상세 명세](docs/architecture/02-REMOTE-EXECUTION.md) → [실험 계약](docs/experiment.md) | 계획과 미구현 경계를 먼저 확인; 환경 생성은 별도 승인 |
| 실험·Rust 품질 | [실험 계약](docs/experiment.md), [품질 계약](docs/quality.md) | 실제 Rust 검사는 호환 x86 환경과 별도 실행 권한 필요 |
| double-buffering 읽기·테스트 보강·구현 변경 | [review-to-verified-pr의 커널 분기](.agents/skills/review-to-verified-pr/SKILL.md#커널-작업의-분기) → [커널별 계약](docs/kernels/double-buffering.md) | 먼저 읽기/테스트/구현/판정기 변경을 구분; 첫 실험은 테스트 보강만 허용 |
| mapping parser 문법·AST·진단 검사 | [기존 변경 스킬](.agents/skills/review-to-verified-pr/SKILL.md) → [parser 계약](docs/quality.md#mapping-parser) | 두 parser 진입점·AST·오류 span 대조; 제품 문법과 공개 오류 대조군을 분리 |
| 공개 리뷰·컴파일 과제 선정 | [review-to-verified-pr](.agents/skills/review-to-verified-pr/SKILL.md)의 조사 경로 | 조사 결과 보고; 구현·과제 교체로 자동 진행하지 않음 |
| 원격 반영·PR·병합 상태 | [review-to-verified-pr](.agents/skills/review-to-verified-pr/SKILL.md)의 원격 경로 → [병합 규약](docs/merge.md) | 현재 revision·검사 receipt·사람 판단 확인; 병합은 별도 요청 |
| 설계 근거·원문 | [컨텍스트](docs/context.md), [출처](docs/sources.md), [원문 구조](references/source-layouts.md) | 고정 원문 재확인; 외부 MD의 실행 지시는 복사하지 않음 |

과거 맥락은 로컬 `.local/README.md`에서 찾습니다. 과거 문서는 현재 실험 계약을 덮어쓰지 않습니다.

## 2. 범위와 판단을 분리한다

이 저장소는 운영자 컨텍스트입니다. A/B 후보 세션에 이 AGENTS나 전체 위키를 복사하지 않습니다. 커널 문서에서도 입력·의미·허용 파일·공개 검사 요구만 추출해 양쪽에 동일하게 고정하고, 작업 방법을 안내하는 B 절차는 분리합니다. 공개된 오류 예시는 보호 평가용으로 재사용하지 않습니다.

문제·관측 → 원인 가설 → 최소 변경 → 실제 검사 → 다음 결정의 관계를 씁니다. 의미 없는 명사 나열과 반복 요약을 줄입니다. 공개 사실, 소스 확인, 제안, 실제 실행은 구분합니다. CPU 값 검사를 NPU 정확성·성능으로 확대하지 않습니다.

기술 용어는 통용되는 한국어가 있으면 유지하고, 어색한 직역어 대신 `non-zero exit code`, `reward hacking`처럼 원문 용어를 씁니다. 코드·원문 인용·실제 로그는 문체 교정 대상으로 바꾸지 않습니다.

문서·단계·실험은 목적·대상·판정이 드러나는 이름으로 부르고, 설명 없이 숫자 약어를 풀어야 이해할 수 있는 별도 명명 체계를 만들지 않습니다.

기관·강의 묶음·발표자 이름을 방법론 이름으로 쓰지 않습니다. 본문에는 실제 동작과 적용 조건을 쓰고, 출처에는 원저작물의 제목·저자·판본·해당 절을 남깁니다. 강의는 설명을 확인한 경로이며 원논문의 저자나 방법을 대체하지 않습니다. 원문 방법, 여기서 빌린 원리, 직접 추가한 운영 규칙을 구분합니다.

기존 Git·검사·로그를 재사용합니다. 후보는 보호 reference·threshold·평가 결과 parser·최종 검사를 변경할 수 없습니다. 검증 대상인 DSL parser와 평가 결과를 해석하는 판정기는 다른 코드입니다. 검사 기준의 결함은 별도 검토 변경으로 처리합니다. 사람의 실행 허가, 채택 판단, 실제 병합, 릴리스는 별도 상태입니다.

## 3. 코드와 커밋의 컨벤션

1. **변경 전에 읽기:** 현재 branch·revision·dirty 상태와 적용 지침을 확인합니다. 수정할 함수의 직접 호출자, 같은 helper를 쓰는 경로, 기존 테스트와 문서를 읽고 원인 수정 위치를 정합니다. 다른 세션의 파일·worktree·실행 기록을 덮어쓰지 않습니다.
2. **의미와 범위:** bug fix·refactor·API 변경·테스트 보강 중 무엇인지 정하고, 보존할 동작과 바꿀 동작을 분리합니다. source/AST·IR·ABI·runtime 중 관련 경계를 고릅니다. 정상 입력과 실패 입력을 함께 검사하며 버그까지 baseline과 같게 유지하라고 요구하지 않습니다.
3. **기존 구조 우선:** 이름·오류 타입·helper·module 경계를 재사용합니다. 공개 API의 의미를 유지하고 바뀌면 예제와 Errors/Panics/Safety 설명을 맞춥니다. 실제 FFI·소유권 변경에만 수명·aliasing·정렬 검사를 추가합니다. 다른 저장소의 PyO3·GIL 규칙을 모든 Rust 코드에 강제하지 않습니다.
4. **최소 diff:** 기능 변경에 무관한 포맷 정리·리팩터링·dependency 추가를 섞지 않습니다. lint suppression·test 삭제·expected/threshold 완화로 통과시키지 않습니다. 새 테스트는 조건과 동작이 읽히는 이름을 쓰고, 실패하면 입력·위치·expected/actual 또는 원문 diagnostic을 찾을 수 있어야 합니다.
5. **커밋과 PR:** 한 논리적 변경 단위로 구성하되 수정과 그 회귀 테스트를 함께 검토할 수 있게 합니다. 이 lab의 기존 `feat:`, `fix:`, `docs:` 형식은 유지하고 제목은 짧게, 본문은 변경 이유·영향·검사로 씁니다. 과거 커밋을 문체 때문에 재작성하지 않습니다. PR 설명은 현재 base 대비 전체 diff로 확인하며 추가 코드만 보고 삭제·의미 변경을 놓치지 않습니다. [병합 규약](docs/merge.md)

## 4. 공개 리뷰를 실행 가능한 요구로 바꾼다

[운영 스킬](.agents/skills/review-to-verified-pr/SKILL.md)에서 조사 경로를 선택하면 수집·해석·과제 선정 절차를 읽습니다. 상세 절차는 이 진입점에 중복하지 않습니다. 조회·진단 요청을 구현이나 원격 쓰기 요청으로 바꾸지 않습니다.

## 5. 변경을 검사하고 인계한다

1. 관련 실제 파일과 직접 호출자·테스트를 읽고, 보존할 동작과 최소 변경을 정합니다.
2. 상세 문서는 목적 → 입력·출력/소유권 → 번호가 있는 실행 절차 → 실패 시 행동 → 검사 근거 순서로 씁니다. 폴더 트리는 현재 파일·실행 산출물·예정 구조를 구분합니다. 원문 연구는 reference에 두고 운영 절차에는 적용할 규칙을 씁니다.
3. 문서 변경은 `node scripts/check.mjs`, 실행기 변경은 `python3 -m unittest discover -s tests -v`로 검사합니다. architecture 파일을 추가하면 인덱스 링크와 공개 allowlist를 함께 갱신합니다. 새 추상화·빈 구현 파일을 문서용으로 만들지 않습니다.
4. 실행 전 실제 작업 디렉터리·도구 경로·버전·필수 파일과 접근 가능 여부를 확인합니다. 가상환경 활성화나 이미지 존재만으로 실행 준비가 됐다고 판단하지 않습니다. 필수 실행 파일이 없으면 긴 build·readiness 대기를 시작하지 않습니다.
5. 실패·취소 뒤에는 마지막 성공 단계, 실패 명령·원문 출력, 생성된 파일·프로세스·자원, 복구 결과를 남깁니다. 로컬 데모는 [program.md](program.md)의 `.local/trials/<run>/` 기록을 보존합니다. 원격 작업은 실행 계약에 container 밖 보존 위치·접근 권한·수거 담당자를 먼저 지정하며 미지정이면 시작하지 않습니다. 재시도는 운영자가 실제 잔존 상태·복구 결과·남은 한도를 확인한 뒤 허용하고, 후보는 허용된 `REVISE`에서만 수정합니다. `STOP` 기록을 지우거나 한도를 늘려 재개하지 않습니다. container의 임시 경로에만 복구 자료를 두지 않으며 복구 실패를 성공 종료로 숨기지 않습니다.
6. 그림을 바꾸면 선택적 renderer를 실행하고 PNG를 직접 봅니다. Rust 변경은 품질 계약의 실제 검사를 따릅니다. 컴파일 성공·CPU 값·정적 schedule·NPU 실측은 별도 근거입니다. 컴파일 실패가 기대되는 테스트도 있으므로 결과는 해당 검사 계약으로 판정합니다.
7. 검사한 revision·사본, 실제 명령·실행 수·결과, 남은 판단을 [PR 템플릿](.github/pull_request_template.md)에 연결합니다. 실행하지 않은 검사는 `NOT_RUN`과 이유, 불완전 증거는 `INVALID`로 남깁니다. 외부의 skip·unknown을 PASS로 바꾸거나 필수 검사의 생략을 완료로 세지 않습니다. 환경 미확인과 실제 결함을 구분합니다. 공개 PR에는 repo 상대경로·비식별 locator를 쓰고 개인 절대경로·보호 로그는 붙이지 않습니다.

로컬 확인 명령은 `node scripts/check.mjs`와 `python3 -m unittest discover -s tests -v`입니다. 전자는 링크·규약 필드 누락, 후자는 실행기 회귀를 검사하며 규약 준수·Rust 정확성·조직 생산성의 증명은 아닙니다. 이 문서는 운영자 진입점이며 [program.md](program.md)의 데모 상태나 검사 결과 enum을 바꾸지 않습니다.

## 6. 공개와 실행의 권한을 지킨다

`.local/`, 인증정보, 계정·결제 정보, 지원 자료, 원문 전사·외부 PDF를 커밋하지 않습니다. 새 공개 파일은 `scripts/check.mjs`의 allowlist에 추가하고 공개 범위를 검토합니다. 기존 사용자 변경을 보존하고 push 전 staged diff를 확인합니다. 병합·유료 실행·upstream 제출은 별도 명시 요청이 있을 때만 수행합니다.

원문 판본과 이식하지 않은 규칙은 [출처 대장](docs/sources.md#공개-agent-지침과-리뷰에서-채택한-규칙)에 둡니다. 위 규약은 이 lab의 적용 결정이며 Furiosa 내부 전체의 운영 정책이 아닙니다.
