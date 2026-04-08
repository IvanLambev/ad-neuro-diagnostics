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

## Still Not Done

- [ ] Build and start the Docker stack locally
- [ ] Wire production Clerk settings
- [ ] Add SSE progress streaming
- [ ] Add database migrations
- [ ] Run a full end-to-end upload through Docker plus the host runner

## Important Files

- `backend/app.py`
- `backend/pipeline.py`
- `backend/report_builder.py`
- `backend/routers/jobs.py`
- `docker-compose.yml`
- `scripts/tribe_runner_service.py`
- `docs/backend-runtime.md`

## Next Execution Order

1. Build Docker images.
2. Start Postgres, Redis, API, and worker locally.
3. Start the bare-metal TRIBE runner on the host.
4. Verify API health and TRIBE runner health.
5. Submit one real job through the API.
6. Confirm queued -> completed flow and output assets.
7. Add SSE progress.
8. Add migrations.
9. Switch auth from development mode to Clerk production mode.
