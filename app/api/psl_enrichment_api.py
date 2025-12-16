from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.services.logger import log_job
from app.services.notion_locations import list_production_location_databases
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
