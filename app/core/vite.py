import json
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "resources" / "static"
MANIFEST_PATH = STATIC_DIR / ".vite" / "manifest.json"

_ENTRY_ALIASES = {
    "js/site.js": "resources/assets/js/site.js",
    "js/admin.js": "resources/assets/js/admin.js",
}


@lru_cache
def _load_manifest() -> dict:
    if not MANIFEST_PATH.is_file():
        return {}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def vite_hmr_client() -> str:
    settings = get_settings()
    if not settings.app_debug:
        return ""
    return f'<script type="module" src="{settings.vite_dev_server_url}/@vite/client"></script>'


def _dev_asset_tag(entry: str) -> str:
    settings = get_settings()
    return f'<script type="module" src="{settings.vite_dev_server_url}/static/{entry}"></script>'


def _prod_asset_tags(entry: str) -> str:
    manifest = _load_manifest()
    manifest_key = _ENTRY_ALIASES.get(entry, entry)
    chunk = manifest.get(manifest_key)
    if not chunk:
        return ""
    tags: list[str] = []
    for css_file in chunk.get("css", []):
        tags.append(f'<link rel="stylesheet" href="/static/{css_file}">')
    tags.append(f'<script type="module" src="/static/{chunk["file"]}"></script>')
    return "\n".join(tags)


def vite_asset(entry: str) -> str:
    settings = get_settings()
    if settings.app_debug:
        return _dev_asset_tag(entry)
    return _prod_asset_tags(entry)
