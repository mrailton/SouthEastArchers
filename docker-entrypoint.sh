#!/bin/bash
# Entrypoint script for web container
# Runs database migrations before starting the app

set -e

echo "⏳ Waiting for database to be ready..."
max_retries=30
retry_count=0
last_error=""
until uv run python -m app.cli db current > /dev/null 2>/tmp/db_check_error || [ $retry_count -eq $max_retries ]; do
    last_error=$(cat /tmp/db_check_error 2>/dev/null || true)
    retry_count=$((retry_count + 1))
    echo "  Database not ready yet (attempt $retry_count/$max_retries)..."
    sleep 2
done

if [ $retry_count -eq $max_retries ]; then
    echo "❌ Database failed to become ready after $max_retries attempts"
    if [ -n "$last_error" ]; then
        echo "Last error:"
        echo "$last_error"
    fi
    exit 1
fi

echo "✅ Database is ready!"
echo "🔄 Running database migrations..."
uv run python -m app.cli db upgrade

echo "🔄 Seeding roles and permissions..."
uv run python -m app.cli rbac seed

echo "🚀 Starting application..."
exec "$@"
