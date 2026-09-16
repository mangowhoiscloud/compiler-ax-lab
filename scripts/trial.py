#!/usr/bin/env python3
"""Bounded local demonstration; no memory/network isolation or Rust adapter."""

import argparse
import hashlib
import json
import math
import os
import selectors
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union, cast

RUNNER = Path(__file__).resolve()
DEFAULT_CHECKER = RUNNER.parent.parent / "examples/group-reduction/check.py"
OUTPUT_LIMIT = 65536


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_path(value: Union[str, Path], *, directory: bool = False) -> Path:
    path = Path(os.path.abspath(value))
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Symlinks are not admitted")
    if path.exists() and not (path.is_dir() if directory else path.is_file()):
        raise ValueError("Unexpected path type")
    return path


def put(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def read(path: Path) -> Any:
    # JSON is untrusted here; callers validate the fields they consume.
    return json.loads(checked_path(path).read_text(encoding="utf-8"))


def require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def frozen_contract(root: Path) -> dict[str, Any]:
    raw = checked_path(root / "contract.json").read_bytes()
    require(digest(raw) == read(root / "admission.json")["contract_sha256"], "Contract drift")
    contract = json.loads(raw)
    require(contract["version"] == 1 and contract["task"] == "group-reduction", "Unsupported task")
    require(contract["python"] == sys.version, "Python runtime drift")
    require(type(contract["max_attempts"]) is int and 1 <= contract["max_attempts"] <= 20, "Invalid attempt budget")
    require(
        type(contract["timeout"]) in (int, float)
        and math.isfinite(contract["timeout"])
        and 0 < contract["timeout"] <= 300
        and contract["output_limit"] == OUTPUT_LIMIT,
        "Invalid execution limits",
    )
    for path, expected in (
        (RUNNER, contract["runner_sha256"]),
        (contract["checker"], contract["checker_sha256"]),
        (root / "checker.py", contract["checker_sha256"]),
    ):
        require(digest(checked_path(path).read_bytes()) == expected, "Protected checker or runner drift")
    return contract


def artifact_hashes(attempt: Path) -> dict[str, str]:
    return {
        name: digest(checked_path(attempt / name).read_bytes())
        for name in ("candidate.py", "invocation.json", "stdout.log", "stderr.log")
    }


def next_state(outcome: Optional[str], number: int, max_attempts: int) -> str:
    return (
        "READY_FOR_REVIEW" if outcome == "PASS" else "REVISE" if outcome == "FAIL" and number < max_attempts else "STOP"
    )


def update_admission(root: Path, admission: dict[str, Any]) -> None:
    pending = root / ".admission.tmp"
    put(pending, admission)
    os.replace(pending, root / "admission.json")


def status(root: Path, *, owns_lock: bool = False) -> dict[str, Any]:
    if (root / ".lock").exists() and not owns_lock:
        return {"state": "STOP", "outcome": "INVALID", "reason": "Active or interrupted lock; inspect before any retry"}
    try:
        if (root / "stop.json").exists():
            result = read(root / "stop.json")
            require(
                result["state"] == "STOP"
                and result["outcome"] == "INVALID"
                and isinstance(result["reason"], str)
                and result["reason"],
                "Invalid stop record",
            )
            return result
        contract = frozen_contract(root)
        attempts = sorted(root.glob("attempt-*"))
        receipts = read(root / "admission.json")["results_sha256"]
        require(isinstance(receipts, list) and len(receipts) == len(attempts), "Admitted attempt count disagrees")
        if len(attempts) > contract["max_attempts"]:
            raise ValueError("Attempt count exceeds contract")
        if not attempts:
            return {"state": "READY", "attempts": 0}
        if [p.name for p in attempts] != [f"attempt-{i:03}" for i in range(1, len(attempts) + 1)]:
            raise ValueError("Attempt sequence is incomplete")
        previous_state = "REVISE"
        for number, attempt in enumerate(attempts, 1):
            require(previous_state == "REVISE", "Attempt follows a terminal state")
            checked_path(attempt, directory=True)
            require(
                digest(checked_path(attempt / "result.json").read_bytes()) == receipts[number - 1],
                "Stored result changed or incomplete",
            )
            result = read(attempt / "result.json")
            hashes = artifact_hashes(attempt)
            require(result["artifacts_sha256"] == hashes, "Stored artifacts changed or receipt missing")
            candidate_hash = hashes["candidate.py"]
            require(result["candidate_sha256"] == candidate_hash, "Stored candidate identity disagrees")
            if number == 1:
                require(candidate_hash == contract["baseline_sha256"], "Stored baseline changed")
            invocation = read(attempt / "invocation.json")
            command = [sys.executable, "-I", str(root / "checker.py"), str(attempt / "candidate.py")]
            require(
                invocation
                == {
                    "command": command,
                    "candidate_sha256": candidate_hash,
                    "contract_sha256": digest((root / "contract.json").read_bytes()),
                },
                "Stored invocation disagrees with contract or candidate",
            )
            require(type(result["attempt"]) is int and result["attempt"] == number, "Stored attempt disagrees")
            require(
                type(result["tests"]) is int and result["tests"] >= 0 and type(result["exit_code"]) is int,
                "Invalid stored counts or exit code",
            )
            elapsed = result["elapsed_seconds"]
            require(
                type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed >= 0, "Invalid stored elapsed time"
            )
            require(result["authority"] == "No merge or release authorization", "Invalid stored authority")
            require(
                sum(checked_path(attempt / name).stat().st_size for name in ("stdout.log", "stderr.log"))
                <= contract["output_limit"],
                "Stored output exceeds limit",
            )
            outcome = result["outcome"]
            require(outcome in ("PASS", "FAIL", "INVALID", "TIMEOUT"), "Invalid stored outcome")
            if outcome in ("PASS", "FAIL"):
                verdict, count = evidence(attempt, contract, candidate_hash, result["exit_code"])
                require(
                    (outcome, result["tests"], result["reason"]) == (verdict, count, None),
                    "Stored result disagrees with raw evidence",
                )
            else:
                require(isinstance(result["reason"], str) and result["reason"], "Missing stop reason")
            previous_state = next_state(outcome, number, contract["max_attempts"])
            require(result["state"] == previous_state, "Stored state disagrees with outcome or budget")
        if (
            result["state"] == "READY_FOR_REVIEW"
            and digest(checked_path(contract["candidate"]).read_bytes()) != result["candidate_sha256"]
        ):
            return {
                "state": "STOP",
                "outcome": "INVALID",
                "reason": "Candidate changed since verified snapshot",
                "verified_sha256": result["candidate_sha256"],
                "attempts": len(attempts),
            }
        return {**result, "attempts": len(attempts)}
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        return {"state": "STOP", "outcome": "INVALID", "reason": f"Incomplete or inconsistent stored evidence: {error}"}


def stop(root: Path, reason: object) -> dict[str, Any]:
    result = {"state": "STOP", "outcome": "INVALID", "reason": str(reason)}
    if not (root / "stop.json").exists():
        put(root / "stop.json", result)
    return result


def init(args: argparse.Namespace) -> dict[str, Any]:
    if args.task != "group-reduction":
        raise ValueError("STOP: Rust adapter UNIMPLEMENTED; no execution admitted")
    if not 1 <= args.max_attempts <= 20 or not math.isfinite(args.timeout) or not 0 < args.timeout <= 300:
        raise ValueError("Require 1..20 attempts and a finite timeout in (0, 300] seconds")
    root = checked_path(args.run_dir, directory=True)
    candidate, checker = checked_path(args.candidate), checked_path(args.checker)
    if candidate == checker or root in candidate.parents or root in checker.parents:
        raise ValueError("Candidate/checker must be distinct and outside the run directory")
    candidate_bytes, checker_bytes = candidate.read_bytes(), checker.read_bytes()
    root.mkdir()  # Parent must exist; never reuse or overwrite a run directory.
    (root / "checker.py").write_bytes(checker_bytes)
    contract = {
        "version": 1,
        "task": args.task,
        "candidate": str(candidate),
        "requirement": "JSON list of integer groups -> each group's own sum; empty group is 0; preserve group order",
        "checker": str(checker),
        "checker_sha256": digest(checker_bytes),
        "runner_sha256": digest(RUNNER.read_bytes()),
        "baseline_sha256": digest(candidate_bytes),
        "max_attempts": args.max_attempts,
        "timeout": args.timeout,
        "output_limit": OUTPUT_LIMIT,
        "python": sys.version,
    }
    put(root / "contract.json", contract)
    put(
        root / "admission.json",
        {"contract_sha256": digest((root / "contract.json").read_bytes()), "results_sha256": []},
    )
    return {"state": "READY", "run_dir": str(root), "attempts": 0}


def execute(command: list[str], attempt: Path, timeout: float, limit: int) -> tuple[Optional[str], int, float]:
    start = time.monotonic()
    process = subprocess.Popen(
        command, cwd=attempt, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True
    )
    selector, total = selectors.DefaultSelector(), 0
    captures: dict[str, BinaryIO] = {}
    stdout, stderr = cast(BinaryIO, process.stdout), cast(BinaryIO, process.stderr)
    outcome = None
    try:
        for label, pipe in (("stdout", stdout), ("stderr", stderr)):
            captures[label] = (attempt / f"{label}.log").open("xb")
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, label)
        while selector.get_map():
            remaining = timeout - (time.monotonic() - start)
            if remaining <= 0:
                outcome = "TIMEOUT"
                break
            for key, _ in selector.select(min(remaining, 0.1)):
                chunk = os.read(key.fd, 8192)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                captures[key.data].write(chunk[: max(0, limit - total)])
                total += len(chunk)
                if total > limit:
                    outcome = "OUTPUT_LIMIT"
                    break
            if outcome:
                break
        if not outcome:
            try:
                process.wait(timeout=max(0.001, timeout - (time.monotonic() - start)))
            except subprocess.TimeoutExpired:
                outcome = "TIMEOUT"
    finally:
        # Also terminate children retaining pipes after the checker exits.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        selector.close()
        for pipe in (stdout, stderr):
            pipe.close()
        for stream in captures.values():
            stream.close()
    return outcome, process.returncode, time.monotonic() - start


