# Coolify Deployment Guide for South East Archers

This guide explains how to deploy the application to Coolify with RQ background workers.

## Architecture Overview

The application consists of 3 main services:
1. **web** - Flask application (handles HTTP requests)
2. **worker** - RQ worker processes (handles background jobs)
3. **redis** - Redis server (job queue storage)

Plus an external MySQL database (managed by Coolify).

## Deployment Options

### Option 1: Using Docker Compose (Recommended for Coolify)

Coolify has excellent docker-compose support. This is the simplest approach.

#### Steps:

1. **Create a new project in Coolify**
   - Go to your Coolify dashboard
   - Click "New Resource" → "Docker Compose"
   - Connect your GitHub repository

2. **Configure Environment Variables**
   
   In Coolify, add these environment variables:
   
   ```bash
   # Flask
   SECRET_KEY=your-random-secret-key-here
   FLASK_ENV=production
   
   # Database (Coolify MySQL)
   DATABASE_URL=mysql+pymysql://user:password@mysql-host:3306/database
   
   # Redis (internal service)
   REDIS_URL=redis://redis:6379/0
   
   # Email
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=noreply@southeastarchers.ie
   
   # SumUp Payment
   SUMUP_API_KEY=your-sumup-api-key
   SUMUP_MERCHANT_CODE=your-merchant-code
   
   # Optional
   PORT=5000
   ```

3. **Deploy**
   - Coolify will automatically detect `docker-compose.yml`
   - Click "Deploy"
   - Coolify will build and start all services:
     - MySQL database (if added as separate service)
     - Redis (from docker-compose)
     - Web application (from docker-compose)
     - Worker process (from docker-compose)

4. **Verify Deployment**
   ```bash
   # Check services are running
   docker ps
   
   # Check worker logs
   docker logs <worker-container-name>
   
   # Check Redis connection
   docker exec <redis-container> redis-cli ping
   ```

### Option 2: Separate Services (More Control)

If you want more granular control, deploy each service separately in Coolify:

#### 2.1 Deploy MySQL Database
1. Add new service → Database → MySQL 8.4
2. Note the connection details

#### 2.2 Deploy Redis
1. Add new service → Database → Redis 7
2. No special configuration needed

#### 2.3 Deploy Web Application
1. Add new service → Application → Dockerfile
2. Set Dockerfile path: `Dockerfile`
3. Set port: `5000`
4. Add environment variables (see above)
5. Set command: `gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app`

