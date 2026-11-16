# Guided labs (90 minutes)

Use the [README quick start](../README.md#cloud-shell-quick-start-no-local-setup) first. Each lab has an observable result and one extension to try.

## Lab 1: concurrent tools (15 min)

1. Read `collect_source` and the `asyncio.gather` call in `resilient_agent/engine.py`.
2. Run `python3 -m resilient_agent --db lab1.db start signals "service readiness"`.
3. Run `python3 -m resilient_agent --db lab1.db show signals`. Find the ordered `evidence` array and `report.review_required` flag.
4. Extension: add a fourth synthetic source to `SOURCES`; rerun with a new job ID and run the tests. Discuss what happens when one concurrent source times out (no partial checkpoint).

## Lab 2: checkpoints and recovery (25 min)

1. Run `python3 -m resilient_agent --db lab2.db start recovery "release review" --fail-once analyze`.
2. Inspect `attempts`: `collect` should be 1, `analyze` should be 2, `report` should be 1.
3. Run `python3 -m resilient_agent --db lab2.db resume recovery`; completed stages should not run again.
4. For an exhausted-retry case, run `python3 -m unittest tests.test_engine.WorkflowTests.test_resume_after_later_stage_failure -v`. The test restarts the store and resumes after a failed later stage.
5. Extension: add a `--retries` CLI option (currently `run_job(..., retries=2)`) and test zero retries. The persistent `error` and `stage` fields should identify where recovery starts.

## Lab 3: ADK tool integration (25 min)

1. Follow [Cloud integration](google-cloud.md#vertex-ai-and-adk-in-cloud-shell) to install dependencies and configure an authorized project.
2. Read `resilient_agent/agent.py` and identify `root_agent`, `start_research`, and `inspect_research`.
3. Run `adk web .` in Cloud Shell, select `resilient_agent`, and request "Research release readiness". Inspect the tool events and verify the answer calls the synthetic data synthetic.
4. Extension: replace `collect_source` with a real authenticated data client. Keep bounded timeouts and errors; add fake-client contract tests before enabling network access. Do not embed credentials in source or logs.

## Lab 4: Cloud Run demo (25 min)

1. Follow the [Cloud Run deployment](google-cloud.md#optional-cloud-run-deployment) commands. Deployment may take longer or fail if billing/IAM is unavailable; use the CLI demo instead.
2. Check `/list-apps`, create a session, and run a prompt through `/run` with an identity token. Demonstrate the tool-call trace.
3. Discuss why neither default ADK in-memory sessions nor the demo's container-local SQLite database provides durable cross-instance state. Diagram a production swap to managed sessions plus a transactional job store.
4. Demo checkpointed failure recovery from Lab 2 and share one thing you would change for a real service.
