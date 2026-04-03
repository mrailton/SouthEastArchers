# South East Archers Club Website

A web application for South East Archers club management, including membership management, shoot scheduling, event booking, payment processing, and member communications.

## ✨ Features

### Member Features
- **Membership Management** - Sign up, view status, and renew annual membership
- **Shoot Registration** - Browse and register for scheduled club shoots
- **Credits System** - Track included credits and purchase additional shoot credits
- **Payment Processing** - Pay by card (SumUp) or cash with admin approval
- **Personal Dashboard** - View membership status, credits, shoot history, and payments

### Admin Features
- **Member Management** - Create, edit, and manage member accounts and memberships
- **Shoot Management** - Schedule shoots, track attendance, manage locations
- **Event Management** - Create and publish club events
- **News Management** - Publish news articles and club updates
- **Payment Approvals** - Approve pending cash payments for membership/credits
- **Settings** - Configure membership costs, year dates, and payment instructions
- **Role-Based Access Control** - Fine-grained permissions for admin functions

### Payment Processing
- **Card Payments** - SumUp integration for secure card processing
- **Cash Payments** - Members request cash payment, admin approves to activate
- **Payment History** - Full payment tracking and receipt emails

### Automated Tasks
- **Membership Expiry** - Automatic membership expiration on year-end
- **Low Credits Reminder** - Weekly email reminders for members with low credits

## 🚀 Stack

