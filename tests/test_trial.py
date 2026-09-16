"""Small stdlib integration checks; no model, network, GPU, or compiler execution."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Union

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/trial.py"
EXAMPLE = ROOT / "examples/group-reduction"


class TrialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.candidate = self.root / "candidate.py"
        self.candidate.write_bytes((EXAMPLE / "candidate.py").read_bytes())
        self.checker = self.root / "check.py"
        self.checker.write_bytes((EXAMPLE / "check.py").read_bytes())
        self.run_dir = self.root / "trial"

    def cli(self, *args: Union[str, Path]) -> dict[str, Any]:
        process = subprocess.run(
            [sys.executable, str(RUNNER), *map(str, args)], capture_output=True, text=True, timeout=10
        )
        result = json.loads(process.stdout)
        expected_code = 0 if result.get("state") in ("READY", "READY_FOR_REVIEW") else 1
        self.assertEqual(process.returncode, expected_code, process.stdout + process.stderr)
        return result

    def initialize(self, *extra: Union[str, Path]) -> dict[str, Any]:
        return self.cli(
            "init", "--run-dir", self.run_dir, "--candidate", self.candidate, "--checker", self.checker, *extra
        )

    def check(self) -> dict[str, Any]:
        return self.cli("check", "--run-dir", self.run_dir)

    def refresh_result_receipt(self) -> None:
        admission = self.run_dir / "admission.json"
        data = json.loads(admission.read_text())
        data["results_sha256"][0] = hashlib.sha256((self.run_dir / "attempt-001/result.json").read_bytes()).hexdigest()
        admission.write_text(json.dumps(data))

    def test_fail_repair_pass_and_preserve_snapshots(self) -> None:
        self.assertEqual(self.initialize()["state"], "READY")
        baseline = self.candidate.read_bytes()
        first = self.check()
        self.assertEqual((first["outcome"], first["state"], first["tests"]), ("FAIL", "REVISE", 5))
        self.candidate.write_text(self.candidate.read_text().replace("total += sum(group)", "total = sum(group)"))
        fixed = self.candidate.read_bytes()
        second = self.check()
        self.assertEqual((second["outcome"], second["state"]), ("PASS", "READY_FOR_REVIEW"))
        self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "READY_FOR_REVIEW")
        self.assertEqual((self.run_dir / "attempt-001/candidate.py").read_bytes(), baseline)
        self.assertEqual(self.candidate.read_bytes(), fixed)
        self.assertFalse(self.check()["admitted"])
        self.assertEqual(len(list(self.run_dir.glob("attempt-*"))), 2)
        self.candidate.write_text("print('changed after verification')\n")
        self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "STOP")

    def test_budget_exhausted(self) -> None:
        self.initialize()
        self.check()
        self.assertEqual(self.check()["state"], "STOP")
        self.assertFalse(self.check()["admitted"])

    def test_timeout_stops_without_retry(self) -> None:
        self.candidate.write_text(
            "import subprocess,sys,time\nfrom pathlib import Path\n"
            "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(20)'])\n"
            "Path('child.pid').write_text(str(p.pid))\ntime.sleep(5)\n"
        )
        self.initialize("--timeout", "1")
        result = self.check()
        self.assertEqual((result["outcome"], result["state"]), ("TIMEOUT", "STOP"))
        self.assertLess(result["elapsed_seconds"], 3)
        self.assertFalse(self.check()["admitted"])
        pid = (self.run_dir / "attempt-001/child.pid").read_text()
        child = subprocess.run(["ps", "-o", "stat=", "-p", pid], capture_output=True, text=True)
        self.assertTrue(not child.stdout.strip() or child.stdout.strip().startswith("Z"), child.stdout)

    def test_incomplete_attempt_and_admission_stop(self) -> None:
        self.run_dir.mkdir()
        self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "STOP")
        self.run_dir.rmdir()
        self.initialize()
        (self.run_dir / "attempt-001").mkdir()
        self.assertFalse(self.check()["admitted"])

    def test_protected_checker_drift(self) -> None:
        self.initialize()
        self.checker.write_text("print('tampered')\n")
        self.assertEqual(self.check()["state"], "STOP")
        self.assertTrue((self.run_dir / "stop.json").is_file())

    def test_baseline_cannot_change_before_first_observation(self) -> None:
        self.initialize()
        self.candidate.write_text(self.candidate.read_text().replace("total +=", "total ="))
        self.assertEqual(self.check()["state"], "STOP")
        self.assertFalse(list(self.run_dir.glob("attempt-*")))

    def test_contract_drift_and_output_limit_stop(self) -> None:
        self.initialize()
        contract = self.run_dir / "contract.json"
        contract.write_text(contract.read_text().replace('"max_attempts": 2', '"max_attempts": 20'))
        self.assertFalse(self.check()["admitted"])
        self.run_dir = self.root / "flood"
        self.checker.write_text("print('x' * 100000)\n")
        self.initialize()
        result = self.check()
        self.assertEqual((result["outcome"], result["state"]), ("INVALID", "STOP"))
        self.assertLessEqual(sum(p.stat().st_size for p in (self.run_dir / "attempt-001").glob("*.log")), 65536)

    def test_zero_tests_or_malformed_evidence(self) -> None:
        for malformed in (False, True):
            with self.subTest(malformed=malformed):
                self.run_dir = self.root / f"trial-{malformed}"
                content = (
                    "print('not json')\n"
                    if malformed
                    else (
                        "import json,hashlib,sys\nfrom pathlib import Path\n"
                        "print(json.dumps({'schema':1,'task':'group-reduction',"
                        "'candidate_sha256':hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),"
                        "'tests':[],'status':'PASS'}))\n"
                    )
                )
                self.checker.write_text(content)
                self.initialize()
                self.assertEqual(self.check()["outcome"], "INVALID")

    def test_lock_symlink_and_unimplemented_admission(self) -> None:
        self.assertEqual(self.initialize("--task", "furiosa")["state"], "STOP")
        self.assertFalse(self.run_dir.exists())
        self.initialize()
        (self.run_dir / ".lock").touch()
        self.assertEqual(self.check()["state"], "STOP")
        self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "STOP")
        self.assertFalse(list(self.run_dir.glob("attempt-*")))
        (self.run_dir / ".lock").unlink()
        self.candidate.unlink()
        self.candidate.symlink_to(EXAMPLE / "candidate.py")
        self.assertEqual(self.check()["state"], "STOP")

    def test_status_rejects_missing_or_changed_artifacts_without_writing(self) -> None:
        self.candidate.write_text(self.candidate.read_text().replace("total +=", "total ="))
        self.initialize()
        self.check()
        attempt = self.run_dir / "attempt-001"
        paths = [
            attempt / name for name in ("candidate.py", "invocation.json", "stdout.log", "stderr.log", "result.json")
        ]
        paths += [self.run_dir / name for name in ("contract.json", "admission.json", "checker.py")]
        paths += [self.candidate, self.checker]
        for path in paths:
            original = path.read_bytes()
            for missing in (True, False):
                with self.subTest(path=path.name, missing=missing):
                    path.unlink() if missing else path.write_bytes(b"corrupted")
                    result = self.cli("status", "--run-dir", self.run_dir)
                    self.assertEqual((result["outcome"], result["state"]), ("INVALID", "STOP"))
                    self.assertFalse((self.run_dir / "stop.json").exists())
                    self.assertEqual(len(list(self.run_dir.glob("attempt-*"))), 1)
                    path.write_bytes(original)
        self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "READY_FOR_REVIEW")

    def test_status_rederives_result_fields_and_requires_receipt(self) -> None:
        self.candidate.write_text(self.candidate.read_text().replace("total +=", "total ="))
        self.initialize()
        self.check()
        path = self.run_dir / "attempt-001/result.json"
        original = json.loads(path.read_text())
        changes = {
            "outcome": "FAIL",
            "state": "REVISE",
            "attempt": 2,
            "tests": 0,
            "exit_code": 1,
            "elapsed_seconds": -1,
            "candidate_sha256": "wrong",
            "authority": "merge",
            "reason": "changed",
        }
        for key, value in [
            *changes.items(),
            ("tests", True),
            ("exit_code", False),
            ("elapsed_seconds", float("nan")),
            ("elapsed_seconds", float("inf")),
            ("elapsed_seconds", 10**1000),
            ("artifacts_sha256", None),
        ]:
            with self.subTest(key=key, value=value):
                changed = {**original, key: value}
                if key == "artifacts_sha256":
                    del changed[key]  # Legacy receipts are not silently upgraded.
                path.write_text(json.dumps(changed))
                self.refresh_result_receipt()  # Exercise semantic checks independently of the byte receipt.
                self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "STOP")
        path.write_text(json.dumps(original))
        self.refresh_result_receipt()
        self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "READY_FOR_REVIEW")
        admission = self.run_dir / "admission.json"
        data = json.loads(admission.read_text())
        del data["results_sha256"]
        admission.write_text(json.dumps(data))
        self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "STOP")

    def test_status_checks_raw_evidence_and_command_not_just_hashes(self) -> None:
        self.candidate.write_text(self.candidate.read_text().replace("total +=", "total ="))
        self.initialize()
        self.check()
        attempt = self.run_dir / "attempt-001"
        result_path = attempt / "result.json"
        original_result = result_path.read_text()
        mutations = [
            ("stdout.log", "status", "FAIL"),
            ("stdout.log", "candidate_sha256", "wrong"),
            ("stdout.log", "tests", []),
            ("invocation.json", "command", ["echo", "PASS"]),
            ("invocation.json", "contract_sha256", "wrong"),
        ]
        for name, key, value in mutations:
            with self.subTest(name=name, key=key):
                path = attempt / name
                original = path.read_bytes()
                changed = json.loads(original)
                changed[key] = value
                path.write_text(json.dumps(changed))
                result = json.loads(original_result)
                result["artifacts_sha256"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
                result_path.write_text(json.dumps(result))
                self.refresh_result_receipt()
                self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "STOP")
                path.write_bytes(original)
        result_path.write_text(original_result)
        self.refresh_result_receipt()
        self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "READY_FOR_REVIEW")

    def test_status_checks_all_attempts_and_prevents_resume_after_corruption(self) -> None:
        self.initialize()
        self.check()
        self.candidate.write_text(self.candidate.read_text().replace("total +=", "total ="))
        self.check()
        first = self.run_dir / "attempt-001"
        first.rename(self.run_dir / "attempt-003")
        self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "STOP")
        (self.run_dir / "attempt-003").rename(first)
        (first / "stderr.log").write_text("changed historical diagnostic")
        result = self.cli("status", "--run-dir", self.run_dir)
        self.assertEqual((result["outcome"], result["state"]), ("INVALID", "STOP"))
        self.assertFalse(self.check()["admitted"])
        self.assertEqual(len(list(self.run_dir.glob("attempt-*"))), 2)

    def test_status_rejects_missing_attempt_suffix_or_all_attempts(self) -> None:
        self.initialize()
        self.check()
        self.assertEqual(self.check()["state"], "STOP")
        (self.run_dir / "attempt-002").rename(self.root / "lost-last")
        self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "STOP")
        (self.run_dir / "attempt-001").rename(self.root / "lost-first")
        self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "STOP")
        self.assertFalse(self.check()["admitted"])
        self.assertFalse(list(self.run_dir.glob("attempt-*")))

    def test_reserved_but_unfinished_attempt_stays_closed(self) -> None:
        self.initialize()
        admission = self.run_dir / "admission.json"
        data = json.loads(admission.read_text())
        data["results_sha256"].append(None)
        admission.write_text(json.dumps(data))
        self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "STOP")
        (self.run_dir / "attempt-001").mkdir()
        self.assertEqual(self.cli("status", "--run-dir", self.run_dir)["state"], "STOP")
        self.assertFalse(self.check()["admitted"])
        self.assertEqual(len(list(self.run_dir.glob("attempt-*"))), 1)

    def test_status_rejects_attempt_after_terminal_state_and_forged_stop(self) -> None:
        self.candidate.write_text(self.candidate.read_text().replace("total +=", "total ="))
        self.initialize()
        self.check()
        (self.run_dir / "attempt-002").mkdir()
        admission = self.run_dir / "admission.json"
        original_admission = admission.read_bytes()
        data = json.loads(original_admission)
        data["results_sha256"].append(None)
        admission.write_text(json.dumps(data))
        result = self.cli("status", "--run-dir", self.run_dir)
        self.assertEqual(result["state"], "STOP")
        self.assertIn("terminal state", result["reason"])
        (self.run_dir / "attempt-002").rmdir()
        admission.write_bytes(original_admission)
        for content in ("not json", "null", '{"outcome":"PASS","state":"READY_FOR_REVIEW","reason":"forged"}'):
            with self.subTest(content=content):
                (self.run_dir / "stop.json").write_text(content)
                result = self.cli("status", "--run-dir", self.run_dir)
                self.assertEqual((result["outcome"], result["state"]), ("INVALID", "STOP"))
                self.assertFalse(self.check()["admitted"])
                self.assertEqual((self.run_dir / "stop.json").read_text(), content)


if __name__ == "__main__":
    unittest.main()
