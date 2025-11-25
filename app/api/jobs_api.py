from fastapi import APIRouter

from app.services.logger import read_logs
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
