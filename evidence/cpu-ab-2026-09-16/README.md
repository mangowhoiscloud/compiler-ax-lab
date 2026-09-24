# Frozen CPU A/B evidence — 16 September 2026

This archive exposes the two frozen candidate test changes, their requirements, and selected source/build/execution evidence from the completed one-task pilot. Publication is not a new SDK run. This is independent research, unaffiliated with FuriosaAI.

The historical result is a tie: each candidate passed three normal implementations and detected one qualified intentional fault. A unit is a **frozen candidate × implementation**, not a fixture or output element. The owner later selected B for its fixed-coordinate discrimination and integer guards. This does not establish a benefit from B's procedure, human productivity, general compiler correctness, physical buffer reuse or NPU performance.

## Evidence map

| Artifact | What it establishes |
|---|---|
| [A tests](A/tests/double_buffering_tests.rs), [A reference](A/tests/support/double_buffering_reference.rs) | Exact frozen common-task candidate |
| [B tests](B/tests/double_buffering_tests.rs), [B reference](B/tests/support/double_buffering_reference.rs) | Exact frozen additional-procedure candidate selected by the owner |
| [Common task](common-task.md), [additional procedure](procedure-b.md) | Verbatim historical candidate-facing inputs |
| [Intentional fault](controls/output-group-swap.patch) | Paired output-group swap; not an upstream defect discovery |
| [Results](results.json), [manifest](manifest.json) | Derived unit/build map, classifications, SHA-256, sizes and field-specific omissions |
| [Builds](builds), [units](units) | Original compile commands/diagnostics, source and binary hashes, eight execution streams and exit/capture receipts |
| [Historical runtime wrapper](historical/run-frozen-test.sh) | Original selected-test command, environment and timeout |

Copied records retain their original bytes. Raw observations remain `REQUIRES_REVIEW`; results.json separately records historical AI-assisted operator classifications. Freeze-time pending status is not rewritten as approval. The later owner decision appears in [PR #11's COMMENT review](https://github.com/mangowhoiscloud/compiler-ax-lab/pull/11#pullrequestreview-5223709126), which is neither a GitHub APPROVE review nor Furiosa approval.

This selected archive is not all 825 operational artifacts. Accounts, authentication, candidate transcripts, personal context, infrastructure inventories, binaries and native dependencies are excluded. The derived summary identifies original-source hashes and field omissions. The public Rust example elsewhere remains the earlier reference; its 720-test/55-doctest integration result does not belong to B.

## Offline check

From the lab repository root, using Python 3.9 or newer:

```bash
python3 evidence/cpu-ab-2026-09-16/check_evidence.py
```

The standard-library check validates hashes, one selected test per historical unit, exits, source/binary references, complete vectors and paired-group permutation. It translates frozen Rust formulas to verify A's 2,332 joint signatures and B's 2,560 unique identity pairs. This source cross-check is not a new SDK execution or an additional control sample.

## SDK replay

Prepare x86-64 Linux, nightly-2026-05-01 and dependencies from [pinned furiosa-opt](https://github.com/furiosa-ai/furiosa-opt/tree/9b9cf0fdc78df00cdc430eae725a5ad9084a735e) under the [environment contract](../../docs/quality.md). Native archives, Cargo dependencies and toolchain must already be available for `--offline`. Historical execution used Ubuntu 24.04 amd64 under Docker/Rosetta, 2 CPUs, 6 GiB, Cargo jobs=1 and one test thread. Record a different environment as a different replay.

Set absolute paths; choose A or B. Use a new checkout and fresh build target for every arm and fault state:

```bash
export AX_ARCHIVE=/absolute/path/to/compiler-ax-lab/evidence/cpu-ab-2026-09-16
export AX_CHECKOUT=/absolute/path/to/new-furiosa-opt-checkout
export AX_ARM=B
git clone https://github.com/furiosa-ai/furiosa-opt.git "$AX_CHECKOUT"
git -C "$AX_CHECKOUT" checkout --detach 9b9cf0fdc78df00cdc430eae725a5ad9084a735e
mkdir -p "$AX_CHECKOUT/furiosa-opt-examples/tests/support"
cp "$AX_ARCHIVE/$AX_ARM/tests/double_buffering_tests.rs" "$AX_CHECKOUT/furiosa-opt-examples/tests/"
cp "$AX_ARCHIVE/$AX_ARM/tests/support/double_buffering_reference.rs" "$AX_CHECKOUT/furiosa-opt-examples/tests/support/"
cd "$AX_CHECKOUT"
export CARGO_TARGET_DIR="$AX_CHECKOUT/target-archive-replay"
export CARGO_BUILD_JOBS=1 RAYON_NUM_THREADS=2 RUST_TEST_THREADS=1
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-opt-examples --test double_buffering_tests --release --no-run
for AX_VARIANT in rolled software_pipelined unrolled; do
  cargo +nightly-2026-05-01 test --offline --locked -p furiosa-opt-examples --test double_buffering_tests --release -- "test_double_buffering_$AX_VARIANT" --exact --nocapture --test-threads=1
done
```

For the fault, prepare another fresh checkout and copy the same arm's tests, then apply the patch before its first build:

```bash
git apply --check "$AX_ARCHIVE/controls/output-group-swap.patch"
git apply "$AX_ARCHIVE/controls/output-group-swap.patch"
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-opt-examples --test double_buffering_tests --release --no-run
cargo +nightly-2026-05-01 test --offline --locked -p furiosa-opt-examples --test double_buffering_tests --release -- test_double_buffering_software_pipelined --exact --nocapture --test-threads=1
```

The fault must compile, execute exactly one test and fail at the numerical comparison: `(0,0,0)`, expected `1`, actual `9`, A test line 67 or B line 38. Build failure, timeout, zero tests, unrelated panic or missing output is not detection. Normal commands require one pass each, zero ignored and complete case output. Replays produce new records; never overwrite historical receipts.

**The disclosed fault cannot be reused as held-out evaluation.** This supports inspection and replay of the completed pilot, not a fresh blinded comparison or reproduction of stochastic candidate generation. Generation order was B-then-A, account/cache conditions changed, and human active time was not measured.

## Attribution

Upstream furiosa-opt material is Apache-2.0 licensed; its original [LICENSE](LICENSE) and [NOTICE](NOTICE) accompany the disclosed patch. Candidate additions are independent lab artifacts, not FuriosaAI-authored or approved changes. Native libraries, binaries, images and third-party dependencies are not redistributed.
