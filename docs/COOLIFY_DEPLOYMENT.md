# Coolify Deployment Guide for South East Archers
## Deploying with GitHub Actions + GHCR

This guide explains how to deploy the application to Coolify using pre-built Docker images from GitHub Container Registry (GHCR).

## Architecture Overview

The application consists of 4 main services:
1. **web** - Flask application (handles HTTP requests)
2. **worker** - RQ worker processes (handles background jobs)
3. **redis** - Redis server (job queue storage)
4. **mysql** - MySQL database (persistent storage)

```
┌───────────────────────────────────────────────────────────┐
│                    Coolify Server                         │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────┐         ┌──────────────────────┐   │
│  │ GitHub Actions  │         │  GHCR Registry       │   │
│  │ - Build images  │────────▶│  - Web image         │   │
│  │ - Run tests     │         │  - Worker image      │   │
│  │ - Push to GHCR  │         └──────┬───────────────┘   │
│  └─────────────────┘                │                    │
│                                     │ pull              │
│                                     ▼                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │   Web    │  │  Worker  │  │  Worker  │             │
│  │  :5000   │  │  (RQ)    │  │  (RQ)    │             │
│  │ (GHCR)   │  │ (GHCR)   │  │ (GHCR)   │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │             │               │                    │
│       └─────────────┴───────────────┘                    │
│                     │                                    │
│            ┌────────┴────────┐                           │
│            │                 │                           │
│       ┌────▼─────┐    ┌─────▼────┐                     │
│       │  Redis   │    │  MySQL   │                     │
│       │  :6379   │    │  :3306   │                     │
│       │(Coolify) │    │(Coolify) │                     │
│       └──────────┘    └──────────┘                     │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Coolify Instance**: Running and accessible
2. **GitHub Repository**: Connected to Coolify
3. **GitHub Actions**: Configured (already done in `.github/workflows/ci.yml`)
4. **GHCR Access**: Repository packages are public or Coolify has access

## Deployment Steps

### Step 1: Set Up GitHub Secrets

Configure these secrets in your GitHub repository:

```
Settings → Secrets and Variables → Actions → New repository secret
```

Add:
- `COOLIFY_WEBHOOK_URL`: Webhook URL from Coolify (see Step 5)
- `COOLIFY_TOKEN`: Your Coolify API token (optional, for advanced webhooks)

### Step 2: Create MySQL Database

1. In Coolify Dashboard:
   ```
   New Resource → Database → MySQL
   ```

2. Configure:
   - **Name**: `southeastarchers-db`
   - **Version**: 8.4
   - **Database**: `southeastarchers`
   - **Username**: Your choice
   - **Password**: Generate strong password

3. Note the internal connection URL:
   ```
   mysql+pymysql://username:password@<internal-host>:3306/southeastarchers
   ```

### Step 3: Create Redis Service

1. In Coolify Dashboard:
   ```
   New Resource → Database → Redis
   ```

2. Configure:
   - **Name**: `southeastarchers-redis`
   - **Version**: 7-alpine

3. Note the internal connection URL:
   ```
   redis://<internal-host>:6379/0
   ```

### Step 4: Create Web Application Service

1. In Coolify Dashboard:
   ```
   New Resource → Application → Docker Image
   ```

2. Configure:
   - **Name**: `southeastarchers-web`
   - **Image**: `ghcr.io/mrailton/southeastarchers:latest`
   - **Port**: `5000`
   - **Exposed Port**: Map to your domain

3. Add Environment Variables:
   ```bash
   FLASK_ENV=production
   SECRET_KEY=<generate-random-32-char-string>
   DATABASE_URL=mysql+pymysql://user:pass@<mysql-internal-host>:3306/southeastarchers
   REDIS_URL=redis://<redis-internal-host>:6379/0
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=<your-app-password>
   MAIL_DEFAULT_SENDER=noreply@southeastarchers.ie
   SUMUP_API_KEY=<your-sumup-key>
   SUMUP_MERCHANT_CODE=<your-merchant-code>
   ```

4. Configure Domain (optional):
   - Add your domain in Coolify
   - SSL will be auto-configured via Let's Encrypt

5. Deploy:
   - Click "Deploy"
   - Coolify pulls image from GHCR and starts the service

### Step 5: Create Worker Service(s)

1. In Coolify Dashboard:
   ```
   New Resource → Application → Docker Image
   ```

2. Configure:
   - **Name**: `southeastarchers-worker`
   - **Image**: `ghcr.io/mrailton/southeastarchers-worker:latest`
   - **No port mapping needed**

3. Add Environment Variables (same as web service):
   ```bash
   FLASK_ENV=production
   SECRET_KEY=<same-as-web-service>
   DATABASE_URL=<same-as-web-service>
   REDIS_URL=<same-as-web-service>
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=<same-as-web-service>
   MAIL_PASSWORD=<same-as-web-service>
   MAIL_DEFAULT_SENDER=<same-as-web-service>
   ```

4. Scale Workers (optional):
   - Default: 1 replica
   - For production: 2-3 replicas recommended
   - Settings → Replicas → Set to 2

5. Deploy:
   - Click "Deploy"
   - Coolify pulls worker image and starts processing jobs

### Step 6: Configure Auto-Deploy Webhook

1. In Coolify (for web service):
   ```
   southeastarchers-web → Webhooks → Create Webhook
   ```
   - Copy the webhook URL

2. In Coolify (for worker service):
   ```
   southeastarchers-worker → Webhooks → Create Webhook
   ```
   - Copy the webhook URL

3. In GitHub Repository:
   ```
   Settings → Secrets and Variables → Actions
   ```
   - Add `COOLIFY_WEBHOOK_URL` with the webhook URL(s)
   - Note: For multiple services, you can add separate secrets or call both webhooks

4. Webhook is already configured in `.github/workflows/ci.yml`:
   ```yaml
   - name: Deploy to Coolify
     run: |
       curl --request GET '${{ secrets.COOLIFY_WEBHOOK_URL }}'
   ```

### Step 7: Initial Database Setup

1. Run migrations via Coolify terminal (web service):
   ```bash
   flask db upgrade
   ```

2. Create admin user:
   ```bash
   python manage.py create-admin
   ```

3. Verify database connection:
   ```bash
   python -c "from app import db; print(db.engine)"
   ```

## Post-Deployment

### Verify Services

**Check Web Service:**
```bash
curl https://your-domain.com/
# Should return 200 OK
```

**Check Worker Logs:**
```
Coolify → southeastarchers-worker → Logs
# Should show: "Starting RQ worker on queue: default"
```

**Check Redis:**
```
Coolify → southeastarchers-redis → Terminal
redis-cli ping
# Should return: PONG
```

**Check Job Queue:**
```
Coolify → southeastarchers-redis → Terminal
redis-cli LLEN rq:queue:default
# Shows number of pending jobs
```

### Test Background Jobs

1. Sign up a new test member on your site
2. Check worker logs for email job processing
3. Verify email was sent (check logs or inbox)

## Scaling

### Scale Workers

```
Coolify → southeastarchers-worker → Settings → Replicas
Set to 3 for higher traffic
```

Recommended scaling based on traffic:
- **Low traffic** (< 100 users/day): 1 worker
- **Medium traffic** (100-1000 users/day): 2 workers
- **High traffic** (> 1000 users/day): 3+ workers

### Monitor Queue Length

```bash
# In Redis terminal
redis-cli LLEN rq:queue:default
```

If queue consistently > 10, add more workers.

## Continuous Deployment Workflow

1. **Push to main branch**
   ```bash
   git push origin main
   ```

2. **GitHub Actions automatically**:
   - Runs tests
   - Builds Docker images (web and worker)
   - Pushes images to GHCR
   - Triggers Coolify webhook

3. **Coolify automatically**:
   - Pulls latest images
   - Restarts services with zero downtime
   - Health checks ensure smooth rollout

## Environment Variables Reference

### Required for All Services

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `SECRET_KEY` | Flask secret key (32+ chars) | Generate with `python -c 'import secrets; print(secrets.token_hex(32))'` |
| `DATABASE_URL` | MySQL connection string | `mysql+pymysql://user:pass@host:3306/db` |
| `REDIS_URL` | Redis connection string | `redis://host:6379/0` |

