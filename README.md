# Building Next Gen Autonomous Agentic Systems with Google — Silicon Valley

Hands-on companion for the Google × AICamp build lab, **Building Resilient Asynchronous Agents**. Speaker listed in the event brief: **Logan Hennessy, Google**. This community workshop repository is not an official Google product.

Build a checkpointed research agent that collects three synthetic signals concurrently, analyzes them, and produces a review-required report. Inject a transient failure, inspect persisted attempts, then resume without repeating finished stages. Optionally expose the same workflow as Google ADK function tools and deploy an ADK API to Cloud Run.

## Cloud Shell quick start (no local setup)

Open [Google Cloud Shell](https://shell.cloud.google.com/) in your own Google Cloud account. A cloud project with billing and permissions is needed **only for optional Vertex AI / Cloud Run steps**. The core lab is offline, deterministic, and needs Python 3.10+.

```bash
git clone https://github.com/hongkyukim/google-async-agents-workshop.git
cd google-async-agents-workshop
python3 -m unittest discover -s tests -v
python3 -m resilient_agent start demo-1 "release readiness" --fail-once collect
python3 -m resilient_agent show demo-1
python3 -m resilient_agent resume demo-1
```

`start` retries an injected one-time collect failure and saves progress to `workshop.db`. Reusing the same job ID and topic returns the same report; conflicting input is rejected. Reports and source signals are deliberately synthetic, **not live data or AI analysis**. Never use them for operational decisions without human review.

## The 90-minute build lab

- 0–15 min: [Lab 1 — concurrent tools](docs/labs.md#lab-1-concurrent-tools-15-min)
- 15–40 min: [Lab 2 — checkpoints, retries, and recovery](docs/labs.md#lab-2-checkpoints-and-recovery-25-min)
- 40–65 min: [Lab 3 — ADK tool integration](docs/labs.md#lab-3-adk-tool-integration-25-min)
- 65–90 min: [Lab 4 — deployment and demo](docs/labs.md#lab-4-cloud-run-demo-25-min)

The ADK/Cloud Run lab requires an existing Google Cloud project, enabled APIs, sufficient IAM permissions, billable resources and a supported Gemini model. It is optional; the Python workflow works without credentials. See [Google Cloud integration](docs/google-cloud.md) for exact commands and persistence caveats.

## Architecture

`CLI / ADK tool → JobStore (SQLite) → collect (async fan-out) → analyze → report`

- `resilient_agent/engine.py`: async orchestration, bounded retry, checkpointed state, synthetic tool adapter.
- `resilient_agent/__main__.py`: start / show / resume CLI.
- `resilient_agent/agent.py`: optional Google ADK agent and function tools (requires `requirements.txt`).
- `tests/`: offline tests for idempotency, retry, restart/resume and checkpoint invariants.

Cloud Shell's local SQLite file survives a process restart within the same Cloud Shell home, but is not a shared production database. Cloud Run's container filesystem is ephemeral. This is a workshop teaching implementation, not a production-grade distributed job queue; see [production upgrades](docs/google-cloud.md#production-upgrades).

## Event context

The supplied event agenda: 5:30–6:00 p.m. check-in/food/networking; 6:00–6:30 p.m. tech talk and Q&A; 6:30–8:00 p.m. hands-on code labs; 8:00–8:30 p.m. demos, open discussion and mixer. No date or venue address was supplied. The lab focuses on task orchestration, state and tool integration, and runtime failure recovery.
