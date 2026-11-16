import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from resilient_agent.engine import JobStore, SOURCES, collect_source, run_job


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / "jobs.db")
        self.store = JobStore(self.path)

    def test_complete_and_idempotent(self):
        self.store.create("job-1", "release readiness")
        done = asyncio.run(run_job(self.store, "job-1"))
        self.assertEqual(done["status"], "done")
        self.assertEqual([x["source"] for x in done["data"]["evidence"]], list(SOURCES))
        self.assertTrue(done["data"]["report"]["review_required"])
        self.assertEqual(asyncio.run(run_job(JobStore(self.path), "job-1")), done)
        with self.assertRaises(ValueError):
            self.store.create("job-1", "different topic")

    def test_retry_recovery_and_persisted_attempts(self):
        self.store.create("job-2", "incident", "collect")
        done = asyncio.run(run_job(self.store, "job-2"))
        self.assertEqual(done["status"], "done")
        self.assertEqual(done["attempts"]["collect"], 2)

    def test_failure_resume_does_not_repeat_completed_stage(self):
        self.store.create("job-3", "operations")
        calls = 0

        async def flaky(source, topic):
            nonlocal calls
            calls += 1
            if calls <= len(SOURCES):
                raise TimeoutError("temporary feed outage")
            return await collect_source(source, topic)

        with patch("resilient_agent.engine.collect_source", side_effect=flaky):
            failed = asyncio.run(run_job(self.store, "job-3", retries=0))
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["stage"], 0)
        resumed = asyncio.run(run_job(JobStore(self.path), "job-3"))
        self.assertEqual(resumed["status"], "done")
        self.assertEqual(resumed["attempts"]["collect"], 2)
        self.assertEqual(resumed["attempts"]["analyze"], 1)

    def test_resume_after_later_stage_failure(self):
        self.store.create("job-4", "inventory", "analyze")
        failed = asyncio.run(run_job(self.store, "job-4", retries=0))
        self.assertEqual(failed["stage"], 1)
        self.assertEqual(failed["attempts"]["collect"], 1)
        resumed = asyncio.run(run_job(JobStore(self.path), "job-4"))
        self.assertEqual(resumed["status"], "done")
        self.assertEqual(resumed["attempts"]["collect"], 1)
        self.assertEqual(resumed["attempts"]["analyze"], 2)


if __name__ == "__main__":
    unittest.main()
