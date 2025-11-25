from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Awaitable, Callable, Dict, List

from app.services.logger import log_job

JobCallable = Callable[[], Awaitable[Any]]

_jobs: Dict[str, Dict[str, Any]] = {}
_lock = asyncio.Lock()
_MAX_COMPLETED = 50


def _prune_completed() -> None:
    completed_ids = [job_id for job_id, meta in _jobs.items() if meta.get("status") in {"success", "error"}]
    if len(completed_ids) <= _MAX_COMPLETED:
        return
    # keep the most recent completed jobs
    completed_ids.sort(key=lambda jid: _jobs[jid].get("start_time", 0), reverse=True)
    for job_id in completed_ids[_MAX_COMPLETED :]:
        _jobs.pop(job_id, None)


async def _record_job(job_id: str, job_type: str, status: str, message: str = "", result: Any = None) -> None:
    async with _lock:
        meta = _jobs.get(job_id, {})
        meta.update({"status": status, "message": message, "result": result})
        _jobs[job_id] = meta
        _prune_completed()


def _log_start(job_id: str, job_type: str) -> None:
    log_job("jobs", "start", "success", f"operation={job_type} job_id={job_id}")


def _log_result(job_id: str, job_type: str, status: str, duration_ms: int, message: str = "") -> None:
    log_job("jobs", "complete", status, f"operation={job_type} job_id={job_id} duration_ms={duration_ms} message={message}")


def schedule_job(job_type: str, coro: JobCallable) -> str:
    """
    Schedule an async job to run in the background.

    Returns a job_id immediately.
    """
    job_id = str(uuid.uuid4())
    now = time.perf_counter()
    _jobs[job_id] = {"job_id": job_id, "type": job_type, "status": "running", "start_time": now, "result": None, "message": ""}
    _log_start(job_id, job_type)

    async def runner() -> None:
        try:
            await coro()
            duration_ms = int((time.perf_counter() - now) * 1000)
            await _record_job(job_id, job_type, "success")
            _log_result(job_id, job_type, "success", duration_ms)
        except Exception as exc:  # noqa: BLE001
            duration_ms = int((time.perf_counter() - now) * 1000)
            await _record_job(job_id, job_type, "error", message=str(exc))
            _log_result(job_id, job_type, "error", duration_ms, message=str(exc))

    asyncio.create_task(runner())
    return job_id


async def get_jobs() -> List[Dict[str, Any]]:
    async with _lock:
        return list(_jobs.values())
