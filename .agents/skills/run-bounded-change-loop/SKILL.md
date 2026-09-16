---
name: run-bounded-change-loop
description: Run or review Compiler AX Lab's bounded local Python change trial with fixed checks, preserved evidence and a human-review handoff. Not a Rust adapter or cloud execution skill.
---

# Bounded change loop

이 저장소의 운영자용 스킬입니다. [README](../../../README.md#공개된-시스템)에서 실제 구현 범위를 확인하고 아래 경로만 읽습니다.

## 실행 순서

1. [program.md](../../../program.md)를 전부 읽습니다. 수정 대상·고정 검사·시도 예산·상태 전이의 정본입니다.
2. 실행 요청이면 기존 run 상태부터 확인합니다. 새 데모는 추적된 seed를 복사한 후보와 새 run 디렉터리에서 시작합니다. 운영자가 정한 검사기·한도 아래에서 관측 → 진단 → 최소 변경 → 재검사를 수행합니다.
3. 원문·명령·후보 사본·결과를 대조합니다. `status`의 요약이나 후보의 성공 설명만 믿지 않습니다. 기록 누락·불일치는 인계를 보류하며 [실행기](../../../scripts/trial.py)의 실제 상태 검사로 확인합니다.
4. `READY_FOR_REVIEW`이면 검사한 변경과 남은 판단을 사람에게 넘깁니다. 자동 병합·릴리스하지 않습니다. 실패·STOP을 지우거나 예산을 늘려 반복하지 않습니다.

## 검사와 적용 범위

실행기 변경은 [언어별 정적 검사](../../../docs/quality.md#언어별-정적-검사와-ci-분기)의 Ruff·mypy·unittest, 공개 파일·문서 변경은 `node scripts/check.mjs`로 검사합니다. 의미·종료·증거 처리의 회귀는 [tests/test_trial.py](../../../tests/test_trial.py)에 있습니다. 이 검사는 Rust·NPU 정확성 검사가 아닙니다. 기존 run은 실행기 hash를 고정하므로 도구 보강 뒤 새 실행기를 과거 기록에 소급 적용하지 않습니다.

실제 Rust 작업은 [품질 계약](../../../docs/quality.md)과 [review-to-verified-pr](../review-to-verified-pr/SKILL.md)의 작업 분기를 따릅니다. 기존 A/B의 동결 계약·운영자 실행기와 Python 데모를 혼합하지 않습니다. 이 운영자 문서를 후보 세션에 통째로 전달하지 않습니다.
