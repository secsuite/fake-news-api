# Deployment And CI/CD

This service uses two GitHub Actions workflows:

- `.github/workflows/model-release.yml`
- `.github/workflows/deploy.yml`

## Required CLI Tools

Install and authenticate:

- GitHub CLI (`gh`)
- Google Cloud CLI (`gcloud`)

Verify both are available:

```bash
gh --version
gcloud --version
gh auth login
```

## Single Source Of Truth

Set values in `.env` and mirror them as GitHub repository variables:

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `SERVICE_NAME`
- `STAGING_SERVICE_NAME`
- `AR_REPO`
- `IMAGE_NAME`
- `MODEL_BUCKET`
- `MODEL_ARTIFACTS_PREFIX`
- `GHA_SA_NAME`
- `REPO_SLUG`

## One-Time Bootstrap

Run these once per GCP project/repository.

### 1. Create project, link billing, and enable required APIs

```bash
set -a; source .env; set +a
gcloud auth login
gcloud projects create "$GCP_PROJECT_ID" --name="$GCP_PROJECT_ID" || true
gcloud billing accounts list
gcloud billing projects link "$GCP_PROJECT_ID" --billing-account="$(gcloud billing accounts list --filter='open=true' --format='value(ACCOUNT_ID)' --limit=1)"
gcloud config set project "$GCP_PROJECT_ID"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com
```

### 2. Create model bucket and upload initial artifacts

```bash
set -a; source .env; set +a
gcloud storage buckets create "gs://${MODEL_BUCKET}" --location="${GCP_REGION}" || true
gcloud storage rsync -r app/ml/models/fake_news "gs://${MODEL_BUCKET}/${MODEL_ARTIFACTS_PREFIX}/bootstrap"
```

### 3. Create GitHub Actions deploy service account

```bash
set -a; source .env; set +a
PROJECT_NUMBER="$(gcloud projects describe "$GCP_PROJECT_ID" --format='value(projectNumber)')"
GHA_SA_NAME="${GHA_SA_NAME:-gha-${GCP_PROJECT_ID}}"
GHA_SA_EMAIL="${GHA_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts create "$GHA_SA_NAME" \
  --display-name="GitHub Actions deployer" || true

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" --member="serviceAccount:${GHA_SA_EMAIL}" --role="roles/cloudbuild.builds.editor"
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" --member="serviceAccount:${GHA_SA_EMAIL}" --role="roles/artifactregistry.admin"
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" --member="serviceAccount:${GHA_SA_EMAIL}" --role="roles/storage.admin"
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" --member="serviceAccount:${GHA_SA_EMAIL}" --role="roles/run.admin"
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" --member="serviceAccount:${GHA_SA_EMAIL}" --role="roles/iam.serviceAccountUser"
```

### 4. Configure Workload Identity Federation (GitHub OIDC)

```bash
set -a; source .env; set +a
PROJECT_NUMBER="$(gcloud projects describe "$GCP_PROJECT_ID" --format='value(projectNumber)')"
POOL_ID=github
PROVIDER_ID=github-provider
GHA_SA_NAME="${GHA_SA_NAME:-gha-${GCP_PROJECT_ID}}"
GHA_SA_EMAIL="${GHA_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
REPO_SLUG="${REPO_SLUG:-$(git config --get remote.origin.url | sed -E 's#(git@github.com:|https://github.com/)##; s#\\.git$##')}"

gcloud iam workload-identity-pools create "$POOL_ID" \
  --project="$GCP_PROJECT_ID" \
  --location="global" \
  --display-name="GitHub pool" || true

gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
  --project="$GCP_PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="$POOL_ID" \
  --display-name="GitHub provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == '${REPO_SLUG}'" || true

gcloud iam service-accounts add-iam-policy-binding "$GHA_SA_EMAIL" \
  --project="$GCP_PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${REPO_SLUG}"

gcloud iam service-accounts add-iam-policy-binding "$GHA_SA_EMAIL" \
  --project="$GCP_PROJECT_ID" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${REPO_SLUG}"
```

### 5. Grant Cloud Build service account permissions

Cloud Build executes image push and Cloud Run deploy in `cloudbuild.yaml`, so grant roles to the project Cloud Build service account:

