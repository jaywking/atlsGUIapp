from __future__ import annotations
import os
from datetime import datetime, timezone

LOG_DIR = "logs"
DEBUG_LOG_BASENAME = "debug_tools"
_DEBUG_ENABLED = os.environ.get("DEBUG_TOOLS", "false").lower() in ("true", "1", "t")

def debug_enabled() -> bool:
    """Return True only when DEBUG_TOOLS=1."""
    return _DEBUG_ENABLED

def debug_log(tool: str, message: str) -> None:
    """
    Append a debug entry when enabled.

    Each entry must include:
    - UTC timestamp
    - Tool name (uppercased)
    - Message body (verbatim)
    """
    if not _DEBUG_ENABLED:
        return
    os.makedirs(LOG_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    log_date = now.strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"{DEBUG_LOG_BASENAME}_{log_date}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{tool.upper()}]\n{message}\n\n")
