# Installation & Setup Guide

## Complete Setup Instructions for South East Archers Application

### Step 1: Prerequisites Check

Ensure you have:
- Docker and Docker Compose installed (recommended)
- OR Python 3.14 + MySQL 8.0 (for local development)
- Git for version control
- Text editor or IDE

### Step 2: Initialize Git Repository

```bash
cd /home/mark/Projects/SEA
git init
git add .
git commit -m "Initial commit: South East Archers application"
```

### Step 3: Configuration

1. Copy environment template:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings (minimally set Secret Key for now)

### Step 4: Start with Docker Compose (Easiest)

```bash
docker-compose up -d
```

Wait for services to start, then initialize:

```bash
docker exec sea_app flask db upgrade
docker exec -it sea_app python cli.py create-user --admin
```

Access:
- App: http://localhost:5000
- Email: http://localhost:8025

### Step 5: Or Local Development Setup

```bash
# Create virtual environment
python3.14 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database connection in .env
# Ensure MySQL is running

# Initialize database
flask db upgrade

# Create admin user
python cli.py create-user --admin

# Run development server
flask run
```

### Step 6: Test the Application

1. Open http://localhost:5000 (or your server)
2. Login with admin credentials
3. Explore admin dashboard
4. Create some test data (news, events, shooting nights)

### Step 7: Create a Regular User Account

```bash
python cli.py create-user
# or
# Go to http://localhost:5000/signup in browser
```

## What's Next?

1. **Configure Email**: Set up SMTP credentials in .env for password resets
2. **Set Up Payments**: Get Sum Up API key and configure in .env
3. **Customize**: Update club information, colors, and branding
4. **Backup Strategy**: Set up database backups
5. **Monitoring**: Configure logging and error tracking
6. **Deploy**: Follow DEPLOYMENT.md for production setup

## Troubleshooting

### Issue: Port 5000 already in use
```bash
lsof -i :5000
kill -9 <PID>
```

### Issue: Database connection error
- Verify MySQL is running
- Check DATABASE_URL in .env
- Verify credentials

### Issue: ModuleNotFoundError
```bash
pip install -r requirements.txt
```

### Issue: Permission denied on Docker
```bash
docker exec -u root sea_app chmod -R 755 /app
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `wsgi.py` | Application entry point |
| `cli.py` | Management CLI commands |
| `config/config.py` | Application configuration |
| `.env.example` | Environment variables template |
| `requirements.txt` | Python dependencies |
| `docker-compose.yml` | Local development environment |
| `Dockerfile` | Production container image |

## Management Commands

```bash
# Create user
python cli.py create-user

# List users
python cli.py list-users

# Delete user
python cli.py delete-user

# Create shooting night
python cli.py create-shooting-night

# Show statistics
python cli.py show-stats

# Initialize database
python cli.py init-db
```

## Database Migrations

```bash
# Create migration after model changes
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Rollback
flask db downgrade
```

## For Windows Users

Use these commands instead:

```bash
# Virtual environment
python -m venv venv
venv\Scripts\activate

# Other commands are the same
```

## Docker Compose Useful Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Execute command in container
docker-compose exec sea_app python cli.py create-user

# Rebuild image
docker-compose build
```

## First Admin Account Creation

When prompted during setup:
- **Name**: Your full name
- **Email**: Your email address (used for login)
- **Password**: Strong password (min 6 characters)
- **Phone**: Optional
- **Date of Birth**: Your DOB (YYYY-MM-DD format)
- **Admin**: Select yes when asked

## Security Reminder

After setup:
1. Change default SECRET_KEY in .env
2. Set up HTTPS/SSL in production
3. Configure secure SMTP for emails
4. Update admin contact email
5. Set up database backups
6. Configure firewall rules

---

For detailed documentation, see:
- README.md - Full feature documentation
- QUICKSTART.md - Quick start guide
- DEPLOYMENT.md - Production deployment
- PROJECT_SUMMARY.md - Complete project overview
