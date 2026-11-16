"""Checkpointed, resumable async research workflow using synthetic live-source doubles."""

import asyncio
import json
import sqlite3
from pathlib import Path

STAGES = ("collect", "analyze", "report")
SOURCES = ("releases", "incidents", "operations")


class TransientSourceError(RuntimeError):
    pass


class JobStore:
    def __init__(self, path: str):
        self.path = str(Path(path).expanduser())
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, topic TEXT NOT NULL, stage INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending', attempts TEXT NOT NULL DEFAULT '{}',
                data TEXT NOT NULL DEFAULT '{}', fail_once TEXT, error TEXT
            )""")

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def create(self, job_id: str, topic: str, fail_once: str | None = None) -> dict:
        if not job_id or not topic.strip():
            raise ValueError("job_id and topic are required")
        if fail_once and fail_once not in STAGES:
            raise ValueError(f"fail_once must be one of {STAGES}")
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO jobs(id, topic, fail_once) VALUES (?, ?, ?)",
                       (job_id, topic.strip(), fail_once))
        job = self.get(job_id)
        if job["topic"] != topic.strip() or job["fail_once"] != fail_once:
            raise ValueError("job_id already exists with different input")
        return job

    def get(self, job_id: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        job = dict(row)
        job["attempts"] = json.loads(job["attempts"])
        job["data"] = json.loads(job["data"])
        return job

    def attempt(self, job_id: str, stage: str) -> int:
        with self.connect() as db:
            job = db.execute("SELECT attempts FROM jobs WHERE id = ?", (job_id,)).fetchone()
            attempts = json.loads(job["attempts"])
            attempts[stage] = attempts.get(stage, 0) + 1
            db.execute("UPDATE jobs SET attempts = ? WHERE id = ?", (json.dumps(attempts), job_id))
        return attempts[stage]

    def checkpoint(self, job_id: str, stage_index: int, data: dict):
        with self.connect() as db:
            db.execute("UPDATE jobs SET stage = ?, data = ?, status = ?, error = NULL WHERE id = ?",
                       (stage_index, json.dumps(data),
                        "done" if stage_index == len(STAGES) else "pending", job_id))

    def error(self, job_id: str, message: str):
        with self.connect() as db:
            db.execute("UPDATE jobs SET status = 'failed', error = ? WHERE id = ?", (message, job_id))


async def collect_source(source: str, topic: str) -> dict:
    """Replace this synthetic adapter with a bounded, authenticated cloud data client."""
    await asyncio.sleep(0)
    return {"source": source, "fact": f"{topic}: synthetic {source} signal"}


async def run_job(store: JobStore, job_id: str, retries: int = 2) -> dict:
    if retries < 0:
        raise ValueError("retries must be nonnegative")
    job = store.get(job_id)
    if job["status"] == "done":
        return job
    for index in range(job["stage"], len(STAGES)):
        stage = STAGES[index]
        for retry in range(retries + 1):
            attempt = store.attempt(job_id, stage)
            try:
                if job["fail_once"] == stage and attempt == 1:
                    raise TransientSourceError(f"injected transient failure at {stage}")
                if stage == "collect":
                    # Gather independent I/O concurrently; a failure never commits partial results.
                    job["data"]["evidence"] = await asyncio.gather(
                        *(collect_source(source, job["topic"]) for source in SOURCES)
                    )
                elif stage == "analyze":
                    job["data"]["findings"] = [item["fact"] for item in job["data"]["evidence"]]
                else:
                    job["data"]["report"] = {
                        "topic": job["topic"], "findings": job["data"]["findings"],
                        "review_required": True,
                    }
                store.checkpoint(job_id, index + 1, job["data"])
                break
            except (TransientSourceError, TimeoutError, OSError) as exc:
                if retry == retries:
                    store.error(job_id, str(exc))
                    return store.get(job_id)
                await asyncio.sleep(min(0.05 * (2 ** retry), 0.5))
    return store.get(job_id)