#### 2.4 Deploy Worker(s)
1. Add new service → Application → Dockerfile
2. Set Dockerfile path: `Dockerfile`
3. Add environment variables (same as web)
4. Set command: `uv run python worker.py`
5. **Important**: No port mapping needed (workers don't serve HTTP)
6. Scale to 2-3 instances for production

## Scaling Workers

### In docker-compose:
```bash
# Scale to 3 worker instances
docker-compose up -d --scale worker=3
```

### In Coolify Dashboard:
1. Go to worker service
2. Click "Scale"
3. Set replicas to desired number (2-3 recommended)

## Monitoring

### Worker Health Check
```bash
# SSH into your server
ssh user@your-server

# Check worker logs
docker logs coolify-worker-<id> -f

# Check Redis queue status
docker exec coolify-redis-<id> redis-cli LLEN rq:queue:default
```

### Application Logs
```bash
# Web application logs
docker logs coolify-web-<id> -f

# All services
docker-compose logs -f
```

### Redis Queue Inspection
```bash
# Connect to Redis
docker exec -it coolify-redis-<id> redis-cli

# Check queue length
LLEN rq:queue:default

# Check failed jobs
LRANGE rq:queue:failed 0 -1

# Check workers
SMEMBERS rq:workers
```

## Coolify-Specific Tips

### 1. Database Connection
Coolify provides a MySQL service. Use the internal hostname:
```
DATABASE_URL=mysql+pymysql://user:pass@mysql-service:3306/dbname
```

### 2. Redis Connection
If using docker-compose, Redis is accessible at:
```
REDIS_URL=redis://redis:6379/0
```

If using separate Redis service:
```
REDIS_URL=redis://coolify-redis-<service-name>:6379/0
```

### 3. Persistent Storage
Coolify handles volumes automatically. Your Redis data will persist across deployments.

### 4. Zero-Downtime Deployments
- Web service: Coolify handles rolling updates
- Workers: Will restart automatically
- Redis: Persists data in volumes

### 5. Health Checks
The `docker-compose.yml` includes health checks for:
- Redis: `redis-cli ping`
- MySQL: `mysqladmin ping`
- Web: Coolify can check HTTP endpoint

## Environment-Specific Configuration

### Development
```bash
FLASK_ENV=development
REDIS_URL=redis://localhost:6379/0
```

### Staging
```bash
FLASK_ENV=production
REDIS_URL=redis://redis:6379/0
```

### Production
```bash
FLASK_ENV=production
REDIS_URL=redis://redis:6379/0
# Add monitoring, backup configs
```

## Troubleshooting

### Workers not processing jobs
1. Check worker is running: `docker ps | grep worker`
2. Check Redis connection: `docker exec worker-container redis-cli -h redis ping`
3. Check worker logs: `docker logs worker-container`
4. Verify environment variables match web service

### Redis connection refused
1. Ensure Redis service is running
2. Check REDIS_URL environment variable
3. Verify network connectivity between services
4. Check Redis logs: `docker logs redis-container`

### Jobs stuck in queue
1. Check worker logs for errors
2. Restart worker: `docker restart worker-container`
3. Inspect queue: `redis-cli LLEN rq:queue:default`
4. Check failed jobs: `redis-cli LRANGE rq:queue:failed 0 -1`

### Database migrations
```bash
# SSH into web container
docker exec -it web-container bash

# Run migrations
uv run flask db upgrade
```

## Performance Tuning

### Worker Count
- **Low traffic**: 1 worker
- **Medium traffic**: 2-3 workers
- **High traffic**: 5+ workers

### Redis Memory
Default Redis config is fine for most use cases. For high volume:
```yaml
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### Gunicorn Workers (Web)
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "wsgi:app"]
```

- **workers**: Number of processes (2-4 × CPU cores)
- **timeout**: Request timeout in seconds

## Scheduled Jobs

For daily membership expiry checks, add a cron job in Coolify:

1. Go to web service → Scheduled Tasks
2. Add cron job:
   ```bash
   0 9 * * * cd /app && uv run python -c "from app.services.background_jobs import check_expiring_memberships_job; check_expiring_memberships_job()"
   ```

Or use external cron service (like cron-job.org) to hit an endpoint.

## Backup Strategy

### Database
Coolify automatically backs up MySQL databases.

### Redis (Queue Data)
Redis data is ephemeral (jobs in queue). No backup needed.
If Redis crashes, queued jobs are lost but can be retried.

### Application Files
Your code is in Git. No need to backup application files.

## Cost Optimization

### Single Worker
For low-traffic sites, 1 worker is sufficient:
```yaml
deploy:
  replicas:
    worker: 1
```

### Shared Redis
Use the same Redis instance for sessions + job queue (already configured).

## Security Checklist

- ✅ SECRET_KEY set to random value
- ✅ DATABASE_URL uses strong password
- ✅ MAIL_PASSWORD stored as Coolify secret
- ✅ SUMUP_API_KEY stored as Coolify secret
- ✅ Redis not exposed to public internet
- ✅ MySQL not exposed to public internet

## Next Steps

1. Deploy to Coolify using docker-compose.yml
2. Verify all services are healthy
3. Test background job: Sign up a new member (triggers email)
4. Monitor worker logs to see job processing
5. Scale workers based on load
6. Set up monitoring alerts

## Support

For issues:
- Check Coolify logs
- Review worker logs
- Inspect Redis queue
- Check application logs

Common log locations in Coolify:
- Web: `/var/log/coolify/web/`
- Worker: `/var/log/coolify/worker/`
- Redis: `/var/log/coolify/redis/`
