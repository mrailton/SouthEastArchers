FROM python:3.14-slim as builder

WORKDIR /app

# Install Node.js for building assets
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy build configuration files
COPY package*.json ./

# Install Node dependencies
RUN npm ci

# Copy source files needed for build
COPY vite.config.js ./
COPY app/resources/static/css ./app/resources/static/css
COPY app/resources/static/js ./app/resources/static/js
COPY app/resources/templates ./app/resources/templates

# Build assets
RUN npm run build

# Final stage
FROM python:3.14-slim

WORKDIR /app

# Install system dependencies and UV
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copy dependency files and install Python dependencies (production only)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY . .
RUN uv sync --frozen --no-dev

# Copy built assets from builder stage
COPY --from=builder /app/app/resources/static/dist ./app/resources/static/dist

# Copy and set entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget -qO- http://127.0.0.1:5000/health || exit 1

# Set entrypoint to run migrations
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Run FastAPI app (app.cli used for migrations/RBAC seed in entrypoint)
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120"]
