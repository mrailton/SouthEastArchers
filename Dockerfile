# Build stage for Node.js assets
FROM node:20-alpine AS node-builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY resources ./resources
COPY vite.config.js ./
RUN npm run build

# Production image with PHP 8.5 Alpine + FrankenPHP
FROM php:8.5-alpine

# Install dependencies and PHP extensions
RUN apk add --no-cache \
    curl \
    icu-libs \
    libzip \
    && apk add --no-cache --virtual .build-deps \
    $PHPIZE_DEPS \
    icu-dev \
    libzip-dev \
    linux-headers \
    && docker-php-ext-install -j$(nproc) \
    pdo_mysql \
    opcache \
    pcntl \
    intl \
    zip \
    bcmath \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && apk del .build-deps \
    && rm -rf /tmp/*

# Install FrankenPHP
RUN curl -fsSL https://github.com/dunglas/frankenphp/releases/latest/download/frankenphp-linux-$(uname -m | sed 's/aarch64/arm64/' | sed 's/x86_64/x86_64/') -o /usr/local/bin/frankenphp \
    && chmod +x /usr/local/bin/frankenphp

# Set working directory
WORKDIR /app

# Copy composer from official image
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

# Copy application files
COPY --chown=www-data:www-data . .

# Copy built assets from node builder
COPY --from=node-builder --chown=www-data:www-data /app/public/build ./public/build

# Install composer dependencies
RUN composer install --no-dev --optimize-autoloader --no-interaction --no-progress \
    && rm -rf /root/.composer

# Create required directories and set permissions
RUN mkdir -p storage/framework/{sessions,views,cache} \
    && mkdir -p storage/logs \
    && mkdir -p bootstrap/cache \
    && chown -R www-data:www-data storage bootstrap/cache

# Configure PHP for production
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini" \
    && echo "opcache.enable=1" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "opcache.memory_consumption=256" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "opcache.interned_strings_buffer=64" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "opcache.max_accelerated_files=32531" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "opcache.validate_timestamps=0" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "opcache.save_comments=1" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "realpath_cache_size=8192K" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "realpath_cache_ttl=600" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "memory_limit=256M" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "upload_max_filesize=64M" >> "$PHP_INI_DIR/conf.d/99-custom.ini" \
    && echo "post_max_size=64M" >> "$PHP_INI_DIR/conf.d/99-custom.ini"

# Create Caddyfile for FrankenPHP
RUN mkdir -p /etc/caddy && printf '{\n\
    frankenphp\n\
    order php_server before file_server\n\
}\n\
\n\
:80 {\n\
    root * /app/public\n\
    encode zstd gzip\n\
    php_server\n\
    file_server\n\
}\n' > /etc/caddy/Caddyfile

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
