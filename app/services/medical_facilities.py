from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import httpx
import json
import re

from app.services.debug_logger import debug_log, debug_enabled
from app.services.notion_locations import get_location_page, update_location_page, normalize_location, _relation_ids
from app.services.notion_medical_facilities import (
    create_medical_facility_page,
    find_medical_facility_by_place_id,
    update_medical_facility_page,
    normalize_facility,
    fetch_all_medical_facilities,
)
from config import Config

NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
MF_RE = re.compile(r"^MF(\d+)$")


async def _get_next_mf_id() -> str:
    """Generate the next MF### ID based on existing rows."""
    all_facilities = await fetch_all_medical_facilities(limit=9999) # A large limit to get all
    max_num = 0
    for facility in all_facilities:
        mf_id = facility.get("medical_facility_id", "")
        m = MF_RE.match(mf_id)
        if m:
            try:
                max_num = max(max_num, int(m.group(1)))
            except (ValueError, TypeError):
                continue
    next_num = max_num + 1
    return f"MF{next_num:03d}"


async def _google_request(url: str, params: Dict[str, Any], *, allow_zero: bool = False) -> Dict[str, Any]:
    api_key = Config.GOOGLE_MAPS_API_KEY
    if not api_key:
        raise RuntimeError("Missing GOOGLE_MAPS_API_KEY")
    payload = dict(params)
    payload["key"] = api_key
    async with httpx.AsyncClient(timeout=12.0) as client:
        resp = await client.get(url, params=payload)
    resp.raise_for_status()
    data = resp.json()
    status = data.get("status")
    if status == "ZERO_RESULTS" and allow_zero:
        return data
    if status != "OK":
        raise ValueError(f"Google API error: {status or 'unknown'}")
    return data

async def _find_nearby_places(latitude: float, longitude: float, keyword: str, rankby: str = "distance") -> List[Dict[str, Any]]:
    """Find nearby places using Google Places API."""
    params = {
        "location": f"{latitude},{longitude}",
        "keyword": keyword,
        "rankby": rankby,
    }
    if rankby != "distance":
        params["radius"] = 50000 # 50km radius if not ranking by distance
    
    if debug_enabled():
        debug_log("MEDICAL_FACILITIES", f"Google Places Nearby Search query: {json.dumps(params)}")

    data = await _google_request(NEARBY_SEARCH_URL, params, allow_zero=True)
    return data.get("results", [])

def _get_place_details(place_id: str):
    # This is a simplified version. In a real app, you might want to cache the results.
    return _google_request(PLACE_DETAILS_URL, {"place_id": place_id, "fields": "name,formatted_address,geometry,website,international_phone_number,place_id,types"})

def _build_mf_properties_from_google_place(place: Dict[str, Any], facility_type: str, mf_id: Optional[str] = None) -> Dict[str, Any]:
    """Build Notion properties for a medical facility from a Google Place result."""
    name = place.get("name")
    address = place.get("formatted_address")
    website = place.get("website")
    phone = place.get("international_phone_number")
    place_id = place.get("place_id")
    
    # A very basic address parser
    address_components = {}
    if place.get("address_components"):
        for comp in place["address_components"]:
            types = comp.get("types", [])
            if "street_number" in types:
                address_components["address1"] = (address_components.get("address1", "") + " " + comp["long_name"]).strip()
            if "route" in types:
                address_components["address1"] = (address_components.get("address1", "") + " " + comp["long_name"]).strip()
            if "locality" in types:
                address_components["city"] = comp["long_name"]
            if "administrative_area_level_1" in types:
                address_components["state"] = comp["short_name"]
            if "postal_code" in types:
                address_components["zip"] = comp["long_name"]
            if "country" in types:
                address_components["country"] = comp["short_name"]

    props = {
        "Name": {"rich_text": [{"text": {"content": name}}]},
        "Type": {"select": {"name": facility_type}},
        "formatted_address_google": {"rich_text": [{"text": {"content": address}}]},
        "Website": {"url": website},
        "Phone": {"rich_text": [{"text": {"content": phone}}]},
        "Place_ID": {"rich_text": [{"text": {"content": place_id}}]},
        "address1": {"rich_text": [{"text": {"content": address_components.get("address1", "")}}]},
        "city": {"rich_text": [{"text": {"content": address_components.get("city", "")}}]},
        "state": {"rich_text": [{"text": {"content": address_components.get("state", "")}}]},
        "zip": {"rich_text": [{"text": {"content": address_components.get("zip", "")}}]},
        "country": {"rich_text": [{"text": {"content": address_components.get("country", "")}}]},
    }
    if mf_id:
        props["MedicalFacilityID"] = {"title": [{"text": {"content": mf_id}}]}
        
    if place.get("geometry", {}).get("location"):
        props["Latitude"] = {"number": place["geometry"]["location"]["lat"]}
        props["Longitude"] = {"number": place["geometry"]["location"]["lng"]}

    return {k: v for k, v in props.items() if v and (v.get("number") is not None or v.get("url") or (v.get("rich_text") and v.get("rich_text")[0].get("text").get("content")) or v.get("select") or v.get("title"))}


