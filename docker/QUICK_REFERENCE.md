# Docker Compose Quick Reference

## Development Commands

```bash
# Start all services (MySQL, Redis, Web, Worker, Mailhog)
make docker-up

# Stop all services
make docker-down

# View logs (follow)
make docker-logs

# Rebuild containers (after dependency changes)
make docker-rebuild

# Open shell in web container
make docker-shell

# Open MySQL shell
make docker-db-shell

# Check status
docker ps
```

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Web App | http://localhost:5000 | Flask application |
| Mailhog UI | http://localhost:8025 | Email testing interface |
| MySQL | localhost:3306 | Database (user: devuser, pass: devpassword) |
| Redis | localhost:6379 | Background jobs queue |

## Production Deployment (Dokploy)

```bash
# 1. In Dokploy UI:
#    - Create new Compose application
#    - Connect Git repository
#    - Set compose file: docker/docker-compose.yml

# 2. Add environment variables in Dokploy:
MYSQL_ROOT_PASSWORD=<secure-password>
MYSQL_USER=appuser
MYSQL_PASSWORD=<secure-password>
SECRET_KEY=<32-char-secret>
MAIL_SERVER=smtp.example.com
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=<email-password>
SUMUP_API_KEY=<your-key>
SUMUP_MERCHANT_CODE=<your-code>

# 3. Deploy!
```

## Common Tasks

### View Logs for Specific Service
```bash
docker-compose -f docker/docker-compose.dev.yml logs -f web
docker-compose -f docker/docker-compose.dev.yml logs -f worker
```

### Run Database Migrations Manually
```bash
make docker-shell
flask db upgrade
```

### Access Database
```bash
# From host
mysql -h 127.0.0.1 -u devuser -pdevpassword southeastarchers

# From container
make docker-db-shell
```

### Execute Command in Container
```bash
docker-compose -f docker/docker-compose.dev.yml exec web flask shell
docker-compose -f docker/docker-compose.dev.yml exec worker python
```

### View Container Resource Usage
```bash
docker stats
```

### Clean Up Everything (including volumes)
```bash
docker-compose -f docker/docker-compose.dev.yml down -v
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :5000

# Kill the process or change port in docker-compose
```

### Container Won't Start
```bash
# Check logs
make docker-logs

# Check specific service
docker-compose -f docker/docker-compose.dev.yml logs db
```

### Database Connection Failed
```bash
# Ensure db is healthy
docker-compose -f docker/docker-compose.dev.yml ps

# Restart services
make docker-down && make docker-up
```

### Changes Not Reflected
```bash
# For code changes: already hot-reloading (no action needed)
# For dependency changes:
make docker-rebuild
```

## Files Overview

```
docker/
├── docker-compose.yml          # Production (uses GHCR images)
├── docker-compose.build.yml    # Production (builds locally)
├── docker-compose.dev.yml      # Development (local)
├── Dockerfile.web              # Web service image
├── Dockerfile.worker           # Worker service image
├── Dockerfile.dev              # Development image
├── docker-entrypoint.sh        # Runs migrations on startup
├── .env.production.example     # Production env template
├── README.md                   # Detailed documentation
└── QUICK_REFERENCE.md          # This file
```

## Key Differences: Dev vs Production

| Feature | Development | Production (GHCR) |
|---------|------------|-------------------|
| Compose File | docker-compose.dev.yml | docker-compose.yml |
| Images | Built locally | Pulled from GHCR |
| Hot Reload | ✅ Yes | ❌ No |
| Code Location | Mounted volume | Copied in image |
| Database Creds | Hardcoded | Environment variables |
| Email | Mailhog | Real SMTP |
| Web Server | Flask dev server | Gunicorn (4 workers) |
| User | root | appuser (non-root) |
| Mailhog | ✅ Included | ❌ Not included |
| CI/CD | Manual build | Auto-built by GH Actions |

## Environment Variables (Production)

Required:
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_USER` 
- `MYSQL_PASSWORD`
- `SECRET_KEY`
- `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD`
- `SUMUP_API_KEY`, `SUMUP_MERCHANT_CODE`

Optional:
- `MYSQL_DATABASE` (default: southeastarchers)
- `WEB_PORT` (default: 5000)
- `FLASK_ENV` (default: production)

## Further Reading

- **Detailed Docker Guide**: [README.md](README.md)
- **Dokploy Deployment**: [../docs/DOKPLOY_DEPLOYMENT.md](../docs/DOKPLOY_DEPLOYMENT.md)
- **Migration Notes**: [../docs/DOCKER_MIGRATION.md](../docs/DOCKER_MIGRATION.md)
- **Main README**: [../README.md](../README.md)
