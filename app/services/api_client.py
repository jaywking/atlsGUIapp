from __future__ import annotations

from urllib.parse import urljoin
import os

from nicegui import ui


def api_url(path: str) -> str:
    """Build an absolute URL for API calls.

    Prefer the active NiceGUI client when available (typical for UI event
    handlers). If called from a background task without a client context, fall
    back to localhost using the configured ``APP_PORT`` (default 8080).
    """

    normalized_path = path if path.startswith("/") else f"/{path}"

    try:
        client = ui.context.client  # requires UI context
        base_url = str(client.request.base_url)
        return urljoin(base_url, normalized_path.lstrip("/"))
    except Exception:
        port = int(os.getenv("APP_PORT", "8000"))
        base_url = f"http://127.0.0.1:{port}/"
        return urljoin(base_url, normalized_path.lstrip("/"))

