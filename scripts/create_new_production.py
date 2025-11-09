import logging
import sys
from pathlib import Path
from notion_client.errors import APIResponseError

# Add project root ('c:\\Utils\\LocationsSync') to path to allow for clean imports
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from config import Config
from scripts import notion_utils as nu

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_locations_db_schema(locations_master_db_id: str) -> dict:
    """
    Returns the standard schema for a new production locations database.
    This ensures consistency across all created databases.
    """
    return {
        # --- Core Properties ---
        "ProdLocID": {"title": {}}, # The official Title property, populated by automation
        "Practical Name": {"rich_text": {}},
        "Location Name": {"rich_text": {}},
        "Full Address": {"rich_text": {}},
        "Status": {"status": {}}, # Keep native Status; options must be set in UI

        # --- Relation & Rollup Fields ---
        "LocationsMasterID": {
            "relation": {
                "database_id": locations_master_db_id,
                "single_property": {}
            }
        },
        "ProductionID": {
            "relation": {
                "database_id": Config.PRODUCTIONS_MASTER_DB,
                "single_property": {}
            }
        },
        "Abbreviation": {
            "rollup": {
                "relation_property_name": "ProductionID",
                "rollup_property_name": "Abbreviation",
                "function": "show_original"
            }
        },

        # --- Geocoding & Automation Fields ---
        "Place_ID": {"rich_text": {}},
        "Latitude": {"number": {}},
        "Longitude": {"number": {}},
        "Last Processed": {"last_edited_time": {}}
    }

def validate_config(required_vars: list[str]) -> bool:
    """Checks if all required variables are present in the Config."""
    missing_vars = [var for var in required_vars if not getattr(Config, var, None)]
    if missing_vars:
        logging.error("Missing one or more required environment variables.")
        print("\n? [ERROR] Missing one or more required environment variables in your .env file:")
        for var in missing_vars:
            print(f"  - {var}")
        return False
    return True

def create_locations_database(production_name: str, parent_page_id: str, locations_master_db_id: str) -> dict:
    """
    Creates a new locations database in Notion for the given production.
    Returns the API response object for the new database.
    """
    print(f"\nAttempting to create a new locations database for '{production_name}'...")
    db_schema = get_locations_db_schema(locations_master_db_id)

    new_db_response = nu.create_database(
        parent_page_id=parent_page_id,
        title=[{"type": "text", "text": {"content": f"{production_name} - Locations"}}],
        schema=db_schema
    )

    new_db_id = new_db_response["id"]
    logging.info(f"Successfully created new database '{production_name} - Locations' with ID: {new_db_id}")
    print(f"? Successfully created new locations database.")

    # --- Post-create: verify Status options and remind if missing ---
    # Notion API does not allow setting Status options programmatically.
    try:
        db_obj = nu.get_database(new_db_id)
        properties = db_obj.get("properties", {})
        status_prop = properties.get("Status")

        if status_prop is None:
            print("! Reminder: Add a 'Status' property (type: Status) in Notion.")
            print("  After adding the property, create these options:"
                  f" {Config.STATUS_ON_RESET}, {Config.STATUS_AFTER_MATCHING}, {Config.STATUS_ERROR}.")
            raise ValueError("Status property missing")

        existing = [opt.get("name") for opt in status_prop.get("status", {}).get("options", []) if isinstance(opt, dict)]
        required = [Config.STATUS_ON_RESET, Config.STATUS_AFTER_MATCHING, Config.STATUS_ERROR]
        missing = [name for name in required if name not in (existing or [])]
        if missing:
            print("! Reminder: Add these Status options in Notion:")
            for name in missing:
                print(f"   - {name}")
            print("  Open the database in Notion, edit the 'Status' property, and add the missing options.")
        else:
            print("? 'Status' property already has the required options.")
    except Exception:
        # Non-fatal: continue even if we cannot fetch/parse the schema
        logging.warning("Could not verify Status options after creation.")

    print(f"   URL: {new_db_response['url']}")
    return new_db_response

def handle_api_error(e: APIResponseError) -> None:
    """Logs and prints a user-friendly error message for Notion API errors."""
    logging.error(f"Notion API Error during production creation: {e}", exc_info=True)
    print(f"\n? [ERROR] A Notion API error occurred: {e}")
    print("  - Please check that your API token has the correct permissions.")
    print("  - Ensure the parent page and master database IDs in your .env file are correct and shared with the integration.")
    print(f"  - Make sure a property named '{Config.PROD_MASTER_LINK_PROP}' of type 'URL' exists in your Productions Master DB.")

