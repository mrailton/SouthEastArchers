# Quick Start Guide - South East Archers

Get the South East Archers application running in minutes!

## Option 1: Docker Compose (Recommended)

### Prerequisites

- Docker and Docker Compose installed
- 5GB disk space

### Steps

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd SEA
   ```

2. **Start services**
   ```bash
   docker-compose up -d
   ```

3. **Initialize database**
   ```bash
   docker exec sea_app flask db upgrade
   ```

4. **Create admin user**
   ```bash
   docker exec -it sea_app python cli.py create-user --admin
   ```
   Follow the prompts to create your admin account.

5. **Access the application**
   - Main app: http://localhost:5000
   - Email testing (MailHog): http://localhost:8025

6. **Stop services**
   ```bash
   docker-compose down
   ```

## Option 2: Local Development

### Prerequisites

- Python 3.14
- MySQL 8.0
- pip package manager

### Steps

1. **Create virtual environment**
   ```bash
   python3.14 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Create database**
   ```bash
   # Start MySQL first
   flask db upgrade
   ```

5. **Create admin user**
   ```bash
   python cli.py create-user --admin
   ```

6. **Run development server**
   ```bash
   flask run
   ```

7. **Access the application**
   - Open http://localhost:5000

## First-Time Setup

After starting the application:

### 1. Login as Admin

- URL: http://localhost:5000/login
- Email: (the one you created)
- Password: (your password)

### 2. Create Shooting Nights

```bash
python cli.py create-shooting-night
```

Or use the admin portal:
- Go to Admin Dashboard
- Click "Create Shooting Night"

### 3. Create Some News

- Admin Dashboard → Manage News → Create News

### 4. Create Test Members

Create regular members:

```bash
python cli.py create-user
```

Or they can sign up via http://localhost:5000/signup

### 5. Test Features

- **Member Portal**: Login as member, view dashboard
- **Shooting Nights**: Register for a night
- **Credit Purchase**: Go to credits page (integrate Sum Up later)
- **Profile**: Edit member information

## Common Commands

### Database Management

```bash
# View all users
python cli.py list-users

# Delete a user
python cli.py delete-user

# Show statistics
python cli.py show-stats
```

### Database Migrations

```bash
# Create new migration
flask db migrate -m "Your migration description"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Check code style
flake8 app/ tests/

# Sort imports
isort app/ tests/
```

## Project Structure Reference

```
SEA/
├── app/                      # Application code
│   ├── models/              # Database models
│   ├── routes/              # Route blueprints
│   ├── forms/               # WTForms forms
│   ├── utils/               # Utilities and decorators
│   └── services/            # External services (Sum Up)
├── resources/               # Static files and templates
│   ├── static/              # CSS, JS, images
│   └── templates/           # Jinja2 HTML templates
├── tests/                   # Test suites
├── migrations/              # Database migrations
├── config/                  # Configuration files
├── cli.py                   # Management CLI
├── wsgi.py                  # Application entry point
└── README.md               # Full documentation
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>
```

### Database Connection Error

1. Check MySQL is running
2. Verify DATABASE_URL in .env
3. Check credentials

### Template Not Found

1. Verify template file exists in `resources/templates/`
2. Check template path in route
3. Restart Flask server

### Permission Denied Errors

```bash
# Fix file permissions
chmod -R 755 resources/
chmod -R 755 migrations/
chmod -R 755 logs/
```

## Next Steps

1. **Read full documentation**: See README.md
2. **Implement payments**: Integrate Sum Up API
3. **Customize branding**: Update colors and logo
4. **Email configuration**: Set up SMTP provider
5. **Deploy**: Follow DEPLOYMENT.md guide

## Getting Help

- Check README.md for detailed documentation
- Review DEPLOYMENT.md for production setup
- Look at code examples in tests/
- Check Flask and SQLAlchemy documentation

## Development Tips

1. **Enable debug mode**: Set `FLASK_ENV=development` in .env
2. **Use CLI for quick data**: `python cli.py` for database operations
3. **Test in browser**: http://localhost:5000
4. **Check logs**: `logs/` directory
5. **Use MailHog**: http://localhost:8025 to view emails in development

Happy coding! 🏹
