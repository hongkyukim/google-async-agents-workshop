# Google Cloud integration (optional)

Official references: [ADK Cloud Run deployment](https://adk.dev/deploy/cloud-run/), [ADK sessions](https://adk.dev/sessions/session/), [Google Cloud Shell](https://cloud.google.com/shell/docs). This repo's synthetic engine runs without Google credentials; only this extension calls Gemini or deploys cloud resources.

## Vertex AI and ADK in Cloud Shell

Choose a project with billing, Vertex AI access and appropriate IAM. APIs and Cloud Run builds can incur charges. In Cloud Shell:

```bash
export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_GENAI_USE_VERTEXAI="TRUE"
gcloud config set project "$GOOGLE_CLOUD_PROJECT"
gcloud services enable aiplatform.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
adk web .
```

Select `resilient_agent` in the ADK dev UI (Cloud Shell web preview for port 8000). Ask it to research a topic. `start_research` writes synthetic evidence to `WORKSHOP_DB` (default `workshop.db` in the current working directory); `inspect_research` reads it. The model can choose tool calls and text, so do not rely on its answer as an authoritative record: inspect the job via the CLI. If the model isn't available in your project/region, change the `model` in `resilient_agent/agent.py` to a supported Gemini model.

## Optional Cloud Run deployment

Cloud Run deploy requires Cloud Build / Artifact Registry permissions and a runtime service account authorized to invoke Vertex AI. Check your organization's IAM and policy before deploying. ADK's deployment CLI may prompt for authentication policy: choose **authenticated access**, not public. Do not include the dev UI for a public service. The default ADK session service is in-memory. Run from the repo root with the venv active:

```bash
adk deploy cloud_run --project="$GOOGLE_CLOUD_PROJECT" --region="$GOOGLE_CLOUD_LOCATION" --service_name=resilient-agent-lab resilient_agent -- --no-allow-unauthenticated --set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION,GOOGLE_GENAI_USE_VERTEXAI=TRUE"
```

After deployment, set the URL returned by the command as `APP_URL`. Use a fresh session ID:

```bash
export APP_URL="YOUR_SERVICE_URL"
export TOKEN="$(gcloud auth print-identity-token)"
curl -fsS -H "Authorization: Bearer $TOKEN" "$APP_URL/list-apps"
curl -fsS -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  "$APP_URL/apps/resilient_agent/users/lab-user/sessions/lab-session" -d '{}'
curl -fsS -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  "$APP_URL/run" -d '{"app_name":"resilient_agent","user_id":"lab-user","session_id":"lab-session","new_message":{"role":"user","parts":[{"text":"Start a synthetic research job about release readiness, using job ID demo-cloud"}]}}'
```

The deployed container's SQLite database and in-memory ADK sessions can disappear on restart or route to different instances; **do not claim cloud deployment is durable or resumable across instances**. For the checkpoint/recovery guarantee, use the Cloud Shell CLI and its persistent Cloud Shell home. The Cloud Run step showcases the ADK API/tool wiring only. Delete your service after the workshop to avoid ongoing costs: `gcloud run services delete resilient-agent-lab --region="$GOOGLE_CLOUD_LOCATION"`.

## Production upgrades

- Replace `JobStore` with Cloud SQL (transactions, unique job IDs, compare-and-swap stage claims, lease expiry, row locking) or another durable transactional store. Parallel workers need an explicit ownership/lease protocol; the SQLite demo assumes one active worker per job.
- Use a managed ADK session service rather than the Cloud Run default in-memory service. The [ADK deployment docs](https://adk.dev/deploy/cloud-run/) document `--session_service_uri` and its prerequisites.
- Replace `collect_source` with injected clients for real data sources, deadlines, rate limits, bounded backoff and explicit error classification. Use an external queue or task service for long-running requests; a synchronous HTTP tool call is not a background job.
- Authenticate the API, scope jobs by user/tenant, validate inputs and prevent prompt injection in untrusted evidence. Keep PII/credentials out of logs and require a human to approve reports.
