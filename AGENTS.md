# Compiler AX Lab: 작업 진입점

먼저 `README.md`를 읽고 요청과 관련된 정본만 이어 읽습니다.

- 로컬 변경 루프 실행: `.agents/skills/run-bounded-change-loop/SKILL.md` → `program.md`.
- 설계 판단: `docs/context.md`. 원문 사례의 폴더 구조: `references/source-layouts.md`.
- 실험 변경: `docs/experiment.md`, `docs/quality.md`.
- PR·병합: `docs/merge.md`, `.github/pull_request_template.md`.
- 벤더·연구 주장: `docs/sources.md`의 고정 원문을 재확인합니다.
- 기존 맥락 복구: 로컬 `.local/README.md`. 과거 문서는 현재 실험 계약을 덮어쓰지 않습니다.

이 저장소는 운영자 컨텍스트입니다. A/B 후보 세션에 이 AGENTS나 전체 위키를 복사하지 않습니다. 동일 공개 요구·기존 upstream 지침을 제공하고 B 절차만 분리합니다. 공개된 오류 예시는 보호 평가용으로 재사용하지 않습니다.

문제·관측 → 원인 가설 → 최소 변경 → 실제 검사 → 다음 결정의 관계를 씁니다. 의미 없는 명사 나열과 반복 요약을 줄입니다. 공개 사실, 소스 확인, 제안, 실제 실행은 구분합니다. CPU 값 검사를 NPU 정확성·성능으로 확대하지 않습니다.

기술 용어는 통용되는 한국어가 있으면 유지하고, 어색한 직역어 대신 `non-zero exit code`, `reward hacking`처럼 원문 용어를 씁니다. 코드·원문 인용·실제 로그는 문체 교정 대상으로 바꾸지 않습니다.

기존 Git·검사·로그를 재사용합니다. 후보는 보호 reference·threshold·parser·최종 검사를 변경할 수 없습니다. 검사 기준의 결함은 별도 검토 변경으로 처리합니다. 사람의 실행 허가, 채택 판단, 실제 병합, 릴리스는 별도 상태입니다.

문서 수정 후 `node scripts/check.mjs`, 실행기 수정 후 `python3 -m unittest discover -s tests -v`를 실행합니다. 그림을 바꾸면 선택적 renderer를 실행하고 PNG를 직접 봅니다. 실제 Rust 변경은 품질 계약의 해당 검사와 별도 x86 실행 환경이 필요합니다. 미실행을 통과로 기록하지 않습니다.

`.local/`, 인증정보, 계정·결제 정보, 지원 자료, 원문 전사·외부 PDF를 커밋하지 않습니다. 새 공개 파일은 `scripts/check.mjs`의 allowlist에 추가하고 공개 범위를 검토합니다. 기존 사용자 변경을 보존하고 push 전 staged diff를 확인합니다. 병합·유료 실행·upstream 제출은 별도 명시 요청이 있을 때만 수행합니다.
