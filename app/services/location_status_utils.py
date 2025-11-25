from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

STATUS_UNRESOLVED = "Unresolved"
STATUS_READY = "Ready"
STATUS_MATCHED = "Matched"


def normalize_status_for_write(place_id: Optional[str], existing_status: Optional[str]) -> str:
    """
    Centralized status guard:
    - No place_id => Unresolved
    - place_id present => keep Matched, else Ready
    - Always returns a non-empty status
    """
    old = existing_status or ""
    if not place_id:
        new_status = STATUS_UNRESOLVED
    elif existing_status == STATUS_MATCHED:
        new_status = STATUS_MATCHED
    else:
        new_status = STATUS_READY

    if new_status != old:
        logger.debug("Auto-normalized status: %s -> %s, place_id=%s", old or "None", new_status, place_id or "None")
    return new_status


def log_status_applied(old_status: Optional[str], new_status: str, place_id: Optional[str], matched: bool, explicit: Optional[str]) -> None:
    logger.debug(
        "Auto-normalized status: %s -> %s, place_id=%s, matched=%s, explicit=%s",
        old_status or "None",
        new_status,
        place_id or "None",
        matched,
        explicit or "None",
    )
