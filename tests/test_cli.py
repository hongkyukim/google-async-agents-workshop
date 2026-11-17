import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliRecoveryTests(unittest.TestCase):
    def test_failed_stage_can_resume_in_new_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "jobs.db")
            command = [sys.executable, "-m", "resilient_agent", "--db", db]
            failed = subprocess.run(
                command + ["start", "job-1", "release readiness", "--fail-once", "analyze",
                           "--retries", "0"], capture_output=True, text=True, check=False,
            )
            self.assertEqual(failed.returncode, 1, failed.stderr)
            first = json.loads(failed.stdout)
            self.assertEqual((first["status"], first["stage"]), ("failed", 1))
            resumed = subprocess.run(
                command + ["resume", "job-1"], capture_output=True, text=True, check=True,
            )
            second = json.loads(resumed.stdout)
            self.assertEqual(second["status"], "done")
            self.assertEqual(second["attempts"], {"collect": 1, "analyze": 2, "report": 1})

    def test_negative_retries_rejected_before_job_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "jobs.db"
            result = subprocess.run(
                [sys.executable, "-m", "resilient_agent", "--db", str(db),
                 "start", "job-1", "topic", "--retries", "-1"],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--retries must be nonnegative", result.stderr)
            self.assertFalse(db.exists())


if __name__ == "__main__":
    unittest.main()
