# Frontend + Backend Handoff

## Goal

Build this as a customer-facing tool for ad makers, not neuroscientists.

The product should let a user:

1. Sign in
2. Upload a video ad up to 60 seconds long
3. Submit it for analysis
4. Watch job progress while the backend processes it
5. See a plain-English report with:
   - attention
   - clarity
   - memorability
   - similar historical ads
   - strongest moments
   - possible weak moments
   - practical recommendations
6. Optionally expand a technical appendix

## Product Language Rules

The main UI must speak like a creative strategist.

Use these labels:

- `Attention` instead of `engagement`
- `Clarity` instead of `confusion`
- `Memorability` instead of `memorability score`
- `Strong moments`
- `Potential drop-off moments`
- `Similar ads`
- `Why we think this`
- `Technical appendix`

Do **not** lead with:

- ROI names
- timestep indexes
- brain region acronyms
- `mean_abs_max`, `max_abs_std`, or other raw feature names

Those should live behind an expandable advanced section.

## Recommended Architecture

### Frontend

- Vite 8
- React + TypeScript
- shadcn/ui
- `--preset b3kJnl0v2`
- deploy frontend on Vercel
- frontend talks directly to the backend API over HTTPS

Recommended frontend libraries:

- `@clerk/clerk-react` for auth
- `@tanstack/react-query` for API state, polling, caching, and mutation flows
- `react-router-dom` for routing
- `react-hook-form` + `zod` for upload/metadata forms
- `recharts` for simple comparison charts and timelines

### Backend

Use the existing Python codebase as the core analysis engine.

Add:

- FastAPI for the HTTP API
- Celery for long-running jobs
- Redis for queue + worker broker
- Postgres for users, jobs, uploads, reports, and audit data

Why this shape:

- FastAPI is a good fit for a typed Python API
- FastAPI's own docs note that heavy background computation should use a bigger tool such as Celery instead of `BackgroundTasks`
- Celery + Redis is a mature, standard solution for long-running queued work
- the current analysis pipeline is already Python, so this keeps the backend aligned with the existing code

### Deployment Topology

- `apps/web` -> Vercel
- Python API -> your machine / VM
- Celery worker -> same machine / VM
- Redis -> same machine or managed Redis
- Postgres -> same machine or managed Postgres
- reverse proxy on the backend machine via Caddy or Nginx

Suggested domains:

- `app.yourdomain.com` -> Vercel frontend
- `api.yourdomain.com` -> backend machine

## Repo Structure

Keep everything in one repo.

Suggested structure:

```text
/apps/web                    # Vite frontend
/ad_neuro_diagnostics        # existing Python analysis package
/backend                     # FastAPI app layer
/tests
/docs
/docker-compose.yml
/package.json                # workspace root for frontend tooling
/pyproject.toml              # Python backend package
```

Frontend team should work mainly inside:

- `apps/web`

Backend/API team should work mainly inside:

- `backend`
- `ad_neuro_diagnostics`

## Frontend Setup

Inside `apps/web`:

```bash
npm create vite@latest apps/web -- --template react-ts
cd apps/web
npx shadcn@latest init -t vite -d --base radix --preset b3kJnl0v2 -f
npm install @clerk/clerk-react @tanstack/react-query react-router-dom react-hook-form zod @hookform/resolvers recharts
```

Notes:

- use `radix`, not `base`
- do not use interactive shadcn init
- keep the frontend as an SPA unless the team later decides they need SSR

## Auth

Use Clerk.

Why:

- it is a working, production auth solution
- Clerk has an official React quickstart for Vite
- Clerk supports sending session tokens to a separate backend
- Clerk documents cross-origin backend auth via `Authorization: Bearer <token>`

### Frontend Auth Flow

- user signs in with Clerk in the Vite app
- frontend gets a Clerk session token
- every API request to the backend includes `Authorization: Bearer <token>`

### Backend Auth Flow

- backend verifies the Clerk session JWT against Clerk JWKS
- backend extracts `user_id`
- backend stores job ownership and access rules by `user_id`

Important:

- do not build custom username/password auth
- do not build custom JWT issuance
- use Clerk-managed auth, backend-side token verification

## Video Constraints

These are product rules and must be enforced in both frontend and backend.

- max duration: `60 seconds`
- accepted formats: `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`
- frontend should pre-validate duration when possible
- backend must be the final authority using `ffprobe`

If the upload is too long, return:

- HTTP `422`
- code: `video_too_long`
- message: `Ads longer than 60 seconds are not supported yet.`

## Long-Running Job Model

The frontend must never wait for analysis in a single request.

Use this pattern:

1. Upload ad
2. Create job
3. Backend returns `202 Accepted` with `job_id`
4. Frontend moves user to a job progress screen
5. Frontend polls or subscribes to progress updates
6. When job is done, frontend loads the report

### Job Statuses

Use these backend statuses:

- `queued`
- `validating`
- `normalizing`
- `running_tribe`
- `extracting_features`
- `benchmarking`
- `generating_report`
- `completed`
- `failed`

### Queue Rules

- start with GPU concurrency = `1`
- queue multiple ads safely
- allow batches by grouping jobs under `batch_id`
- first MVP can process jobs one at a time on the GPU queue

## Frontend Pages

### 1. Marketing / Landing

Purpose:

- explain the product simply
- show example outputs
- explain that results compare an ad against a historical library

### 2. Sign In

Use Clerk components.

