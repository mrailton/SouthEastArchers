# Coolify Quick Deploy - Cheat Sheet

## 🚀 One-Click Deploy

### Step 1: Create Project
```
Coolify Dashboard → New Resource → Docker Compose
→ Connect GitHub: mrailton/SouthEastArchers
→ Branch: architecture (or main)
```

### Step 2: Add Environment Variables
```bash
# Required
SECRET_KEY=<generate-random-32-char-string>
DATABASE_URL=mysql+pymysql://user:password@mysql-host:3306/dbname

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=<your-app-password>
MAIL_DEFAULT_SENDER=noreply@southeastarchers.ie

# Payment
SUMUP_API_KEY=<your-key>
SUMUP_MERCHANT_CODE=<your-code>

# Optional (auto-configured)
REDIS_URL=redis://redis:6379/0
FLASK_ENV=production
```

### Step 3: Deploy
```
Click "Deploy" → Wait for build → Done! ✅
```

## 📊 What Gets Deployed

```
┌─────────────────────────────────────────────┐
│              Coolify Server                 │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   Web    │  │  Worker  │  │  Worker  │ │
│  │  :5000   │  │  (RQ)    │  │  (RQ)    │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │             │               │       │
│       └─────────────┴───────────────┘       │
│                     │                       │
│            ┌────────┴────────┐              │
│            │                 │              │
│       ┌────▼─────┐    ┌─────▼────┐         │
│       │  Redis   │    │  MySQL   │         │
│       │  :6379   │    │  :3306   │         │
│       └──────────┘    └──────────┘         │
│                                             │
└─────────────────────────────────────────────┘
```

## 🔧 Service Configuration

### Web Service
- **Port**: 5000 (auto-mapped by Coolify)
- **Replicas**: 1
- **Command**: `gunicorn --bind 0.0.0.0:5000 wsgi:app`
- **Health Check**: HTTP GET /

### Worker Service
- **Replicas**: 2 (adjustable)
- **Command**: `uv run python worker.py`
- **No exposed port**
- **Scales independently**

### Redis Service
- **Image**: redis:7-alpine
- **Port**: 6379 (internal only)
- **Persistent**: Yes (volume: redis_data)

### MySQL Database
- **Add as separate service** in Coolify
- **Version**: 8.4
- **Persistent**: Yes (managed by Coolify)

## 📝 Post-Deployment

### 1. Run Database Migrations
```bash
# In Coolify terminal for 'web' service
uv run flask db upgrade
```

### 2. Create Admin User
```bash
# In Coolify terminal for 'web' service
uv run python manage.py create-admin
```

### 3. Verify Services
```bash
# Check all containers running
docker ps

# Check worker logs
docker logs <project>-worker-1 -f

# Test Redis
docker exec <project>-redis-1 redis-cli ping
```

## 🎯 Common Tasks

### Scale Workers
```
Coolify Dashboard → worker service → Scale → Set replicas to 3
```

### View Logs
```
Coolify Dashboard → Service → Logs tab
Or: docker logs <container-name> -f
```

### Restart Service
```
Coolify Dashboard → Service → Restart button
Or: docker restart <container-name>
```

### Update Environment Variable
```
Coolify Dashboard → Environment → Edit → Redeploy
```

### Manual Deploy
```
Coolify Dashboard → Deploy button
Or: git push (if webhook enabled)
```

## 🔍 Health Checks

### Web Service
```bash
curl https://your-domain.com/
# Should return 200 OK
```

### Worker Service
```bash
docker logs <project>-worker-1 --tail 50
# Should show: "Starting RQ worker on queue: default"
```

### Redis Service
```bash
docker exec <project>-redis-1 redis-cli ping
# Should return: PONG
```

### Queue Status
```bash
docker exec <project>-redis-1 redis-cli LLEN rq:queue:default
# Shows number of pending jobs
```

## 🐛 Troubleshooting

### Workers Not Processing Jobs
```bash
# 1. Check worker logs
docker logs <project>-worker-1

# 2. Restart worker
docker restart <project>-worker-1

# 3. Check Redis connection
docker exec <project>-worker-1 env | grep REDIS
```

### Database Connection Issues
```bash
# Check DATABASE_URL is set correctly
docker exec <project>-web-1 env | grep DATABASE_URL

# Test connection
docker exec <project>-web-1 uv run python -c "from app import db; print(db.engine)"
```

### Redis Connection Refused
```bash
# Check Redis is running
docker ps | grep redis

# Check REDIS_URL
docker exec <project>-web-1 env | grep REDIS_URL

# Should be: redis://redis:6379/0
```

## 📈 Monitoring

### View Active Workers
```bash
docker exec <project>-redis-1 redis-cli SMEMBERS rq:workers
```

### View Failed Jobs
```bash
docker exec <project>-redis-1 redis-cli LRANGE rq:queue:failed 0 -1
```

### Check Job Processing Rate
```bash
# Run this a few times with 10 second intervals
docker exec <project>-redis-1 redis-cli LLEN rq:queue:default
```

## 🔐 Security Checklist

- [x] SECRET_KEY is random and unique
- [x] DATABASE_URL password is strong
- [x] Email credentials stored as secrets
- [x] SumUp API key stored as secret
- [x] Redis not exposed to internet
- [x] MySQL not exposed to internet
- [x] HTTPS enabled (via Coolify)
- [x] CSRF protection enabled (Flask-WTF)

## 🚨 Emergency Commands

### Stop Everything
```bash
docker-compose down
```

### Restart Everything
```bash
docker-compose restart
```

### Clear Redis Queue (CAUTION!)
```bash
docker exec <project>-redis-1 redis-cli FLUSHDB
```

### Backup Database
```bash
# Coolify handles this automatically
# Or manually:
docker exec <project>-db-1 mysqldump -u user -p dbname > backup.sql
```

## 📚 Resources

- Full Guide: `docs/COOLIFY_DEPLOYMENT.md`
- Background Jobs: `docs/BACKGROUND_JOBS.md`
- Coolify Docs: https://coolify.io/docs
- RQ Docs: https://python-rq.org/

## 💡 Tips

1. **Start with 1 worker**, scale up based on load
2. **Enable Coolify webhooks** for auto-deploy on git push
3. **Set up health check notifications** in Coolify
4. **Monitor logs regularly** during first week
5. **Test background jobs** by signing up a test member
6. **Use Coolify's built-in monitoring** for resource usage
7. **Schedule daily membership expiry check** via Coolify cron

---

**Need Help?**
- Check logs first: `docker logs <service> -f`
- Review environment variables
- Verify all services are running: `docker ps`
- Check Coolify documentation
