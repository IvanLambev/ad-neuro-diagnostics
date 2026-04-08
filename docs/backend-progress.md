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

## Still Not Done

- [ ] Wire production Clerk settings
- [ ] Add SSE progress streaming
- [ ] Add database migrations
- [ ] Start the bare-metal TRIBE runner on the host machine
- [ ] Run a full end-to-end upload through Docker plus the host runner

## Current Notes

- API is reachable locally at `http://localhost:8000/health` and returns `{"status":"ok"}`.
- `docker compose ps` currently shows `api`, `worker`, `postgres`, and `redis` up.
- The backend image is production-oriented, so `pytest` is not installed inside the container by default.
- Full job execution is still blocked until the host-side TRIBE runner is started and reachable from Docker.

## Important Files

- `backend/app.py`
- `backend/pipeline.py`
- `backend/report_builder.py`
- `backend/routers/jobs.py`
- `docker-compose.yml`
- `scripts/tribe_runner_service.py`
- `docs/backend-runtime.md`

## Next Execution Order

1. Start the bare-metal TRIBE runner on the host.
2. Verify TRIBE runner health from Docker.
3. Submit one real job through the API.
4. Confirm queued -> completed flow and output assets.
5. Add SSE progress.
6. Add migrations.
7. Switch auth from development mode to Clerk production mode.
