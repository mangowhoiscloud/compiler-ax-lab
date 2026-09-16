# Compiler AX Lab

Compiler AX Lab explores how to turn coding-agent drafts into reviewable software changes. It connects a bounded change to its cause, preserved behavior, executed checks, and remaining human decisions.

The public repository contains a Python standard-library runner, Rust test examples for the public `furiosa-opt` SDK, and the contracts needed to reproduce and review them. It is independent research, unaffiliated with FuriosaAI; it does not reproduce Furiosa's internal production compiler or NPU.

## How it works

1. **Bound the task.** Fix the editable files, behavior to preserve, reference values, checker, and execution budget before modifying a candidate.
2. **Check the change.** Compare actual results with independent expectations. Use normal and intentional-fault controls to distinguish a useful test failure from a build or environment failure.
3. **Preserve the evidence.** Link the checked source, commands, binary where applicable, raw output, and exit status. A stale binary or zero executed tests cannot establish success.
4. **Hand off for review.** Present the smallest change with its evidence and unresolved risks. Passing checks, accepting a result, merging code, and releasing software are separate decisions.

## Quick start

From the root of a Git clone, use Git, Node.js 22 or later, and Python 3.9 or later on a Unix-like system. These checks require no additional packages:

```bash
node scripts/check.mjs
python3 -m unittest discover -s tests -v
```

The first command checks the public-file allowlist, sensitive-data patterns, documentation links, and CI contracts. The second runs the local runner's regression tests. Neither executes the Rust SDK or an NPU.

To try a bounded change, follow the [group-reduction demo](program.md). Copy the intentionally faulty seed; do not edit the tracked example. The default budget is two checks, including the baseline, with ten seconds per check invocation. Edit only in `REVISE`. `READY_FOR_REVIEW` is a handoff, not approval; missing evidence, timeouts, and exhausted limits produce `STOP`.

## Public system

