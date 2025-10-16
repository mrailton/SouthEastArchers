#!/usr/bin/env sh
set -e

export PORT="${PORT:-5000}"

if [ -n "${DATABASE_URL}" ]; then
  echo "Running database migrations..."
  flask db upgrade
else
  echo "DATABASE_URL not set; skipping migrations."
fi

exec gunicorn wsgi:app --bind "0.0.0.0:5000" --workers "${WORKERS:-4}"
