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
COPY resources ./resources
COPY vite.config.js ./
COPY app/templates ./app/templates

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

# Copy dependency files
COPY pyproject.toml .

# Install Python dependencies (production only)
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code
COPY . .

# Copy built assets from builder stage (overwrites empty static folder)
COPY --from=builder /app/resources/static ./resources/static

# Copy and set entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Set entrypoint to run migrations
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Run Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "web:app"]
