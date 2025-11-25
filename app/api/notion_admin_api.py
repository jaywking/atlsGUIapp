from __future__ import annotations

from typing import Dict

from fastapi import APIRouter

from app.services.notion_schema_utils import ensure_all_schemas

router = APIRouter(prefix="/api/notion", tags=["notion-admin"])


@router.get("/update_schema_all")
async def update_schema_all() -> Dict[str, object]:
    updated, skipped, failed = await ensure_all_schemas()
    status = "success" if not failed else "partial"
    return {
        "status": status,
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
    }
