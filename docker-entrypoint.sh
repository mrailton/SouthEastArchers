#!/bin/bash
# Entrypoint script for web container
# Runs database migrations before starting the app

set -e

echo "⏳ Waiting for database to be ready..."
# Wait for database to be ready
max_retries=30
retry_count=0
until flask db current > /dev/null 2>&1 || [ $retry_count -eq $max_retries ]; do
    retry_count=$((retry_count + 1))
    echo "  Database not ready yet (attempt $retry_count/$max_retries)..."
    sleep 2
done

if [ $retry_count -eq $max_retries ]; then
    echo "❌ Database failed to become ready after $max_retries attempts"
    exit 1
fi

echo "✅ Database is ready!"
echo "🔄 Running database migrations..."
flask db upgrade

echo "🚀 Starting application..."
exec "$@"
