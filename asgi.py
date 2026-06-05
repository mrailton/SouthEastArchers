"""ASGI entrypoint for uvicorn and production servers."""

import app.core.config  # noqa: F401 - loads .env into os.environ before startup

from app.main import app

__all__ = ["app"]
