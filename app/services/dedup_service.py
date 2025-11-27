from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def _normalize_str(value: Any) -> str:
    """Lowercase, trim, and collapse internal whitespace for comparisons."""
    return " ".join(str(value or "").strip().lower().split())


def _normalize_zip(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits:
        return digits[:5]
    return _normalize_str(raw)


def _to_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def dedup_group_key(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize master row fields used for dedup heuristics.
    Aligns with normalized Locations Master schema field names.
    """
    return {
        "place_id": _normalize_str(row.get("place_id")),
        "address1": _normalize_str(row.get("address1")),
        "city": _normalize_str(row.get("city")),
        "state": _normalize_str(row.get("state")),
        "zip": _normalize_zip(row.get("zip")),
        "country": (row.get("country") or "").strip().upper(),
        "latitude": _to_float(row.get("latitude")),
        "longitude": _to_float(row.get("longitude")),
    }


def _reason_rank(reason: Optional[str]) -> int:
    order = {
        "place_id": 0,
        "address_full": 1,
        "address_no_zip": 2,
        "coordinate_proximity": 3,
    }
    return order.get(reason or "", 99)


def _best_reason(*reasons: Optional[str]) -> Optional[str]:
    best: Optional[str] = None
    best_rank = 99
    for reason in reasons:
        if not reason:
            continue
        rank = _reason_rank(reason)
        if rank < best_rank:
            best_rank = rank
            best = reason
    return best


def _union(groups: List[int], a: int, b: int, reasons: Dict[int, Optional[str]], reason: str) -> None:
    def find(x: int) -> int:
        while groups[x] != x:
            groups[x] = groups[groups[x]]
            x = groups[x]
        return x

    root_a = find(a)
    root_b = find(b)
    if root_a == root_b:
        reasons[root_a] = _best_reason(reasons.get(root_a), reason)
        return

    best = _best_reason(reasons.get(root_a), reasons.get(root_b), reason)
    groups[root_b] = root_a
    reasons[root_a] = best


def _group_by(values: List[Tuple[int, Tuple[Any, ...]]], reasons: Dict[int, Optional[str]], label: str, parents: List[int]) -> None:
    buckets: Dict[Tuple[Any, ...], List[int]] = {}
    for idx, key in values:
        if not all(key):
            continue
        buckets.setdefault(key, []).append(idx)

    for idx_list in buckets.values():
        if len(idx_list) < 2:
            continue
        base = idx_list[0]
        for other in idx_list[1:]:
            _union(parents, base, other, reasons, label)


def find_master_duplicates(master_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect duplicate Locations Master rows using tiered heuristics.
    Returns a list of clusters with sequential group_ids.
    """
    if not master_rows:
        return []

    normalized: List[Tuple[int, Dict[str, Any]]] = [(idx, dedup_group_key(row)) for idx, row in enumerate(master_rows)]
    parents = list(range(len(normalized)))
    reasons: Dict[int, Optional[str]] = {}

    # Hard match: same Place_ID
    place_keys = [(idx, (keys["place_id"],)) for idx, keys in normalized if keys.get("place_id")]
    _group_by(place_keys, reasons, "place_id", parents)

    # Strong fuzzy: exact address match (Address1, City, State, Zip, Country)
    address_full = [
        (
            idx,
            (
                keys["address1"],
                keys["city"],
                keys["state"],
                keys["zip"],
                keys["country"],
            ),
        )
        for idx, keys in normalized
    ]
    _group_by(address_full, reasons, "address_full", parents)

    # Soft fuzzy: address without ZIP (Address1, City, State)
    address_no_zip = [
        (
            idx,
            (
                keys["address1"],
                keys["city"],
                keys["state"],
                keys["country"],
            ),
        )
        for idx, keys in normalized
    ]
    _group_by(address_no_zip, reasons, "address_no_zip", parents)

    # Soft fuzzy: coordinate proximity < 50m
    coords: List[Tuple[int, float, float]] = []
    for idx, keys in normalized:
        lat = keys.get("latitude")
        lon = keys.get("longitude")
        if lat is None or lon is None:
            continue
        coords.append((idx, lat, lon))

    for i in range(len(coords)):
        idx_a, lat_a, lon_a = coords[i]
        for j in range(i + 1, len(coords)):
            idx_b, lat_b, lon_b = coords[j]
            if _haversine_meters(lat_a, lon_a, lat_b, lon_b) <= 50:
                _union(parents, idx_a, idx_b, reasons, "coordinate_proximity")

    # Collect clusters
    clusters: Dict[int, List[int]] = {}

    def find_root(x: int) -> int:
        while parents[x] != x:
            parents[x] = parents[parents[x]]
            x = parents[x]
        return x

    for idx in range(len(normalized)):
        root = find_root(idx)
        clusters.setdefault(root, []).append(idx)

    results: List[Dict[str, Any]] = []
    group_num = 1

    for root_idx in sorted(clusters.keys()):
        member_indices = clusters[root_idx]
        if len(member_indices) < 2:
            continue
        reason = reasons.get(root_idx) or "unknown"
        rows = [master_rows[i] for i in member_indices]
        results.append(
            {
                "group_id": f"DUP{group_num:03d}",
                "reason": reason,
                "rows": rows,
            }
        )
        group_num += 1

    return results
