from __future__ import annotations

import time

from fastapi import APIRouter

from app.services.backfill_jobs import backfill_structured_addresses, facilities_backfill_job, locations_backfill_job
from app.services.job_manager import get_jobs, schedule_job
from app.services.logger import log_job, read_logs
from app.services.prune_logs import prune_logs


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _success(message: str, **payload) -> dict:
    response = {"status": "success", "message": message}
    response.update(payload)
    return response


def _error(exc: Exception) -> dict:
    return {"status": "error", "message": str(exc)}


@router.get("/logs")
def get_job_logs() -> dict:
    try:
        logs = read_logs()
        return _success("Logs retrieved", logs=logs)
    except Exception as exc:  # noqa: BLE001
        return _error(exc)


@router.post("/prune")
def prune_job_logs() -> dict:
    try:
        stats = prune_logs()
        return _success("Old log entries pruned", stats=stats)
    except Exception as exc:  # noqa: BLE001
        return _error(exc)


@router.get("/facilities/backfill")
async def schedule_facilities_backfill() -> dict:
    try:
        job_id = schedule_job("facilities_backfill", facilities_backfill_job)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to schedule facilities backfill: {exc}"
        log_job("jobs", "facilities_backfill", "error", err)
        return {"status": "error", "message": err}

    log_job("jobs", "facilities_backfill", "start", f"Scheduled facilities backfill job_id={job_id}")
    return {
        "status": "success",
        "message": "Facilities backfill job scheduled.",
        "data": {"job_id": job_id},
    }


@router.get("/locations/backfill")
async def schedule_locations_backfill() -> dict:
    try:
        job_id = schedule_job("locations_backfill", locations_backfill_job)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to schedule locations backfill: {exc}"
        log_job("jobs", "locations_backfill", "error", err)
        return {"status": "error", "message": err}

    log_job("jobs", "locations_backfill", "start", f"Scheduled locations backfill job_id={job_id}")
    return {
        "status": "success",
        "message": "Locations backfill job scheduled.",
        "data": {"job_id": job_id},
    }


@router.get("/locations/structured_backfill")
async def schedule_structured_backfill() -> dict:
    try:
        job_id = schedule_job("locations_structured_backfill", backfill_structured_addresses)
    except Exception as exc:  # noqa: BLE001
        err = f"Failed to schedule structured address backfill: {exc}"
        log_job("jobs", "locations_structured_backfill", "error", err)
        return {"status": "error", "message": err}

    log_job("jobs", "locations_structured_backfill", "start", f"Scheduled structured address backfill job_id={job_id}")
    return {
        "status": "success",
        "message": "Structured address backfill job scheduled.",
        "data": {"job_id": job_id},
    }


@router.get("/")
async def list_jobs() -> dict:
    started = time.perf_counter()
    jobs = await get_jobs()
    duration_ms = int((time.perf_counter() - started) * 1000)
    log_job("jobs", "list", "success", f"Returned {len(jobs)} jobs in {duration_ms} ms")
    return {"status": "success", "message": f"Returned {len(jobs)} jobs", "data": jobs}
