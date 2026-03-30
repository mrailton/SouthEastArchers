import os
import warnings

# Suppress SyntaxWarning from third-party libraries (e.g., sumup package)
warnings.filterwarnings("ignore", category=SyntaxWarning)

from dotenv import load_dotenv
from whitenoise import WhiteNoise

load_dotenv()

from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))

# Add WhiteNoise for serving static files (use absolute path)
static_root = os.path.join(os.path.dirname(__file__), "resources", "static")
app.wsgi_app = WhiteNoise(
    app.wsgi_app,
    root=static_root,
    prefix="static/",
    max_age=31536000 if not app.debug else 0,
)


if __name__ == "__main__":
    app.run()
