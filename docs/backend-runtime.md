# Backend Runtime Notes

## Runtime Split

This project now assumes:

- API runs in Docker
- queue worker runs in Docker
- Redis runs in Docker
- Postgres runs in Docker
- TRIBE v2 runs on bare metal on the host machine

## Why This Split Exists

The backend stack should be easy to redeploy when the machine changes or is restarted often.

Docker gives us:

- repeatable API deployment
- repeatable worker deployment
- repeatable Redis/Postgres deployment

TRIBE stays on bare metal because:

- it is the heaviest GPU dependency
- keeping it outside the container reduces overhead and environment friction
- we can keep the exact GPU/venv setup stable while the API layer changes independently

## Communication Harness

The Docker services talk to the host-side TRIBE runner via:

- `http://host.docker.internal:8765`

The compose file sets:

- `extra_hosts: host.docker.internal:host-gateway`

That gives Linux containers a stable path back to the host machine.

## Compute Isolation

To avoid traffic interference:

- API runs in its own container
- worker runs in its own container
- GPU queue is isolated from the API
- Celery worker uses `--queues=gpu --concurrency=1`
- bare-metal TRIBE runner uses a process lock so only one GPU inference job runs at a time

With this setup:

- users can still create jobs and poll status while another ad is being evaluated
- API traffic stays light
- GPU work is serialized and predictable

## Expected Throughput

At the current traffic target:

- up to `10` users
- only one TRIBE GPU job should run at once
- all other jobs queue behind it

This is the safest first production posture.

## Restart Story

If the machine restarts:

- `docker compose up -d` restores API, worker, Redis, and Postgres
- data survives through mounted Docker volumes and bind mounts
- the host-side TRIBE runner must also be started again

## Required Host Paths

The backend expects:

- a writable host data root mounted to `/data`
- a read-only rated reference workspace mounted to `/data/reference/workspace_small`
- the same host data root exposed to API/worker via `ADND_HOST_DATA_ROOT` so the bare-metal runner can translate container paths back to host paths

The compose file supports:

- `ADND_HOST_DATA_ROOT`
- `ADND_HOST_REFERENCE_WORKSPACE`
- `ADND_CORS_ORIGINS`
- `ADND_RUN_MIGRATIONS_ON_STARTUP`

## Bare-Metal Runner Start

Example:

```bash
cd /path/to/repo
source /path/to/tribev2/.venv/bin/activate
pip install uv fastapi uvicorn
python scripts/tribe_runner_service.py
```

Run it under a system service or process manager in production.

Systemd unit in this repo:

- `deploy/systemd/adnd-tribe-runner.service`

Install example:

```bash
sudo cp deploy/systemd/adnd-tribe-runner.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now adnd-tribe-runner
sudo systemctl status adnd-tribe-runner
```

## Deployment Sequence

1. Start bare-metal TRIBE runner
2. Copy `.env.backend.example` to `.env.backend`
3. Set host bind paths and a real `ADND_POSTGRES_PASSWORD`
4. Run `docker compose up -d --build`
5. Verify:
   - `GET /health` on API
   - `GET /health` on TRIBE runner
   - `GET /v1/jobs/{job_id}/events` streams status updates for the frontend

## Database Migrations

The API container now runs `alembic upgrade head` on startup before serving traffic.

Manual commands:

```bash
alembic upgrade head
alembic current
```

## Clerk Production Mode

To switch from development auth to Clerk-backed production auth:

1. Set `ADND_AUTH_MODE=clerk`
2. Set `ADND_CLERK_JWKS_URL`
3. Set `ADND_CLERK_ISSUER`
4. Optionally set `ADND_CLERK_AUDIENCE`
5. Set `ADND_CORS_ORIGINS` to your Vercel frontend origin

When `ADND_AUTH_MODE=clerk`, startup config now requires the Clerk issuer and JWKS URL.