async def _upsert_medical_facility(place: Dict[str, Any], facility_type: str, location_master_id: str) -> Optional[Dict[str, Any]]:
    """Upsert a medical facility and link it to the location master."""
    place_id = place.get("place_id")
    if not place_id:
        return None

    mf_page = await find_medical_facility_by_place_id(place_id)
    
    if mf_page:
        # Update existing MF
        props = _build_mf_properties_from_google_place(place, facility_type)
        if debug_enabled():
            debug_log("MEDICAL_FACILITIES", f"Updating existing medical facility: {mf_page['id']} for place_id {place_id}")
        mf_page = await update_medical_facility_page(mf_page["id"], props)
    else:
        # Create new MF
        new_mf_id = await _get_next_mf_id()
        props = _build_mf_properties_from_google_place(place, facility_type, mf_id=new_mf_id)
        if debug_enabled():
            debug_log("MEDICAL_FACILITIES", f"Creating new medical facility for place_id {place_id} with new id {new_mf_id}")
        mf_page = await create_medical_facility_page(props)

    # MF -> LM relation
    existing_lm_ids = _relation_ids(mf_page.get("properties", {}), "LocationsMasterID")
    if location_master_id not in existing_lm_ids:
        if debug_enabled():
            debug_log("MEDICAL_FACILITIES", f"Linking MF {mf_page['id']} to LM {location_master_id}")
        new_relations = [{"id": lm_id} for lm_id in existing_lm_ids] + [{"id": location_master_id}]
        await update_medical_facility_page(mf_page["id"], {"LocationsMasterID": {"relation": new_relations}})
    
    return mf_page


def _is_er(place: Dict[str, Any]) -> bool:
    """Check if a place is an Emergency Room."""
    if "hospital" not in place.get("types", []):
        return False
    
    name = place.get("name", "").lower()
    er_keywords = ["emergency", "er", "emergency room", "emergency department"]
    
    for keyword in er_keywords:
        if keyword in name:
            return True
            
    return False

async def generate_nearby_medical_facilities(location_master_id: str):
    """Generate and link nearby medical facilities for a Location Master row."""
    if debug_enabled():
        debug_log("MEDICAL_FACILITIES", f"Starting generation for LM: {location_master_id}")

    # 1. Get LM page and check eligibility
    lm_page = await get_location_page(location_master_id)
    lm_props = lm_page.get("properties", {})
    normalized_lm = normalize_location(lm_page)

    lat = normalized_lm.get("latitude")
    lon = normalized_lm.get("longitude")
    place_id = normalized_lm.get("place_id")

    if not (lat and lon) and not place_id:
        if debug_enabled():
            debug_log("MEDICAL_FACILITIES", f"LM {location_master_id} is not eligible: missing lat/lon and place_id.")
        return {"status": "error", "message": "Location is not eligible for facility generation."}

    # If lat/lon are missing, get them from place_id
    if not (lat and lon) and place_id:
        place_details = await _get_place_details(place_id)
        location = place_details.get("geometry", {}).get("location", {})
        lat = location.get("lat")
        lon = location.get("lng")
        if not (lat and lon):
            if debug_enabled():
                debug_log("MEDICAL_FACILITIES", f"LM {location_master_id} is not eligible: failed to get lat/lon from place_id.")
            return {"status": "error", "message": "Location is not eligible for facility generation."}


    # 2. Rerun prevention
    if _relation_ids(lm_props, "ER"):
        if debug_enabled():
            debug_log("MEDICAL_FACILITIES", f"Skipping generation for LM {location_master_id}: ER already populated.")
        return {"status": "skipped", "message": "ER already populated."}

    # 3. Discovery
    hospitals = await _find_nearby_places(lat, lon, "hospital")
    urgent_cares = await _find_nearby_places(lat, lon, "urgent care")

    # 4. Classification and Deduplication
    er_facilities = [p for p in hospitals if _is_er(p)]
    uc_facilities = [p for p in urgent_cares if "health" in p.get("types", []) or "doctor" in p.get("types", [])]
    
    # Simple deduplication
    er_place_ids = {p["place_id"] for p in er_facilities}
    uc_facilities = [p for p in uc_facilities if p["place_id"] not in er_place_ids]


    # 5. Upsert and Link
    selected_er_id = None
    selected_uc_ids = []

    if er_facilities:
        # For simplicity, we pick the first one (closest)
        er_place = er_facilities[0]
        mf_page = await _upsert_medical_facility(er_place, "ER", location_master_id)
        if mf_page:
            selected_er_id = mf_page["id"]

    if uc_facilities:
        for uc_place in uc_facilities[:3]: # Max 3 urgent cares
            mf_page = await _upsert_medical_facility(uc_place, "Urgent Care", location_master_id)
            if mf_page:
                selected_uc_ids.append(mf_page["id"])

    # 6. Link LM -> MF
    lm_update_props = {}
    if selected_er_id:
        lm_update_props["ER"] = {"relation": [{"id": selected_er_id}]}
    if selected_uc_ids:
        for i, uc_id in enumerate(selected_uc_ids):
            lm_update_props[f"UC{i+1}"] = {"relation": [{"id": uc_id}]}
    
    if lm_update_props:
        if debug_enabled():
            debug_log("MEDICAL_FACILITIES", f"Linking LM {location_master_id} to facilities: {json.dumps(lm_update_props)}")
        await update_location_page(location_master_id, lm_update_props)
        return {"status": "success", "message": "Successfully generated and linked medical facilities."}
    else:
        return {"status": "no_facilities_found", "message": "No facilities found to link."}