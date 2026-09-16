# Compiler AX Lab

An experiment in turning coding-agent drafts into **changes a compiler developer can review**. The focus is not how much code was generated, but what changed and which checks actually verified it.

Successful compilation does not establish that output semantics were preserved. Correct values may come from a stale binary; a failed test may detect an environment problem rather than the intended fault. This lab fixes the change scope first, then uses independent expected values, normal/fault controls, and source-to-binary evidence to distinguish those cases.

```text
Problem and preserved behavior → Cause hypothesis → Bounded change → Fixed checks
                                                                         ↓
                                        Cross-check source, commands, values, and exit status
                                                                         ↓
                                                         Human review → Separate merge
```

This is independent research, unaffiliated with FuriosaAI. It uses Rust examples from the public `furiosa-opt` repository; it does not reproduce Furiosa's internal production compiler or NPU.

## Public system

| Component | Responsibility | Entrypoint |
|---|---|---|
| Work rules | Define request scope, conventions, Git flow, and publication boundaries. | [AGENTS.md](AGENTS.md) |
| Experiment supervision | Resume the authorized phase, validate raw evidence, preserve failures, and collect before advancing. | [Operator program](program.md#supervise-an-approved-experiment) |
| Execution skill | Diagnose, change, and check a separate candidate copy within a finite attempt budget. | [run-bounded-change-loop](.agents/skills/run-bounded-change-loop/SKILL.md), [program.md](program.md) |
| Local runner | Freeze the contract and checker; revalidate attempt reservations, raw evidence, copies, and results. | [trial.py](scripts/trial.py), [regression tests](tests/test_trial.py) |
| Rust test cases | Check numerical semantics for three kernels and grammar, AST, and diagnostic locations for the parser. | [double-buffering](docs/kernels/double-buffering.md), [mapping parser](docs/quality.md#mapping-parser) |
| Review and PR skill | Link the current diff to the actual checked revision and update the existing PR. | [review-to-verified-pr](.agents/skills/review-to-verified-pr/SKILL.md), [merge contract](docs/merge.md) |

The public runner is a Python standard-library demo. The Rust cases are tests and patches reproduced through Cargo in a compatible x86-64 environment, not through `trial.py --task furiosa`. A/B operator runners, account records, protected inputs, and raw evidence remain local.

## Quick checks

Run from the root of a Git clone. Git, Node.js 22 or later, and Python 3.9 or later on a Unix-like system are sufficient to check the public system without extra packages.

```bash
node scripts/check.mjs
python3 -m unittest discover -s tests -v
```

The first command checks public files, sensitive information, reading routes, and PR/CI contracts. The second checks normal, failed, and stopped runner behavior and validation of stored evidence. Neither checks Rust or NPU correctness.

Before submitting a change, also run the [language-specific quality checks](docs/quality.md#language-specific-static-checks-and-ci-routing). CI always checks public files, documentation, and workflows. Changed paths select Python Ruff, mypy, and regression checks; JavaScript Biome checks; or Rust formatting, independent-reference Clippy/tests, and patch checks. `lab-ci` rejects failed, cancelled, or missing selected jobs. Only the check tools are development dependencies; the demo does not require them.

Follow [program.md](program.md) for the change demo. The seed contains an intentional defect, so edit only a copy. The default budget is two checks including the baseline, with ten seconds per invocation. Edit only in `REVISE`; `READY_FOR_REVIEW` is a human handoff state, not automatic approval. Missing evidence, timeouts, and exhausted limits leave the run in `STOP`.

## Reproducing the Rust cases

The baseline is `furiosa-opt` v0.8.1, commit `9b9cf0fdc78df00cdc430eae725a5ad9084a735e`, with `nightly-2026-05-01`. Prepare SDK-compatible x86-64 Linux and native dependencies, then record the lockfile, tools, commands, and limits under the [quality contract](docs/quality.md). The Rust CI job does not install the SDK's native environment; it checks only the independent reference and patch applicability.

- **Double-buffering:** Apply the [SDK tests](examples/furiosa-double-buffering/tests/double_buffering_tests.rs) and [independent scalar reference](examples/furiosa-double-buffering/tests/support/double_buffering_reference.rs) to the pinned checkout. Compare every output coordinate across the three implementations under the [input/numerical contract and commands](docs/kernels/double-buffering.md).
- **Mapping parser:** Apply the [test patch](examples/furiosa-mapping-parser/tests.patch) to check ASTs, diagnostic text, and byte ranges through both parser entrypoints. Follow the [scope and commands](docs/quality.md#mapping-parser).
- Public fault patches test the checker's ability to distinguish faults in a separate copy. They are neither bugs discovered upstream nor answers for the protected A/B evaluation.

## Verification status

The following evidence comes from distinct executions. Test counts, element comparisons, and A/B evaluation units are not interchangeable and are not summed.

| Execution | Verified result | Scope |
|---|---|---|
| AWS unchanged CPU smoke | One designated assertion passed; 94 files collected and checked; created resources reclaimed | Native x86 environment readiness, not a new candidate's performance |
| Public double-buffering test improvement | Three SDK tests, 18 input executions, and 46,080 matching values; two helper tests passed. The public fault copy compiled, then failed the designated numerical assertion | CPU checks for fixed shapes and exactly representable bf16 inputs |
| Public mapping-parser test improvement | Expanded from six to twelve passing checks. The designated check detected the public fault copy's incorrect acceptance | ASTs and diagnostics through two entrypoints. The fault copy failed at the mapping assertion first |
| CPU workspace integration of both changes | 720 regular tests, 55 doctests, and all-target release Clippy passed | Default features. Excludes 17 ignored tests; 44 of the 55 doctests are `compile_fail` |
| Local runner | Sixteen regression tests passed | Python demo and evidence handling, separate from compiler correctness |

Local CPU experiments use Ubuntu 24.04 amd64/Rosetta, 2 CPUs, 6 GiB, and Cargo jobs=1. The remote unchanged smoke is a separate AWS x86 run. Verified scope excludes NPU timing, overlap and performance, full non-default-feature coverage, and human acceptance.

### A/B pilot: execution complete, human review pending

**Final execution completed 2026-09-16 19:39 KST.** The pilot compares A, given the detailed common task, with B, given the same task plus a research, diagnosis, change, and verification procedure. It uses one task and one pair, with candidate generation in a fixed B-then-A order.

| Item | A: common task | B: additional procedure |
|---|---|---|
| Generation | Draft complete | Draft complete |
| Public checks | After one revision, formatting, compilation, three SDK tests, one helper test, and Clippy passed; earlier interruption and recovery records preserved | After one revision, formatting, compilation, three SDK tests, one helper test, and Clippy passed |
| Source freeze | Complete; source and review message frozen | Complete; source and review message frozen |
| Private implementation build | Compiled; source and binary linked to the frozen candidate | Compiled; source and binary linked to the frozen candidate |
| Final normal/fault comparison | Three normal controls passed (TN); one qualified fault detected (TP) | Three normal controls passed (TN); one qualified fault detected (TP) |
| Invalid or unexecuted final units | 0 of 4 | 0 of 4 |
| Human work time and acceptance | PENDING | PENDING |

All eight final units ran once after both source trees and review messages were frozen. Each executed exactly one selected SDK test, with none ignored. Review traced the two expected failures to the intended numerical assertions, not compilation, timeout, or unrelated panics. Source snapshots, binary identities, complete output vectors, test counts, and runtime exits agreed; all 825 final artifacts were rehashed. Raw observations remain separate from operator classifications and human acceptance. Owned staging/runtime containers and temporary images were removed after collection.

**The final control result is a tie: no observed false positives or false negatives in this small control set.** A exercised six fixtures per normal implementation and B four; these are different coverage choices, not extra independent evaluation units. Both used integer scalar references and exactly representable bf16 fixtures. This establishes feasibility of generating and checking bounded Rust test changes, not a measured benefit from B's extra procedure, an upstream defect discovery, or NPU performance.

Protected results were not returned for candidate repair, and no model calls were added during final evaluation. Budgets fixed before generation remained unchanged; interruptions and resumptions are recorded separately. The subscription account changed with user approval, and host caches were cleaned during execution, so this is not a strictly single-factor-controlled productivity experiment. Model runtime does not substitute for human work time. Broader 1/2-slot calibration and independent-task transfer remain outside this completed pilot.

## Changes and publication

Git flow is feature branch → `dev` → `main`. Squash feature changes through a PR into `dev`; promote verified `dev` through a separate merge-commit PR into `main`, preserving shared ancestry for future promotions. Both stages require current head/base CI and an explicit merge request. See the [merge contract](docs/merge.md) and [PR template](.github/pull_request_template.md).

Use Draft only while implementation or required checks remain. Mark reviewable changes Ready for review; Draft status is not a substitute for review or merge authorization. Do not bypass merging with direct branch pushes or rewrite history. Human acceptance of an experiment result is separate from merging a repository change.

The public tree contains executable code, tests, skills, and necessary contracts only. Research originals, design history, presentations, experiment logs, protected evaluations, and credentials are Git-ignored local material. The public snapshot is not a live dashboard; it is updated after the next completed check. Earlier public material remains in Git history.

## Design references

[The Last AI Built by Humans: Toward Genuine Recursive Self-Improvement, v2](https://arxiv.org/pdf/2609.11873v2), §§2.2–3.3, distinguishes in-task output refinement (B0) from persistent improvement execution (L1) and strategy autonomy (L2). This is the authors' survey taxonomy, not a certification. Our frozen one-task A/B tests candidate outputs, not a successor agent that inherits an improved procedure: it is B0-level evidence, despite substantial execution automation. Committing instructions or merging code alone does not demonstrate L1/L2 self-improvement. The actionable extension is explicit inheritance evidence: a later independent task must load a reviewed policy revision and test transfer, regressions, and cost under fixed criteria. The [operator program](program.md#supervise-an-approved-experiment) records that boundary; this pilot does not perform that later experiment. No model-weight training or autonomous evaluator changes are added.

- [autoresearch procedure](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/program.md): separate editable files, fixed evaluation, and execution records. This lab ends with finite attempts and human review rather than indefinite search.
- [Dioxus Agent Guide](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/AGENTS.md): read only the structure needed for the task, then move to the actual implementation.
- [Furiosa torch-fx-rs instructions](https://github.com/furiosa-ai/torch-fx-rs/blob/3024d6d157732e51b02ef67b808131bec4d652ef/AGENTS.md) and [Agent Skills](https://github.com/furiosa-ai/agent_skills/blob/d5fc482fdca0af78aada5d1e183b4aad18ffbfc7/AGENTS.md): preserve existing API semantics, make small changes, run targeted checks, and describe PRs from the final diff.
- [Furiosa Kernel Validation](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/docs/src/quick-start/kernel-validation.md): distinguish CPU value checks from target validation.
- [Furiosa CI](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/.github/workflows/build.yml) and [Dioxus CI](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/.github/workflows/main.yml): connect language tools, targeted checks, and documentation checks to actual jobs. This lab adopts only checks needed for its scale and public code.
- [GEODE operating principles](https://github.com/mangowhoiscloud/geode/blob/c221191bd9f90fd4a1df116f45371ec08797c2dd/GEODE.md): persistence within scope, evidence-based decisions, and bounded recovery that preserves failures. GEODE runtime features and authority tiers are not represented as implemented in this lab.
- [Trajectory publication contract](https://github.com/mangowhoiscloud/geode-eval-artifacts/blob/d277607f3a179f191ad24b1497c0934beb9d2470/TRAJECTORIES.md): distinguish originals, derived summaries, and score receipts; preserve order, pairs, provenance, and incompleteness. This lab uses existing run records without adding a schema or storage engine.
- [OpenAI Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering) and [Claude Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices): separate goals, constraints, examples, and reference context, and specify completion criteria. The source text was checked on 2026-09-16. Model-specific recommendations are not universal rules; instruction effectiveness requires separate evaluation.

Do not copy project-specific commands or mandates from external guides verbatim. This lab's work rules are in [AGENTS.md](AGENTS.md), its execution procedure in [program.md](program.md), and its verification obligations in the [quality contract](docs/quality.md).
