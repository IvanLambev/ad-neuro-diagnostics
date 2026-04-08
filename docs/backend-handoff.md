# Backend Handoff

## Goal

Host the analysis backend on the machine / VM and keep everything in one repo.

The backend must:

1. Receive uploads
2. Validate file type and duration
3. Queue long-running analysis
4. Run the existing Python analysis pipeline
5. Store job state and outputs
6. Return structured report JSON to the frontend

## Stack

- existing `ad_neuro_diagnostics` Python package as the analysis engine
- FastAPI for HTTP API
- Celery for long-running jobs
- Redis for queue broker
- Postgres for app data

Recommended deployment:

- Python API on the VM
- Celery worker on the VM
- Redis on the VM or managed
- Postgres on the VM or managed
- reverse proxy with Caddy or Nginx

## Repo Structure

Suggested structure:

```text
/apps/web
/ad_neuro_diagnostics
/backend
/tests
/docs
/docker-compose.yml
/package.json
/pyproject.toml
```

## Analysis Rules

- max ad length: `60 seconds`
- accepted formats: `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`
- TRIBE stays frozen
- downstream scoring is built on top of TRIBE/media-derived features

## Long-Running Job Design

The backend must not process the whole analysis inline in a single request.

Use this pattern:

1. API receives upload
2. API creates job row in database
3. API enqueues Celery task
4. API returns `202 Accepted` with `job_id`
5. Worker processes the job
6. Frontend polls or subscribes to updates
7. API returns final report JSON

## Job Statuses

Use:

- `queued`
- `validating`
- `normalizing`
- `running_tribe`
- `extracting_features`
- `benchmarking`
- `generating_report`
- `completed`
- `failed`

## Auth

Use Clerk.

Backend behavior:

- receive `Authorization: Bearer <token>`
- verify Clerk session JWT against Clerk JWKS
- extract `user_id`
- associate jobs and reports with that `user_id`

Do not build custom auth or custom JWT issuance.

## API Endpoints

### `POST /v1/jobs`

Creates a new analysis job.

Input:

- `multipart/form-data`
- `file`
- `title`
- `brand`
- `campaign`
- `notes` optional

Response:

```json
{
  "job_id": "job_123",
  "status": "queued"
}
```

### `GET /v1/jobs`

Lists current user jobs.

### `GET /v1/jobs/:job_id`

Returns job progress.

Example:

```json
{
  "job_id": "job_123",
  "status": "running_tribe",
  "progress": 56,
  "current_step": "running_tribe",
  "created_at": "2026-04-08T12:00:00Z",
  "updated_at": "2026-04-08T12:10:00Z"
}
```

### `GET /v1/jobs/:job_id/events`

Optional SSE stream for progress.

### `GET /v1/jobs/:job_id/report`

Returns structured report JSON.

### `GET /v1/jobs/:job_id/assets/:asset_name`

Returns generated images and other assets.

### `POST /v1/jobs/:job_id/retry`

Retries failed jobs.

## Validation Rules

Backend is the final authority.

If video is too long:

- HTTP `422`
- code: `video_too_long`
- message: `Ads longer than 60 seconds are not supported yet.`

## Worker Pipeline

Each job should run:

1. validate auth ownership and input
2. validate video duration and file type
3. save upload
4. normalize clip
5. run TRIBE
6. extract features
7. compare against historical rated set
8. build customer-facing report JSON
9. persist outputs and assets

## Report Contract

Backend should expose JSON with:

- ad metadata
- summary bands for attention / clarity / memorability
- strengths
- risks
- similar ads
- moment-level insights
- plain-English reasons
- technical appendix fields
- URLs for generated assets

## Storage

Need storage for:

- uploaded source files
- normalized clips
- TRIBE artifacts
- generated features
- generated reports
- generated visual assets
- job metadata
- user ownership

Suggested split:

- Postgres for structured data
- filesystem or object storage for large media and assets

## Queue Rules

- GPU concurrency starts at `1`
- jobs can queue safely
- support `batch_id` for future multi-upload batches
- first MVP can process one GPU job at a time

## MVP Deliverable

One completed backend flow:

1. authenticated upload
2. queued processing
3. completed report JSON
4. asset URLs
5. retry on failure

## Non-Goals For V1

- retraining TRIBE
- strong business-outcome prediction claims
- ads longer than 60 seconds
- advanced multi-tenant org logic

## References

- [Clerk authenticated requests](https://clerk.com/docs/guides/development/making-requests)
- [Clerk manual JWT verification](https://clerk.com/docs/guides/sessions/manual-jwt-verification)
- [FastAPI background task caveat](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [BullMQ overview](https://docs.bullmq.io/)
