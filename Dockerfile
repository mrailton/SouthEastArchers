# Stage 1: Build assets
FROM node:20-alpine AS assets-builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Application with serversideup FrankenPHP
FROM serversideup/php:8.5-frankenphp

WORKDIR /var/www/html

# Copy application files
COPY --chown=www-data:www-data . .

# Copy built assets from Stage 1
COPY --from=assets-builder --chown=www-data:www-data /app/public/build ./public/build

# Get latest Composer and install dependencies
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer
RUN composer install --no-interaction --optimize-autoloader --no-dev --no-scripts

# Set permissions
RUN chown -R www-data:www-data /var/www/html/storage /var/www/html/bootstrap/cache

# Environment variables for PHP configuration
ENV PHP_OPCACHE_ENABLE="1" \
    PHP_UPLOAD_MAX_FILE_SIZE="64M" \
    PHP_POST_MAX_SIZE="64M" \
    PHP_MEMORY_LIMIT="256M"

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/up || exit 1
