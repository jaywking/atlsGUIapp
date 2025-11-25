from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

import aiofiles

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FACILITIES_CACHE_PATH = DATA_DIR / "medical_facilities_cache.json"
LOCATIONS_CACHE_PATH = DATA_DIR / "locations_cache.json"
DEFAULT_MAX_AGE_SECONDS = 3600


def _utc_now() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


async def _load_cache(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            text = await f.read()
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        return {}
    return {}


async def _save_cache(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(payload, ensure_ascii=False, indent=2))


async def load_facilities_cache() -> Dict[str, Any]:
    return await _load_cache(FACILITIES_CACHE_PATH)


async def load_locations_cache() -> Dict[str, Any]:
    return await _load_cache(LOCATIONS_CACHE_PATH)


async def save_facilities_cache(data: Dict[str, Any]) -> None:
    await _save_cache(FACILITIES_CACHE_PATH, data)


async def save_locations_cache(data: Dict[str, Any]) -> None:
    await _save_cache(LOCATIONS_CACHE_PATH, data)


def is_cache_stale(cache: Dict[str, Any], max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS) -> bool:
    timestamp = cache.get("timestamp")
    if not timestamp:
        return True
    try:
        ts = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return True
    threshold = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
    return ts < threshold

