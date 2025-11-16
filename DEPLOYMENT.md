# Deployment Guide - South East Archers

This guide covers deploying the South East Archers application to Coolify.

## Prerequisites

- Coolify instance running (self-hosted or cloud)
- Git repository with code
- MySQL 8.0 instance (can be managed by Coolify)
- Domain name (optional but recommended)

## Deployment Steps

### 1. Prepare Your Repository

Ensure all code is committed:

```bash
git add .
git commit -m "Initial commit: SEA application"
git push origin main
```

### 2. Create Coolify Project

1. Log into your Coolify instance
2. Go to Projects → New Project
3. Select "Git Repository"
4. Choose your Git provider (GitHub, GitLab, etc.)
5. Select the South East Archers repository

### 3. Configure Services

#### Database Service (MySQL)

1. Click "Services" in the project
2. Select "MySQL" from available services
3. Configure:
   - Database Name: `sea_db`
   - Username: `sea_user`
   - Password: (Generate secure password)
   - Port: 3306 (internal)
4. Save and start the service

#### Application Service

1. Click "Services" → New Service
2. Select "Docker" or "Docker Compose"
3. Configure:
   - **Build**: Docker
   - **Source**: Git repository
   - **Dockerfile Path**: `/Dockerfile`
   - **Port**: 5000
   - **Restart Policy**: Always

### 4. Set Environment Variables

In Coolify project settings, configure:

```env
# Flask
FLASK_ENV=production
SECRET_KEY=<generate-strong-secret-key>

# Database
DATABASE_URL=mysql+pymysql://sea_user:PASSWORD@mysql:3306/sea_db

# Email (SMTP)
MAIL_SERVER=<your-smtp-server>
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<your-email>
MAIL_PASSWORD=<your-password>
MAIL_DEFAULT_SENDER=noreply@southeastarchers.ie

# Sum Up Payment API
SUMUP_API_KEY=<your-sumup-api-key>

# Application
APP_ENV=production
```

### 5. Configure Database URL

Link MySQL service to application:

1. In Services, select the application
2. Go to "Variables" tab
3. Link the MySQL service to generate `DATABASE_URL`

### 6. Setup Domain & SSL

1. Go to "Domains" in project settings
2. Add your domain (e.g., `app.southeastarchers.ie`)
3. Enable SSL (automatic with Let's Encrypt)
4. Configure DNS records to point to Coolify instance

### 7. Deploy

1. Click "Deploy" button
2. Monitor deployment logs
3. Once successful, verify:
   - Application loads: `https://app.southeastarchers.ie`
   - Database connection works
   - Email configuration is functional

### 8. Database Initialization

After first deployment:

1. SSH into the Coolify instance
2. Run migrations:
   ```bash
   docker exec <app-container-id> flask db upgrade
   ```
3. Create admin user:
   ```bash
   docker exec -it <app-container-id> python cli.py create-user --admin
   ```

## Production Checklist

- [ ] Secret key is strong and unique
- [ ] Email SMTP credentials are correct
- [ ] Sum Up API key is configured
- [ ] Database backups are scheduled
- [ ] SSL certificate is valid
- [ ] Error logging is configured
- [ ] Database migrations are up to date
- [ ] Admin user is created
- [ ] Backup email address is configured
- [ ] Domain DNS is pointed correctly

## Monitoring

### Health Checks

Configure a health check endpoint:

```bash
Coolify → Service → Health Check
Endpoint: /
Interval: 60s
```

### Logs

View application logs:

1. Coolify Dashboard → Service
2. Click "Logs" tab
3. Monitor for errors and warnings

### Backups

Configure database backups:

1. Coolify → MySQL Service
2. Enable automatic backups
3. Set retention policy (e.g., 30 days)

## Troubleshooting

### Application Won't Start

1. Check logs: `Coolify → Service → Logs`
2. Verify environment variables
3. Check database connection
4. Look for Python import errors

### Database Connection Issues

1. Verify DATABASE_URL is correct
2. Check MySQL service is running
3. Verify credentials
4. Check network connectivity between services

### Email Not Sending

1. Verify SMTP credentials
2. Check MAIL_SERVER setting
3. Review mail logs
4. Test with CLI: `python cli.py send-test-email`

### Static Files Not Loading

1. Check Webassets manifest generation
2. Verify static file path configuration
3. Check file permissions
4. Review web server configuration

## Updates & Maintenance

### Deploying Updates

1. Make changes locally
2. Commit and push to git
3. Coolify auto-deploys on push (if configured)
4. Or manually trigger deployment in Coolify

### Database Migrations

After schema changes:

```bash
# Create migration
flask db migrate -m "Description"

# Deploy via Coolify, then run:
docker exec <app-container-id> flask db upgrade
```

### Backup Strategy

- Automate MySQL backups daily
- Store backups in separate location
- Test restore procedure monthly
- Keep at least 30 days of backups

## Performance Optimization

### Gunicorn Workers

Adjust in Dockerfile based on load:

```dockerfile
CMD ["gunicorn", "--workers", "4", "--threads", "2", "--worker-class", "gthread", ...]
```

### Database Optimization

1. Create indexes on frequently queried columns
2. Monitor slow query logs
3. Optimize N+1 queries with eager loading

### Caching

Implement caching layer:

```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})
```

## Security Hardening

1. **HTTPS**: Always use HTTPS in production
2. **CSRF Protection**: Enabled by default with Flask-WTF
3. **SQL Injection**: Protected by SQLAlchemy ORM
4. **Password**: Hashed with Werkzeug security
5. **Sessions**: Secure cookies with HttpOnly and SameSite
6. **Rate Limiting**: Consider adding rate limiting
7. **Input Validation**: Validate all user input
8. **Secrets Management**: Never commit secrets to git

## Support & Issues

For deployment issues:

1. Check Coolify documentation
2. Review application logs
3. Verify environment variables
4. Contact Coolify support
5. Open issue on GitHub repository
