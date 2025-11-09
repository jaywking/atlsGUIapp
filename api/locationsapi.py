from fastapi import APIRouter

router = APIRouter()

@router.post("/process_locations")
def process_locations():
    # Placeholder for connection to process_new_locations.py
    return {"status": "ok", "message": "Locations processed (placeholder)"}