### Email Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USE_TLS` | Use TLS | `True` |
| `MAIL_USERNAME` | Email username | `your-email@gmail.com` |
| `MAIL_PASSWORD` | Email password or app password | Your app password |
| `MAIL_DEFAULT_SENDER` | Default from address | `noreply@southeastarchers.ie` |

### Payment Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `SUMUP_API_KEY` | SumUp API key | Your API key |
| `SUMUP_MERCHANT_CODE` | SumUp merchant code | Your merchant code |

## Monitoring

### View Service Logs

```
Coolify → Service → Logs
```

### Check Active Workers

```bash
# In Redis terminal
redis-cli SMEMBERS rq:workers
```

### View Failed Jobs

```bash
# In Redis terminal
redis-cli LRANGE rq:queue:failed 0 -1
```

### Monitor Resource Usage

```
Coolify → Service → Metrics
View CPU, memory, and network usage
```

## Troubleshooting

### Service Won't Start

**Check logs:**
```
Coolify → Service → Logs
```

**Common issues:**
- Missing environment variables
- Invalid DATABASE_URL or REDIS_URL
- Image pull failed (check GHCR access)

**Solution:**
```
1. Verify all environment variables are set
2. Check internal hostnames for MySQL and Redis
3. Ensure GHCR images are public or Coolify has access
```