- **Backend:** Python 3.14+, Flask 3.1.2
- **Database:** MySQL with SQLAlchemy & Flask-Migrate
- **Package Manager:** [UV](https://github.com/astral-sh/uv)
- **Frontend:** Vite 7.3, Tailwind CSS 4.1, Alpine.js, LightningCSS
- **Payments:** SumUp API
- **Email:** Flask-Mail
- **Task Scheduling:** Custom CLI-based scheduler
- **Deployment:** Docker, Gunicorn, WhiteNoise

## 📋 Requirements

- Python 3.14 or higher
- Node.js (LTS recommended)
- MySQL Server
- [UV](https://docs.astral.sh/uv/getting-started/installation/) (recommended for Python dependency management)

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd SouthEastArchers
   ```

2. **Set up environment variables:**
   Copy the example environment file and update it with your settings:
   ```bash
   cp .env.example .env
   ```

3. **Install dependencies:**
   ```bash
   make install
   ```

4. **Initialize the database:**
   ```bash
   flask db upgrade
   ```

5. **Seed roles and permissions:**
   ```bash
   flask rbac seed
   ```

6. **Create an admin user:**
   ```bash
   flask user create --admin
   ```

## 🏃 Running the Application

### Development Mode
Runs both the Flask development server and Vite asset watcher:
```bash
make dev
```
- Flask: http://localhost:5000
- Vite: http://localhost:5173 (Asset hot-reloading)

### Individual Servers
- **Flask only:** `flask run --debug`
- **Vite only:** `npm run dev`

### Scheduled Tasks
Run scheduled tasks (membership expiry, low credits reminders):
```bash
flask schedule run
```
For production, set up a cron job to run this command every minute.

## 📂 Project Structure

```
├── app/                    # Core Flask application
│   ├── models/             # SQLAlchemy database models
│   ├── routes/             # Flask blueprints (admin, member, auth, payment)
│   ├── services/           # Business logic layer
│   ├── forms/              # WTForms definitions
│   ├── templates/          # Jinja2 templates
│   ├── utils/              # Helper functions and utilities
│   └── scheduler/          # Task scheduling logic
├── resources/              # Frontend assets (CSS, JS, images)
├── tests/                  # Test suite (95% coverage)
├── migrations/             # Database migration files
├── web.py                  # WSGI entry point
└── pyproject.toml          # Python dependencies and configuration
```

## 🔐 Role Based Access Control (RBAC)

The application uses a fine-grained RBAC system for security.

### Key Concepts

- **Permissions:** Granular actions (e.g., `members.read`, `events.create`, `payments.approve`)
- **Roles:** Collections of permissions (e.g., `Admin`, `Content Manager`, `Membership Manager`)
- **Users:** Users are assigned roles, granting them all associated permissions

### Default Roles

| Role               | Description                                       |
|--------------------|---------------------------------------------------|
| Admin              | Full access to all features                       |
| Membership Manager | Manage members, memberships, and approve payments |
| Content Manager    | Manage news, events, and shoots                   |
| Member             | Standard member access                            |

### Implementation

- **Models:** `Role` and `Permission` in `app/models/rbac.py`
- **Decorators:** Use `@permission_required("perm.name")` in routes to enforce access
- **Service:** `RBACService` for managing roles and permissions

## ⌨️ Commands

### Makefile (dev/test tooling)

| Command                    | Description                                                |
|----------------------------|------------------------------------------------------------|
| `make install`             | Install Python and Node.js dependencies                    |
| `make dev`                 | Run development servers (Flask + Vite)                     |
| `make clean`               | Remove cache and temporary files                           |
| `make test`                | Run the test suite                                         |
| `make test-file FILE=path` | Run a single test file                                     |
| `make test-k K="keyword"`  | Run tests matching a keyword                               |
| `make test-coverage`       | Run tests with coverage report                             |
| `make lint`                | Run all quality checks (Ruff + format + import boundaries) |
| `make lint-fix`            | Auto-fix lint and formatting issues                        |
| `make typecheck`           | Run mypy type checking                                     |
| `make assets`              | Build production assets                                    |
| `make assets-watch`        | Watch and rebuild assets on change                         |

Run `make help` for a full list of targets.

### Flask CLI (app-level commands)

| Command               | Description                                 |
|-----------------------|---------------------------------------------|
| `flask db upgrade`    | Apply database migrations                   |
| `flask user create`   | Create a new user (add `--admin` for admin) |
| `flask user list`     | List all users                              |
| `flask shoot create`  | Create a shoot                              |
| `flask shoot list`    | List shoots                                 |
| `flask schedule run`  | Run due scheduled tasks                     |
| `flask schedule list` | List all scheduled tasks                    |
| `flask rbac seed`     | Seed default roles and permissions          |
| `flask stats`         | Show application statistics                 |
| `flask db-reset`      | Reset the database (destructive)            |

Run `flask --help` for a full list of commands.

## ⚙️ Environment Variables

Key environment variables in `.env`:

| Variable        | Description                | Default                 |
|-----------------|----------------------------|-------------------------|
| `FLASK_ENV`     | Application environment    | `development`           |
| `SECRET_KEY`    | Flask secret key           | (required)              |
| `DATABASE_URL`  | MySQL connection string    | (required)              |
| `MAIL_SERVER`   | SMTP server for emails     | `localhost`             |
| `MAIL_PORT`     | SMTP port                  | `587`                   |
| `MAIL_USERNAME` | SMTP username              | (optional)              |
| `MAIL_PASSWORD` | SMTP password              | (optional)              |
| `SUMUP_API_KEY` | SumUp API key for payments | (required for payments) |

## 🧪 Testing & Quality

The project maintains 95% test coverage with 539 tests.

```bash
# Run tests
make test

# Run with coverage report
make test-coverage

# Linting
make lint

# Type checking
make typecheck
```

## 🐳 Docker & Production

The project is Dockerized for production deployment.

### Building and Running
```bash
docker build -t southeastarchers .
docker run -p 5000:5000 --env-file .env southeastarchers
```

### Docker Container Features
1. Waits for the database to be ready
2. Automatically runs `flask db upgrade`
3. Serves the app using Gunicorn on port 5000
4. Uses WhiteNoise to serve pre-built static assets

### Production Checklist
- [ ] Set `FLASK_ENV=production`
- [ ] Configure secure `SECRET_KEY`
- [ ] Set up MySQL database
- [ ] Configure SMTP for email notifications
- [ ] Set up SumUp API credentials
- [ ] Configure cron job for `flask schedule run`

## 📝 License

TODO: Add license information.
