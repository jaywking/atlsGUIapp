# Standard library imports
import os
import sys
from pathlib import Path
import argparse

# Set up project root and load environment variables FIRST.
# This is crucial so that modules like 'config' have access to them when imported.
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# Third-party imports
from dotenv import load_dotenv
load_dotenv(dotenv_path=project_root / '.env')

# Local application imports
from scripts import notion_utils as nu
from config import Config

def main(db_id_or_url: str | None = None) -> None:
    """
    Prompts the user for a Notion Database ID or URL and prints its schema.
    Can also accept the ID/URL as an argument.
    """
    if not db_id_or_url:
        db_id_or_url = input("Enter the Notion Database ID or URL to inspect: ").strip()

    # Sanitize the input to get a clean database ID
    db_id = db_id_or_url.split('?')[0].split('/')[-1]

    try:
        data = nu.get_database(db_id)
        title = data.get('title', [{}])[0].get('plain_text', db_id)
        print(f"\n? Properties in Database '{title}':\n")

        for name, meta in sorted(data["properties"].items()):
            prop_type = meta['type']
            details = ""
            # For select, multi_select, and status, show the available options
            if prop_type in ("select", "multi_select", "status"):
                options = meta.get(prop_type, {}).get("options", [])
                if options:
                    option_names = [f"'{opt['name']}'" for opt in options]
                    details = f" (Options: {', '.join(option_names)})"
            print(f"  - {name} (Type: {prop_type}){details}")
    except Exception as e:
        print(f"\n? Could not inspect database: {e}")

if __name__ == "__main__":
    # Initialize Config from environment (after load_dotenv above)
    Config.setup()
    # Check for the Notion token before proceeding
    if not Config.NOTION_TOKEN:
        print("? NOTION_TOKEN not found in your .env file or environment variables.")
        print("   Please ensure a valid token is set in the .env file at the project root.")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Inspect the schema of a Notion database."
    )
    parser.add_argument(
        "db_id_or_url",
        nargs="?",
        default=None,
        help="The ID or URL of the Notion database to inspect (optional)."
    )
    args = parser.parse_args()

    main(args.db_id_or_url)