### Workers Not Processing Jobs

**Check worker status:**
```
Coolify → southeastarchers-worker → Status
Should show "Running"
```

**Check worker logs:**
```
Coolify → southeastarchers-worker → Logs
Should show "Starting RQ worker..."
```

**Check Redis connection:**
```bash
# In worker terminal
env | grep REDIS_URL
```

**Solution:**
- Restart worker service
- Verify REDIS_URL matches Redis internal hostname
- Check Redis service is running

### Database Connection Errors

**Check DATABASE_URL:**
```bash
# In web or worker terminal
env | grep DATABASE_URL
```

**Verify format:**
```
mysql+pymysql://username:password@internal-host:3306/database
```

**Solution:**
- Use Coolify's internal hostname for MySQL
- Verify credentials
- Check MySQL service is running

### Jobs Failing

**View failed jobs:**
```bash
# In Redis terminal
redis-cli LRANGE rq:queue:failed 0 -1
```

**Check job errors:**
```
Coolify → southeastarchers-worker → Logs
Look for stack traces
```

**Common causes:**
- Missing email configuration
- Template not found
- Database connection timeout

### Images Not Updating

**Check GitHub Actions:**
```
GitHub → Actions → Latest workflow
Verify build completed successfully
```

**Check GHCR:**
```
GitHub → Packages → southeastarchers
Verify latest tag timestamp
```

**Force update in Coolify:**
```
Service → Force Redeploy
```

**Solution:**
1. Verify GitHub Actions completed
2. Check images pushed to GHCR
3. Manually trigger webhook or redeploy
4. Check webhook URL in GitHub secrets

## Performance Tuning

### Web Service

**Adjust Gunicorn workers:**
Edit Dockerfile.web:
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "8", "--timeout", "120", "wsgi:app"]
```

**Formula:** `workers = (2 × CPU cores) + 1`

### Worker Service

**Adjust number of replicas:**
```
Coolify → southeastarchers-worker → Settings → Replicas
```

**Monitor queue length to determine if more workers needed.**

### Redis Memory

**Check memory usage:**
```bash
redis-cli INFO memory
```

**Increase if needed:**
```
Coolify → southeastarchers-redis → Settings
Adjust memory limit
```

## Security Best Practices

- ✅ Use strong SECRET_KEY (32+ characters, random)
- ✅ Store secrets in Coolify environment variables (not in code)
- ✅ Use app passwords for email (not main account password)
- ✅ Restrict database access to internal network only
- ✅ Enable HTTPS via Coolify (automatic with Let's Encrypt)
- ✅ Regularly update Docker images (automatic via GitHub Actions)
- ✅ Keep dependencies up to date (`make upgrade-deps`)
- ✅ Monitor logs for suspicious activity
- ✅ Use different SECRET_KEY for each environment

## Backup and Recovery

### Database Backups

Coolify automatically backs up managed databases.

**Manual backup:**
```bash
# In MySQL service terminal
mysqldump -u username -p database > backup.sql
```

### Restore from Backup

```bash
# In MySQL service terminal
mysql -u username -p database < backup.sql
```

### Redis Backups

Redis uses RDB persistence (automatic).

**Manual save:**
```bash
redis-cli SAVE
```

## Cost Optimization

1. **Right-size services**: Start with 1 web, 2 workers, scale as needed
2. **Monitor resources**: Use Coolify metrics to identify underutilized services
3. **Image cleanup**: Regularly prune old GHCR images (GitHub retention policies)
4. **Database optimization**: Index frequently queried columns
5. **Redis memory**: Monitor and adjust based on queue size

## Additional Resources

- [Coolify Documentation](https://coolify.io/docs)
- [RQ Documentation](https://python-rq.org/)
- [GHCR Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/stable/deploying/)

## Support

For issues specific to this deployment setup:
1. Check Coolify service logs
2. Review GitHub Actions workflow logs
3. Verify environment variables
4. Check GHCR image availability
5. Test connectivity between services

For application issues:
- Review application logs in Coolify
- Check test coverage: `make test`
- Run locally: `make dev`
