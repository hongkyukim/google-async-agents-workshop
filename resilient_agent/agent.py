"""Optional Google ADK agent: deterministic workflow exposed as callable tools."""

import asyncio
import os

from google.adk.agents import Agent

from .engine import JobStore, run_job


def start_research(job_id: str, topic: str) -> dict:
    """Start or resume a synthetic research job. Reuse the same job_id for retries."""
    store = JobStore(os.getenv("WORKSHOP_DB", "workshop.db"))
    try:
        store.create(job_id, topic)
        job = asyncio.run(run_job(store, job_id))
        return {"status": job["status"], "job_id": job_id, "report": job["data"].get("report"),
                "error": job["error"]}
    except ValueError as exc:
        return {"error": str(exc)}


def inspect_research(job_id: str) -> dict:
    """Inspect durable checkpoint and attempts for an existing research job."""
    store = JobStore(os.getenv("WORKSHOP_DB", "workshop.db"))
    try:
        job = store.get(job_id)
        return {"status": job["status"], "stage": job["stage"], "attempts": job["attempts"],
                "report": job["data"].get("report"), "error": job["error"]}
    except KeyError:
        return {"error": "unknown job_id"}


root_agent = Agent(
    name="resilient_agent",
    model="gemini-2.5-flash",
    instruction=("You help users run synthetic research jobs. For each new request, choose a short "
                 "job_id and call start_research. Use inspect_research to check status. "
                 "Never claim synthetic findings are real or that a human approved the report."),
    tools=[start_research, inspect_research],
)
