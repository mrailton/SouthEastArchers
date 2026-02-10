# Build stage for Node.js assets
FROM node:20-alpine AS node-builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY resources ./resources
COPY vite.config.js ./
RUN npm run build

# Production image with FrankenPHP
FROM dunglas/frankenphp:latest-php8.5-alpine

# Install PHP extensions
RUN install-php-extensions \
    pdo_mysql \
    redis \
    opcache \
    pcntl \
    intl \
    zip \
    bcmath

# Set working directory
WORKDIR /app

# Copy application files
COPY --chown=www-data:www-data . .

# Copy built assets from node builder
COPY --from=node-builder --chown=www-data:www-data /app/public/build ./public/build

# Install composer dependencies
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer
RUN composer install --no-dev --optimize-autoloader --no-interaction --no-progress

# Create required directories and set permissions
RUN mkdir -p storage/framework/{sessions,views,cache} \
    && mkdir -p storage/logs \
    && mkdir -p bootstrap/cache \
    && chown -R www-data:www-data storage bootstrap/cache

# Configure PHP for production
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

# Create custom PHP config
RUN echo "opcache.enable=1" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "opcache.memory_consumption=256" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "opcache.interned_strings_buffer=64" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "opcache.max_accelerated_files=32531" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "opcache.validate_timestamps=0" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "opcache.save_comments=1" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "opcache.fast_shutdown=0" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "realpath_cache_size=8192K" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "realpath_cache_ttl=600" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "memory_limit=256M" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "upload_max_filesize=64M" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "post_max_size=64M" >> "$PHP_INI_DIR/conf.d/99-custom.ini"

# Create Caddyfile for FrankenPHP
RUN echo '{\n\
    frankenphp\n\
    order php_server before file_server\n\
}\n\
\n\
:80 {\n\
    root * /app/public\n\
    encode zstd gzip\n\
    php_server\n\
    file_server\n\
}' > /etc/caddy/Caddyfile

# Cache configuration and routes
RUN php artisan config:clear \
    && php artisan route:clear \
    && php artisan view:clear

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/up || exit 1

# Start FrankenPHP
CMD ["frankenphp", "run", "--config", "/etc/caddy/Caddyfile"]
