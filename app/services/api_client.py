from __future__ import annotations

from urllib.parse import urljoin

from nicegui import ui


def api_url(path: str) -> str:
    """Build an absolute URL for the current client without hardcoding hostnames."""

    client = ui.context.client
    base_url = str(client.request.base_url)
    normalized_path = path if path.startswith("/") else f"/{path}"
    return urljoin(base_url, normalized_path.lstrip("/"))
