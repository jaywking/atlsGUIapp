from fastapi import APIRouter

from app.services.logger import log_job
from scripts import process_new_locations

router = APIRouter(prefix="/api/locations", tags=["locations"])


def _run_location_job() -> dict:
    try:
        result = process_new_locations.main()
        message = str(result)
        log_job(category="locations", action="process", status="success", message=message)
        return {"status": "success", "message": message}
    except Exception as exc:  # noqa: BLE001
        err = str(exc)
        log_job(category="locations", action="process", status="error", message=err)
        return {"status": "error", "message": err}


@router.post("/process")
def process_locations() -> dict:
    return _run_location_job()
