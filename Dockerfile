FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

RUN useradd -m appuser && chown -R appuser:appuser /app && \
    chmod +x /app/entrypoint.sh \

USER appuser

ENV PORT=5000

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]