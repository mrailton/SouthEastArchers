# South East Archers - Membership & Events Portal

A modern web application for managing archery club memberships, shooting nights, and events built with Flask, MySQL, Tailwind CSS, and Alpine.js.

## Features

- **Public Website**: Information, news, and events pages
- **Member Portal**: Dashboard, shooting nights management, credit purchases, profile management
- **Admin Portal**: Membership management, shooting night recording, news and events management
- **Payment Processing**: Integration with Sum Up for membership and credit purchases
- **Authentication**: Email-based login with password reset functionality
- **Mobile Friendly**: Responsive design with Tailwind CSS 4.1
- **Docker Support**: Full Docker and Docker Compose setup for easy deployment

## Tech Stack

- **Backend**: Flask 3.0.0 with Python 3.14
- **Database**: MySQL 8.0
- **Frontend**: Tailwind CSS 4.1 + Alpine.js 3
- **Asset Pipeline**: Webassets with minification
- **Testing**: pytest with comprehensive coverage
- **Deployment**: Docker + Coolify
- **Email**: SMTP for password resets and notifications
- **Payments**: Sum Up API

## Project Structure

```
.
├── app/                       # Flask application package
│   ├── models/               # SQLAlchemy models
│   ├── routes/               # Blueprint routes
│   ├── forms/                # WTForms forms
│   ├── utils/                # Utility functions and decorators
│   └── services/             # External service integrations
├── resources/                # Static assets and templates
│   ├── static/               # CSS, JS, images
│   └── templates/            # Jinja2 templates
├── migrations/               # Alembic database migrations
├── tests/                    # Test suites
├── config/                   # Configuration files
├── cli.py                    # Management CLI
├── wsgi.py                   # WSGI entry point
├── Dockerfile                # Container image definition
├── docker-compose.yml        # Local development environment
└── requirements.txt          # Python dependencies
```

## Installation & Setup

### Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.14
- MySQL 8.0 (if not using Docker)

### Quick Start with Docker

```bash
# Clone the repository
git clone <repo>
cd SEA

# Start services
docker-compose up -d

# Initialize database
docker exec sea_app flask db upgrade

# Create admin user
docker exec -it sea_app python cli.py create-user --admin

# Access the application
# App: http://localhost:5000
# MailHog (email testing): http://localhost:8025
```

### Local Development Setup

```bash
# Create virtual environment
python3.14 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Initialize database
flask db upgrade

# Create admin user
python cli.py create-user --admin

# Run development server
flask run
```

## Configuration

Copy `.env.example` to `.env` and configure:

```env
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/db

# Email (SMTP)
MAIL_SERVER=localhost
MAIL_PORT=587
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-password

# Sum Up Payment API
SUMUP_API_KEY=your-sumup-api-key
```

## Management CLI

The `cli.py` script provides various management commands:

```bash
# Initialize database
python cli.py init-db

# Create a new user
python cli.py create-user

# List all users
python cli.py list-users

# Delete a user
python cli.py delete-user

# Create a shooting night
python cli.py create-shooting-night

# Show statistics
python cli.py show-stats
```

## Membership Pricing

- **Annual Membership**: €100/year
  - Includes: 20 shooting nights
  - Valid for: 365 days
  
- **Additional Credits**: €5 per shooting night
  - Can be purchased anytime
  - No expiration (unless configured)

## Testing

Run the full test suite with coverage:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py
```

## API Integration

### Sum Up Payment

The application integrates with Sum Up API for payment processing:

```python
from app.services import SumUpService

service = SumUpService()
checkout = service.create_checkout(
    amount=100.00,
    currency='EUR',
    description='Annual Membership',
    return_url='https://example.com/payment-success'
)
```

## Database Models

- **User**: Member and admin accounts
- **Membership**: Annual membership tracking
- **ShootingNight**: Available shooting sessions
- **Credit**: Additional shooting credits
- **News**: Club news articles
- **Event**: Club events
- **Payment**: Transaction records

## Security Features

- Password hashing with Werkzeug
- CSRF protection with Flask-WTF
- Secure session cookies (HttpOnly, SameSite)
- Admin role-based access control
- Input validation and sanitization

## Deployment

### Docker Deployment

The application includes production-ready Docker setup:

```bash
# Build image
docker build -t sea-app:latest .

# Run container
docker run -d \
  --name sea_app \
  -p 5000:5000 \
  -e DATABASE_URL=mysql://... \
  -e SUMUP_API_KEY=... \
  sea-app:latest
```

### Coolify Deployment

1. Push code to Git repository
2. Create new project in Coolify
3. Configure environment variables
4. Connect MySQL service
5. Deploy from git repository

## Development Workflow

1. Create feature branch
2. Make changes and test locally
3. Run test suite and linting
4. Commit with meaningful messages
5. Create pull request
6. Deploy to production after review

## Contributing

1. Follow PEP 8 style guide
2. Write tests for new features
3. Update documentation
4. Ensure all tests pass before submitting PR

## License

[Your License Here]

## Support

For issues and questions, please open an issue on the project repository.
