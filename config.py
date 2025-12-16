from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

# Load .env from repo root if present; silently continue when missing.
load_dotenv(dotenv_path=ENV_FILE if ENV_FILE.exists() else None)


class Config:
    """Expose environment-backed settings expected by legacy scripts."""

    NOTION_TOKEN: str | None = os.getenv("NOTION_TOKEN")
    GOOGLE_MAPS_API_KEY: str | None = os.getenv("GOOGLE_MAPS_API_KEY")
    LOG_PATH: str = os.getenv("LOG_PATH", str(Path("app/data/jobs.log")))
    LOCATIONS_MASTER_DB: str | None = os.getenv("LOCATIONS_MASTER_DB") or os.getenv("NOTION_LOCATIONS_DB_ID")
    MEDICAL_FACILITIES_DB: str | None = os.getenv("MEDICAL_FACILITIES_DB") or os.getenv("NOTION_MEDICAL_DB_ID")
    PRODUCTIONS_MASTER_DB: str | None = os.getenv("PRODUCTIONS_MASTER_DB") or os.getenv("NOTION_PRODUCTIONS_DB_ID")
    PRODUCTIONS_DB_ID: str | None = os.getenv("PRODUCTIONS_DB_ID") or os.getenv("NOTION_PRODUCTIONS_DB_ID")
    NOTION_DATABASES_PARENT_PAGE_ID: str | None = os.getenv("NOTION_DATABASES_PARENT_PAGE_ID")
    STATUS_ON_RESET: str | None = os.getenv("STATUS_ON_RESET", "Ready")
    STATUS_AFTER_MATCHING: str | None = os.getenv("STATUS_AFTER_MATCHING", "Matched")
    STATUS_ERROR: str | None = os.getenv("STATUS_ERROR", "Error")
    PROD_MASTER_LINK_PROP: str | None = os.getenv("PROD_MASTER_LINK_PROP", "LocationsMasterID")
    PROD_MASTER_TITLE_PROP: str | None = os.getenv("PROD_MASTER_TITLE_PROP", "ProductionID")
    PROD_MASTER_ABBR_PROP: str | None = os.getenv("PROD_MASTER_ABBR_PROP", "Abbreviation")
    DB_HOST: str | None = os.getenv("DB_HOST")
    DB_PORT: str | None = os.getenv("DB_PORT")
    DB_NAME: str | None = os.getenv("DB_NAME")
    DB_USER: str | None = os.getenv("DB_USER")
    DB_PASSWORD: str | None = os.getenv("DB_PASSWORD")

    @classmethod
    def ensure_log_path(cls) -> Path:
        """Ensure the log directory exists and return the resolved path."""
        log_path = Path(cls.LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path

    @classmethod
    def setup(cls) -> None:
        """Compatibility shim for legacy callers; values are already loaded at import."""
        return