"""Public toy cases, not sealed tests. Execute candidate code in a child process."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

CASES = [
    ("no-groups", [], []),
    ("single-group", [[2, 3]], [5]),
    ("group-boundary", [[1, 2], [10, 20]], [3, 30]),
    ("empty-middle", [[5], [], [-2]], [5, 0, -2]),
    ("signed-ragged", [[-4, 1], [0], [7, -2, 3]], [-3, 0, 8]),
]


def run_candidate(candidate, inputs, name):
    process = subprocess.Popen([sys.executable, "-I", str(candidate)], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=sys.stderr)
    output = bytearray()
    try:
        process.stdin.write(json.dumps(inputs).encode())
        process.stdin.close()
        while chunk := process.stdout.read(4096):
            output.extend(chunk)
            if len(output) > 8192:
                raise ValueError("Candidate output limit exceeded")
        code = process.wait()
        print(f"{name}: candidate exit={code}, stdout={output.decode(errors='replace')!r}", file=sys.stderr)
        if code != 0:
            raise ValueError("Candidate did not complete; not a value-comparison failure")
        return json.loads(output)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        process.stdout.close()


def main():
    candidate = Path(sys.argv[1])
    candidate_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
    tests = []
    for name, inputs, expected in CASES:
        actual = run_candidate(candidate, inputs, name)
        passed = json.dumps(actual) == json.dumps(expected)
        tests.append({"name": name, "expected": expected, "actual": actual, "passed": passed})
    passed = all(test["passed"] for test in tests)
    print(json.dumps({"schema": 1, "task": "group-reduction", "candidate_sha256": candidate_hash,
                      "tests": tests, "status": "PASS" if passed else "FAIL"}))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
