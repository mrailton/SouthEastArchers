# Multi-stage Dockerfile for Django application with Tailwind CSS
# Supports both ARM64 and AMD64 architectures
# Production-optimized build

# Stage 1: Python dependencies
FROM python:3.14-slim AS python-builder

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install Python dependencies
RUN uv pip install --system -r pyproject.toml

# Stage 2: Build Tailwind CSS
FROM python:3.14-slim AS tailwind-builder

# Install Node.js (required by django-tailwind)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies from previous stage
COPY --from=python-builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Copy application code needed for Tailwind build
COPY manage.py ./
COPY config/ ./config/
COPY theme/ ./theme/
COPY accounts/ ./accounts/
COPY core/ ./core/
COPY events/ ./events/
COPY memberships/ ./memberships/
COPY news/ ./news/
COPY shooting/ ./shooting/
COPY pyproject.toml ./

# Install Tailwind dependencies and build CSS
# Set minimal environment variables for build
ENV DEBUG=False \
    SECRET_KEY=build-time-secret-key \
    DB_NAME=build_db \
    DB_USER=build_user \
    DB_PASSWORD=build_password \
    DB_HOST=localhost \
    DB_PORT=3306 \
    DJANGO_SETTINGS_MODULE=config.settings

RUN python manage.py tailwind install && \
    python manage.py tailwind build

# Stage 3: Final production image
FROM python:3.14-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 django && \
    mkdir -p /app/staticfiles /app/media && \
    chown -R django:django /app

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=python-builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=django:django . .

# Copy built Tailwind CSS from tailwind-builder
COPY --from=tailwind-builder --chown=django:django /app/theme/static/css/dist /app/theme/static/css/dist

# Collect static files (must be done as root before switching user)
RUN python manage.py collectstatic --noinput --clear || true

# Fix permissions after collectstatic
RUN chown -R django:django /app/staticfiles /app/media

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health/ || exit 1

# Run gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
