from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List

import httpx

from app.services.address_normalizer import is_empty
from app.services.logger import log_job
from app.services.notion_locations import _headers, update_location_page


FIELD_TO_NOTION_PROP = {
    # Locations Master property names (lowercase keys in this DB)
    "address1": "address1",
    "address2": "address2",
    "address3": "address3",
    "city": "city",
    "state": "state",
    "zip": "zip",
    "country": "country",
    "place_id": "Place_ID",
    "name": "Name",
}


def _rich_text(value: str) -> Dict[str, Any]:
    return {"rich_text": [{"text": {"content": value}}]}


def _build_properties(row_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    props: Dict[str, Any] = {}
    for key, value in fields.items():
        notion_key = FIELD_TO_NOTION_PROP.get(key)
        if not notion_key:
            continue
        if is_empty(value):
            if isinstance(value, str) and value.strip() == "":
                log_job(
                    "address_writeback",
                    "whitespace_detected",
                    "success",
                    f"row_id={row_id} field={key} whitespace_only",
                )
            continue
        props[notion_key] = _rich_text(str(value))
    return props


async def update_master_fields(row_id: str, fields: Dict[str, Any]) -> None:
    props = _build_properties(row_id, fields)
    if not props:
        return
    await update_location_page(row_id, props)


async def archive_master_rows(
    row_ids: List[str],
    status_name: str = "ARCHIVED",
    throttle_seconds: float = 0.2,
) -> Dict[str, int]:
    attempted = len(row_ids)
    successful = 0
    failed = 0
    last_request_ts = 0.0
    progress: List[Dict[str, int]] = []
    archived_ids: List[str] = []

    for rid in row_ids:
        elapsed = time.perf_counter() - last_request_ts
        if elapsed < throttle_seconds:
            await asyncio.sleep(throttle_seconds - elapsed)

        props = {"Status": {"status": {"name": status_name}}}
        delays = [0.1, 0.2, 0.4, 0.8]
        for attempt, delay in enumerate(delays, start=1):
            try:
                await update_location_page(rid, props)
                successful += 1
                archived_ids.append(rid)
                log_job("dedup_resolve", "archive", "success", f"row_id={rid} status={status_name}")
                break
            except httpx.HTTPStatusError as exc:
                log_job(
                    "dedup_resolve",
                    "archive_response",
                    "error",
                    f"row_id={rid} status={exc.response.status_code} body={exc.response.text}",
                )
                if "Invalid status option" in exc.response.text or "Status is expected to be status" in exc.response.text:
                    # Fallback: hard archive flag if Status option missing
                    try:
                        headers = _headers()
                        url = f"https://api.notion.com/v1/pages/{rid}"
                        async with httpx.AsyncClient(timeout=15.0) as client:
                            resp = await client.patch(url, headers=headers, json={"archived": True})
                            if resp.is_success:
                                successful += 1
                                archived_ids.append(rid)
                                log_job("dedup_resolve", "archive_flag", "success", f"row_id={rid} archived=true")
                                break
                            log_job("dedup_resolve", "archive_flag", "error", f"row_id={rid} status={resp.status_code} body={resp.text}")
                    except Exception as flag_exc:  # noqa: BLE001
                        log_job("dedup_resolve", "archive_flag", "error", f"row_id={rid} error={flag_exc}")
                if attempt == len(delays):
                    failed += 1
                else:
                    await asyncio.sleep(delay)
            except Exception as exc:  # noqa: BLE001
                failed += 1 if attempt == len(delays) else failed
                log_job("dedup_resolve", "archive", "error", f"row_id={rid} error={exc}")
                if attempt < len(delays):
                    await asyncio.sleep(delay)

        last_request_ts = time.perf_counter()
        processed = successful + failed
        if processed % 5 == 0 or processed == attempted:
            progress.append({"processed": processed, "attempted": attempted, "successful": successful, "failed": failed})

    log_job(
        "dedup_resolve",
        "archive_summary",
        "success",
        f"attempted={attempted} successful={successful} failed={failed}",
    )
    return {"attempted": attempted, "successful": successful, "failed": failed, "progress": progress, "archived_ids": archived_ids}


async def write_address_updates(updates: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Apply address field updates to Notion with throttling and backoff.
    """
    attempted = len(updates)
    successful = 0
    failed = 0
    last_request_ts = 0.0
    progress_ticks: List[Dict[str, int]] = []

    throttle_seconds = 0.2  # ~5 req/sec target (previously ~0.34s)

    for item in updates:
        row_id = item.get("row_id") or ""
        fields = item.get("fields") or {}
        if not row_id or not fields:
            failed += 1
            continue

        # Throttle to ~5 req/sec
        elapsed = time.perf_counter() - last_request_ts
        if elapsed < throttle_seconds:
            await asyncio.sleep(throttle_seconds - elapsed)

        properties = _build_properties(row_id, fields)
        if not properties:
            failed += 1
            continue

        delays = [0.1, 0.2, 0.4, 0.8]
        attempt_ok = False
        for attempt, delay in enumerate(delays, start=1):
            try:
                await update_location_page(row_id, properties)
                attempt_ok = True
                successful += 1
                log_job(
                    "address_writeback",
                    "update",
                    "success",
                    f"row_id={row_id} fields={list(fields.keys())}",
                )
                break
            except Exception as exc:  # noqa: BLE001
                if attempt == len(delays):
                    failed += 1
                    log_job(
                        "address_writeback",
                        "update",
                        "error",
                        f"row_id={row_id} fields={list(fields.keys())} error={exc}",
                    )
                else:
                    await asyncio.sleep(delay)
        last_request_ts = time.perf_counter()

        processed = successful + failed
        if processed % 5 == 0 or processed == attempted:
            progress_entry = {"processed": processed, "attempted": attempted, "successful": successful, "failed": failed}
            progress_ticks.append(progress_entry)
            log_job(
                "address_writeback",
                "progress",
                "success",
                f"processed={processed}/{attempted} successful={successful} failed={failed}",
            )

    log_job(
        "address_writeback",
        "summary",
        "success",
        f"attempted={attempted} successful={successful} failed={failed}",
    )
    return {
        "attempted": attempted,
        "successful": successful,
        "failed": failed,
        "progress": progress_ticks,
    }


async def update_production_master_links(
    updates: List[Dict[str, Any]],
    relation_property: str = "LocationsMasterID",
    throttle_seconds: float = 0.2,
) -> Dict[str, int]:
    attempted = len(updates)
    successful = 0
    failed = 0
    last_request_ts = 0.0
    progress: List[Dict[str, int]] = []

    for item in updates:
        row_id = item.get("prod_loc_id") or item.get("row_id") or ""
        new_master = item.get("new_master_id")
        if not row_id or not new_master:
            failed += 1
            continue

        elapsed = time.perf_counter() - last_request_ts
        if elapsed < throttle_seconds:
            await asyncio.sleep(throttle_seconds - elapsed)

        props = {relation_property: {"relation": [{"id": new_master}]}}
        delays = [0.1, 0.2, 0.4, 0.8]
        for attempt, delay in enumerate(delays, start=1):
            try:
                await update_location_page(row_id, props)
                successful += 1
                log_job(
                    "dedup_resolve",
                    "prod_pointer_updated",
                    "success",
                    f"prod_loc_id={row_id} new_master_id={new_master}",
                )
                break
            except Exception as exc:  # noqa: BLE001
                if attempt == len(delays):
                    failed += 1
                    log_job(
                        "dedup_resolve",
                        "prod_pointer_update_failed",
                        "error",
                        f"prod_loc_id={row_id} error={exc}",
                    )
                else:
                    await asyncio.sleep(delay)

        last_request_ts = time.perf_counter()
        processed = successful + failed
        if processed % 5 == 0 or processed == attempted:
            progress.append({"processed": processed, "attempted": attempted, "successful": successful, "failed": failed})

    log_job(
        "dedup_resolve",
        "prod_pointer_summary",
        "success",
        f"attempted={attempted} successful={successful} failed={failed}",
    )
    return {"attempted": attempted, "successful": successful, "failed": failed, "progress": progress}
