#!/bin/sh
set -eu

if [ "${ADND_RUN_MIGRATIONS_ON_STARTUP:-1}" = "1" ]; then
  LEGACY_SCHEMA_STATE="$(python - <<'PY'
import os

import psycopg

conn = psycopg.connect(
    host=os.environ.get("ADND_POSTGRES_HOST", "postgres"),
    port=os.environ.get("ADND_POSTGRES_PORT", "5432"),
    dbname=os.environ.get("ADND_POSTGRES_DB", "ad_neuro_diagnostics"),
    user=os.environ.get("ADND_POSTGRES_USER", "adnd_app"),
    password=os.environ["ADND_POSTGRES_PASSWORD"],
)
try:
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass('public.analysis_jobs'), to_regclass('public.alembic_version')")
        analysis_jobs, alembic_version = cur.fetchone()
        if analysis_jobs and not alembic_version:
            print("stamp")
        else:
            print("upgrade")
finally:
    conn.close()
PY
)"

  if [ "$LEGACY_SCHEMA_STATE" = "stamp" ]; then
    alembic stamp head
  fi

  alembic upgrade head
fi

exec "$@"
