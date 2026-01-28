# South East Archers Club Website

A web application for South East Archers club management, including membership, event booking, shoot tracking, and news.

## 🚀 Stack

- **Backend:** Python 3.14+, Flask 3.1.2
- **Database:** MySQL with SQLAlchemy & Flask-Migrate
- **Package Manager:** [UV](https://github.com/astral-sh/uv)
- **Frontend:** Vite 7.3, Tailwind CSS 4.1, Alpine.js, LightningCSS
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
   cp .env.example .env  # Note: Create .env.example if it doesn't exist, or edit .env directly
   ```

3. **Install dependencies:**
   Using the management script (installs both Python and Node.js dependencies):
   ```bash
   python manage.py install
   ```

4. **Initialize the database:**
   ```bash
   python manage.py db upgrade
   ```

5. **Create an admin user:**
   ```bash
   python manage.py user create --admin
   ```

## 🏃 Running the Application

### Development Mode
Runs both the Flask development server and Vite asset watcher:
```bash
python manage.py dev
```
- Flask: http://localhost:5000
- Vite: http://localhost:5173 (Asset hot-reloading)

### Individual Servers
- **Flask only:** `python manage.py runserver`
- **Vite only:** `npm run dev`

## 📂 Project Structure

- `app/`: Core Flask application
  - `models/`: SQLAlchemy database models
  - `routes/`: Flask blueprints (admin, member, public, auth, payment)
  - `services/`: Business logic layer
  - `forms/`: WTForms definitions
  - `templates/`: Jinja2 templates
  - `utils/`: Helper functions and utilities
  - `scheduler/`: Task scheduling logic
- `resources/`: Frontend assets (CSS, JS, images)
- `tests/`: Test suite
- `migrations/`: Database migration files
- `web.py`: Main application entry point
- `manage.py`: CLI management tool
- `pyproject.toml`: Python dependencies and tool configuration
- `package.json`: Node.js dependencies and scripts

## ⌨️ CLI Commands (`manage.py`)

The project includes a comprehensive CLI tool for management tasks:

| Command | Description |
|---------|-------------|
| `python manage.py dev` | Run development servers (Flask + Vite) |
| `python manage.py install` | Install Python and Node.js dependencies |
| `python manage.py db upgrade` | Apply database migrations |
| `python manage.py user create` | Create a new user (add `--admin` for admin) |
| `python manage.py test run` | Run the test suite |
| `python manage.py lint all` | Run linting and formatting (Ruff) |
| `python manage.py assets build` | Build production assets |
| `python manage.py schedule run` | Run due scheduled tasks |
| `python manage.py stats` | Show application statistics |
| `python manage.py clean` | Remove cache and temporary files |

Run `python manage.py --help` for a full list of commands.

## ⚙️ Environment Variables

Key environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Application environment | `development` |
| `SECRET_KEY` | Flask secret key | (required) |
| `DATABASE_URL` | MySQL connection string | (required) |
| `MAIL_SERVER` | SMTP server for emails | `localhost` |
| `SUMUP_API_KEY` | SumUp API key for payments | (required for payments) |

## 🧪 Testing & Quality

- **Tests:** `python manage.py test run`
- **Coverage:** `python manage.py test coverage`
- **Linting:** `python manage.py lint check`
- **Type Checking:** `python manage.py lint typecheck`

## 🐳 Docker & Production

The project is Dockerized for production.

### Building and Running
```bash
docker build -t southeastarchers .
docker run -p 5000:5000 --env-file .env southeastarchers
```

The Docker container:
1. Waits for the database to be ready.
2. Automatically runs `flask db upgrade`.
3. Serves the app using Gunicorn on port 5000.
4. Uses WhiteNoise to serve pre-built static assets.

## 📝 License

TODO: Add license information.
