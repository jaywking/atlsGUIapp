"""Helpers for validating external service credentials."""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import httpx


logger = logging.getLogger(__name__)

NOTION_BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
MAPS_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
MAPS_TEST_ADDRESS = "New York, NY"


async def check_notion_connection(
    token: Optional[str], db_id: Optional[str] = None
) -> Tuple[bool, str]:
    """Return (success, message) for a lightweight Notion API check."""

    if not token:
        return False, "Missing Notion token"

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    endpoint = f"{NOTION_BASE_URL}/databases/{db_id}" if db_id else f"{NOTION_BASE_URL}/search"
    payload = None if db_id else {"page_size": 1}

    logger.info(
        "Checking Notion connectivity (db_id=%s, token_present=%s)",
        db_id,
        bool(token),
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if db_id:
                response = await client.get(endpoint, headers=headers)
            else:
                response = await client.post(endpoint, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        logger.error("Notion connectivity failed: %s", exc)
        return False, f"Request failed: {exc}"

    if response.status_code == 200:
        logger.info("Notion connectivity success")
        return True, "Connected"

    detail = _extract_error(response)
    logger.warning("Notion connectivity error: %s", detail)
    return False, detail


async def check_maps_connection(api_key: Optional[str]) -> Tuple[bool, str]:
    """Return (success, message) for a simple Google Maps geocode request."""

    if not api_key:
        return False, "Missing Google Maps API key"

    params = {"address": MAPS_TEST_ADDRESS, "key": api_key}

    logger.info("Checking Google Maps connectivity (key_present=%s)", bool(api_key))

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(MAPS_GEOCODE_URL, params=params)
    except httpx.HTTPError as exc:
        logger.error("Google Maps connectivity failed: %s", exc)
        return False, f"Request failed: {exc}"

    try:
        data = response.json()
    except ValueError:
        logger.error("Google Maps response was not JSON")
        return False, "Invalid JSON response"

    status = data.get("status")
    if status == "OK":
        logger.info("Google Maps connectivity success")
        return True, "Connected"

    message = data.get("error_message") or status or "Unknown response"
    logger.warning("Google Maps connectivity error: %s", message)
    return False, str(message)


def _extract_error(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return f"{response.status_code} {response.text[:200]}"
    return data.get("message") or data.get("error", {}).get("message") or str(data)
