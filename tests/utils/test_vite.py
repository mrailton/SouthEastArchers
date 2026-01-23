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


def test_vite_asset_dev_server_both_fail(monkeypatch, app):
    """Test vite_asset falls back to production when both dev servers fail"""
    from app.utils.vite import vite_asset

    monkeypatch.setenv("VITE_DEV_SERVER", "http://localhost:5173")
    app.config["DEBUG"] = True

    # Both primary and alternate servers fail
    def fake_get(url, timeout):
        raise Exception("Connection refused")

    monkeypatch.setattr("requests.get", fake_get)

    # Create manifest for fallback
    root_path = app.root_path
    _write_manifest(root_path, "js/main.js", "assets/js/main.abc123.js")

    with app.test_request_context():
        result = vite_asset("js/main.js")
        # Should fall back to production manifest
        assert "assets/js/main.abc123.js" in str(result)


def test_vite_asset_prod_no_css(monkeypatch, app):
    """Test vite_asset in production without CSS files"""
    from app.utils.vite import vite_asset

    app.config["DEBUG"] = False
    root_path = app.root_path
    # Manifest without CSS
    _write_manifest(root_path, "js/app.js", "assets/js/app.xyz789.js")

    with app.test_request_context():
        result = vite_asset("js/app.js")
        s = str(result)
        # Should not have CSS link
        assert '<link rel="stylesheet"' not in s
        # Should have script tag
        assert 'script type="module"' in s
        assert "assets/js/app.xyz789.js" in s


def test_vite_asset_prod_json_decode_error(monkeypatch, app):
    """Test vite_asset handles corrupted manifest gracefully"""
    from app.utils.vite import vite_asset

    app.config["DEBUG"] = False
    root_path = app.root_path

    # Write invalid JSON to manifest
    dir_path = os.path.join(root_path, "../resources/static/.vite")
    os.makedirs(dir_path, exist_ok=True)
    manifest_path = os.path.join(dir_path, "manifest.json")
    with open(manifest_path, "w") as f:
        f.write("{ invalid json }")

    with app.test_request_context():
        result = vite_asset("js/main.js")
        # Should fall back to direct path
        assert "static/js/main.js" in str(result)


def test_vite_hmr_client_alternate_server(monkeypatch, app):
    """Test vite_hmr_client uses alternate server when primary fails"""
    from app.utils.vite import vite_hmr_client

    monkeypatch.setenv("VITE_DEV_SERVER", "http://localhost:5173")
    app.config["DEBUG"] = True

    # Primary fails, alternate succeeds
    def fake_get(url, timeout):
        if "5173" in url:
            raise Exception("Connection refused")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        return mock_resp

    monkeypatch.setattr("requests.get", fake_get)

    with app.test_request_context():
        res = vite_hmr_client()
        assert "@vite/client" in str(res)
        assert "5174" in str(res)  # Should use alternate port


def test_vite_hmr_client_both_fail(monkeypatch, app):
    """Test vite_hmr_client returns empty when both servers fail"""
    from app.utils.vite import vite_hmr_client

    monkeypatch.setenv("VITE_DEV_SERVER", "http://localhost:5173")
    app.config["DEBUG"] = True

    # Both servers fail
    def fake_get(url, timeout):
        raise Exception("Connection refused")

    monkeypatch.setattr("requests.get", fake_get)

    with app.test_request_context():
        res = vite_hmr_client()
        # Should return empty string
        assert res == ""
