# Task: strengthen public double-buffering output tests

Add maintainable CPU integration tests for the three existing double-buffering kernels in this clean furiosa-opt v0.8.1 checkout. The change should let a maintainer judge whether output values preserve token, group and output-channel identity. This is test strengthening, not permission to repair or optimize product kernels.

## Fixed context

- Source revision: 9b9cf0fdc78df00cdc430eae725a5ad9084a735e.
- Rust nightly-2026-05-01, Ubuntu24.04 x86_64 CPU backend, existing dependencies and release profile.
- Inspect the public implementation, public docs and existing tests in this checkout as needed. No external network or earlier lab solutions are available.
- `Tok=16`, `Red=64`, `Out=8`, `Group=20`, `Pairs=10`.
- Activation is bf16[16,64], weight bf16[20,8,64], result bf16[16,20,8]. Required meaning: output[t,g,o] = sum_r activation[t,r] * weight[g,o,r]. Preserve all axes and existing shape support.
- Test rolled, software_pipelined and unrolled entrypoints. Use the SDK launch/copy APIs as demonstrated by existing integration tests. CPU agreement does not establish NPU timing, overlap or correctness.

## Allowed changes and shared acceptance criteria

Create only:
1. furiosa-opt-examples/tests/double_buffering_tests.rs
2. furiosa-opt-examples/tests/support/double_buffering_reference.rs

Do not edit any other tracked source, macro, build script, lock, dependency, kernel or configuration. No new unsafe/FFI, skipped tests, lint suppression, weakened assertions, external process, filesystem/environment introspection, network code or source-inspection macros. A normal module path to the permitted reference file is allowed. Return a blocked explanation if the task cannot be met within this scope.

Give the three SDK tests these names so the controller can discover and select them exactly:
- test_double_buffering_rolled
- test_double_buffering_software_pipelined
- test_double_buffering_unrolled

Use deterministic inputs covering every group/output, first and last groups, within-pair and between-pair boundaries, a nonzero-to-zero invocation on the same Device, and signed dense reduction. Independent scalar expected values must not call the kernel or the same SDK contraction implementation. Comparing only the three kernels to each other is insufficient. Explain the numerical comparison choice: choose exactly representable bounded integer inputs/results if using exact bf16 equality, rather than assuming arbitrary floating-point reduction is exact. Include a small helper check where it materially catches an oracle/indexing mistake.

Assert full result length and every output coordinate; reject non-finite unexpected results. Failures identify variant, input case, coordinate and expected/actual. Print reproducible input/case identity and complete expected/actual vectors with --nocapture, followed by a success marker only after comparison. Do not inflate test counts with output element counts.

Follow the existing Rust style and rustfmt, preserve the existing warning policy and upstream APIs. Avoid unrelated refactoring. A useful small change is preferable to a new generic framework.

## Available work and public checks

The native candidate shell can inspect this public checkout and write the two allowed test files; the required x86 SDK toolchain runs in the controller's separate CPU worker. Do not claim local SDK tests passed if you cannot execute them. The controller will provide exact public stdout/stderr and exit status, and allow at most one revision on that feedback. You may do local checks that the provided shell supports; no elevated access or installation is allowed.

Public checks on the same environment for both candidates:
- diff/file-scope inspection;
- pinned nightly cargo fmt --all -- --check;
- cargo test --offline --locked -p furiosa-opt-examples --test double_buffering_tests --release -- --list;
- the same target with -- --nocapture --test-threads=1;
- cargo clippy --offline --locked -p furiosa-opt-examples --test double_buffering_tests --release -- -D warnings.

At most 900 seconds for the first draft and one 600-second revision. A final frozen candidate is subsequently evaluated separately; final evaluation results are not revision input. Work independently of any other candidate.

## Final message

Use these short headings: Purpose; Scope; Diagnosis and choice; Checks actually run; Checks remaining; Risks. Describe the reason for the test design and how a maintainer can verify it. Do not invent CPU results, discovered vendor bugs, human adoption or performance claims.
