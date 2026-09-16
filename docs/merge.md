# Pull requests and merges

This contract applies to changes to documentation, the local runner, and Rust examples. The [README](../README.md#verification-status) records execution scope and results; the [quality contract](quality.md) defines Rust evaluation obligations. CI success, human acceptance, and merge are separate states.

## Branches and review status

The path is feature branch → `dev` → `main`. Use a squash PR for feature→dev and a separate merge-commit PR for dev→main. Repeatedly squash-merging a long-lived dev branch into main leaves their common ancestor unchanged and can reintroduce old changes into later promotions; preserve ancestry during promotion.

Both `dev` and `main` require `lab-ci` against the latest base, protections enforced for administrators, resolved conversations, and no force pushes or deletions. Merge commits are allowed, so linear history is not required. The required number of independent reviewer approvals is zero. Compare this contract with the live server settings before every merge. Do not disable required checks or bypass protection as an administrator without a user request. At the next work cycle, merge a main→dev synchronization PR with a merge commit before adding a new feature to dev, keeping the base current. Do not reuse a feature branch that has already been squash-merged; start from synchronized dev. Do not reset branches directly.

Draft means implementation or required checks are still incomplete. Move a reviewable diff to Ready for review. Removing Draft status, passing checks, accepting experiment results, and merging the repository are distinct actions. When the user explicitly requests sequential merges, execute within that scope after checking each step's current revision and results. Do not turn that authorization into a record that a person has personally reviewed every experiment result.

## From change to merge

1. **Define scope.** Freeze the problem, reproduction conditions, behavior to preserve, allowed files, and required checks. Keep changes to the evaluator or quality criteria separate from the candidate being evaluated.
2. **Inspect the existing branch.** Change only the code and regression checks needed for one hypothesis. Inspect the current diff and ownership; avoid unrelated refactoring and history rewriting.
3. **Check locally.** Run `node scripts/check.mjs` and the [static and regression checks for changed languages](quality.md#language-specific-static-checks-and-ci-routing). Record selection-plan reasons for inapplicable checks and `NOT_RUN` for checks not executed.
4. **Update the feature→dev PR.** Reuse an existing PR when present. Use the [template](../.github/pull_request_template.md) to explain the entire diff against the current base and its actual evidence. Stage only exact publishable files, commit logical changes separately, and push. For work in progress, record an as-of time and remaining steps.
5. **Verify current CI.** After pushing, compare the remote head, PR head, base, and actual checkout SHA. Distinguish the `pull_request` test-merge SHA from the head SHA. If the head or base changes, do not reuse the previous successful check.
6. **Verify review and authority.** Review structure, API semantics, test discrimination, and risks in unexecuted scope. Record remaining human decisions. AI review does not grant approval authority or allow filling human checkboxes. Mark the PR Ready for review once implementation and required checks are complete.
7. **Merge in the requested order.** Recheck the explicit merge request, current head/base, and exact `success` results for required jobs, then squash feature→dev. After dev's post-merge CI passes, create a dev→main PR using that SHA as head. Recheck that PR's current CI before merging with a merge commit. Do not bypass the process with scheduled auto-merge or direct pushes.
8. **Verify after merging.** Check post-merge CI for the new main SHA and tree equality with the promoted dev revision. On regression, create an issue and a minimal-fix or revert PR for the affected change. Release, paid execution, and upstream submission require separate approval.

## Required CI and records

In [quality.yml](../.github/workflows/quality.yml), `lab-system` always checks publication boundaries, links, CI contracts, and actionlint. Changed paths select `lab-python`, `lab-javascript`, and `lab-rust`. `lab-ci` runs with `if: always()`, requires exact `success` from selected jobs, and allows `skipped` only for language jobs excluded by the plan. A missing plan, unexpected skip, cancellation, or neutral result fails the gate. Python/Rust tests also reject zero executed tests and skipped/ignored tests. CI checks the standalone Rust reference; it does not run the full SDK, NPU, or A/B experiment.

PR records must include the request, baseline/head/base/actual checkout SHAs, commands, actual test counts, results, publishable evidence locators, exceptions, and decision owner. Intentional-fault detection requires successful compilation followed by failure at the designated assertion; distinguish it from environment failure. Preserve stop records and verify evidence collection and resource cleanup.

Do not publish protected raw records, answers, accounts, or personal absolute paths. Do not invent numbers or successes in a public summary that are absent from the private original. Templates and CI are themselves editable code requiring review, not a security barrier that isolates evaluation from malicious code.
