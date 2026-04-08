# Frontend Handoff

## Goal

Build a customer-facing tool for ad makers, not neuroscientists.

The frontend should let a user:

1. Sign in
2. Upload a video ad up to 60 seconds long
3. Submit it for analysis
4. Watch job progress
5. Read a plain-English report

## Stack

- Vite 8
- React + TypeScript
- shadcn/ui
- preset: `--preset b3kJnl0v2`
- deploy on Vercel

Recommended libraries:

- `@clerk/clerk-react`
- `@tanstack/react-query`
- `react-router-dom`
- `react-hook-form`
- `zod`
- `@hookform/resolvers`
- `recharts`

## Setup

```bash
npm create vite@latest apps/web -- --template react-ts
cd apps/web
npx shadcn@latest init -t vite -d --base radix --preset b3kJnl0v2 -f
npm install @clerk/clerk-react @tanstack/react-query react-router-dom react-hook-form zod @hookform/resolvers recharts
```

Use `radix`, not `base`.

## Product Language

Use these labels in the UI:

- `Attention`
- `Clarity`
- `Memorability`
- `Strong moments`
- `Potential weak moments`
- `Similar ads`
- `Why we think this`
- `Technical appendix`

Do not lead with:

- ROI names
- brain acronyms
- raw feature names like `mean_abs_max`

## Pages

### 1. Landing

Explain:

- what the tool does
- that it compares ads against a historical library
- that results are guidance, not absolute truth

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

- accepted formats: `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`
- max duration: `60 seconds`

### 5. Job Progress

Show:

- current stage
- progress state
- failure with retry

### 6. Report View

Top-level sections:

- `Quick Read`
- `What This Means`
- `Similar Ads You Should Compare Against`
- `Historical Benchmark`
- `Why The System Thinks That`
- `Technical Appendix`

### 7. Historical Library

Show:

- prior analyzed ads
- filters by brand, campaign, date, status

## Frontend API Behavior

The frontend should never wait for full analysis in one request.

Flow:

1. Upload ad
2. Receive `job_id`
3. Route to progress screen
4. Poll or subscribe for updates
5. Fetch final report when done

Use TanStack Query for:

- job list
- job detail polling
- report fetch
- retry mutation

Recommended polling:

- active jobs every 5 seconds
- stop polling at `completed` or `failed`

## Main API Endpoints

- `POST /v1/jobs`
- `GET /v1/jobs`
- `GET /v1/jobs/:job_id`
- `GET /v1/jobs/:job_id/events`
- `GET /v1/jobs/:job_id/report`
- `POST /v1/jobs/:job_id/retry`

## Report JSON Shape

Frontend should render from structured JSON, not raw markdown only.

Expected top-level shape:

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
    "attention": {},
    "clarity": {},
    "memorability": {}
  },
  "strengths": [],
  "risks": [],
  "similar_ads": [],
  "moments": [],
  "why": {},
  "assets": {},
  "technical": {}
}
```

## Auth

Use Clerk.

Frontend behavior:

- sign in with Clerk
- send `Authorization: Bearer <token>` to backend

Do not build custom auth.

## Vercel Notes

This app will be deployed on Vercel as a Vite app.

If deployed as an SPA, deep-link rewrites may be needed in `vercel.json`.

## Non-Goals For V1

- brain-science-first UI
- multi-minute ads
- custom auth
- real-time collaborative editing

## References

- [shadcn/ui Vite docs](https://ui.shadcn.com/docs/installation/vite)
- [shadcn CLI docs](https://ui.shadcn.com/docs/cli)
- [shadcn monorepo docs](https://ui.shadcn.com/docs/monorepo)
- [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite)
- [Clerk React quickstart](https://clerk.com/docs/react/getting-started/quickstart)
- [Clerk authenticated requests](https://clerk.com/docs/guides/development/making-requests)
