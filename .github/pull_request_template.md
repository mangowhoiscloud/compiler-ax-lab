## Problem and change

- Purpose / issue / reproduction conditions:
- Fix selected from observations and rejected alternatives:
- Behavior to preserve / intentionally changed behavior:
- Allowed scope / excluded scope:
- Selected workflow / applicable contracts (for kernel work, distinguish test strengthening, implementation changes, and evaluation-criteria changes):
- Review requirement → change → verification evidence (original permalink where applicable):

## Revision

- Baseline SHA:
- Merge path (feature → dev / dev → main):
- PR head SHA:
- PR base SHA:
- Actual verification checkout SHA (distinguish head from test merge):
- For work-in-progress publication: as-of time / complete, running, and not run / next update condition:

## Verification

| Command / check | Result (PASS / FAIL / INVALID / NOT_RUN) | Execution count and scope | Run / artifact / revision |
|---|---|---|---|
| `node scripts/check.mjs` | | | |
| Additional checks required by the change | | | |

- Changed languages / CI selection plan / intentionally excluded jobs and reasons:
- Static-check tools and versions / executed test count / skipped and ignored counts:

- Unexecuted checks, exceptions, residual risks, and decision owner:
- Environment evidence (actual tool paths, versions, working directory, and preparation failures):
- State after failure / recovery result / evidence location / retry decision owner (explain if not applicable):
- Evidence that a failing check distinguishes the intended defect:
- Record protected-check results only as publishable summaries and restricted locators. Do not attach raw records, answers, or individual logs.
- Public environment/path records use repository-relative paths or de-identified locators, without personal absolute paths or credentials.

## Human review

- AI-assisted scope / code and evidence personally checked by a human:
- [ ] Structure, API semantics, test meaning, and relevant documentation have been reviewed.
- [ ] No criteria were relaxed, checks deleted, or results ignored to obtain a pass.
- [ ] The review distinguishes expected rejection from tool failure and does not turn unexecuted or missing checks into PASS.
- [ ] The diff, including new files, contains no personal information, keys, or local-only material.
- [ ] Selected required checks for the current head/base have actually succeeded, with none missing, skipped, or cancelled. Only language jobs excluded by the plan are skipped.
- Reviewer / decision / remaining conditions:

## After merge

- Target branch post-merge run (dev / main; record after merging):
- Fix / revert path for a regression:
- Release, paid execution, and Furiosa upstream-submission approval remain separate and must not be inferred from this PR's approval.
