# ---- Stage 1: frontend asset build ----
FROM node:22-slim AS frontend-builder
WORKDIR /app

COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

COPY vite.config.js ./
COPY app/resources/static/css ./app/resources/static/css
COPY app/resources/static/js ./app/resources/static/js
COPY app/resources/templates ./app/resources/templates
RUN npm run build

# ---- Stage 2: python dependency build (compiled deps live here, not in final image) ----
FROM python:3.14-slim AS python-builder
WORKDIR /app

# Build-time only: headers/toolchain needed to compile mysqlclient etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Bring in built frontend assets so they're part of the synced project dir
COPY --from=frontend-builder /app/app/resources/static/dist ./app/resources/static/dist

# ---- Stage 3: final runtime image ----
FROM python:3.14-slim
WORKDIR /app

# Runtime-only shared lib for mysqlclient (no headers/toolchain needed here)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

# Create user before copying anything, so ownership is set in one layer via --chown
RUN useradd -m -u 1000 appuser

COPY --from=python-builder --chown=appuser:appuser /app /app
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER appuser
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health').status == 200" || exit 1

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "4"]
