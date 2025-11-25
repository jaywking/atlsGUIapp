from fastapi import APIRouter

import sys

from app.services.logger import log_job
from scripts import fetch_medical_facilities as run_fetch_medical_facilities

router = APIRouter(prefix="/api/facilities", tags=["facilities"])


def _run_facility_job() -> dict:
    original_argv = sys.argv[:]  # avoid argparse consuming uvicorn arguments
    sys.argv = ["fetch_medical_facilities"]
    try:
        result = run_fetch_medical_facilities()
        message = str(result)
        log_job(category="facilities", action="fetch", status="success", message=message)
        return {"status": "success", "message": message}
    except BaseException as exc:  # noqa: BLE001
        err = f"{exc}"
        log_job(category="facilities", action="fetch", status="error", message=err)
        return {"status": "error", "message": err}
    finally:
        sys.argv = original_argv


@router.post("/fetch")
def fetch_facilities() -> dict:
    return _run_facility_job()