### 3. Dashboard

Show:

- recent jobs
- current statuses
- completed reports
- failed jobs

### 4. New Analysis

Form fields:

- video upload
- ad title
- brand
- campaign
- optional notes

Validation:

- file type
- max duration 60s
- show estimated processing time

### 5. Job Progress

Show:

- upload complete
- queue position if available
- current stage
- stage timestamps
- failure state with retry button

### 6. Report View

Top-level sections:

- `Quick Read`
- `What This Means`
- `Similar Ads`
- `Strong moments`
- `Potential weak moments`
- `Why we think this`
- `Technical appendix`

### 7. Historical Library

Show:

- previously analyzed ads
- filters by brand, campaign, date, and status
- ability to open any report

## Report Shape The Frontend Should Expect

Frontend should render a report from a JSON contract, not from raw markdown only.

Suggested result payload:

```json
{
  "job_id": "job_123",
  "status": "completed",
  "ad": {
    "ad_id": "brand-abc123",
    "title": "Spring Promo 1",
    "brand": "Brand",
    "duration_sec": 29.8
  },
  "summary": {
    "attention": {
      "band": "slightly_strong",
      "score": 2.67,
      "dataset_mean": 2.47,
      "peer_mean": 2.22
    },
    "clarity": {
      "band": "strong",
      "score": 1.67,
      "dataset_mean": 2.33,
      "peer_mean": 2.33
    },
    "memorability": {
      "band": "average",
      "score": 2.33,
      "dataset_mean": 2.33,
      "peer_mean": 2.11
    }
  },
  "strengths": [
    "The ad looks better than average at holding attention."
  ],
  "risks": [
    "The ending may not be especially memorable compared with similar ads."
  ],
  "similar_ads": [
    {
      "ad_id": "doritos-fvybcesuxmm",
      "brand": "Doritos",
      "distance": 6.37,
      "why_similar": "Close pacing and response pattern"
    }
  ],
  "moments": [
    {
      "start_sec": 0,
      "end_sec": 5,
      "label": "Strong hook",
      "impact": ["attention"]
    }
  ],
  "why": {
    "attention": [
      "Bigger swings in intensity",
      "Fewer repeated spikes of attention"
    ],
    "clarity": [
      "Shorter unfolding arc"
    ],
    "memorability": [
      "Shorter runtime"
    ]
  },
  "assets": {
    "activation_curve_url": "https://api.yourdomain.com/files/...",
    "brain_strongest_url": "https://api.yourdomain.com/files/...",
    "brain_animation_url": "https://api.yourdomain.com/files/..."
  },
  "technical": {
    "top_rois": ["V8-rh", "V8-lh"],
    "strongest_timestep": 11
  }
}
```

## API Contract

### `POST /v1/jobs`

Creates a new analysis job.

Request:

- `multipart/form-data`
- fields:
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

List jobs for the signed-in user.

### `GET /v1/jobs/:job_id`

Get current job state and progress.

Response:

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

Server-Sent Events stream for real-time progress.

Use this if available.
If not, frontend should poll `GET /v1/jobs/:job_id` every 3 to 5 seconds.

### `GET /v1/jobs/:job_id/report`

Returns the structured report JSON.

### `GET /v1/jobs/:job_id/assets/:asset_name`

Returns generated assets like:

- activation curve
- strongest-frame image
- brain animation

### `POST /v1/jobs/:job_id/retry`

Retries a failed job if allowed.

## Frontend Data Strategy

Use TanStack Query for:

- job list
- job detail polling
- report fetch
- retry mutation

Recommended behavior:

- poll active jobs every 5 seconds
- stop polling when status is `completed` or `failed`
- invalidate job list after upload and retry

## Backend Processing Pipeline

Each queued job should run these steps:

1. validate auth
2. validate file type and duration
3. save upload
4. normalize clip
5. run TRIBE
6. extract features
7. compare against historical rated set
8. build customer-facing report JSON
9. store assets and final report

## MVP Recommendation

For the first usable product:

- support one ad upload at a time per user
- support multiple queued jobs overall
- do not expose brain-region detail in the main UI
- do expose similar ads and comparison language
- keep the technical appendix behind an accordion

## Non-Goals For V1

- retraining TRIBE
- promising true business-outcome prediction
- multi-minute ads
- collaborative editing
- complicated role systems

## References

These architecture choices are aligned with current official docs:

- shadcn/ui Vite install: [ui.shadcn.com/docs/installation/vite](https://ui.shadcn.com/docs/installation/vite)
- shadcn CLI presets and Vite template: [ui.shadcn.com/docs/cli](https://ui.shadcn.com/docs/cli)
- shadcn monorepo support: [ui.shadcn.com/docs/monorepo](https://ui.shadcn.com/docs/monorepo)
- Vite on Vercel: [vercel.com/docs/frameworks/frontend/vite](https://vercel.com/docs/frameworks/frontend/vite)
- Clerk React quickstart for Vite: [clerk.com/docs/quickstarts/react](https://clerk.com/docs/quickstarts/react)
- Clerk cross-origin request auth: [clerk.com/docs/guides/development/making-requests](https://clerk.com/docs/guides/development/making-requests)
- Clerk session token verification: [clerk.com/docs/request-authentication/validate-session-tokens](https://clerk.com/docs/request-authentication/validate-session-tokens)
- FastAPI background task caveat for heavy jobs: [fastapi.tiangolo.com/tutorial/background-tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
