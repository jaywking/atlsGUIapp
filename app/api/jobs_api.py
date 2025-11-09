from fastapi import APIRouter
from app.services.logger import read_logs
from app.services.prune_logs import prune_logs


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/logs")
def get_job_logs():
    try:
        logs = read_logs()
        return {"status": "success", "message": "Logs retrieved", "logs": logs}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/prune")
def prune_job_logs():
    try:
        stats = prune_logs()
        return {
            "status": "success",
            "message": "Old log entries pruned",
            "stats": stats,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
