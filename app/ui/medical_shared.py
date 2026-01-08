from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Tuple

import httpx

from app.services.api_client import api_url

logger = logging.getLogger(__name__)


async def load_medical_facilities(limit: int = 2000) -> List[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(api_url("/api/medicalfacilities/all"), params={"limit": limit})
        response.raise_for_status()
        payload = response.json() or {}
        if payload.get("status") != "success":
            raise ValueError(payload.get("message") or "Unable to load medical facilities")
        return payload.get("data") or []
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unable to load medical facilities: %s", exc)
        return []


async def load_locations_master_map() -> Dict[str, Dict[str, str]]:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(api_url("/api/locations/master"))
        response.raise_for_status()
        payload = response.json() or {}
        if payload.get("status") != "success":
            raise ValueError(payload.get("message") or "Unable to load locations")
        rows = payload.get("data") or []
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unable to load locations master: %s", exc)
        return {}

    mapping: Dict[str, Dict[str, str]] = {}
    for row in rows:
        page_id = row.get("row_id") or row.get("id") or ""
        master_id = row.get("prod_loc_id") or row.get("master_id") or ""
        name = row.get("practical_name") or row.get("name") or ""
        if not page_id:
            continue
        mapping[page_id] = {
            "master_id": master_id,
            "name": name,
        }
    return mapping


async def load_production_location_map() -> Dict[str, List[Dict[str, str]]]:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(api_url("/api/productions/fetch"))
        response.raise_for_status()
        payload = response.json() or {}
        if payload.get("status") != "success":
            raise ValueError(payload.get("message") or "Unable to load productions")
        productions = payload.get("data") or []
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unable to load productions: %s", exc)
        return {}

    production_ids = [row.get("ProductionID") for row in productions if row.get("ProductionID")]
    mapping: Dict[str, Dict[str, str]] = {}
    semaphore = asyncio.Semaphore(5)

    async with httpx.AsyncClient(timeout=20.0) as client:
        async def _fetch(prod_id: str) -> None:
            async with semaphore:
                try:
                    response = await client.get(api_url("/api/productions/detail"), params={"production_id": prod_id})
                    response.raise_for_status()
                    payload = response.json() or {}
                    if payload.get("status") != "success":
                        return
                    data = payload.get("data") or {}
                    production = data.get("production") or {}
                    production_name = production.get("Name") or prod_id
                    locations = data.get("locations") or []
                    for loc in locations:
                        master_id = loc.get("master_id") or ""
                        if not master_id:
                            continue
                        mapping.setdefault(master_id, {})[prod_id] = production_name
                except Exception:
                    return

        tasks = [asyncio.create_task(_fetch(prod_id)) for prod_id in production_ids]
        if tasks:
            await asyncio.gather(*tasks)

    return {master_id: [{"id": pid, "name": name} for pid, name in entries.items()] for master_id, entries in mapping.items()}


def build_facility_associations(
    facility: Dict[str, Any],
    location_map: Dict[str, Dict[str, str]],
    production_map: Dict[str, List[Dict[str, str]]],
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    locations: List[Dict[str, str]] = []
    seen_locations: set[str] = set()
    for page_id in facility.get("locations_master_ids") or []:
        loc_info = location_map.get(page_id) or {}
        master_id = loc_info.get("master_id") or ""
        if not master_id or master_id in seen_locations:
            continue
        seen_locations.add(master_id)
        locations.append(
            {
                "master_id": master_id,
                "name": loc_info.get("name") or "",
            }
        )

    productions: Dict[str, str] = {}
    for loc in locations:
        for prod in production_map.get(loc["master_id"], []):
            prod_id = prod.get("id") or ""
            if prod_id:
                productions[prod_id] = prod.get("name") or prod_id

    production_list = [{"id": pid, "name": name} for pid, name in productions.items()]
    production_list.sort(key=lambda item: (item.get("name") or "").lower())
    locations.sort(key=lambda item: (item.get("master_id") or "").lower())
    return production_list, locations
