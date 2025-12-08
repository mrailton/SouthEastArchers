# Dokploy Deployment Quick Start

This guide shows you how to deploy South East Archers to Dokploy using Docker Compose.

## Prerequisites

- Dokploy instance running
- Git repository with this code
- Domain name (optional, but recommended)

## Step-by-Step Deployment

### 1. Create Compose Application in Dokploy

1. Log into your Dokploy dashboard
2. Click **"Create Application"**
3. Select **"Compose"** as the application type
4. Enter application name: `southeastarchers`

### 2. Connect Git Repository

1. Choose your Git provider (GitHub, GitLab, etc.)
2. Select or enter your repository URL
3. Select branch: `main` (or your default branch)
4. **Set compose file path**: `docker/docker-compose.yml`

### 3. Configure Environment Variables

In the Dokploy environment variables section, add:

```bash
# Database Configuration
MYSQL_ROOT_PASSWORD=<generate-secure-password>
MYSQL_DATABASE=southeastarchers
MYSQL_USER=appuser
MYSQL_PASSWORD=<generate-secure-password>

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<generate-secure-32-char-key>

# Email Configuration
MAIL_SERVER=smtp.your-provider.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=noreply@southeastarchers.ie

# Payment Configuration
SUMUP_API_KEY=your-sumup-api-key
SUMUP_MERCHANT_CODE=your-merchant-code
```

