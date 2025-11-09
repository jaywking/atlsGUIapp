from fastapi import APIRouter
from scripts import process_new_locations

router = APIRouter(prefix="/api/locations", tags=["locations"])

@router.post("/process")
def process_locations():
    try:
        result = process_new_locations.main()  # Call your existing script
        return {"status": "success", "message": str(result)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
