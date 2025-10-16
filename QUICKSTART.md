# Quick Start Guide

## Getting Started in 5 Minutes

### 1. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 2. Run the Application
```bash
flask run
```

### 3. Open Your Browser
Navigate to: http://127.0.0.1:5000

### 4. Login Credentials

**Admin Access:**
- Email: admin@southeastarchers.ie
- Password: admin123

**Member Access:**
- Email: member@example.com
- Password: member123

## What You Can Do

### As a Visitor
- Browse the homepage
- Read news articles
- View upcoming events
- Register for membership

### As a Member
- View your dashboard
- Check your credit balance
- Purchase additional credits
- View membership details

### As an Admin
- Access admin dashboard
- Create/edit/delete news articles
- Create/edit/delete events
- View all members
- See member details and credit history

## Application Features

### Membership System
- €100 per year
- Includes 20 shooting credits
- Each credit = 1 night of shooting

### Credit Purchase
- €5 per additional credit
- No bulk discount
- Instant credit addition

### Content Management
- Full CRUD for news articles
- Full CRUD for events
- Publish/draft functionality

## File Structure Overview

```
app/
  routes/
    main.py     - Public pages (home, news, events)
    auth.py     - Login, register, logout
    member.py   - Member dashboard and features
    admin.py    - Admin management pages
  templates/    - All HTML templates
  models.py     - Database models
  forms.py      - Form definitions
```

## Common Tasks

### Create a New Admin User
```bash
flask shell
>>> from app.models import User
>>> from app import db
>>> admin = User(email='new@admin.com', first_name='New', last_name='Admin', is_admin=True)
>>> admin.set_password('password123')
>>> db.session.add(admin)
>>> db.session.commit()
>>> exit()
```

### Reset Database
```bash
rm app.db
flask db upgrade
python create_sample_data.py
```

### View Database Contents
```bash
flask shell
>>> from app.models import *
>>> User.query.all()
>>> News.query.all()
>>> Event.query.all()
```

## Troubleshooting

### Port Already in Use
```bash
# Kill existing Flask process
pkill -f flask

# Or use a different port
flask run --port 5001
```

### Database Issues
```bash
# Remove and recreate database
rm app.db
flask db upgrade
python create_sample_data.py
```

### Module Not Found
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Next Steps

1. **Customize Content**: Login as admin and add your own news and events
2. **Update About Page**: Edit `app/templates/about.html`
3. **Add More Members**: Use the registration form or create via Flask shell
4. **Configure Production**: Update `.env` for production settings
5. **Setup MySQL**: Change DATABASE_URL in `.env` for production database

## Support

For detailed documentation, see the main README.md file.
