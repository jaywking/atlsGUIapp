# scripts/google_address_businesses.py
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from dotenv import load_dotenv


def _clean_key(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()
    if "#" in cleaned:
        cleaned = cleaned.split("#", 1)[0].strip()
    if " " in cleaned or "\t" in cleaned:
        cleaned = cleaned.split()[0].strip()
    return cleaned or None


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)

API_KEY = _clean_key(os.getenv("GOOGLE_MAPS_API_KEY"))
if len(sys.argv) > 1:
    ADDRESS = " ".join(sys.argv[1:]).strip()
else:
    ADDRESS = input("Enter address: ").strip() or "474 N Lake Shore Dr, Chicago, IL 60611, USA"

if not API_KEY:
    raise SystemExit("GOOGLE_MAPS_API_KEY not set (check .env in repo root)")
if len(API_KEY) < 20:
    raise SystemExit(
        f"GOOGLE_MAPS_API_KEY looks too short (len={len(API_KEY)}). "
        "Ensure the repo .env has the full key and no placeholder value."
    )

def _request(url):
    req = urllib.request.Request(url, headers={"User-Agent": "atlsguiapp/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))

def geocode(address):
    params = urllib.parse.urlencode({"address": address, "key": API_KEY})
    data = _request(f"https://maps.googleapis.com/maps/api/geocode/json?{params}")
    if data.get("status") != "OK" or not data.get("results"):
        message = data.get("error_message") or data.get("status")
        raise RuntimeError(f"Geocode failed: {message}")
    return data["results"][0]

def place_details(place_id):
    fields = "place_id,name,formatted_address,address_component,geometry,types"
    params = urllib.parse.urlencode({"place_id": place_id, "fields": fields, "key": API_KEY})
    data = _request(f"https://maps.googleapis.com/maps/api/place/details/json?{params}")
    if data.get("status") != "OK" or not data.get("result"):
        return None
    return data["result"]

def normalize_address_components(result):
    comps = result.get("address_components") or []
    def get_comp(type_name):
        for c in comps:
            if type_name in c.get("types", []):
                return c.get("short_name") or c.get("long_name")
        return ""
    return {
        "street_number": get_comp("street_number"),
        "route": get_comp("route"),
        "city": get_comp("locality") or get_comp("postal_town"),
        "zip": get_comp("postal_code"),
    }

def matches_target(components, target):
    if not components["street_number"] or not components["route"]:
        return False
    if components["street_number"].lower() != target["street_number"].lower():
        return False
    if components["route"].lower() != target["route"].lower():
        return False
    if target["city"] and components["city"].lower() != target["city"].lower():
        return False
    if target["zip"] and components["zip"].lower() != target["zip"].lower():
        return False
    return True

# 1) Geocode to get lat/lng
geo = geocode(ADDRESS)
loc = geo["geometry"]["location"]
latlng = f"{loc['lat']},{loc['lng']}"
target = normalize_address_components(geo)

# 2) Nearby search (all types, small radius)
params = urllib.parse.urlencode({
    "location": latlng,
    "radius": 100,  # keep tight; increase if needed
    "key": API_KEY,
})
nearby = _request(f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?{params}")
results = nearby.get("results", [])

matches = []

# 3) Place Details for each candidate and filter exact address match
for r in results:
    pid = r.get("place_id")
    if not pid:
        continue
    details = place_details(pid)
    if not details:
        continue
    comps = normalize_address_components(details)
    if matches_target(comps, target):
        matches.append({
            "name": details.get("name"),
            "place_id": details.get("place_id"),
            "formatted_address": details.get("formatted_address"),
            "types": details.get("types", []),
        })

print(json.dumps(matches, indent=2))
