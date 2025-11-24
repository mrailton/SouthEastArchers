# Background Jobs with Redis & RQ

This application uses **Redis** and **RQ (Redis Queue)** for asynchronous background job processing.

## Overview

Background jobs handle time-consuming tasks without blocking HTTP requests:
- Sending emails (payment receipts, password resets, membership reminders)
- Processing payment webhooks
- Scheduled tasks (membership expiry checks)

## Architecture

```
┌─────────────┐      ┌─────────┐      ┌──────────┐
│   Flask     │─────▶│  Redis  │◀─────│ RQ Worker│
│   App       │ Queue │  Queue  │ Pop  │ Process  │
└─────────────┘      └─────────┘      └──────────┘
```

## Setup

### 1. Install Dependencies
```bash
make install-py
```

### 2. Start Redis
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or using docker-compose
docker-compose up redis -d

# Or install locally (macOS)
brew install redis
brew services start redis
```

### 3. Start RQ Worker
```bash
# Production
make worker

# Development (with auto-reload)
make worker-dev
```

### 4. Run Application
```bash
make run
```

## Available Jobs

### Email Jobs

#### `send_payment_receipt_job(user_id, payment_id)`
Sends payment receipt email to user after successful payment.

#### `send_password_reset_job(user_id, token)`
Sends password reset link via email.

#### `send_membership_expiry_reminder_job(user_id)`
Sends reminder email when membership is expiring soon.

### Scheduled Jobs

#### `check_expiring_memberships_job()`
Checks for memberships expiring in 7 days and sends reminders.
**Should be run daily via cron:**

```bash
# Add to crontab
0 9 * * * cd /path/to/app && uv run python -c "from app.services.background_jobs import check_expiring_memberships_job; check_expiring_memberships_job()"
```

## Usage in Code

### Queueing a Job
```python
from app import task_queue
from app.services.background_jobs import send_payment_receipt_job

# Queue job for background execution
if task_queue:
    task_queue.enqueue(send_payment_receipt_job, user_id, payment_id)
```

### Fallback Behavior
If Redis is unavailable, the application automatically falls back to synchronous execution:
```python
from app.services.payment_service import PaymentProcessingService

# Automatically uses background queue if available, otherwise runs synchronously
PaymentProcessingService.queue_payment_receipt(user_id, payment_id)
```

## Docker Deployment

The `docker-compose.yml` includes three services:

1. **redis** - Job queue storage
2. **web** - Flask application (queues jobs)
3. **worker** - RQ worker process (executes jobs)

```bash
# Start all services
docker-compose up -d

# View worker logs
docker-compose logs -f worker

# Scale workers
docker-compose up -d --scale worker=3
```

## Environment Variables

```bash
# .env file
REDIS_URL=redis://localhost:6379/0
```

## Monitoring

### Check Queue Status
```python
from redis import Redis
from rq import Queue

redis_conn = Redis.from_url('redis://localhost:6379/0')
queue = Queue(connection=redis_conn)

print(f"Jobs in queue: {len(queue)}")
print(f"Failed jobs: {len(queue.failed_job_registry)}")
```

### RQ Dashboard (Optional)
```bash
pip install rq-dashboard
rq-dashboard --redis-url redis://localhost:6379/0
```
Access at: http://localhost:9181

## Testing

Tests include both job execution and queueing:

```bash
# Run all tests
make test

# Run background job tests only
uv run pytest tests/services/test_background_jobs.py -v
```

## Troubleshooting

### Redis Connection Failed
- Check Redis is running: `redis-cli ping` (should return `PONG`)
- Verify REDIS_URL in `.env`
- Check firewall/network settings

### Jobs Not Processing
- Verify worker is running: `ps aux | grep worker.py`
- Check worker logs for errors
- Restart worker: `make worker`

### Jobs Timing Out
- Increase timeout in worker: `Queue(connection=redis_conn, default_timeout=600)`
- Check email server connectivity

## Production Considerations

1. **Multiple Workers**: Scale horizontally for high load
   ```bash
   docker-compose up -d --scale worker=5
   ```

2. **Job Monitoring**: Use RQ Dashboard or Sentry
3. **Job Retry**: Configure retry policies for failed jobs
4. **Job Prioritization**: Use multiple queues (high, default, low)
5. **Dead Letter Queue**: Monitor failed jobs and handle appropriately

## Further Reading

- [RQ Documentation](https://python-rq.org/)
- [Redis Documentation](https://redis.io/docs/)
- [Flask Background Jobs](https://flask.palletsprojects.com/en/latest/patterns/celery/)
