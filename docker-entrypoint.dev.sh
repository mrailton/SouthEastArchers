#!/bin/bash
set -e

echo "📦 Syncing Python dependencies..."
uv pip install --system -r pyproject.toml --group dev --quiet

echo "📦 Installing Node dependencies..."
npm install --silent

echo "⏳ Waiting for database to be ready..."
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
python manage.py db upgrade

echo "🔄 Seeding roles and permissions..."
python manage.py rbac seed

# Ensure static images are accessible in dev (Vite handles JS/CSS)
mkdir -p resources/static
ln -snf /app/resources/assets/images resources/static/images

echo "🔥 Starting Vite dev server..."
npx vite --host 0.0.0.0 &

echo "🚀 Starting Flask dev server..."
exec flask run --host 0.0.0.0 --port 80 --debug
