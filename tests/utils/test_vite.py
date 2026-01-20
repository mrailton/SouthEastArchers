import json
import os
from unittest.mock import MagicMock

from markupsafe import Markup


def _write_manifest(root_path, asset_name, file_path, css_files=None):
    dir_path = os.path.join(root_path, "../resources/static/.vite")
    os.makedirs(dir_path, exist_ok=True)
    manifest_path = os.path.join(dir_path, "manifest.json")
    manifest = {
        asset_name: {
            "file": file_path,
        }
    }
    if css_files:
        manifest[asset_name]["css"] = css_files

    with open(manifest_path, "w") as f:
        json.dump(manifest, f)


def test_vite_asset_dev_server_primary(monkeypatch, app):
    from app.utils.vite import vite_asset

    monkeypatch.setenv("VITE_DEV_SERVER", "http://localhost:5173")
    app.config["DEBUG"] = True

    # Mock requests.get to return status 200 for primary server
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    monkeypatch.setattr("requests.get", lambda url, timeout: mock_resp)

    with app.test_request_context():
        result = vite_asset("js/main.js")
        assert isinstance(result, Markup)
        assert "http://localhost:5173/static/js/main.js" in str(result)


def test_vite_asset_dev_server_alternate(monkeypatch, app):
    from app.utils.vite import vite_asset

    monkeypatch.setenv("VITE_DEV_SERVER", "http://localhost:5173")
    app.config["DEBUG"] = True

    # First call fails, second (alternate) returns 200
    def fake_get(url, timeout):
        if "5173" in url:
            raise Exception("nope")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        return mock_resp

    monkeypatch.setattr("requests.get", fake_get)

    with app.test_request_context():
        result = vite_asset("js/main.js")
        assert isinstance(result, Markup)
        assert "http://localhost:5174/static/js/main.js" in str(result)


def test_vite_asset_prod_with_css(monkeypatch, app):
    from app.utils.vite import vite_asset

    app.config["DEBUG"] = False
    # Create manifest pointing to css + file
    root_path = app.root_path
    _write_manifest(root_path, "js/main.js", "assets/js/main.abc123.js", css_files=["assets/css/main.abc123.css"])

    with app.test_request_context():
        result = vite_asset("js/main.js")
        s = str(result)
        assert '<link rel="stylesheet" href="' in s
        assert 'script type="module"' in s


def test_vite_asset_prod_fallback(monkeypatch, app):
    from app.utils.vite import vite_asset

    app.config["DEBUG"] = False
    # Ensure no manifest exists for this asset
    root_path = app.root_path
    dir_path = os.path.join(root_path, "../resources/static/.vite")
    try:
        # remove manifest if present
        os.remove(os.path.join(dir_path, "manifest.json"))
    except Exception:
        pass

    with app.test_request_context():
        result = vite_asset("js/nonexistent.js")
        assert "static/js/nonexistent.js" in str(result)


def test_vite_hmr_client_dev_and_fallback(monkeypatch, app):
    from app.utils.vite import vite_hmr_client

    monkeypatch.setenv("VITE_DEV_SERVER", "http://localhost:5173")
    app.config["DEBUG"] = True

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    monkeypatch.setattr("requests.get", lambda url, timeout: mock_resp)

    with app.test_request_context():
        res = vite_hmr_client()
        assert "@vite/client" in str(res)

    # Now simulate not in DEBUG
    app.config["DEBUG"] = False
    with app.test_request_context():
        res = vite_hmr_client()
        assert res == ""
