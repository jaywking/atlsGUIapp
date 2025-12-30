"""Application-wide logging helpers."""

from __future__ import annotations

import logging
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"


def configure_logging() -> None:
    """Attach a file handler that writes to ./logs/app.log."""

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text("", encoding="utf-8")  # reset per run for clean dev diagnostics

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    already_configured = any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", "") == str(LOG_FILE)
        for handler in root.handlers
    )

    if not already_configured:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
