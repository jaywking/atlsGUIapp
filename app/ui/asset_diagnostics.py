from __future__ import annotations

from typing import Any, Dict, List, Set
from urllib.parse import urlparse


def asset_prefix(asset_id: str) -> str:
    return (asset_id or "")[:3].upper()


def is_valid_url(value: str) -> bool:
    if not value:
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def compute_hero_conflicts(assets: List[Dict[str, Any]]) -> Set[str]:
    hero_by_location: Dict[str, List[str]] = {}
    for asset in assets:
        asset_id = asset.get("asset_id") or ""
        if asset_prefix(asset_id) != "PIC":
            continue
        if (asset.get("visibility_flag") or "") != "Hero":
            continue
        for loc_id in asset.get("locations_master_ids") or []:
            hero_by_location.setdefault(loc_id, []).append(asset_id)

    conflicts: Set[str] = set()
    for asset_ids in hero_by_location.values():
        if len(asset_ids) > 1:
            conflicts.update(asset_ids)
    return conflicts


def compute_asset_diagnostics(
    asset: Dict[str, Any],
    *,
    hero_conflicts: Set[str] | None = None,
    surfaced_in_location_detail: bool = False,
) -> List[Dict[str, str]]:
    diags: List[Dict[str, str]] = []
    asset_id = asset.get("asset_id") or ""
    prefix = asset_prefix(asset_id)
    production_ids = asset.get("production_ids") or []
    prod_loc_ids = asset.get("prod_loc_ids") or []
    master_ids = asset.get("locations_master_ids") or []

    # Missing or weak context
    if prefix == "PIC" and production_ids and not master_ids:
        diags.append({"severity": "INFO", "label": "Missing LocationsMasterID"})
    if prefix == "PIC" and production_ids and not prod_loc_ids:
        diags.append({"severity": "INFO", "label": "Missing ProdLocID"})
    if prefix == "FOL" and not prod_loc_ids:
        diags.append({"severity": "INFO", "label": "Missing ProdLocID"})

    # Metadata gaps
    if prefix == "PIC" and not (asset.get("asset_name") or "").strip():
        diags.append({"severity": "CHECK", "label": "Missing Asset Name"})
    if prefix == "PIC" and not (asset.get("notes") or "").strip():
        diags.append({"severity": "INFO", "label": "Missing Notes"})
    if prefix == "PIC" and not (asset.get("hazard_types") or []):
        diags.append({"severity": "INFO", "label": "No Hazard Types"})
    if prefix == "AST" and not (asset.get("asset_categories") or []):
        diags.append({"severity": "CHECK", "label": "No Asset Category"})

    # Visibility inconsistencies
    if surfaced_in_location_detail and (asset.get("visibility_flag") or "") == "Hidden":
        diags.append({"severity": "CHECK", "label": "Hidden asset surfaced"})
    if hero_conflicts and asset_id in hero_conflicts:
        diags.append({"severity": "WARNING", "label": "Multiple Hero photos for location"})

    # External URL issues
    external_url = (asset.get("external_url") or "").strip()
    if not external_url:
        diags.append({"severity": "WARNING", "label": "Missing External URL"})
    elif not is_valid_url(external_url):
        diags.append({"severity": "WARNING", "label": "Invalid External URL"})

    return diags


def severity_counts(diags: List[Dict[str, str]]) -> Dict[str, int]:
    counts = {"INFO": 0, "CHECK": 0, "WARNING": 0}
    for diag in diags:
        severity = (diag.get("severity") or "INFO").upper()
        if severity in counts:
            counts[severity] += 1
    return {k: v for k, v in counts.items() if v > 0}
