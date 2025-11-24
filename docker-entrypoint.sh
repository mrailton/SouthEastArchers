#!/bin/bash
# Entrypoint script for web container
# Runs database migrations before starting the app

set -e

echo "🔄 Running database migrations..."
flask db upgrade

echo "🚀 Starting application..."
exec "$@"
