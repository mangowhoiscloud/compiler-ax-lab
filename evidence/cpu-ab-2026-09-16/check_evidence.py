"""Check historical evidence and fixture arithmetic without executing the SDK."""

import hashlib
import json
from pathlib import Path
import re


def fixture_vectors(arm: str) -> dict[str, list[int]]:
    """Translate the hash-identified frozen Rust formulas for a source cross-check."""
    coords = [(t, g, o) for t in range(16) for g in range(20) for o in range(8)]
    signed = [-2, -1, 1, 2]
    if arm == "A":
        values = {
            f"basis_offset_{j}": [1 + (17 * (4 * t + j) + 8 * g + o) % 251 for t, g, o in coords]
            for j in range(4)
        }
        values["zero_weights_after_basis_offset_3"] = [0] * 2560
        values["signed_dense"] = [
            sum(
                signed[(17 * t + 7 * r + 3 * t * r) % 31 % 4]
                * signed[(13 * g + 5 * o + 11 * r + g * r + 3 * o * r) % 29 % 4]
                for r in range(64)
            )
            for t, g, o in coords
        ]
        return values
    assert arm == "B"
    return {
        "identity_low_v1": [i % 251 + 1 for i in range(2560)],
        "zero_activation_after_identity_low_v1": [0] * 2560,
        "identity_high_v1": [i // 251 + 1 for i in range(2560)],
        "signed_dense_v1": [
            sum(
                (-1 if (t * 11 + r * 7 + r // 3 + t * r) % 17 < 8 else 1)
                * signed[(g * 13 + o * 7 + r * 3 + r // 5 + g * r + o * r) % 11 % 4]
                for r in range(64)
            )
            for t, g, o in coords
        ],
    }


def main() -> None:
    if not __debug__:
        raise SystemExit("Run without -O: this check requires assertions")
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "manifest.json").read_text())
    listed = {entry["path"] for entry in manifest["files"]}
    actual_files = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    assert actual_files == listed | {"manifest.json"}, "Missing or unlisted archive file"
    for entry in manifest["files"]:
        relative = Path(entry["path"])
        assert not relative.is_absolute() and ".." not in relative.parts
        path = root / relative
        assert path.is_file() and not path.is_symlink()
        data = path.read_bytes()
        assert len(data) == entry["bytes"], entry["path"]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], entry["path"]

    vectors = {arm: fixture_vectors(arm) for arm in ["A", "B"]}
    a_signatures = set(zip(*vectors["A"].values()))
    b_pairs = list(zip(vectors["B"]["identity_low_v1"], vectors["B"]["identity_high_v1"]))
    assert len(a_signatures) == 2332 and len(set(b_pairs)) == 2560
    assert all(251 * (high - 1) + low - 1 == i for i, (low, high) in enumerate(b_pairs))
    assert tuple(values[0] for values in vectors["A"].values()) == (1, 18, 35, 52, 0, -11)
    assert all(values[0] == values[(7 * 20 + 3) * 8 + 2] for values in vectors["A"].values())

    results = json.loads((root / "results.json").read_text())
    assert [unit["id"] for unit in results["units"]] == [f"{arm}-{i}" for arm in "AB" for i in range(1, 5)]
    for build in results["builds"]:
        base = root / build["path"]
        assert (base / "compile.exit").read_text().strip() == "0"
        assert (base / "compile.capture-exit").read_text().strip() == "0"
        hashes = dict(line.split("  ", 1)[::-1] for line in (base / "source-at-compile.sha256").read_text().splitlines())
        for name in ["double_buffering_tests.rs", "support/double_buffering_reference.rs"]:
            candidate = root / build["arm"] / "tests" / name
            assert hashes[f"furiosa-opt-examples/tests/{name}"] == hashlib.sha256(candidate.read_bytes()).hexdigest()
        binary_hashes = [line.split()[0] for line in (base / "binary.sha256").read_text().splitlines()]
        assert binary_hashes == [build["binarySha256"]] * 2

    for unit in results["units"]:
        base = root / unit["evidencePath"]
        stdout, stderr = (base / "execute.stdout").read_text(), (base / "execute.stderr").read_text()
        code = int((base / "execute.exit").read_text())
        receipt = json.loads((base / "execute.result.json").read_text())
        assert code == unit["commandExit"] == receipt["code"]
        assert receipt["signal"] is None and receipt["captureError"] is None and receipt["stopReason"] is None
        assert (base / "execute.capture-exit").read_text().strip() == "0"
        assert re.findall(r"^selected_test=(.+)$", stdout, re.M) == [unit["test"]]
        assert re.findall(r"^test (\S+) \.\.\.", stdout, re.M) == [unit["test"]]
        assert re.findall(r"^running (\d+) tests?$", stdout, re.M) == ["1"]
        assert stdout.count(f"{unit['binarySha256']}  /trial/test\n") == 1
        assert f"runtime_exit={code}\n" in stdout
        assert re.search(r"^oom 0$", stdout, re.M) and re.search(r"^oom_kill 0$", stdout, re.M)
        assert "runtime_wall_seconds=" in stderr and "RECORD_UNAVAILABLE" not in stdout + stderr
        fault = unit["implementation"] == "output-group-swap"
        summary = "FAILED. 0 passed; 1 failed" if fault else "ok. 1 passed; 0 failed"
        assert len(re.findall(r"^test result:", stdout, re.M)) == 1
        assert f"test result: {summary}; 0 ignored; 0 measured; 3 filtered out;" in stdout
        assert code == (101 if fault else 0)
        expected_pairs = re.findall(r"^variant=\S+ case=(\S+) expected=(\[.*\])$", stdout, re.M)
        actual_pairs = re.findall(r"^variant=\S+ case=(\S+) actual=(\[.*\])$", stdout, re.M)
        cases = list(vectors[unit["arm"]])[:1] if fault else list(vectors[unit["arm"]])
        assert [name for name, _ in expected_pairs] == [name for name, _ in actual_pairs] == cases
        for (name, expected_text), (_, actual_text) in zip(expected_pairs, actual_pairs):
            expected = json.loads(expected_text)
            observed = json.loads(re.sub(r"bf16\(([^()]*)\)", r"\1", actual_text))
            assert expected == vectors[unit["arm"]][name] and len(observed) == 2560
            if fault:
                swapped = [expected[(t * 20 + (g ^ 1)) * 8 + o] for t in range(16) for g in range(20) for o in range(8)]
                assert observed == swapped and observed != expected
            else:
                assert observed == expected
        if fault:
            assert f"double_buffering_tests.rs:{unit['assertionLine']}:" in stderr
            assert "coordinate=(0,0,0) expected=1 actual=bf16(9.0)" in stderr
    print("PASS: archive hashes, 8 historical units, source/binary links, complete vectors, A=2332 and B=2560 identities")
    print("Scope: offline archival checks and translated fixture arithmetic; no SDK, model, NPU or new experiment execution")


if __name__ == "__main__":
    main()
