#!/bin/sh
set -eu

if [ "${ADND_RUN_MIGRATIONS_ON_STARTUP:-1}" = "1" ]; then
  alembic upgrade head
fi

exec "$@"
