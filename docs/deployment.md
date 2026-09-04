# Deployment (Google Cloud Run)

This project's FastAPI wrapper (`src/pathology_extraction/api.py`) can be deployed to Google Cloud Run
directly from source, no Dockerfile required.

> **Why Cloud Run rather than AWS Lambda**: Cloud Run's source-based deploy avoids
> needing a Dockerfile, and matches this project's FastAPI service model more
> directly than Lambda's event-driven invocation model, which would need an
> adapter (e.g. Mangum) to run a persistent HTTP server. 

## Prerequisites

- A Google Cloud account with billing enabled.
- The `gcloud` CLI installed and authenticated (`gcloud auth login`).
- A Google Cloud project created and set as active:
  ```powershell
  gcloud projects create <project-id>
  gcloud config set project <project-id>
  ```
- Billing linked to the project:
  ```powershell
  gcloud billing accounts list
  gcloud billing projects link <project-id> --billing-account=<BILLING_ACCOUNT_ID>
  ```

## One-time setup

Enable the required APIs (Cloud Run will prompt to enable Cloud Build and Artifact
Registry automatically on first deploy if you skip this):

```powershell
gcloud services enable run.googleapis.com secretmanager.googleapis.com
```

## Providing the Groq API key securely

Do not pass the key via `--set-env-vars` or `echo "key" | ...`, both print the raw
value to your terminal and shell history. Instead, write it to a temporary file:

```powershell
notepad key.txt   # paste the key, save, close
gcloud secrets create groq-api-key --data-file=key.txt
Remove-Item key.txt
```

To update the key later (e.g. after rotation):

```powershell
notepad key.txt
gcloud secrets versions add groq-api-key --data-file=key.txt
Remove-Item key.txt
```

Grant Cloud Run's default service account permission to read the secret. Find the
project number with `gcloud projects describe <project-id>`, then:

```powershell
gcloud secrets add-iam-policy-binding groq-api-key --member="serviceAccount:<PROJECT_NUMBER>-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

## Deploying

A `Procfile` at the project root tells Cloud Run's buildpacks how to start the app
(source-based deploys can't infer this automatically for a `pyproject.toml` project):

```
web: uvicorn pathology_extraction.api:app --host 0.0.0.0 --port $PORT
```

Deploy:

```powershell
gcloud run deploy pathology-extraction-api --source . --region europe-west6 --allow-unauthenticated --set-secrets=GROQ_API_KEY=groq-api-key:latest
```

`--allow-unauthenticated` makes the endpoint publicly reachable with no login, appropriate
for a demo API. See [limitations.md](limitations.md) for the implications of this choice.

If you previously deployed with a plain `--set-env-vars=GROQ_API_KEY=...` and are
switching to the secret-based approach, Cloud Run will reject the update unless you
also remove the old binding in the same command:

```powershell
gcloud run deploy pathology-extraction-api --source . --region europe-west6 --allow-unauthenticated --remove-env-vars=GROQ_API_KEY --set-secrets=GROQ_API_KEY=groq-api-key:latest
```

## Monitoring a deployment

`gcloud run deploy` prints a Cloud Build logs URL as soon as the build starts
(`https://console.cloud.google.com/cloud-build/builds/...`). Open it to watch
live build progress, useful for judging whether a slow-looking deploy is still
actively working or genuinely stuck. Given this project's dependencies (notably
`sentence-transformers`, which pulls in PyTorch), a full build can reasonably
take 10-15 minutes; the logs page is the way to distinguish "still building" from
"hung."

## Common failure modes (and root causes found during development)

**Build fails: "provide a main.py or app.py file or a script command in pyproject.toml... or a Procfile"**: 
Buildpacks successfully detected the Python project but has no way to know how to
start it. Fixed by adding the `Procfile` above.

**Deploy succeeds but the container fails its startup health check ("failed to start
and listen on the port")**:
Check for any module-level code that depends on an environment variable being present
at import time. In this project, `Groq()` was originally instantiated at module load
in `extraction.py`; if `GROQ_API_KEY` isn't set, the import itself raises an exception,
so the FastAPI app object never gets created and nothing ever binds to the port.
Cloud Run's health check just times out with a generic message rather than surfacing
the Python traceback directly. The fix was moving client instantiation inside the
function that uses it, so a missing key only fails the specific request, not the
whole app's startup.

To reproduce this failure locally before redeploying (much faster than a full cloud
build/deploy cycle):

```powershell
$env:PORT = "8080"
uvicorn pathology_extraction.api:app --host 0.0.0.0 --port $env:PORT
```

**"Cannot update environment variable... it has already been set with a different type"**:
Happens when switching a variable from a plain env var to a secret reference (or vice
versa) on an existing service. Add `--remove-env-vars=<NAME>` to the same deploy
command that sets the secret.

**"Permission denied on secret... The service account used must be granted the
'Secret Manager Secret Accessor' role"**:
Creating a secret does not automatically let any particular service read it. Grant
access explicitly with `gcloud secrets add-iam-policy-binding`, as shown above.

## Status
Deployment currently fails at container startup on Cloud Run, root cause not yet identified (works correctly when run locally, including with the real secret).
