"""Vite helper for Flask templates"""

import json
import os

from flask import current_app, url_for
from markupsafe import Markup


def vite_asset(asset_name):
    """
    Get the Vite asset URL/tags for production or development.

    In development mode with Vite dev server running, returns script tag.
    In production, reads from manifest.json and returns CSS + JS tags.

    Args:
        asset_name: Asset path relative to resources/assets (e.g., 'js/main.js')

    Returns:
        Markup with HTML tags for the asset(s)
    """
    # Check if we're in development mode and Vite dev server is available
    vite_dev_server = os.environ.get("VITE_DEV_SERVER", "http://localhost:5173")
    is_dev = current_app.config.get("DEBUG", False)

    if is_dev:
        # Try to use Vite dev server
        try:
            import requests

            response = requests.get(f"{vite_dev_server}/static/@vite/client", timeout=0.1)
            if response.status_code == 200:
                # Vite is running - return script tag for dev server
                return Markup(f'<script type="module" src="{vite_dev_server}/static/{asset_name}"></script>')
        except Exception:
            pass

        # Try alternate port (5174)
        try:
            vite_dev_server_alt = "http://localhost:5174"
            response = requests.get(f"{vite_dev_server_alt}/static/@vite/client", timeout=0.1)
            if response.status_code == 200:
                return Markup(f'<script type="module" src="{vite_dev_server_alt}/static/{asset_name}"></script>')
        except Exception:
            pass

    # Production mode: read from manifest
    manifest_path = os.path.join(current_app.root_path, "../resources/static/.vite/manifest.json")

    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        if asset_name in manifest:
            entry = manifest[asset_name]
            file_path = entry["file"]

            # Check if this entry has CSS files
            css_files = entry.get("css", [])
            if css_files:
                # Return both CSS link tags and JS script tag
                html_parts = []
                for css_file in css_files:
                    html_parts.append(f'<link rel="stylesheet" href="{url_for("static", filename=css_file)}">')
                html_parts.append(f'<script type="module" src="{url_for("static", filename=file_path)}"></script>')
                return Markup("\n    ".join(html_parts))

            # No CSS, just return script tag
            return Markup(f'<script type="module" src="{url_for("static", filename=file_path)}"></script>')
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        pass

    # Fallback to direct asset path
    return Markup(f'<script type="module" src="{url_for("static", filename=asset_name)}"></script>')


def vite_hmr_client():
    """
    Returns the Vite HMR client script tag for development mode.
    Returns empty string in production.
    """
    is_dev = current_app.config.get("DEBUG", False)
    vite_dev_server = os.environ.get("VITE_DEV_SERVER", "http://localhost:5173")

    if is_dev:
        # Try default port
        try:
            import requests

            response = requests.get(f"{vite_dev_server}/static/@vite/client", timeout=0.1)
            if response.status_code == 200:
                return Markup(f'<script type="module" src="{vite_dev_server}/static/@vite/client"></script>')
        except Exception:
            pass

        # Try alternate port (5174)
        try:
            vite_dev_server_alt = "http://localhost:5174"
            response = requests.get(f"{vite_dev_server_alt}/static/@vite/client", timeout=0.1)
            if response.status_code == 200:
                return Markup(f'<script type="module" src="{vite_dev_server_alt}/static/@vite/client"></script>')
        except Exception:
            pass

    return ""
