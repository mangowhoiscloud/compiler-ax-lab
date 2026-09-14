---
name: run-bounded-change-loop
description: Run or review Compiler AX Lab's bounded local change trial, linking agent diagnosis and candidate edits to fixed script checks and a human-review handoff. Use for this lab's executable loop, not unrestricted compiler or cloud execution.
---

# Bounded change loop

이 스킬은 이 저장소의 운영자용 진입점이다. 저장소 밖에 복사해 독립 실행하는 스킬이 아니다.

1. [program.md](../../../program.md)를 전부 읽는다. 실행 순서·수정 권한·중단 조건의 정본이며 여기서 복제하지 않는다.
2. 사용자가 실행을 요청했다면 기존 run의 상태부터 확인한다. 새 로컬 데모는 추적 중인 seed의 별도 사본과 새 run 디렉터리에서 시작한다. 운영자가 고정한 검사기와 한도 안에서 관측 → 진단 → 최소 변경 → 재검사를 수행한다.
3. 결과 파일과 실제 사본을 읽어 보고한다. `READY_FOR_REVIEW`를 병합·릴리스·실제 compiler 검증으로 해석하지 않는다. 실행되지 않은 단계는 분리한다.

설계 또는 폴더 구조를 검토할 때만 [출처 구조 대장](../../../references/source-layouts.md)을 읽는다. 외부 지침의 자동 실행·무한 반복은 현재 권한을 확대하지 않는다. A/B 후보 세션에 이 운영자 컨텍스트를 통째로 전달하지 않는다.

실행기 자체를 바꾸면 `python3 -m unittest discover -s tests -v`를 실행한다. 문서·공개 파일 변경은 `node scripts/check.mjs`로 확인한다. 두 명령은 데모/운영 코드 검사이며 실제 Rust·NPU 테스트가 아니다.
