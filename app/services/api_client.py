from __future__ import annotations

import os
from urllib.parse import urljoin, urlsplit

from nicegui import ui

_cached_origin: str | None = None


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
        origin = _extract_origin(base_url)
        global _cached_origin  # noqa: PLW0603
        _cached_origin = origin
        return urljoin(origin, normalized_path.lstrip("/"))
    except Exception:
        origin = _cached_origin
        if origin is None:
            port = int(os.getenv("APP_PORT", "8080"))
            origin = f"http://127.0.0.1:{port}/"
        return urljoin(origin, normalized_path.lstrip("/"))


def _extract_origin(url: str) -> str:
    parsed = urlsplit(url)
    scheme = parsed.scheme or "http"
    netloc = parsed.hostname or "127.0.0.1"
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return f"{scheme}://{netloc}/"
