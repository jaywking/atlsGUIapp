from fastapi import APIRouter
from scripts import process_new_locations
from app.services.logger import log_job

router = APIRouter(prefix="/api/locations", tags=["locations"])

@router.post("/process")
def process_locations():
    try:
        result = process_new_locations.main()  # Call your existing script
        message = str(result)
        log_job(category="locations", action="process", status="success", message=message)
        return {"status": "success", "message": message}
    except Exception as e:
        err = str(e)
        log_job(category="locations", action="process", status="error", message=err)
        return {"status": "error", "message": err}
