"""Cloud Shell CLI: create, resume, and inspect a checkpointed job."""

import argparse
import asyncio
import json
import os
import sys

from .engine import JobStore, STAGES, run_job


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=os.getenv("WORKSHOP_DB", "workshop.db"))
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("job_id")
    start.add_argument("topic")
    start.add_argument("--fail-once", choices=STAGES)
    start.add_argument("--retries", type=int, default=2, help="retries per stage (default: 2)")
    resume = commands.add_parser("resume")
    resume.add_argument("job_id")
    resume.add_argument("--retries", type=int, default=2, help="retries per stage (default: 2)")
    show = commands.add_parser("show")
    show.add_argument("job_id")
    args = parser.parse_args()
    if args.command != "show" and args.retries < 0:
        parser.error("--retries must be nonnegative")
    store = JobStore(args.db)
    try:
        if args.command == "start":
            store.create(args.job_id, args.topic, args.fail_once)
        job = store.get(args.job_id) if args.command == "show" else asyncio.run(
            run_job(store, args.job_id, retries=args.retries)
        )
    except (KeyError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(job, indent=2))
    return 0 if job["status"] in ("done", "pending") else 1


if __name__ == "__main__":
    sys.exit(main())
