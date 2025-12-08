import os
import warnings

# Suppress SyntaxWarning from third-party libraries (e.g., sumup package)
warnings.filterwarnings("ignore", category=SyntaxWarning)

from dotenv import load_dotenv
from whitenoise import WhiteNoise

load_dotenv()

from app import create_app, db

app = create_app(os.environ.get("FLASK_ENV", "development"))

# Add WhiteNoise for serving static files
app.wsgi_app = WhiteNoise(app.wsgi_app, root="./resources/static", prefix="static/")


@app.shell_context_processor
def make_shell_context():
    """Register shell context for flask shell"""
    return {"db": db}


if __name__ == "__main__":
    app.run()
