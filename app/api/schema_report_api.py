from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.schema_report import generate_schema_report_stream

router = APIRouter(prefix="/api/schema_report", tags=["schema-report"])


@router.get("/stream")
async def schema_report_stream() -> StreamingResponse:
    async def streamer():
        async for line in generate_schema_report_stream():
            yield line
    return StreamingResponse(streamer(), media_type="text/plain")

