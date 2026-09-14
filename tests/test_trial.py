"""Small stdlib integration checks; no model, network, GPU, or compiler execution."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/trial.py"
EXAMPLE = ROOT / "examples/group-reduction"


class TrialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.candidate = self.root / "candidate.py"
        self.candidate.write_bytes((EXAMPLE / "candidate.py").read_bytes())
        self.checker = self.root / "check.py"
        self.checker.write_bytes((EXAMPLE / "check.py").read_bytes())
        self.run = self.root / "trial"

    def cli(self, *args):
        process = subprocess.run([sys.executable, str(RUNNER), *map(str, args)], capture_output=True, text=True, timeout=10)
        return json.loads(process.stdout)

    def initialize(self, *extra):
        return self.cli("init", "--run-dir", self.run, "--candidate", self.candidate, "--checker", self.checker, *extra)

    def check(self):
        return self.cli("check", "--run-dir", self.run)

    def test_fail_repair_pass_and_preserve_snapshots(self):
        self.assertEqual(self.initialize()["state"], "READY")
        baseline = self.candidate.read_bytes()
        first = self.check()
        self.assertEqual((first["outcome"], first["state"], first["tests"]), ("FAIL", "REVISE", 5))
        self.candidate.write_text(self.candidate.read_text().replace("total += sum(group)", "total = sum(group)"))
        fixed = self.candidate.read_bytes()
        second = self.check()
        self.assertEqual((second["outcome"], second["state"]), ("PASS", "READY_FOR_REVIEW"))
        self.assertEqual((self.run / "attempt-001/candidate.py").read_bytes(), baseline)
        self.assertEqual(self.candidate.read_bytes(), fixed)
        self.assertFalse(self.check()["admitted"])
        self.assertEqual(len(list(self.run.glob("attempt-*"))), 2)
        self.candidate.write_text("print('changed after verification')\n")
        self.assertEqual(self.cli("status", "--run-dir", self.run)["state"], "STOP")

    def test_budget_exhausted(self):
        self.initialize()
        self.check()
        self.assertEqual(self.check()["state"], "STOP")
        self.assertFalse(self.check()["admitted"])

    def test_timeout_stops_without_retry(self):
        self.candidate.write_text("import subprocess,sys,time\nfrom pathlib import Path\n"
                                  "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(20)'])\n"
                                  "Path('child.pid').write_text(str(p.pid))\ntime.sleep(5)\n")
        self.initialize("--timeout", "0.3")
        result = self.check()
        self.assertEqual((result["outcome"], result["state"]), ("TIMEOUT", "STOP"))
        self.assertLess(result["elapsed_seconds"], 2)
        self.assertFalse(self.check()["admitted"])
        pid = (self.run / "attempt-001/child.pid").read_text()
        child = subprocess.run(["ps", "-o", "stat=", "-p", pid], capture_output=True, text=True)
        self.assertTrue(not child.stdout.strip() or child.stdout.strip().startswith("Z"), child.stdout)

    def test_incomplete_attempt_and_admission_stop(self):
        self.run.mkdir()
        self.assertEqual(self.cli("status", "--run-dir", self.run)["state"], "STOP")
        self.run.rmdir()
        self.initialize()
        (self.run / "attempt-001").mkdir()
        self.assertFalse(self.check()["admitted"])

    def test_protected_checker_drift(self):
        self.initialize()
        self.checker.write_text("print('tampered')\n")
        self.assertEqual(self.check()["state"], "STOP")
        self.assertTrue((self.run / "stop.json").is_file())

    def test_baseline_cannot_change_before_first_observation(self):
        self.initialize()
        self.candidate.write_text(self.candidate.read_text().replace("total +=", "total ="))
        self.assertEqual(self.check()["state"], "STOP")
        self.assertFalse(list(self.run.glob("attempt-*")))

    def test_contract_drift_and_output_limit_stop(self):
        self.initialize()
        contract = self.run / "contract.json"
        contract.write_text(contract.read_text().replace('"max_attempts": 2', '"max_attempts": 20'))
        self.assertFalse(self.check()["admitted"])
        self.run = self.root / "flood"
        self.checker.write_text("print('x' * 100000)\n")
        self.initialize()
        result = self.check()
        self.assertEqual((result["outcome"], result["state"]), ("INVALID", "STOP"))
        self.assertLessEqual(sum(p.stat().st_size for p in (self.run / "attempt-001").glob("*.log")), 65536)

    def test_zero_tests_or_malformed_evidence(self):
        for malformed in (False, True):
            with self.subTest(malformed=malformed):
                self.run = self.root / f"trial-{malformed}"
                content = "print('not json')\n" if malformed else (
                    "import json,hashlib,sys\nfrom pathlib import Path\n"
                    "print(json.dumps({'schema':1,'task':'group-reduction',"
                    "'candidate_sha256':hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),"
                    "'tests':[],'status':'PASS'}))\n")
                self.checker.write_text(content)
                self.initialize()
                self.assertEqual(self.check()["outcome"], "INVALID")

    def test_lock_symlink_and_unimplemented_admission(self):
        self.assertEqual(self.initialize("--task", "furiosa")["state"], "STOP")
        self.assertFalse(self.run.exists())
        self.initialize()
        (self.run / ".lock").touch()
        self.assertEqual(self.check()["state"], "STOP")
        self.assertEqual(self.cli("status", "--run-dir", self.run)["state"], "STOP")
        self.assertFalse(list(self.run.glob("attempt-*")))
        (self.run / ".lock").unlink()
        self.candidate.unlink()
        self.candidate.symlink_to(EXAMPLE / "candidate.py")
        self.assertEqual(self.check()["state"], "STOP")


if __name__ == "__main__":
    unittest.main()
