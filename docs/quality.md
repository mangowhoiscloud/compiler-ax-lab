# Quality contract: what a passing check establishes

This document defines the lab's coding conventions, checks, and acceptance criteria, not a vendor's internal policy. See [verification status in the README](../README.md#verification-status) for recorded results, [AGENTS](../AGENTS.md) for authority boundaries, and the [merge contract](merge.md) for PR handoff. Documentation changes do not alter an already frozen run contract.

### Language-specific static checks and CI routing

Runtime code uses the standard library; only development check tools are added as pinned dependencies. Checks do not apply automatic fixes. Formatting changes also require diff review.

| Target | Pinned tools and execution | Coverage and exclusions |
|---|---|---|
| Four Python files | [pyproject.toml](../pyproject.toml), [requirements-dev.txt](../requirements-dev.txt): Ruff lint/format, mypy; unittest on Python 3.9 and 3.12 | Undefined names, imports, formatting, function types, and 16 behavioral regressions. Existing runtime validation handles `Any` at JSON boundaries; this is not a complete schema-level type proof. |
| JavaScript and check configuration | [Biome](../biome.json), [package lock](../package-lock.json): `npm ci --ignore-scripts`, `npm run check` | Recommended lint rules, formatting, and import organization. Not TypeScript type checking or proof of semantic preservation. |
| Rust files and patches | nightly-2026-05-01 rustfmt, `clippy-driver --test -D warnings` and two tests for the standalone reference; `git apply --check` against pinned upstream | SDK test-file syntax and formatting; standalone-reference types, Clippy, and behavior; patch applicability. SDK integration typing, linking, parser execution, and NPU checks remain separate. |
| Markdown and publication boundary | `node scripts/check.mjs` | Allowlist, local links and anchors, sensitive-data patterns, skill entry points, and required CI contracts. External URL availability and factual claims require separate review. |
| GitHub Actions YAML and shell | actionlint v1.7.12; also uses ShellCheck when available on the runner | YAML, expressions, job dependencies, and shell diagnostics. Not a substitute for actual cloud execution results. |

Reproduce Python checks in a separate environment with the commands below. Python 3.9 is a regression check for the existing compatibility floor, not a recommended version for a new production environment.

```bash
python3 -m venv .local/static-env
.local/static-env/bin/python -m pip install -r requirements-dev.txt
.local/static-env/bin/python -m ruff check scripts tests examples/group-reduction
.local/static-env/bin/python -m ruff format --check scripts tests examples/group-reduction
.local/static-env/bin/python -m mypy
.local/static-env/bin/python -m unittest discover -s tests -v
npm ci --ignore-scripts
npm run check
node scripts/check.mjs
```

[quality.yml](../.github/workflows/quality.yml) executes the routing; [check.mjs](../scripts/check.mjs) selects and aggregates jobs. `lab-system` always runs. A `.py` change selects Python; `.mjs` or npm/Biome configuration selects JavaScript; `.rs` or `.patch` selects Rust. Shared instructions, quality/CI configuration, and unknown paths select all language checks. README, merge-documentation, or PR-template-only changes do not select language jobs. Deleted and renamed files are evaluated using both old and new paths. An unreadable comparison base selects all checks.

The required check remains `lab-ci`. Every selected job must return `success`; `skipped` is allowed only for language jobs excluded by the selection plan. Failed, cancelled, unexpectedly skipped, or missing required jobs and missing plans are rejected. Reproduce selection and aggregation acceptance/rejection cases with `node scripts/check.mjs --self-test`. Changes to the checker itself select all jobs. Do not hide failures with `continue-on-error`.

When adding a tool or rule, update the affected language's code, configuration, CI, and this table together. CI does not measure instruction compliance or model problem-solving performance. Full SDK checks follow the separate commands and environment contract below.

### Report publication

The owner-approved [report.pdf](../report.pdf) is the only published binary. Before replacing it, inspect extracted text, link annotations, metadata, and rendered pages for private information, unsupported claims, and layout defects. Update its approved SHA-256 in `scripts/check.mjs` only after that review. The checker rejects different bytes; it does not interpret PDF content or establish factual correctness. Sources, protected inputs, and raw evidence remain local.

The existing quality workflow publishes only `report.pdf` after `lab-ci` succeeds on a push to `main`. PR and `dev` runs cannot deploy; Pages write permissions are confined to the deployment job and its `github-pages` environment. Changes still follow feature → dev → main. After deployment, retrieve the public URL and compare its SHA-256 with the checked repository copy before reporting completion.

### Input and numerical contracts

Freeze shape, dtype, formula, input domain, tolerances, and an independent oracle before checking. The [double-buffering contract](kernels/double-buffering.md) defines numerical obligations for finite integer inputs; the [parser contract below](#mapping-parser) defines AST and error-location expectations. Do not fill unknown values or missing evidence with success, or treat CPU results as NPU evidence.

### Conventions preserve existing structure and explain the change

- Read the affected crate's implementation, direct callers, existing tests, and documentation. Define allowed files and behavior to preserve. Stop and agree on a new scope before expanding it; do not mix unrelated refactoring into the change.
- Reuse existing names, modules, error types, and helpers. Test names describe conditions and behavior; failures preserve the input, location, expected/actual values, or original diagnostic. Do not derive expected values from the kernel under test or the same calculation helper.
- Keep `nightly-2026-05-01`, the 120-column width, and existing Clippy exceptions. Checks are check-only; `--fix` belongs only in the candidate-editing phase. Do not add global pedantic/restriction rules or a ban on `unwrap` in tests.
- Do not obtain a pass through new blanket allows, warning caps, `#[ignore]`, test deletion, or weaker assertions/tolerances. Exceptions require separate approval of scope, rationale, owner, and reconsideration criteria.
- Record the source pin, Cargo.lock, actual rustc/Clippy versions, host triple, GLIBC, native tag/hash, and licenses. Verify provenance and checksums for `LOCAL_PREBUILT` too; a matching hash does not authenticate provenance. Do not change the lockfile during evaluation.
- Add ownership, aliasing, lifetime, alignment, concurrency, and failure-effect obligations only where relevant to authorized unsafe, FFI, or API changes. A `Safety` comment or passing Miri run does not prove NPU or external FFI safety.
- Hand off the purpose, preserved behavior, choice rationale, rejected alternatives, check results, and unexecuted scope. Align Errors/Panics/Safety documentation, examples, and change history for API changes; test-only work does not justify unrelated version or changelog edits.

### Quality gates and failure handling

Freeze identical public requirements, tools, and acceptance criteria for both A/B arms; vary only the additional working procedure. Do not attribute differences in protected answers or quality thresholds to the procedure. Do not give candidates the complete operator documentation.

| Gate | Required checks and evidence | Action on failure or missing evidence |
|---|---|---|
| Contract and environment | Pin/lock/toolchain/native dependencies, allowed files and prohibited effects, resource/time limits, commands and test inventory for an unchanged baseline | Do not start the candidate comparison if preparation fails. Record existing warnings and flaky failures in advance. |
| Scope and code quality | Review the diff including new files; `make fmt`, targeted check/Clippy; `make check`, `make clippy`, and `cargo machete` for a stable candidate | Repair or hand off using the original diagnostic; do not conceal it with suppression. |
| Output behavior | Exact release-mode test names and counts, seeds, inputs, independent expected values, actual values, and exit status | A value mismatch is a counterexample. Zero tests, early returns, and missing logs are not success. |
| Integration and documentation | `make test` on a stable revision; for upstream documentation changes, `make mdbook-build` plus relevant examples/`make mdbook-test`; regenerated-artifact diff | Separate ignored, excluded, and unexecuted NPU checks. Check lab documents with `node scripts/check.mjs`; a documentation build is not an execution result. |
| Independent final evaluation | After public revisions finish and both snapshots are frozen, run each frozen normal/intentional-fault evaluation once; manage the reference, result parser, and tolerances outside candidate control | Separate false alarms on normal code, missed faults, and invalid checks. Do not return protected logs for repair of the same candidate; later changes require a new experiment. |
| Human acceptance | Purpose, structure, API, test meaning, residual risks, and required receipts for the same candidate revision | Missing, skipped, or cancelled required checks are not completion. Acceptance, PR creation, merge, and release are separate decisions. |

Preserve `PASS / FAIL / INVALID / NOT_RUN` and the stop reason for each check. A timeout is incomplete execution. Define exclusions, their reasons, and their owners before running; do not improve a pass rate with retrospective N/A labels. Resolve baseline failures first or agree on an exception in advance. Review changes to the reference separately and reevaluate affected results.

### CPU smoke observability and record format

Reuse the existing commands, logs, and collection paths. The names below describe operator-record roles, not a requirement for a new framework or observability service.

| Record | What the producer records | What the reviewer verifies |
|---|---|---|
| Contract | Version, run ID, authorized scope, source/lock/toolchain/native dependencies, argv/cwd, seed/shape/dtype/oracle, and limits | Agreement with the actual environment and conditions; keep account and resource IDs private. |
| Raw phase output | stdout/stderr, command, UTC start/end, `time -v`, original command exit, and capture exit | Original diagnostics and execution counts; PTY recordings support replay but do not replace raw streams or establish a global order between them. |
| Resources | cgroup/VM limits, thread settings, five-second `vmstat` samples, before/after `df/du` with units | Distinguish maximum process RSS from whole-workload peak; the first `vmstat` CPU row is the average since boot, while later rows cover sample intervals. |
| Collection manifest | Relative path, role, bytes, SHA-256, required/optional status, present/missing/partial status, and comparison with the original | Completeness of required evidence; hashes identify bytes, not meaning, order, or correctness. |
| Decision and cleanup | Passed/failed/ignored/filtered counts, STOP reason, collection result, deletion of created resources, and a fresh resource query | Verify test completion and operational cleanup separately; preserve other tasks' resources and records. |

Bound output collection time as well. A child retaining a pipe or a failed collection leaves incomplete evidence. Distinguish preparation failure from a worker that never started. Compare copies collected during execution with the final originals before deletion. Do not claim lossless capture across an uncollected interval caused by network loss or forced termination. Exit 137 alone does not establish OOM; inspect cgroup, kernel, and controller evidence together.

Preserve reproducible evidence as in Dioxus's [failing input and original error](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/packages/fuzz/src/case.rs#L119) and [expected/actual diagnostics](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/packages/fuzz/src/harness.rs#L224). Neither a coverage count nor a replay that discards comparison results establishes correctness. Do not overwrite expected values or the corpus while checking. Add fuzzing, Miri, or sanitizers only when the risk is relevant and execution is feasible.

### Actual commands and execution evidence

Link run/attempt IDs, candidate/parent candidate, actual commands, and results at handoff. Preserve observation order and tool call/result pairs using identifiers present in the original record; do not invent missing times, order, or IDs. The current Python demo's attempt record is a check receipt, not a complete agent-conversation trajectory. If a separate agent transcript exists, link it through a restricted locator.

The producing system's record is the original; normalized records and summaries are derivatives. Distinguish original event time, collection time, publication time, scope completeness, and replayability. Identify truncated output, missing pairs, and unverified intervals. Record public redactions separately with their own digest; do not publish private prompts, credentials, or hidden reasoning. A receipt retaining only a collection manifest and hashes is not a recoverable backup of the original.

On compatible x86-64 Linux, first prepare the dependencies in the [pinned upstream README](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/README.md). The source pin is `9b9cf0fdc78df00cdc430eae725a5ad9084a735e`. Fix job counts, test/internal thread counts, a dedicated `CARGO_TARGET_DIR`, initial cache state, and time/output/resource limits. Even `--list` can trigger a build.

```bash
cargo +nightly-2026-05-01 fmt --all -- --check
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-opt-examples --release --test binary_add_tests -- --list
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-opt-examples --release --test binary_add_tests -- --exact test_binary_add_2048 --test-threads=1
```

The [existing smoke test](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/tests/binary_add_tests.rs) uses seed=42, two `i8[2048]` inputs, an `i32[2048]` output, and a host i32 elementwise-addition oracle. Verify exactly one pass, zero failures, zero ignored, one filtered, successful command/capture exits, and an unchanged lockfile. Successful arrays are not printed: record `NOT_EMITTED` rather than fabricating values.

These commands use the plain Cargo CPU path. Do not merely append `test` to the [upstream Dockerfile](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/Dockerfile)'s default `cargo furiosa-opt` entrypoint; explicitly select Cargo or a shell. The [Makefile](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/Makefile)'s `make test` runs release-mode checks; `clippy-npu` is separate. `--all-targets` does not mean every feature combination or doctest. Distinguish the direct commands' `--locked` policy from the Makefile, and isolate target paths set internally by mdbook too.

Old mtimes on copied files can cause reuse of a previous binary. Connect source hashes, the copy method, recompilation logs, and the executed binary; rebuild or use a fresh target when uncertain. Compare test listings and execution per target; do not count child-process summaries twice. Distinguish expected rejection in `compile_fail` doctests, ignored tests, and NPU-only targets that execute zero tests on CPU.

### Mapping parser

The [test patch](../examples/furiosa-mapping-parser/tests.patch) checks the contracts of the pinned [grammar](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-mapping-macro/src/parser/parser.lalrpop), [AST/parser](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-mapping-macro/src/parser/mod.rs), and [diagnostics](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-mapping-macro/src/parser/diagnostic.rs). It checks exact ASTs or error messages and byte ranges, not merely whether `parse_mapping` and `parse_index` accept an input. Index inputs append `: value` and must preserve one assignment and the value token `value`.

| Shared input | Extent preserved in `Stride(Symbol(A), extent)` |
|---|---|
| `A / 4` | `Const(Lit(4))` |
| `A / {N}` | `Const(Const(tokens N))`; outer braces excluded |
| `A / B` | `Axis(B)` |
| `A / (B, C)` | `Mapping(Pair(Symbol(B), Symbol(C)))`; left/right order preserved |

`[B]` is an atom represented as `Symbol(B)` at both entry points, but `A / [B]` is not a valid Extent. Both modes must identify `[` at `4..5` and return the corresponding message below. EOF in `A /` points to the final `/` at `2..3`, distinguishing mapping and index modes. Ranges are zero-based, end-exclusive byte ranges.

```text
unexpected token `[`; expected an axis name, an integer, a braced Rust expression, or `(`
unexpected end of mapping expression; expected an axis name, an integer, a braced Rust expression, or `(`
unexpected end of index expression; expected an axis name, an integer, a braced Rust expression, or `(`
```

The change is limited to two helpers and six tests inside `cfg(test)` in `diagnostic.rs`, preserving the existing six tests. Product grammar, AST, diagnostics, dependencies, and lockfile remain unchanged. Verify the inventory and execution counts for the six-test normal baseline and twelve-test candidate, formatting, and targeted release-mode Clippy separately.

```bash
git apply --check /path/to/compiler-ax-lab/examples/furiosa-mapping-parser/tests.patch
git apply /path/to/compiler-ax-lab/examples/furiosa-mapping-parser/tests.patch
cargo +nightly-2026-05-01 fmt --all -- --check
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-mapping-macro --lib --release -- --list
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-mapping-macro --lib --release -- --nocapture --test-threads=1
cargo +nightly-2026-05-01 clippy --offline --locked -p furiosa-mapping-macro --all-targets --release -- -D warnings
```

Add the [public fault patch](../examples/furiosa-mapping-parser/controls/accept-bracket-extent.patch) only in a separate checkout and target. Add `parser::diagnostic::tests::brackets_are_atoms_not_extents --exact` to the same test command. After successful compilation, verify that exactly one test executes and fails at the intended assertion. This control fails first at the mapping assertion; it does not establish independent fault detection for index mode. Compile errors, zero tests, OOM, and missing evidence are not detection.

This example checks ASTs and `syn::Error` for tokenizable DSL input. It does not establish full macro-expansion, Rust typing, mapping-execution, or NPU-lowering correctness. The public intentional fault is neither an upstream defect nor protected evaluation material. Judge static compilation, CPU values, schedules, device measurements, and human acceptance on their respective evidence. See the [merge contract](merge.md).