def print_final_instructions() -> None:
    """Prints the final instructions for the user after successful creation."""
    print("\n--- Automation Complete! ---")
    print("Next Step: You must now sync the application with your Notion changes.")
    print("Please run '[2] Sync Production Tables from Notion' from the main menu.")

def generate_next_production_id(db_id: str, title_prop: str) -> str:
    """Generates the next sequential ProductionID based on existing entries."""
    print("\n?? Determining next ProductionID...")
    all_pages = nu.query_database(db_id)
    
    max_id = 0
    for page in all_pages:
        try:
            title_list = page.get("properties", {}).get(title_prop, {}).get("title", [])
            if title_list:
                prod_id_str = title_list[0].get("plain_text", "")
                if prod_id_str.startswith("PM") and prod_id_str[2:].isdigit():
                    current_id = int(prod_id_str[2:])
                    if current_id > max_id:
                        max_id = current_id
        except (ValueError, TypeError):
            continue # Ignore pages with malformed ProductionIDs
            
    next_id = max_id + 1
    new_prod_id = f"PM{next_id:03d}"
    print(f"  - ? Next ProductionID will be: {new_prod_id}")
    return new_prod_id

def add_to_master_list(production_name: str, db_url: str, productions_master_db_id: str, link_prop_name: str, title_prop_name: str, abbreviation: str, production_id: str) -> None:
    """
    Adds a new entry to the Productions Master database, linking to the new locations DB.
    """
    print(f"\nAdding '{production_name}' to the Productions Master list...")
    
    master_page_properties = {
        title_prop_name: {"title": [{"text": {"content": production_id}}]},
        "Name": {"rich_text": [{"text": {"content": production_name}}]},
        link_prop_name: {"url": db_url},
        "Abbreviation": {"rich_text": [{"text": {"content": abbreviation}}]}
    }

    nu.create_page(productions_master_db_id, master_page_properties)
    logging.info(f"Successfully added '{production_name}' to Productions Master DB.")
    print("? Successfully added entry to Productions Master list.")

def main() -> None:
    """
    Guides the user through creating a new production and its associated
    Notion database, then adds it to the Productions Master list.
    """
    print("--- Create New Production Utility ---")
    
    # 1. Validate configuration from config.py
    required_vars = [
        'NOTION_TOKEN', 'PRODUCTIONS_MASTER_DB', 
        'LOCATIONS_MASTER_DB', 'NOTION_DATABASES_PARENT_PAGE_ID',
        'PROD_MASTER_TITLE_PROP'
    ]
    if not validate_config(required_vars):
        return

    production_name = input("Enter the name for the new production (e.g., 'Project Phoenix'): ").strip()
    if not production_name:
        print("? Production name cannot be empty. Aborting.")
        return

    while True:
        abbreviation = input("Enter a short, unique abbreviation for this production (e.g., 'PHX'): ").strip().upper()
        if abbreviation:
            break
        print("? Abbreviation cannot be empty.")

    try:
        # Generate the next ProductionID before creating any databases
        next_prod_id = generate_next_production_id(
            Config.PRODUCTIONS_MASTER_DB,
            Config.PROD_MASTER_TITLE_PROP
        )

        # Create the new database and get its URL
        new_db = create_locations_database(
            production_name,
            Config.NOTION_DATABASES_PARENT_PAGE_ID,
            Config.LOCATIONS_MASTER_DB
        )

        # Add the new production to the master list
        add_to_master_list(
            production_name,
            new_db["url"],
            Config.PRODUCTIONS_MASTER_DB,
            Config.PROD_MASTER_LINK_PROP,
            Config.PROD_MASTER_TITLE_PROP,
            abbreviation,
            next_prod_id
        )

        print_final_instructions()

    except APIResponseError as e:
        handle_api_error(e)

if __name__ == "__main__":
    # This block is for standalone execution, which is not the primary use case
    # but it's good practice to ensure it works.
    # The main application entry point (run.py) handles this setup.
    from dotenv import load_dotenv
    # Add project root ('c:\\Utils\\LocationsSync') to path to allow for clean imports
    project_root = Path(__file__).resolve().parents[1]
    sys.path.append(str(project_root))

    # Load environment variables for all scripts that will be called
    dotenv_path = project_root / '.env'
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print("Warning: .env file not found. Script may fail if config is not set in environment.")

    # Import and set up the central config after loading the .env file
    Config.setup()
    main()