**Generate secure keys:**
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Or use openssl
openssl rand -hex 32
```

### 4. Domain Configuration (Optional)

1. In Dokploy, go to the **Domains** section
2. Add your domain name
3. Enable SSL/TLS (Let's Encrypt)
4. Dokploy will automatically configure HTTPS

### 5. Deploy!

1. Click **"Deploy"** button
2. Dokploy will:
   - Clone your repository
   - Pull pre-built images from GHCR (no build step needed!)
   - Start all services (db, redis, web, worker)
   - Run database migrations automatically
   - Expose your application

Watch the deployment logs in real-time.

**Note:** Images are automatically built by GitHub Actions and pushed to GHCR on every push to `main`. This means Dokploy just pulls the latest images - fast and efficient!

### 6. Verify Deployment

Once deployed, verify everything works:

1. **Visit your application URL**
   - Should see the homepage
   
2. **Check service status in Dokploy**
   - All services should be "Running"
   
3. **Test functionality**
   - Try registering/logging in
   - Check if emails are being sent
   - Test a payment flow (if applicable)

## Architecture Overview

Dokploy will deploy 4 services:

1. **db** - MySQL 8.4 database
2. **redis** - Redis for background jobs
3. **web** - Flask application (pulled from `ghcr.io/mrailton/southeastarchers-web:latest`)
4. **worker** - Background job processor (pulled from `ghcr.io/mrailton/southeastarchers-worker:latest`)

All services are networked together and can communicate using service names.

**Image Source:** Images are automatically built by GitHub Actions on every push to `main` and pushed to GitHub Container Registry (GHCR). Dokploy pulls these pre-built images, making deployments fast and consistent.

## Managing Your Deployment

### View Logs

In Dokploy:
1. Go to your application
2. Click on **Logs** tab
3. Select service: web, worker, db, or redis

### Update Application

To deploy updates:

1. **Option 1: Git Push (Automatic)**
   - Enable webhook in Dokploy
   - Push to your Git repository
   - Dokploy automatically redeploys

2. **Option 2: Manual Deploy**
   - Click **"Redeploy"** button in Dokploy
   - Select branch/commit
   - Deploy

### Database Access

To access the database:

1. **Via Dokploy Console:**
   - Go to service "db"
   - Click **"Console"**
   - Run: `mysql -u appuser -p southeastarchers`

2. **Via External Tool:**
   - Expose MySQL port in Dokploy (optional)
   - Use tool like MySQL Workbench or DBeaver
   - Connect using container's external port

### Environment Variables

To update environment variables:

1. Go to application settings
2. Update the variable
3. **Redeploy** for changes to take effect

### Scaling

To scale the worker:

1. Edit `docker/docker-compose.yml`
2. Add to worker service:
   ```yaml
   deploy:
     replicas: 3  # Run 3 worker instances
   ```
3. Commit and deploy

## Troubleshooting

### Build Failed

**Check logs in Dokploy:**
- Look for errors during image build
- Common issues:
  - Missing dependencies
  - Syntax errors in Dockerfiles
  - Build context issues

**Solution:** Fix the issue, commit, and redeploy

### Web Service Won't Start

**Check environment variables:**
- Ensure all required variables are set
- Check for typos in variable names

**Check database connection:**
- Verify db service is running
- Check DATABASE_URL format

### Database Connection Failed

**Verify service is healthy:**
- Check if db service is running
- Look at db logs for errors

**Check credentials:**
- MYSQL_USER and MYSQL_PASSWORD must match in:
  - Database service environment
  - Web/worker DATABASE_URL

### Migrations Not Running

The web service automatically runs migrations on startup via `docker-entrypoint.sh`.

**If migrations fail:**
1. Check web service logs
2. Verify database is accessible
3. May need to manually run:
   ```bash
   # In Dokploy console for web service
   flask db upgrade
   ```

### Worker Not Processing Jobs

**Check worker logs:**
- Look for connection errors to Redis
- Check if worker started successfully

**Verify Redis:**
- Ensure redis service is running
- Check REDIS_URL environment variable

### Port Conflicts

If port 5000 is already in use:

1. Add `WEB_PORT=5001` to environment variables
2. Update compose file to use `${WEB_PORT:-5000}:5000`
3. Redeploy

## Advanced Configuration

### Using External Database

To use an external MySQL database instead of the container:

1. Remove `db` service from docker-compose.yml
2. Update DATABASE_URL to point to external database
3. Ensure external database is accessible from Dokploy

### Using External Redis

Similar to database:

1. Remove `redis` service
2. Update REDIS_URL to external Redis
3. Ensure accessibility

### Custom Domain with SSL

Dokploy handles this automatically:

1. Add domain in Dokploy UI
2. Point DNS to Dokploy server
3. Enable SSL (Let's Encrypt)
4. Done!

### Backups

**Database Backups:**

1. **Via Dokploy:**
   - Use Dokploy's built-in backup features
   
2. **Manual:**
   ```bash
   # Export database
   docker exec <db-container> mysqldump -u appuser -p southeastarchers > backup.sql
   
   # Restore database
   docker exec -i <db-container> mysql -u appuser -p southeastarchers < backup.sql
   ```

3. **Automated:**
   - Set up cron job on Dokploy server
   - Use mysqldump in scheduled task
   - Store backups in S3 or similar

## Monitoring

### Built-in Dokploy Monitoring

Dokploy provides:
- Service health status
- Resource usage (CPU, Memory)
- Container logs
- Restart counts

### External Monitoring (Optional)

Consider adding:
- **Sentry** for error tracking
- **Uptime Robot** for availability monitoring
- **Google Analytics** for user analytics

## Cost Optimization

### Resource Limits

Add to docker-compose.yml:

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### Volume Management

Periodically clean up:
- Old logs
- Unused volumes
- Temporary files

## Getting Help

1. **Check logs first** - Most issues show up in logs
2. **Review this guide** - Common solutions documented
3. **Dokploy Documentation** - https://docs.dokploy.com/
4. **Main Docker README** - [docker/README.md](README.md)
5. **GitHub Issues** - Report bugs or ask questions

## Next Steps

After deployment:

- [ ] Set up automated backups
- [ ] Configure monitoring/alerts
- [ ] Set up custom domain and SSL
- [ ] Test all functionality
- [ ] Set up staging environment
- [ ] Configure webhook for auto-deploy
- [ ] Document your specific configuration

---

**Congratulations!** 🎉 Your South East Archers application is now running on Dokploy!
