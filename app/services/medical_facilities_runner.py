from __future__ import annotations

from typing import Any, AsyncGenerator, Dict

from app.services.debug_logger import debug_enabled, debug_log
from app.services.medical_facilities import generate_nearby_medical_facilities
from app.services.notion_locations import fetch_location_pages_raw, normalize_location


async def stream_generate_medical_facilities_all() -> AsyncGenerator[str, None]:
    """Stream summary-only generation of medical facilities for eligible LM rows."""
    try:
        pages = await fetch_location_pages_raw()
    except Exception as exc:  # noqa: BLE001
        yield f"error: failed to load Locations Master: {exc}\n"
        return

    total = len(pages)
    yield f"Scanning Locations Master ({total} rows)...\n"

    counts: Dict[str, int] = {
        "eligible": 0,
        "processed": 0,
        "skipped_er": 0,
        "skipped_missing": 0,
        "errors": 0,
    }

    for page in pages:
        page_id = page.get("id") or ""
        props = page.get("properties") or {}
        er_rel = props.get("ER", {}).get("relation") or []
        if er_rel:
            counts["skipped_er"] += 1
            if debug_enabled():
                debug_log("MEDICAL_FACILITIES_RUN", f"skip (ER populated) lm={page_id} er_count={len(er_rel)}")
            continue

        normalized = normalize_location(page)
        lat = normalized.get("latitude")
        lon = normalized.get("longitude")
        place_id = normalized.get("place_id")

        has_coords = lat is not None and lon is not None
        has_place = bool(place_id)
        if not (has_coords or has_place):
            counts["skipped_missing"] += 1
            if debug_enabled():
                debug_log("MEDICAL_FACILITIES_RUN", f"skip (missing geo/place_id) lm={page_id}")
            continue

        counts["eligible"] += 1

        try:
            result = await generate_nearby_medical_facilities(page_id)
            if isinstance(result, dict) and result.get("status") == "error":
                counts["errors"] += 1
                if debug_enabled():
                    debug_log("MEDICAL_FACILITIES_RUN", f"error lm={page_id} message={result.get('message')}")
                continue
            counts["processed"] += 1
            if debug_enabled():
                debug_log("MEDICAL_FACILITIES_RUN", f"processed lm={page_id}")
        except Exception as exc:  # noqa: BLE001
            counts["errors"] += 1
            if debug_enabled():
                debug_log("MEDICAL_FACILITIES_RUN", f"error lm={page_id} exception={exc}")
            continue

    summary = (
        f"Done. total_scanned={total} eligible={counts['eligible']} "
        f"processed={counts['processed']} skipped_er={counts['skipped_er']} "
        f"skipped_missing={counts['skipped_missing']} errors={counts['errors']}\n"
    )
    yield summary
