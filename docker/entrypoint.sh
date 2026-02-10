#!/bin/bash
set -e

echo "Starting Laravel deployment tasks..."

# Run migrations
echo "Running migrations..."
php artisan migrate --force

# Run seeders
echo "Running seeders..."
php artisan db:seed --force

# Create storage link
echo "Creating storage link..."
php artisan storage:link --force || true

# Cache configuration
echo "Caching configuration..."
php artisan config:cache
php artisan route:cache
php artisan view:cache
php artisan event:cache

echo "Deployment tasks complete. Starting server..."

# Start FrankenPHP server
exec frankenphp run --config /etc/caddy/Caddyfile "$@"
