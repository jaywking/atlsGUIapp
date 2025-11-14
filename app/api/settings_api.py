import asyncio
import logging
import os
from fastapi import APIRouter

from app.services.config_tester import (
    check_maps_connection,
    check_notion_connection,
    run_with_timing,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.post("/test_connections")
async def test_connections():
    notion_token = os.getenv("NOTION_TOKEN")
    notion_db_id = os.getenv("NOTION_LOCATIONS_DB_ID")
    productions_db_id = os.getenv("NOTION_PRODUCTIONS_DB_ID")
    maps_key = os.getenv("GOOGLE_MAPS_API_KEY")

    logger.info(
        "Received settings test request (notion_token=%s, maps_key=%s, productions_db_id=%s)",
        bool(notion_token),
        bool(maps_key),
        bool(productions_db_id),
    )

    timing = {
        "notion_locations": None,
        "notion_productions": None,
        "google_maps": None,
    }

    try:
        notion_task = asyncio.create_task(
            run_with_timing(check_notion_connection(notion_token, notion_db_id))
        )
        maps_task = asyncio.create_task(
            run_with_timing(check_maps_connection(maps_key))
        )

        productions_task = None
        productions_ok: bool
        productions_msg: str
        if productions_db_id:
            productions_task = asyncio.create_task(
                run_with_timing(
                    check_notion_connection(notion_token, productions_db_id)
                )
            )
        else:
            productions_ok, productions_msg = False, "Missing Productions DB ID"
            timing["notion_productions"] = 0.0

        (notion_result, notion_duration) = await notion_task
        notion_ok, notion_msg = notion_result
        timing["notion_locations"] = round(notion_duration, 3)

        (maps_result, maps_duration) = await maps_task
        maps_ok, maps_msg = maps_result
        timing["google_maps"] = round(maps_duration, 3)

        if productions_task:
            (productions_result, productions_duration) = await productions_task
            productions_ok, productions_msg = productions_result
            timing["notion_productions"] = round(productions_duration, 3)

        overall_ok = notion_ok and maps_ok and productions_ok
        response = {
            "status": "success" if overall_ok else "error",
            "message": "Connections verified"
            if overall_ok
            else "Check credentials",
            "notion": "Connected" if notion_ok else notion_msg,
            "productions": "Connected" if productions_ok else productions_msg,
            "maps": "Connected" if maps_ok else maps_msg,
            "timing": timing,
        }
        return response
    except Exception as exc:  # noqa: BLE001
        logger.exception("Settings diagnostics failed")
        return {
            "status": "error",
            "message": f"Settings diagnostics failed: {exc}",
            "notion": "Error",
            "productions": "Error",
            "maps": "Error",
            "timing": timing,
        }
