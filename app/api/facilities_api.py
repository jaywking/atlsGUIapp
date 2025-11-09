from fastapi import APIRouter
from scripts import fetch_medical_facilities
from app.services.logger import log_job

router = APIRouter(prefix="/api/facilities", tags=["facilities"])

@router.post("/fetch")
def fetch_facilities():
    try:
        result = fetch_medical_facilities.main()
        message = str(result)
        log_job(category="facilities", action="fetch", status="success", message=message)
        return {"status": "success", "message": message}
    except Exception as e:
        err = str(e)
        log_job(category="facilities", action="fetch", status="error", message=err)
        return {"status": "error", "message": err}