def evidence(attempt: Path, contract: dict[str, Any], candidate_hash: str, exit_code: int) -> tuple[str, int]:
    data = read(attempt / "stdout.log")
    require(data["schema"] == 1 and data["task"] == contract["task"], "Wrong evidence task/schema")
    require(data["candidate_sha256"] == candidate_hash, "Wrong candidate identity")
    tests = data["tests"]
    require(isinstance(tests, list) and tests, "Zero tests is not a pass")
    names = set()
    for test in tests:
        require(isinstance(test["name"], str) and test["name"] and test["name"] not in names, "Invalid test name")
        names.add(test["name"])
        equal = json.dumps(test["actual"], sort_keys=True, allow_nan=False) == json.dumps(
            test["expected"], sort_keys=True, allow_nan=False
        )
        require(type(test["passed"]) is bool and test["passed"] == equal, "Comparison/result disagreement")
    verdict = "PASS" if all(t["passed"] for t in tests) else "FAIL"
    require(data["status"] == verdict and exit_code == (0 if verdict == "PASS" else 1), "Verdict/exit disagreement")
    return verdict, len(tests)


def check(root: Path) -> dict[str, Any]:
    lock = root / ".lock"
    with lock.open("x"):
        pass
    try:
        previous = status(root, owns_lock=True)
        if previous["state"] not in ("READY", "REVISE"):
            if previous.get("outcome") == "INVALID":
                stop(root, previous["reason"])
            return {**previous, "admitted": False}
        contract = frozen_contract(root)
        number = previous["attempts"] + 1
        if number > contract["max_attempts"]:
            return stop(root, "Attempt budget exhausted")
        candidate = checked_path(contract["candidate"])
        snapshot = candidate.read_bytes()
        if number == 1 and digest(snapshot) != contract["baseline_sha256"]:
            return stop(root, "First attempt must observe the admitted baseline before editing")
        admission = read(root / "admission.json")
        admission["results_sha256"].append(None)  # Reserve the attempt before execution; interrupted work stays closed.
        update_admission(root, admission)
        attempt = root / f"attempt-{number:03}"
        attempt.mkdir()
        candidate_copy = attempt / "candidate.py"
        candidate_copy.write_bytes(snapshot)
        candidate_hash = digest(snapshot)
        command = [sys.executable, "-I", str(root / "checker.py"), str(candidate_copy)]
        put(
            attempt / "invocation.json",
            {
                "command": command,
                "candidate_sha256": candidate_hash,
                "contract_sha256": digest((root / "contract.json").read_bytes()),
            },
        )
        outcome, code, elapsed = execute(command, attempt, contract["timeout"], contract["output_limit"])
        count, reason = 0, outcome
        if outcome is None:
            try:
                outcome, count = evidence(attempt, contract, candidate_hash, code)
            except (AssertionError, ValueError, KeyError, TypeError, OSError) as error:
                outcome, reason = "INVALID", f"Malformed or incomplete checker evidence: {error}"
        elif outcome == "OUTPUT_LIMIT":
            outcome = "INVALID"
        if (
            digest(checked_path(candidate_copy).read_bytes()) != candidate_hash
            or digest(checked_path(candidate).read_bytes()) != candidate_hash
        ):
            outcome, reason = "INVALID", "Candidate changed during verification"
        if digest(checked_path(root / "checker.py").read_bytes()) != contract["checker_sha256"]:
            outcome, reason = "INVALID", "Checker changed during verification"
        if frozen_contract(root) != contract:
            outcome, reason = "INVALID", "Protected input changed during verification"
        state = next_state(outcome, number, contract["max_attempts"])
        result = {
            "outcome": outcome,
            "state": state,
            "attempt": number,
            "tests": count,
            "exit_code": code,
            "elapsed_seconds": elapsed,
            "candidate_sha256": candidate_hash,
            "reason": reason,
            "authority": "No merge or release authorization",
            "artifacts_sha256": artifact_hashes(attempt),
        }
        put(attempt / "result.json", result)
        admission["results_sha256"][-1] = digest((attempt / "result.json").read_bytes())
        update_admission(root, admission)
        return result
    except (OSError, ValueError, KeyError, TypeError) as error:
        return stop(root, error)
    finally:
        lock.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("init", help="Owner freezes one local task and finite budget")
    setup.add_argument("--run-dir", required=True)
    setup.add_argument("--candidate", required=True)
    setup.add_argument("--checker", default=str(DEFAULT_CHECKER), help="Owner-selected stdlib Python checker")
    setup.add_argument("--task", choices=("group-reduction", "furiosa"), default="group-reduction")
    setup.add_argument("--max-attempts", type=int, default=2)
    setup.add_argument("--timeout", type=float, default=10)
    for name in ("check", "status"):
        sub.add_parser(name).add_argument("--run-dir", required=True)
    args = parser.parse_args()
    try:
        result = (
            init(args)
            if args.command == "init"
            else (check if args.command == "check" else status)(checked_path(args.run_dir, directory=True))
        )
    except (OSError, ValueError) as error:
        result = {"state": "STOP", "outcome": "INVALID", "reason": str(error)}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("state") in ("READY", "READY_FOR_REVIEW") else 1


if __name__ == "__main__":
    sys.exit(main())
