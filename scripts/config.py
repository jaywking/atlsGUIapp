"""Configuration shim to keep legacy LocationSync scripts working."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / ".env"

# Load .env from repo root if present; silently continue when missing.
load_dotenv(dotenv_path=ENV_FILE if ENV_FILE.exists() else None)


class Config:
    """Expose environment-backed settings expected by legacy scripts."""

    NOTION_TOKEN: str | None = os.getenv("NOTION_TOKEN")
    GOOGLE_MAPS_API_KEY: str | None = os.getenv("GOOGLE_MAPS_API_KEY")
    LOG_PATH: str = os.getenv("LOG_PATH", str(Path("app/data/jobs.log")))

    @classmethod
    def ensure_log_path(cls) -> Path:
        """Ensure the log directory exists and return the resolved path."""
        log_path = Path(cls.LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path
