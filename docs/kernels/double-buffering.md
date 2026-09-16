# Double-buffering test contract: distinguish per-group outputs and boundaries

This document defines the allowed changes, numerical obligations, and reproduction procedure for the public test example. Results and unfinished work are recorded in [verification status in the README](../../README.md#verification-status). A pass here does not establish a separate A/B, NPU, or human-acceptance result. Documentation changes do not alter frozen experiment requirements.

## 1. Purpose and allowed changes

Check whether the pinned `rolled`, `software_pipelined`, and `unrolled` implementations produce the expected per-group outputs for identical inputs. This is host-test strengthening to distinguish normal code from a public intentional fault, not a product bug fix or kernel optimization. Changes are limited to these two new files:

- `furiosa-opt-examples/tests/double_buffering_tests.rs` ← [SDK tests](../../examples/furiosa-double-buffering/tests/double_buffering_tests.rs)
- `furiosa-opt-examples/tests/support/double_buffering_reference.rs` ← [Inputs, independent oracle, and comparator checks](../../examples/furiosa-double-buffering/tests/support/double_buffering_reference.rs)

Stop and agree on a new scope if kernel, runtime, macro, build-script, dependency, lockfile, unsafe, FFI, or API changes are needed. Preserve the three implementations and current shapes; do not add support for odd Group counts. Apply fault patches only in a separate checkout. The public oracle and output-level comparator are not the protected evaluator for independent final evaluation. See the [quality contract](../quality.md) and [authority boundaries](../../AGENTS.md).

## 2. Pinned source and input/output

The target is `furiosa-opt` v0.8.1, commit `9b9cf0fdc78df00cdc430eae725a5ad9084a735e`, using `nightly-2026-05-01`. Prepare the x86-64 Linux host, compatible GLIBC, and native dependencies specified in the [pinned README](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/README.md). Record the source, lockfile, toolchain, native tag/hash, and licenses.

The [shared definitions](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering.rs#L5-L13) are `Tok=16, Red=64, Out=8, Group=20, Pairs=10`. All three functions share the same logical input/output types.

| Data | Type and shape | Raw data size |
|---|---|---:|
| activation | `bf16[16,64]` | 2 KiB |
| weight | `bf16[20,8,64]` | 20 KiB |
| output | `bf16[16,20,8]` | 5 KiB |

At two bytes per element, raw data totals 27 KiB. This excludes layout, alignment, intermediate buffers, host copies, the oracle, and build memory; it is neither a VM requirement nor maximum RSS. The flattened output index is `(t*20+g)*8+o`, with the required computation `out[t,g,o] = sum_r A[t,r]*W[g,o,r]`.

## 3. Data movement and implementation-specific obligations

| Implementation and pinned source | Group processing in the source | Obligation to check |
|---|---|---|
| [rolled](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/rolled_kernel.rs#L19-L43) | Loads group `g` weights into TRF and writes the corresponding output view | Correspondence of every input and output group |
| [software_pipelined](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/software_pipelined_kernel.rs#L19-L64) | Separately loads, computes, and writes `first=pair*2` and `second=first+1` | Correspondence within pairs, between pairs, and at the final group |
| [unrolled](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/unrolled_kernel.rs#L19-L44) | Writes each output view through the `#[unroll]` group loop | Identical per-group values after loop unrolling |

The functions move HBM activation and weight data through `device.tdma`'s `to_dm`. `device.sub` loads group weights through `begin → fetch → collect → to_trf`; `device.main` performs the reduction through `contract_outer → contract_packet → contract_time → contract_lane`. Results pass through `cast::<bf16>`, `commit_trim`, and `commit_view` into output DM, then return through `to_hbm_view`. The host test retrieves them and compares them with independently computed expectations.

Keep the mappings `Chip=m![1]`, `Cluster=m![Tok / 8 % 2]`, and `Slice=m![Tok % 8 # 256]`. These are source-level [mapping and DM-transfer relationships](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-examples/src/double_buffering/rolled_kernel.rs#L4-L17), not observed NPU timing or physical buffer placement. CPU value checks do not establish whether writes precede consumer completion or measure actual execution overlap.

## 4. Finite integer fixtures and an independent oracle

Compute expected values with scalar i32 sums without calling the SDK contraction, cast, or kernel again. Inputs are deterministic and have no seed. Define `h(k,r)=(-1)^popcount(k & r)`, `c=8g+o+1`, and `k=2o+(g mod 2)`.

| Case | Input construction | Closed-form expectation and check purpose |
|---|---|---|
| `Basis(q)`, q=0,1,2,3 | `A[t,r]=1` iff `r=16q+t`, otherwise 0; `W[g,o,r]=1+((8g+o+17r) mod 251)` | The selected weight, an integer from 1 to 251; distinguishes all 64 reduction positions, groups, and outputs |
| `SignedDense` | `A[t,r]=h(t,r)`; `W[g,o,r]=(-1)^o*c*h(k,r)` | `(-1)^o*64c` when `t=k`, otherwise 0; checks sign, reduction, and cancellation |
| `Zero` | All A values are 0; W is the same as Basis | All outputs are 0; runs after nonzero cases on the same Device |

The pinned SDK [widens bf16 operands to f32](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-std/src/cast.rs#L335-L386) for reduction, then converts the result to bf16. General real-valued inputs can differ with [summation order](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/furiosa-opt-std/src/backend/mod.rs#L178-L181), so exact comparison is not universally valid. For these fixtures, every Dense product and partial sum in any order is an integer with absolute value at most `64*160=10,240`, exactly representable in f32. The final `64c` is also exactly representable in bf16 because `c≤160`; Basis and Zero remain within exact ranges too.

The helper separately checks bf16 representability and the closed forms for inputs and expected values. SDK tests verify axis sizes, convert to `HostTensor<bf16>`, and run six cases sequentially on the same Device within each variant. They retrieve the host result as `[Tok,Group,Out]`, verify its 2,560-element length, and compare every value for numerical equality. NaN/Inf are rejected against finite expectations; +0/-0 are equal. General real values, NaN inputs, subnormals, rounding boundaries, and other shapes are outside scope.

`CASE_RESULT` prints the variant, case, and complete expected/actual arrays. `CASE_PASS` is printed only after comparison succeeds. Failures include `(t,g,o)` and both values. Preserve raw `--nocapture` output and per-case arrays; missing output is not success. This public example checks three variants × six cases × 2,560 values. Do not aggregate retries into that count or treat it as a universal test count for other candidates.

## 5. Public controls and failure classification

The helper's output-level controls directly feed the comparator a group rotation, omitted odd groups, a group/output transposition, short output, and NaN/Inf. These do not constitute execution of a faulty SDK. Comparing normal implementations with one another or checking only a total sum does not replace an independent oracle.

[reuse-first-trf.patch](../../examples/furiosa-double-buffering/controls/reuse-first-trf.patch) introduces a public intentional fault in a separate copy: the second group in `software_pipelined` reads `first_trf` instead of `second_trf`. After verifying successful compilation and execution of exactly one test, classify detection by the intended assertion failure at `Basis(0), t=0/g=1/o=0`, expected=9 and actual=1. Command exit 101 alone is insufficient.

Record the control revision, violated requirement, and independent confirmation. Compile errors, OOM, runner crashes, zero tests, and collection failures are not fault detection; a timeout is incomplete execution. Do not adjust normal-baseline expectations to match observed output. Public controls do not establish upstream defects, unknown-fault detection rates, or agent superiority, and must not be reused as protected evaluation.

## 6. Reproduction procedure

1. Verify environment compatibility and execution authority. In a normal checkout with verified pin, lockfile, and native dependencies, copy only the two files above at their matching relative paths. Record jobs=1, test threads=1, internal thread limits, dedicated target/cache, time/output/resource limits, and the cleanup owner. Verify worker readiness with the existing `test_binary_add_2048`.
2. Run the commands below with plain Cargo in the pinned upstream checkout. Dependencies must be prepared before using `--offline`. `--list` also builds; its inventory must contain three SDK tests and two helper tests. Separate normal and fault targets. Connect source hashes, recompilation logs, and executed binaries to exclude stale-binary reuse.

```bash
cargo +nightly-2026-05-01 fmt --all -- --check
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-opt-examples --test double_buffering_tests --release -- --list
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-opt-examples --test double_buffering_tests --release -- --nocapture --test-threads=1
cargo +nightly-2026-05-01 clippy --offline --locked -p furiosa-opt-examples --test double_buffering_tests --release -- -D warnings
```

3. SDK test names are `test_double_buffering_rolled`, `test_double_buffering_software_pipelined`, and `test_double_buffering_unrolled`. Count the helper tests `fixtures_match_closed_forms_and_are_exact_bf16_values` and `comparison_rejects_wrong_groups_missing_outputs_and_nonfinite_values` separately. Link names, cases, complete values, command/capture exits, and source/binary hashes.
4. Apply the same tests and public patch only to the fault checkout. Add `test_double_buffering_software_pipelined --exact --nocapture --test-threads=1` to the test command above. Verify successful compilation, exactly one executed test, and failure at the intended value assertion. Preserve the normal source and lockfile unchanged.
5. Apply the [shared required checks](../quality.md#quality-gates-and-failure-handling) to a stable revision and compare the inventory with execution per target. Collect and compare raw output, final sources, and binaries before removing only the resources created for this run; then query for leftovers. Preserve stop records and other tasks' material.

To check only the helper, run the following from the lab root. These two tests have no SDK dependency. A host pass does not establish SDK API compilation or NPU validation.

```bash
mkdir -p .local/checks
rustc --edition 2024 -D warnings --test examples/furiosa-double-buffering/tests/support/double_buffering_reference.rs -o .local/checks/double-buffering-reference
.local/checks/double-buffering-reference --nocapture
```

## 7. Acceptance and interpretation boundaries

The [Python demo](../../program.md) is not a Rust runner. Reuse existing Cargo, recording, and collection paths. A person reviews the checked revision, actual commands, execution counts, raw evidence, and incomplete-work reasons under the [merge contract](../merge.md). A passing check, human acceptance, PR creation, merge, release, and additional paid execution are separate states and authorities.

This test-only change does not automatically add `cargo furiosa-opt compile`, NPU ELF generation, physical-device execution, or schedule optimization. Following the official [Kernel Validation](https://github.com/furiosa-ai/furiosa-opt/blob/9b9cf0fdc78df00cdc430eae725a5ad9084a735e/docs/src/quick-start/kernel-validation.md#L3-L14) guidance, static compilation establishes translation and mapping/shape checks; CPU execution provides values for executed inputs; a schedule is a plan; NPU execution provides observations under recorded device conditions. Agree on scope and checks again before changing the target.
