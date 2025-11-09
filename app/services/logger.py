import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from app.services.prune_logs import prune_logs


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_FILE = DATA_DIR / "jobs.log"


def _ensure_paths() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.touch()


def log_job(category: str, action: str, status: str, message: str) -> None:
    """
    Append a job entry to the JSONL log file.

    Each line is a JSON object including:
    - timestamp (ISO 8601)
    - category
    - action
    - status
    - message
    """
    _ensure_paths()
    entry: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "category": category,
        "action": action,
        "status": status,
        "message": message,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    try:
        prune_logs()
    except Exception:
        # Pruning failures should never block log writes
        pass


def read_logs() -> List[Dict[str, Any]]:
    """Return all log entries as a list of dicts. Gracefully handle empty/missing files."""
    _ensure_paths()
    entries: List[Dict[str, Any]] = []
    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                # Skip malformed lines but keep processing
                continue
    return entries
