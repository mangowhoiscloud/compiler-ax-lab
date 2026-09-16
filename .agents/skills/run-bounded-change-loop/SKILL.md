---
name: run-bounded-change-loop
description: Run or review Compiler AX Lab's bounded local Python change trial with fixed checks, preserved evidence and a human-review handoff. Not a Rust adapter or cloud execution skill.
---

# Bounded change loop

This skill is for the repository operator. Check the actual implementation scope in the [README](../../../README.md#public-system), then read only the routes below.

## Execution procedure

1. Read [program.md](../../../program.md) in full. It is authoritative for the editable target, fixed checks, attempt budget, and state transitions.
2. For an execution request, first inspect the existing run state. Start a new demo with a candidate copied from the tracked seed and a fresh run directory. Follow observation → diagnosis → minimal change → recheck under the operator's checker and limits.
3. Cross-check raw evidence, commands, candidate copies, and results. Do not rely solely on the `status` summary or the candidate's success narrative. Withhold handoff when records are missing or inconsistent and verify the actual state through the [runner](../../../scripts/trial.py).
4. At `READY_FOR_REVIEW`, hand the checked change and remaining judgments to a human. Do not automatically merge or release. Do not erase failed or STOP records or increase the budget to keep trying.

## Checks and scope

Check runner changes with Ruff, mypy, and unittest under the [language-specific static checks](../../../docs/quality.md#language-specific-static-checks-and-ci-routing); check public-file and documentation changes with `node scripts/check.mjs`. [tests/test_trial.py](../../../tests/test_trial.py) covers semantic, termination, and evidence-handling regressions. These are not Rust or NPU correctness checks. Existing runs freeze the runner hash, so do not retroactively apply an updated runner to earlier records.

For actual Rust work, follow the [quality contract](../../../docs/quality.md) and task branches in [review-to-verified-pr](../review-to-verified-pr/SKILL.md). Do not mix the existing A/B experiment's frozen contract and operator runner with the Python demo. Do not pass this operator document wholesale to candidate sessions.
