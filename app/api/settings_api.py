import logging
import os
from fastapi import APIRouter

from app.services.config_tester import check_maps_connection, check_notion_connection


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.post("/test_connections")
async def test_connections():
    notion_token = os.getenv("NOTION_TOKEN")
    notion_db_id = os.getenv("NOTION_LOCATIONS_DB_ID")
    maps_key = os.getenv("GOOGLE_MAPS_API_KEY")

    logger.info(
        "Received settings test request (notion_token=%s, maps_key=%s)",
        bool(notion_token),
        bool(maps_key),
    )

    notion_ok, notion_msg = await check_notion_connection(notion_token, notion_db_id)
    maps_ok, maps_msg = await check_maps_connection(maps_key)

    overall_ok = notion_ok and maps_ok
    response = {
        "status": "success" if overall_ok else "error",
        "message": "Connections verified" if overall_ok else "Check credentials",
        "notion": "Connected" if notion_ok else notion_msg,
        "maps": "Connected" if maps_ok else maps_msg,
    }
    return response
