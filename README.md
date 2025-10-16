# South East Archers

A Flask web application for managing an archery club with membership, credit tracking, news, and events.

## Features

- **Public Website**
  - Club information and about page
  - News and events listings
  - Responsive design with TailwindCSS
  - Interactive UI with Alpine.js

- **Member Features**
  - User registration with automatic membership creation (€100/year, includes 20 credits)
  - Member dashboard showing credits and membership status
  - Purchase additional credits (€5 per credit)
  - View credit purchase history
  - User authentication and authorization

- **Admin Features**
  - Admin dashboard with statistics
  - Create, edit, and delete news articles
  - Create, edit, and delete events
  - View all members and their details
  - View membership and credit purchase history

## Technology Stack

- **Backend**: Python 3.13, Flask 3.1.0
- **Database**: SQLite (development) / MySQL with PyMySQL (production)
- **ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Migrations**: Flask-Migrate (Alembic)
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF, WTForms
- **Frontend**: TailwindCSS 4.1.13 (CDN), Alpine.js 3.15.0 (CDN)

## Setup Instructions

### Prerequisites

- Python 3.13+
- MySQL (optional, for production)

### Installation

1. Clone or navigate to the project directory:
```bash
cd /Users/mark/Projects/SouthEastArchers
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Create sample data (optional):
```bash
python create_sample_data.py
```

7. Run the application:
```bash
flask run
```

The application will be available at http://127.0.0.1:5000

## Default Login Credentials

After running `create_sample_data.py`:

- **Admin**: admin@southeastarchers.ie / admin123
- **Member**: member@example.com / member123

## Database Configuration

### SQLite (Default - Development)
The application uses SQLite by default, which requires no additional setup.

### MySQL (Production)
To use MySQL, update your `.env` file:
```
DATABASE_URL=mysql+pymysql://username:password@localhost/southeastarchers
```

Then create the database:
```sql
CREATE DATABASE southeastarchers CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run migrations:
```bash
flask db upgrade
```

## Project Structure

```
SouthEastArchers/
├── app/
│   ├── __init__.py           # Application factory
│   ├── models.py             # Database models
│   ├── forms.py              # WTForms definitions
│   ├── routes/               # Blueprint routes
│   │   ├── __init__.py
│   │   ├── main.py          # Public routes
│   │   ├── auth.py          # Authentication routes
│   │   ├── member.py        # Member dashboard routes
│   │   └── admin.py         # Admin routes
│   ├── templates/            # Jinja2 templates
│   │   ├── base.html        # Base template
│   │   ├── index.html       # Homepage
│   │   ├── about.html       # About page
│   │   ├── news.html        # News listing
│   │   ├── events.html      # Events listing
│   │   ├── auth/            # Authentication templates
│   │   ├── member/          # Member templates
│   │   └── admin/           # Admin templates
│   └── static/              # Static files
├── migrations/              # Database migrations
├── venv/                    # Virtual environment
├── app.py                   # Application entry point
├── config.py                # Configuration
├── requirements.txt         # Python dependencies
├── create_sample_data.py   # Sample data script
├── .env                     # Environment variables (not in git)
├── .env.example            # Example environment file
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## Database Models

### User
- Email, password (hashed), name, phone
- Admin flag
- Relationships: memberships, credit_purchases

### Membership
- User relationship
- Start/end dates
- Credits remaining
- Amount paid
- Active status

### CreditPurchase
- User relationship
- Credits purchased
- Amount paid
- Purchase date

### News
- Title, content
- Author relationship
- Published status
- Created/updated timestamps

### Event
- Title, description
- Event date and location
- Creator relationship
- Published status
- Created/updated timestamps

## Routes

### Public Routes
- `/` - Homepage
- `/about` - About page
- `/news` - News listing
- `/news/<id>` - News detail
- `/events` - Events listing
- `/events/<id>` - Event detail

### Authentication Routes
- `/auth/login` - Login page
- `/auth/register` - Registration page
- `/auth/logout` - Logout

### Member Routes (Login Required)
- `/member/dashboard` - Member dashboard
- `/member/credits/purchase` - Purchase credits
- `/member/profile` - View profile

### Admin Routes (Admin Required)
- `/admin/dashboard` - Admin dashboard
- `/admin/news` - Manage news
- `/admin/news/create` - Create news
- `/admin/news/<id>/edit` - Edit news
- `/admin/news/<id>/delete` - Delete news
- `/admin/events` - Manage events
- `/admin/events/create` - Create event
- `/admin/events/<id>/edit` - Edit event
- `/admin/events/<id>/delete` - Delete event
- `/admin/members` - View members
- `/admin/members/<id>` - Member details

## Membership & Credits

- **Annual Membership**: €100 (includes 20 shooting credits)
- **Additional Credits**: €5 per credit
- 1 credit = 1 night of shooting
- Credits are added to the current membership
- No expiration on credits

## Development

### Creating Migrations

After modifying models:
```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

### Adding an Admin User

Use the Flask shell:
```bash
flask shell
>>> from app.models import User
>>> from app import db
>>> admin = User(email='admin@example.com', first_name='Admin', last_name='User', is_admin=True)
>>> admin.set_password('your-password')
>>> db.session.add(admin)
>>> db.session.commit()
```

## Security Considerations

- Change `SECRET_KEY` in production
- Use strong passwords for admin accounts
- Use HTTPS in production
- Consider implementing CSRF protection (already included via Flask-WTF)
- Implement rate limiting for login attempts
- Regular database backups

## Production Deployment

1. Set `FLASK_ENV=production` in `.env`
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Use MySQL or PostgreSQL instead of SQLite
4. Configure a reverse proxy (Nginx, Apache)
5. Enable HTTPS with SSL certificates
6. Set a strong `SECRET_KEY`
7. Configure proper logging
8. Set up automated backups

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 127.0.0.1:8000 app:app
```

## License

This project is created for South East Archers archery club.

## Support

For issues or questions, contact the club administrator.
