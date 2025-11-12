# Deployment Guide - Coolify

## Quick Start

1. **Push to GitHub** (triggers CI/CD automatically)
2. **Wait for build** (check Actions tab)
3. **Deploy in Coolify**

## Coolify Configuration

### Docker Image Settings

```
Registry: ghcr.io
Image: ghcr.io/<your-github-username>/southeast:latest
```

### Required Environment Variables

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-production-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration
DB_NAME=southeast_archers
DB_USER=your_db_user
DB_PASSWORD=your_secure_db_password
DB_HOST=your_db_host
DB_PORT=3306

# MySQL Root Password (for database container if using)
MYSQL_ROOT_PASSWORD=your_mysql_root_password
```

### Health Check

```
Path: /health/
Port: 8000
Interval: 30s
Timeout: 10s
```

### Port Configuration

```
Container Port: 8000
Public Port: 80 (or 443 with SSL)
```

## Using GitHub Container Registry

### Option 1: Public Package (Recommended)

1. Go to GitHub → Packages → southeast
2. Package settings → Change visibility → Public
3. Coolify can pull without authentication

### Option 2: Private Package

1. Create GitHub Personal Access Token:
   - Settings → Developer settings → Personal access tokens
   - Generate new token (classic)
   - Scopes: `read:packages`
   - Copy token

2. Add to Coolify:
   - Registry: ghcr.io
   - Username: your-github-username
   - Password: paste-token-here

## Database Setup

### Using Coolify's Database

1. Create MySQL 8.0 database in Coolify
2. Note the connection details
3. Add to environment variables

### Using External Database

1. Set up MySQL 8.0+ server
2. Create database: `southeast_archers`
3. Configure SSL if required (recommended)
4. Add connection details to env vars

## Initial Deployment Steps

1. **Deploy the container**
   ```
   Image: ghcr.io/<username>/southeast:latest
   ```

2. **Run migrations** (one-time)
   ```bash
   docker exec <container-name> python manage.py migrate
   ```

3. **Create superuser** (one-time)
   ```bash
   docker exec -it <container-name> python manage.py createsuperuser
   ```

4. **Collect static files** (if needed)
   ```bash
   docker exec <container-name> python manage.py collectstatic --noinput
   ```

## Updating the Application

1. **Push changes to GitHub**
2. **Wait for Actions to complete**
3. **Redeploy in Coolify**
   - Click "Redeploy" or "Restart"
   - Coolify pulls latest image automatically

## Domain Configuration

1. **Add domain in Coolify**
   - Settings → Domains
   - Add your domain

2. **Enable HTTPS**
   - Coolify automatically provisions Let's Encrypt SSL

3. **Update ALLOWED_HOSTS**
   ```bash
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

## Monitoring

### Check Application Logs

In Coolify:
- Click on your application
- Go to "Logs" tab

### Health Check

```bash
curl https://yourdomain.com/health/
# Should return: {"status": "healthy"}
```

### Database Connection

```bash
# Test database connectivity
docker exec <container> python manage.py dbshell
```

## Rollback

If something goes wrong:

1. **Tag-based rollback:**
   ```
   Change image to: ghcr.io/<username>/southeast:main-<previous-sha>
   ```

2. **Version rollback:**
   ```
   Use a specific version tag: ghcr.io/<username>/southeast:v1.0.0
   ```

## Troubleshooting

### Container won't start

1. Check logs in Coolify
2. Verify all environment variables are set
3. Check database connectivity

### Database connection fails

1. Verify `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`
2. Check network connectivity
3. Ensure database exists

### Static files not loading

1. Ensure STATIC_URL is accessible
2. Check WhiteNoise configuration
3. Verify collectstatic ran successfully

### 500 errors

1. Set `DEBUG=True` temporarily to see errors
2. Check application logs
3. Verify SECRET_KEY is set
4. Check ALLOWED_HOSTS includes your domain

## Best Practices

✅ Use environment variables for secrets
✅ Enable HTTPS (automatic with Coolify)
✅ Set up database backups
✅ Monitor application logs
✅ Use version tags for production
✅ Test in staging before production
✅ Keep dependencies updated

## Support

- GitHub Issues: Report bugs and request features
- Documentation: Check README.md and other docs
- Logs: Always check application and database logs first
