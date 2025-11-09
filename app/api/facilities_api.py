from fastapi import APIRouter
from scripts import fetch_medical_facilities

router = APIRouter(prefix="/api/facilities", tags=["facilities"])

@router.post("/fetch")
def fetch_facilities():
    try:
        result = fetch_medical_facilities.main()
        return {"status": "success", "message": str(result)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
