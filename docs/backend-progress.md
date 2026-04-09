# Backend Progress Tracker

## Current Checkpoint

- [x] Dockerized backend stack added
- [x] FastAPI API skeleton added
- [x] Celery worker wiring added
- [x] Redis and Postgres compose services added
- [x] Bare-metal TRIBE runner bridge added
- [x] Initial job model and job endpoints added
- [x] Initial customer-report builder added
- [x] Runtime notes documented
- [x] Docker stack built and started locally
- [x] API health endpoint verified locally
- [x] Redis/Postgres startup ordering fixed with service health checks
- [x] Hardcoded Postgres credentials removed from tracked files
- [x] Bare-metal runner path translation added for Docker-to-host handoff
- [x] SSE progress streaming added
- [x] Database migrations added and wired into container startup
- [x] Bare-metal TRIBE runner deployed as a host service on the VM
- [x] Smoke upload through Docker plus the host runner verified on the VM
- [x] Full end-to-end upload through Docker plus the host runner previously completed on the VM

## Still Not Done

- [ ] Wire production Clerk settings

## Current Notes

- API is reachable locally at `http://localhost:8000/health` and returns `{"status":"ok"}`.
- `docker compose ps` currently shows `api`, `worker`, `postgres`, and `redis` up.
- The backend image is production-oriented, so `pytest` is not installed inside the container by default.
- Compose now requires explicit Postgres env vars instead of shipping a committed password-like value.
- The backend now translates `/data/...` container paths to host paths before calling the bare-metal TRIBE runner.
- The host-side TRIBE runner is installed as a systemd service on the VM and exposes `http://127.0.0.1:8765/health`.
- The Docker API/worker stack is running on the VM at commit `426eda4`.
- Alembic now stamps legacy databases and upgrades cleanly on startup.
- `ADND_CORS_ORIGINS` is now parsed safely from a plain comma-separated env string.
- Smoke validation on the VM created job `2485f2a7-9ff0-4d34-97a3-3e937b5976f0`, which advanced to `running_tribe` at `45%`.
- SSE validation on the VM returned `event: job` followed by heartbeat frames for the same job.
- A prior VM job `3038e63e-5432-4a26-9dc6-7277afe103a4` completed end to end with report generation.
- Running `tests/test_backend_config.py` from `~/tribev2/.venv` is not valid because that host venv does not include backend dependencies such as `pydantic-settings`.

## Important Files

- `backend/app.py`
- `backend/config.py`
- `backend/pipeline.py`
- `backend/report_builder.py`
- `backend/routers/jobs.py`
- `backend/migrations/env.py`
- `docker-compose.yml`
- `docker/backend-entrypoint.sh`
- `deploy/systemd/adnd-tribe-runner.service`
- `scripts/tribe_runner_service.py`
- `docs/backend-runtime.md`

## Next Execution Order

1. Wire real Clerk issuer, JWKS URL, and audience into the VM `.env.backend`.
2. Submit a Clerk-authenticated job from the frontend.
3. Let one current-revision VM job run all the way to `completed` and re-verify report/assets on the live stack.
4. Add deployment automation for VM rebuilds so restarts are one command.