| Component | Purpose | Entrypoint |
|---|---|---|
| Local runner and tests | Execute the Python demo and validate attempt budgets, candidate copies, raw evidence, and stored results | [trial.py](scripts/trial.py), [regression tests](tests/test_trial.py) |
| Rust examples | Check numerical values for three kernels, plus parser ASTs and diagnostic locations | [double-buffering contract](docs/kernels/double-buffering.md), [parser contract](docs/quality.md#mapping-parser) |
| Execution procedure | Diagnose and check a candidate copy; supervise separately authorized experiments | [program.md](program.md), [execution skill](.agents/skills/run-bounded-change-loop/SKILL.md) |
| Review and publication | Connect the current diff to its checks, ownership, and permitted Git actions | [AGENTS.md](AGENTS.md), [review skill](.agents/skills/review-to-verified-pr/SKILL.md), [merge contract](docs/merge.md) |

The Python runner has no Rust adapter: `trial.py init --task furiosa` does not execute a compiler task. Rust cases use Cargo in a compatible x86-64 environment. Private A/B controllers, protected inputs, and raw experiment records are not part of the public checkout.

## Reproducing the Rust cases

The baseline is `furiosa-opt` v0.8.1, commit `9b9cf0fdc78df00cdc430eae725a5ad9084a735e`, with `nightly-2026-05-01`. Prepare SDK-compatible x86-64 Linux and native dependencies, then record the lockfile, tools, commands, and limits under the [quality contract](docs/quality.md). The Rust CI job does not install the SDK's native environment; it checks only the independent reference and patch applicability.

- **Double-buffering:** Apply the [SDK tests](examples/furiosa-double-buffering/tests/double_buffering_tests.rs) and [independent scalar reference](examples/furiosa-double-buffering/tests/support/double_buffering_reference.rs) to the pinned checkout. Compare every output coordinate across the three implementations under the [input/numerical contract and commands](docs/kernels/double-buffering.md).
- **Mapping parser:** Apply the [test patch](examples/furiosa-mapping-parser/tests.patch) to check ASTs, diagnostic text, and byte ranges through both parser entrypoints. Follow the [scope and commands](docs/quality.md#mapping-parser).
- Public fault patches test the checker's ability to distinguish faults in a separate copy. They are neither bugs discovered upstream nor answers for the protected A/B evaluation.

## Verification status

Recorded CPU results as of **2026-09-16**. These are distinct executions: test counts, value comparisons, and A/B units are not interchangeable and must not be summed.

| Execution | Verified result | Scope |
|---|---|---|
| Unchanged AWS CPU smoke | One designated assertion passed | Native x86 environment readiness; no candidate improvement measured |
| Public double-buffering tests | Three SDK tests, 18 input executions, 46,080 matching values, and two helper tests passed; a compiled public fault failed the intended assertion | Fixed shapes and exactly representable bf16 inputs |
| Public mapping-parser tests | Baseline 6/6 and candidate 12/12 passed; a compiled public fault failed the intended mapping assertion | ASTs and diagnostics through two entrypoints; fault detection established for the mapping assertion |
| Separate source-clean parser replay | Baseline 6/6 and candidate 12/12 passed; one selected public-fault test failed as intended; formatting and targeted Clippy passed | Fresh source trees and empty build targets, but reused dependencies/toolchain; initial preparation failure recorded separately |
| CPU workspace integration | 720 regular tests, 55 doctests, and all-target release Clippy passed | Default features; 17 ignored tests excluded; 44 doctests are `compile_fail` |
| Python runner | 16 regression tests passed | Demo behavior and evidence handling, not compiler correctness |

Local CPU experiments used Ubuntu 24.04 amd64/Rosetta, 2 CPUs, 6 GiB, and Cargo jobs=1. The AWS smoke was a separate native-x86 run. These results do not establish NPU correctness, overlap, timing, or performance, nor full non-default-feature coverage.

### A/B pilot: tied controls, bounded B selection

The frozen pilot compared one pair on one Rust test-improvement task. A received the common task; B also received a research, diagnosis, change, and verification procedure. Final execution completed on 2026-09-16 at 19:39 KST.

| Item | A: common task | B: additional procedure |
|---|---|---|
| Final controls | Three normal controls passed; one qualified fault detected | Three normal controls passed; one qualified fault detected |
| Invalid or unexecuted units | 0 of 4 | 0 of 4 |
| Owner decision | Retained, not selected; not rejected as incorrect | Frozen test change selected for the fixed-shape CPU scope |
| Human active work time | Not measured | Not measured |

All eight units ran after both candidates were frozen. Each executed one selected SDK test, with none ignored; the two expected failures were traced to the intended numerical assertions. **The control result was a tie.** Source, binary, output, and exit records were cross-checked, and protected results were not returned for candidate repair.

The project owner selected frozen B after an [AI-assisted source review](https://github.com/mangowhoiscloud/compiler-ax-lab/pull/11#pullrequestreview-5223709126) of output-coordinate discrimination and explicit fixture bounds. That coverage argument was not an additional scored fault execution. The selection is local CPU-test adoption, not evidence that B's procedure is more effective, a personal human Rust audit, or Furiosa approval. The public Rust example remains the earlier, separately measured reference; it is not the frozen B candidate.

Candidate generation used a fixed B-then-A order; an approved account change and host-cache cleanup also prevent a clean productivity comparison. Human active time was not measured. Different fixture counts do not create additional independent evaluation units.

A separate synthetic status-reconstruction task also ended in a tie: one generation per arm, both exactly matching the fixed answer. No benefit from the extra procedure was observed. That experiment neither enlarged the Rust A/B population nor tested transfer of an adopted procedure.

## Verified boundaries

- **CPU values, compilation, schedules, and device measurements answer different questions.** A passing host test does not establish NPU behavior or performance.
- **CI is narrower than the recorded SDK experiments.** It checks public contracts and selected language checks. Rust CI covers formatting, the standalone reference, and patch applicability; it does not install the native SDK or run the full compiler, NPU, or private A/B evaluation.
- **The runner is not a security sandbox.** File hashes and separate processes under the same user account do not isolate malicious candidates or protect evaluation secrets. Use it only for trusted local demonstrations.
- **Procedure effectiveness remains unestablished.** A later independent task must actually load a reviewed procedure and evaluate transfer, regressions, and cost. Neither B's selection nor a repository merge supplies that evidence.

## Changes and publication

Use feature branch → `dev` → `main`: squash feature PRs into `dev`, then promote verified `dev` with a merge-commit PR. Both stages require current head/base CI and an explicit merge request. Follow the [merge contract](docs/merge.md), [PR template](.github/pull_request_template.md), and [language-specific quality checks](docs/quality.md#language-specific-static-checks-and-ci-routing).

Use Draft while implementation or required checks remain; mark a checked diff Ready for review. The required `lab-ci` gate rejects failed, cancelled, missing, or unexpectedly skipped selected jobs. Do not push directly to shared branches or rewrite history. Human acceptance of an experiment result remains separate from a merge.

Research originals, design history, presentations, protected evaluations, raw logs, and credentials remain Git-ignored local material. The public tree contains executable examples and their necessary contracts, not a live experiment dashboard. Earlier published material remains in Git history.

## Design references

These sources inform specific operating choices; they do not establish equivalent implementations or results. The [operator program](program.md#supervise-an-approved-experiment) defines this lab's execution scope.

- [autoresearch procedure](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/program.md): editable-file boundaries, fixed evaluation, and execution records. This lab adds finite attempts and a human handoff.
- [The Last AI Built by Humans, v2](https://arxiv.org/pdf/2609.11873v2), §§2.2–3.3, and [Darwin Godel Machine, v3](https://arxiv.org/pdf/2505.22954v3) with its [pinned outer loop](https://github.com/jennyzzt/dgm/blob/a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2/DGM_outer.py): distinguish output refinement, candidate retention, and tested inheritance. This lab has not demonstrated persistent procedure improvement or implemented DGM's search.
- [Dioxus Agent Guide](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/AGENTS.md): read only the structure needed for the task, then move to the actual implementation.
- [Furiosa torch-fx-rs instructions](https://github.com/furiosa-ai/torch-fx-rs/blob/3024d6d157732e51b02ef67b808131bec4d652ef/AGENTS.md) and [Agent Skills](https://github.com/furiosa-ai/agent_skills/blob/d5fc482fdca0af78aada5d1e183b4aad18ffbfc7/AGENTS.md): small changes, preserved API contracts, targeted checks, and final-diff review.
- [Furiosa Kernel Validation](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/docs/src/quick-start/kernel-validation.md): distinguish CPU value checks from target validation.
- [Furiosa CI](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/.github/workflows/build.yml) and [Dioxus CI](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/.github/workflows/main.yml): language-specific and documentation checks connected to actual jobs.
- [GEODE operating principles](https://github.com/mangowhoiscloud/geode/blob/c221191bd9f90fd4a1df116f45371ec08797c2dd/GEODE.md) and [trajectory publication contract](https://github.com/mangowhoiscloud/geode-eval-artifacts/blob/d277607f3a179f191ad24b1497c0934beb9d2470/TRAJECTORIES.md): bounded recovery, preserved failures, and separation of originals from summaries. GEODE's runtime and a new storage system are not implemented here.
- [OpenAI Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering) and [Claude Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices): separate goals, constraints, examples, and reference context. Instruction effectiveness still requires evaluation.

Do not copy project-specific commands or mandates from external guides verbatim. This lab's work rules are in [AGENTS.md](AGENTS.md), its execution procedure in [program.md](program.md), and its verification obligations in the [quality contract](docs/quality.md).