```bash
set -a; source .env; set +a
PROJECT_NUMBER="$(gcloud projects describe "$GCP_PROJECT_ID" --format='value(projectNumber)')"
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" --member="serviceAccount:${CB_SA}" --role="roles/storage.objectViewer"
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" --member="serviceAccount:${CB_SA}" --role="roles/run.admin"
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" --member="serviceAccount:${CB_SA}" --role="roles/iam.serviceAccountUser"
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" --member="serviceAccount:${CB_SA}" --role="roles/artifactregistry.writer"
```

### 6. Set GitHub repository variables

```bash
set -a; source .env; set +a
PROJECT_NUMBER="$(gcloud projects describe "$GCP_PROJECT_ID" --format='value(projectNumber)')"
GHA_SA_NAME="${GHA_SA_NAME:-gha-${GCP_PROJECT_ID}}"
GHA_SA_EMAIL="${GHA_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

gh variable set GCP_PROJECT_ID --body "$GCP_PROJECT_ID"
gh variable set GCP_REGION --body "$GCP_REGION"
gh variable set MODEL_BUCKET --body "$MODEL_BUCKET"
gh variable set MODEL_ARTIFACTS_PREFIX --body "$MODEL_ARTIFACTS_PREFIX"
gh variable set SERVICE_NAME --body "$SERVICE_NAME"
gh variable set STAGING_SERVICE_NAME --body "$STAGING_SERVICE_NAME"
gh variable set AR_REPO --body "$AR_REPO"
gh variable set IMAGE_NAME --body "$IMAGE_NAME"
gh variable set GCP_WORKLOAD_IDENTITY_PROVIDER --body "projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github/providers/github-provider"
gh variable set GCP_SERVICE_ACCOUNT --body "${GHA_SA_EMAIL}"
```

## Required GitHub Variables

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `MODEL_BUCKET`
- `MODEL_ARTIFACTS_PREFIX`
- `SERVICE_NAME`
- `STAGING_SERVICE_NAME`
- `AR_REPO`
- `IMAGE_NAME`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`

## Recommended GitHub Environments

- `staging`
- `production` (optionally add required reviewers)

## Workflow Behavior

### Pull Request To `master`

`Deploy` workflow runs:

1. `Quality Gates` job (`make quality`)

### Push/Merge To `master`

`Deploy` workflow runs only `Deploy Staging`.
`Quality Gates` is not rerun on `master` push.

Staging deploy flow:

1. Resolve model URI from workflow input or `gs://<MODEL_BUCKET>/<MODEL_ARTIFACTS_PREFIX>/latest.txt`
2. Build and deploy to Cloud Run
3. Grant public invoker (`roles/run.invoker` to `allUsers`)
4. Smoke check `GET /health`

### Manual Deploy (`workflow_dispatch`)

- `environment=staging`: runs staging deploy path.
- `environment=production`: runs production deploy path with the same smoke check.

Production also grants public invoker automatically.

## Pipeline Usage

First-time order:

1. Upload bootstrap model artifacts to GCS.
2. Run `Model Release` to publish a version and update `latest.txt`.
3. Run `Deploy`.

Model release run:

```bash
set -a; source .env; set +a
gh workflow run "Model Release" \
  -f source_uri="gs://${MODEL_BUCKET}/${MODEL_ARTIFACTS_PREFIX}/bootstrap" \
  -f update_latest=true
```

Manual deploy runs:

```bash
gh workflow run "Deploy" -f environment=staging
gh workflow run "Deploy" -f environment=production
```

## Model Release Flow

`model-release.yml` publishes model artifacts from a source GCS URI to a
versioned destination under:

`gs://<MODEL_BUCKET>/<MODEL_ARTIFACTS_PREFIX>/<version>`

It validates required files:

- `model.onnx`
- `config.json`
- `tokenizer_config.json`
- `vocab.json`
- `merges.txt`
- `special_tokens_map.json`

It then writes `manifest.json` and optionally updates:

`gs://<MODEL_BUCKET>/<MODEL_ARTIFACTS_PREFIX>/latest.txt`

Deploy workflow consumes this `latest.txt` pointer by default.

## Public Access Policy

Public invocation for staging and production is automated in deployment workflow.
Manual post-deploy IAM updates are not required for smoke checks.

## Post-Deploy Checks

Fetch deployed URLs:

```bash
set -a; source .env; set +a
gcloud run services describe "$STAGING_SERVICE_NAME" --region="$GCP_REGION" --format='value(status.url)'
gcloud run services describe "$SERVICE_NAME" --region="$GCP_REGION" --format='value(status.url)'
```

Smoke endpoints:

- `https://<service-url>/health`
- `https://<service-url>/docs`
