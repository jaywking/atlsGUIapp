"""
populate_productions_used_in.py
Backfills the "Productions Used In" relation on Locations Master
using all existing PSL tables.

Safe, idempotent, and logs all updates.
"""

import os
import time
from notion_client import Client

from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")

# Initialize Notion client. Explicit notion_version avoids server-side 400s on bad defaults.
notion = Client(auth=NOTION_TOKEN, notion_version="2022-06-28")

# ---------------------------------------------
# CONFIG: Fill in your DB IDs here
# ---------------------------------------------

LM_DB = "20633cd663488145bb62dbf0bdf4762a"   # Locations Master

PSL_TABLES = [
    "20633cd663488095b1c4d21452e35ed7",  # AMCL_Locations
    "28f33cd6634881b48a17e538aa9bf92e",  # I Play Rocky_Locations
    "29433cd6634881708306cbb2bcb9997d",  # PAR_Locations
    "29033cd66348818db5bcf2a836b43bf9",  # RIP - Locations
    "26833cd6634880888b46f975a82baddf",  # SAMO_Locations
    "22233cd663488065a1d5ca9ffc772f5d",  # TGD_Locations
    "28b33cd663488112aa67c9196b2dc399",  # TEST_ONE_Locations
    "21333cd663488096aaf9e4788cf62ea7",  # YDEO_Locations
    # Add future PSL tables here
]


# ---------------------------------------------
# Helper function to safely append to a relation
# ---------------------------------------------
def append_relation(existing_list, new_id):
    if existing_list is None:
        existing_list = []
    # Skip duplicates
    if any(rel.get("id") == new_id for rel in existing_list):
        return existing_list
    # Return a new list with the appended id to avoid mutating caller's list
    return [*existing_list, {"id": new_id}]


# ---------------------------------------------
# Main loop
# ---------------------------------------------
def backfill_productions_used_in():
    print("\nStarting backfill of 'Productions Used In'...\n")

    for psl_db in PSL_TABLES:
        print(f"Processing PSL table: {psl_db}")

        updated_count = 0
        skipped_no_lm = 0
        skipped_no_prod = 0
        processed = 0

        # Query PSL database (handle pagination)
        start_cursor = None
        while True:
            response = notion.request(
                path=f"databases/{psl_db}/query",
                method="POST",
                body={"start_cursor": start_cursor} if start_cursor else {},
            )

            psl_rows = response.get("results", [])

            for row in psl_rows:
                processed += 1
                props = row["properties"]

                # Skip rows with no LM link
                lm_rel = props.get("LocationsMasterID", {}).get("relation")
                if not lm_rel:
                    skipped_no_lm += 1
                    continue

                lm_id = lm_rel[0]["id"]

                # Skip rows with no ProductionID
                psl_prod_rel = props.get("ProductionID", {}).get("relation")
                if not psl_prod_rel:
                    skipped_no_prod += 1
                    continue

                production_id = psl_prod_rel[0]["id"]

                # Fetch the LM row
                lm_page = notion.pages.retrieve(page_id=lm_id)
                lm_props = lm_page["properties"]

                # Current values in Productions Used In
                existing = lm_props.get("Productions Used In", {}).get("relation") or []
                if not isinstance(existing, list):
                    # Defensive: Notion should return a list, but guard in case of malformed data
                    existing = []

                # Append safely without mutating the original list
                updated_rel = append_relation(existing, production_id)

                # Write back only if something changed
                if len(updated_rel) != len(existing):
                    notion.pages.update(
                        page_id=lm_id,
                        properties={
                            "Productions Used In": {"relation": updated_rel}
                        }
                    )
                    print(f"Updated LM {lm_id} with Production {production_id}")
                    updated_count += 1

            if response.get("has_more"):
                start_cursor = response.get("next_cursor")
            else:
                break

        print(
            f"Completed PSL table: {psl_db} | processed={processed}, "
            f"updated={updated_count}, skipped_no_lm={skipped_no_lm}, skipped_no_prod={skipped_no_prod}\n"
        )
        time.sleep(0.6)  # Slightly stronger throttle for Notion API

    print("\nBackfill complete.\n")


if __name__ == "__main__":
    backfill_productions_used_in()
