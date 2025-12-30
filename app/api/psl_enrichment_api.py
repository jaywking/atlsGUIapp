from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.services.logger import log_job
from app.services.notion_locations import (
    fetch_master_by_id,
    fetch_production_locations_by_master,
    list_production_location_databases,
)
from app.services.psl_enrichment import stream_enrich_psl
from config import Config

router = APIRouter(prefix="/api/psl", tags=["psl_enrichment"])


@router.get("/enrich_stream")
async def enrich_stream(db_id: str = Query(...), production: str | None = Query(None)) -> StreamingResponse:
    async def _generator():
        async for line in stream_enrich_psl(db_id, production_label=production):
            if line is None:
                continue
            yield line if line.endswith("\n") else line + "\n"

    return StreamingResponse(_generator(), media_type="text/plain")


@router.get("/enrich_batch_stream")
async def enrich_batch_stream() -> StreamingResponse:
    productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
    if not productions_db_id:
        return StreamingResponse(iter(["error: Missing productions master database id\n"]), media_type="text/plain")

    try:
        prod_entries = await list_production_location_databases(productions_db_id)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to list production databases: {exc}"
        log_job("psl_enrichment", "discover", "error", err)
        return StreamingResponse(iter([f"error: {err}\n"]), media_type="text/plain")

    async def _generator():
        total_enriched = total_not_ready = total_ambiguous = total_errors = 0
        for entry in prod_entries:
            db_id = entry.get("locations_db_id")
            label = entry.get("display_name") or entry.get("production_title") or entry.get("production_id") or db_id or "Production"
            if not db_id:
                continue
            yield f"Production: {label} ({db_id})\n"
            async for line in stream_enrich_psl(db_id, production_label=label):
                if line.startswith("Done."):
                    parts = line.replace("Done.", "").strip().split()
                    for part in parts:
                        if part.startswith("enriched="):
                            total_enriched += int(part.split("=")[1])
                        elif part.startswith("skipped_not_ready="):
                            total_not_ready += int(part.split("=")[1])
                        elif part.startswith("ambiguous="):
                            total_ambiguous += int(part.split("=")[1])
                        elif part.startswith("errors="):
                            total_errors += int(part.split("=")[1])
                yield line if line.endswith("\n") else line + "\n"
        yield f"Batch done. enriched={total_enriched} skipped_not_ready={total_not_ready} ambiguous={total_ambiguous} errors={total_errors}\n"

    return StreamingResponse(_generator(), media_type="text/plain")


@router.get("/detail")
async def psl_detail(production_id: str | None = None, master_id: str | None = None) -> Dict[str, Any]:
    production_id = (production_id or "").strip()
    master_id = (master_id or "").strip()
    if not production_id or not master_id:
        return {"status": "error", "message": "production_id and master_id are required", "data": {}}

    productions_db_id = Config.PRODUCTIONS_MASTER_DB or Config.PRODUCTIONS_DB_ID or Config.NOTION_PRODUCTIONS_DB_ID
    if not productions_db_id:
        return {"status": "error", "message": "Missing productions master database id", "data": {}}

    try:
        prod_entries = await list_production_location_databases(productions_db_id)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to list production databases: {exc}"
        log_job("psl_detail", "discover", "error", err)
        return {"status": "error", "message": err, "data": {}}

    entry = next(
        (
            e
            for e in prod_entries
            if (e.get("production_id") or "").strip().lower() == production_id.lower()
            or (e.get("production_title") or "").strip().lower() == production_id.lower()
            or (e.get("display_name") or "").strip().lower() == production_id.lower()
        ),
        None,
    )
    if not entry:
        return {"status": "error", "message": f"Production {production_id} not found", "data": {}}

    locations_db_id = entry.get("locations_db_id") or ""
    if not locations_db_id:
        return {"status": "error", "message": f"No locations table found for {production_id}", "data": {}}

    master_row = await fetch_master_by_id(master_id)
    if not master_row:
        return {"status": "error", "message": f"Location {master_id} not found", "data": {}}

    master_page_id = master_row.get("row_id") or master_row.get("id") or ""
    if not master_page_id:
        return {"status": "error", "message": f"Location {master_id} not found", "data": {}}

    psl_rows = await fetch_production_locations_by_master(locations_db_id, master_page_id)

    records = []
    for row in psl_rows:
        records.append(
            {
                "psl_id": row.get("prod_loc_id") or "",
                "location_name": row.get("location_name") or row.get("name") or "",
                "address": row.get("address") or "",
                "city": row.get("city") or "",
                "state": row.get("state") or "",
                "notes": row.get("notes") or "",
                "status": row.get("status") or "",
                "location_op_status": row.get("location_op_status") or "",
                "created_time": row.get("created_time") or "",
                "updated_time": row.get("updated_time") or "",
                "notion_page_id": row.get("row_id") or row.get("id") or "",
            }
        )

    production_name = entry.get("display_name") or entry.get("production_title") or entry.get("production_id") or production_id
    context = {
        "production": {"id": entry.get("production_id") or production_id, "name": production_name},
        "location": {
            "master_id": master_id,
            "practical_name": master_row.get("practical_name") or master_row.get("name") or "",
            "city": master_row.get("city") or "",
            "state": master_row.get("state") or "",
        },
    }

    return {
        "status": "success",
        "message": f"Loaded PSL rows for {production_id} + {master_id}",
        "data": {"context": context, "rows": records},
    }
