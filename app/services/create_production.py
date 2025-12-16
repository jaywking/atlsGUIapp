"""Service for creating productions and PSL copies."""

from __future__ import annotations

import copy
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError

# Ensure project root on path for config shim when run from scripts
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from config import Config  # noqa: E402

NOTION_VERSION = "2022-06-28"
PSL_TEMPLATE_DB_ID = "2c833cd6634880b3b4c8fbdfe05fb9a0"
NOTION_BASE_URL = "https://www.notion.so"


class CreateProductionError(Exception):
    """Raised when production creation fails."""


def hyphenate_id(notion_id: str) -> str:
    raw = notion_id.replace("-", "")
    if len(raw) != 32:
        return notion_id
    return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"


def get_psl_template_id() -> str:
    env_value = os.getenv("PSL_TEMPLATE_DB_ID")
    if env_value:
        return env_value.strip()
    logging.info("PSL_TEMPLATE_DB_ID not set; falling back to built-in constant.")
    return PSL_TEMPLATE_DB_ID


def load_env() -> None:
    env_path = PROJECT_ROOT / ".env"
    load_dotenv(env_path if env_path.exists() else None)


def _fail(message: str) -> None:
    raise CreateProductionError(message)


def format_api_error(exc: APIResponseError) -> str:
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        return body.get("message") or body.get("error") or str(body)
    message_attr = getattr(exc, "message", None)
    return message_attr or str(exc)


def validate_env() -> None:
    if not Config.NOTION_TOKEN:
        _fail("NOTION_TOKEN is missing in environment.")
    if not Config.PRODUCTIONS_MASTER_DB:
        _fail("PRODUCTIONS_MASTER_DB is missing in environment.")


def build_value(value: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    field_type = schema.get("type")
    if field_type == "title":
        return {"title": [{"text": {"content": value}}]}
    if field_type == "rich_text":
        return {"rich_text": [{"text": {"content": value}}]}
    if field_type == "status":
        return {"status": {"name": value}}
    if field_type == "url":
        return {"url": value}
    if field_type == "number":
        try:
            num = float(value)
        except ValueError:
            num = None
        return {"number": num}
    return {"rich_text": [{"text": {"content": value}}]}


def get_title_property(db_obj: Dict[str, Any]) -> Optional[str]:
    for name, definition in (db_obj.get("properties") or {}).items():
        if definition.get("type") == "title":
            return name
    return None


def _extract_title_value(page: Dict[str, Any]) -> str:
    props = page.get("properties") or {}
    for value in props.values():
        if value.get("type") == "title":
            title_items = value.get("title") or []
            if title_items:
                return title_items[0].get("plain_text") or title_items[0].get("text", {}).get("content", "")
    return ""


def generate_next_production_id(client: Client, productions_db_id: str) -> str:
    max_id = 0
    start_cursor = None
    pattern = re.compile(r"PM(\d{3})$")
    while True:
        payload: Dict[str, Any] = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        res = client.request(path=f"databases/{productions_db_id}/query", method="POST", body=payload)
        if not isinstance(res, dict):
            break
        for page in res.get("results", []) or []:
            title_val = _extract_title_value(page)
            match = pattern.match(title_val.strip() if isinstance(title_val, str) else "")
            if match:
                try:
                    num = int(match.group(1))
                    if num > max_id:
                        max_id = num
                except ValueError:
                    continue
        if res.get("has_more") and res.get("next_cursor"):
            start_cursor = res["next_cursor"]
        else:
            break
    next_id = max_id + 1
    return f"PM{next_id:03d}"


def _extract_rich_text(props: Dict[str, Any], name: str) -> str:
    value = props.get(name) or {}
    if value.get("type") != "rich_text":
        return ""
    parts = []
    for item in value.get("rich_text") or []:
        text = item.get("plain_text") or item.get("text", {}).get("content")
        if text:
            parts.append(text)
    return "".join(parts)


def ensure_abbreviation_unique(client: Client, productions_db_id: str, abbreviation: str) -> None:
    """Raise if abbreviation already exists (case-insensitive) in Productions Master."""
    start_cursor = None
    abbrev_lower = abbreviation.lower()
    while True:
        payload: Dict[str, Any] = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        res = client.request(path=f"databases/{productions_db_id}/query", method="POST", body=payload)
        if not isinstance(res, dict):
            break
        for page in res.get("results", []) or []:
            props = page.get("properties") or {}
            existing = _extract_rich_text(props, "Abbreviation")
            if existing and existing.lower() == abbrev_lower:
                _fail(f"Abbreviation '{abbreviation}' already exists in Productions Master.")
        if res.get("has_more") and res.get("next_cursor"):
            start_cursor = res["next_cursor"]
        else:
            break


def notion_url_for_id(notion_id: str) -> str:
    sanitized = (notion_id or "").replace("-", "")
    return f"{NOTION_BASE_URL}/{sanitized}"


def create_production_page(
    client: Client,
    productions_db_id: str,
    production_id: str,
    abbreviation: str,
    production_name: str,
    extras: Dict[str, str],
) -> str:
    db_obj = client.databases.retrieve(productions_db_id)
    properties_schema = db_obj.get("properties") or {}

    title_prop = "ProductionID"
    required_props = ["ProductionID", "Name", "Abbreviation", "ProdStatus"]
    for prop in required_props:
        if prop not in properties_schema:
            _fail(f"Productions Master database is missing '{prop}' property.")
    title_property_in_schema = get_title_property(db_obj)
    if title_property_in_schema != title_prop:
        _fail(f"Title property mismatch: expected '{title_prop}', found '{title_property_in_schema or 'None'}'.")

    payload: Dict[str, Any] = {
        title_prop: build_value(production_id, properties_schema.get(title_prop, {})),
        "Name": build_value(production_name, properties_schema.get("Name", {})),
        "Abbreviation": build_value(abbreviation, properties_schema.get("Abbreviation", {})),
    }
    optional_mappings = {
        "Nickname": "Nickname",
        "ProdStatus": "ProdStatus",
        "ClientPlatform": "Client / Platform",
        "ProductionType": "Production Type",
        "Studio": "Studio",
    }
    for key, notion_name in optional_mappings.items():
        val = extras.get(key)
        if val and notion_name in properties_schema:
            schema_def = properties_schema.get(notion_name, {})
            if schema_def.get("type") == "status":
                options = [
                    opt.get("name")
                    for opt in schema_def.get("status", {}).get("options", []) or []
                    if isinstance(opt, dict)
                ]
                if not options or val not in options:
                    _fail(f"{notion_name} must be one of: {', '.join(options) if options else 'no options configured in Notion'}")
            payload[notion_name] = build_value(val, schema_def)

    try:
        page = client.pages.create(parent={"database_id": productions_db_id}, properties=payload)
    except APIResponseError as exc:
        _fail(f"Failed to create production page: {format_api_error(exc)}")

    page_id = page.get("id")
    if not page_id:
        _fail("Production page created but no ID returned.")
    return page_id


def duplicate_psl_template(client: Client) -> Dict[str, Any]:
    parent_page = getattr(Config, "NOTION_DATABASES_PARENT_PAGE_ID", None)
    template_id = get_psl_template_id()
    if not template_id:
        _fail("PSL template ID is missing. Set PSL_TEMPLATE_DB_ID in the environment.")
    id_variants = [template_id, hyphenate_id(template_id)]
    attempts = []
    for nid in id_variants:
        attempts.append((f"blocks/{nid}/copy", {"target": {"page_id": parent_page}} if parent_page else {}))
        attempts.append((f"blocks/{nid}/duplicate", {"target": {"page_id": parent_page}} if parent_page else {}))
        attempts.append((f"databases/{nid}/duplicate", {}))
        attempts.append((f"pages/{nid}/duplicate", {}))
    errors: list[str] = []
    for path, body in attempts:
        try:
            logging.info("Attempting PSL duplicate via %s", path)
            response = client.request(path=path, method="POST", body=body)
            if not isinstance(response, dict) or "id" not in response:
                errors.append(f"{path}: missing id in response")
                continue
            return response
        except APIResponseError as exc:
            errors.append(f"{path}: {format_api_error(exc)}")
    logging.warning("Direct duplication failed. Falling back to schema copy.")
    clone = clone_template_schema(client, template_id, parent_page)
    if clone:
        return clone
    _fail("Failed to duplicate PSL template. Attempts: " + " | ".join(errors))


def scrub_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {}
    for name, prop in properties.items():
        if not isinstance(prop, dict):
            continue
        prop_copy = {k: copy.deepcopy(v) for k, v in prop.items() if k not in {"id", "name"}}
        if "description" in prop_copy and not prop_copy["description"]:
            prop_copy.pop("description", None)
        if prop_copy.get("type") == "status":
            prop_copy.get("status", {}).pop("options", None)
            prop_copy.get("status", {}).pop("groups", None)
        cleaned[name] = prop_copy
    return cleaned


def _resolve_parent_for_clone(template_db: Dict[str, Any], override_parent_page: Optional[str]) -> Dict[str, Any]:
    if override_parent_page:
        return {"page_id": override_parent_page}
    parent = template_db.get("parent") or {}
    if parent.get("type") == "page_id" and parent.get("page_id"):
        return {"page_id": parent["page_id"]}
    if parent.get("type") == "workspace" and parent.get("workspace"):
        return {"workspace": True}
    _fail("No valid parent found for cloning. Set NOTION_DATABASES_PARENT_PAGE_ID.")


def clone_template_schema(client: Client, template_id: str, override_parent_page: Optional[str]) -> Dict[str, Any]:
    try:
        template_db = client.databases.retrieve(template_id)
    except APIResponseError as exc:
        _fail(f"Failed to retrieve PSL template: {format_api_error(exc)}")

    properties = template_db.get("properties") or {}
    if not properties:
        _fail("PSL template has no properties to clone.")

    cleaned_properties = scrub_properties(properties)
    if not cleaned_properties:
        _fail("Failed to prepare properties from PSL template.")

    try:
        parent = _resolve_parent_for_clone(template_db, override_parent_page)
        body = {
            "parent": parent,
            "title": [{"type": "text", "text": {"content": "PSL Clone"}}],
            "properties": cleaned_properties,
        }
        response = client.request(path="databases", method="POST", body=body)
        if not isinstance(response, dict) or "id" not in response:
            _fail("Fallback clone succeeded without returning an id.")
        return response
    except APIResponseError as exc:
        _fail(f"Failed to clone PSL template schema: {format_api_error(exc)}")


def rename_database(client: Client, database_id: str, new_name: str) -> None:
    try:
        client.databases.update(
            database_id=database_id,
            title=[{"type": "text", "text": {"content": new_name}}],
        )
    except APIResponseError as exc:
        _fail(f"Failed to rename duplicated database: {format_api_error(exc)}")


def update_production_with_psl_id(
    client: Client,
    page_id: str,
    psl_db_id: str,
    productions_schema: Dict[str, Any],
) -> None:
    prop_name = "Locations Table"
    if prop_name not in productions_schema:
        _fail(f"Productions Master database is missing '{prop_name}' property.")
    psl_url = notion_url_for_id(psl_db_id)
    payload = {
        prop_name: build_value(psl_url, productions_schema[prop_name]),
    }
    try:
        client.pages.update(page_id=page_id, properties=payload)
    except APIResponseError as exc:
        _fail(f"Failed to update production with Locations Table URL: {format_api_error(exc)}")


def create_production(
    production_code: str,
    production_name: str,
    nickname: Optional[str] = None,
    prod_status: Optional[str] = None,
    client_platform: Optional[str] = None,
    production_type: Optional[str] = None,
    studio: Optional[str] = None,
) -> Dict[str, str]:
    load_env()
    validate_env()

    abbreviation = (production_code or "").strip()
    if not abbreviation:
        _fail("Abbreviation is required.")
    abbreviation = abbreviation.upper()
    if not production_name or not production_name.strip():
        _fail("Production name is required.")

    notion = Client(auth=Config.NOTION_TOKEN, notion_version=NOTION_VERSION)

    ensure_abbreviation_unique(notion, Config.PRODUCTIONS_MASTER_DB, abbreviation)
    production_id = generate_next_production_id(notion, Config.PRODUCTIONS_MASTER_DB)

    extras = {
        "Nickname": (nickname or "").strip(),
        "ProdStatus": (prod_status or "").strip(),
        "ClientPlatform": (client_platform or "").strip(),
        "ProductionType": (production_type or "").strip(),
        "Studio": (studio or "").strip(),
    }

    prod_page_id = create_production_page(
        notion,
        Config.PRODUCTIONS_MASTER_DB,
        production_id,
        abbreviation,
        production_name,
        extras,
    )
    logging.info("Created production page %s", prod_page_id)

    duplicate = duplicate_psl_template(notion)
    new_psl_db_id = duplicate.get("id")
    new_name = f"{abbreviation}_Locations"
    rename_database(notion, new_psl_db_id, new_name)
    logging.info("Duplicated PSL template to %s (%s)", new_name, new_psl_db_id)

    prod_db_obj = notion.databases.retrieve(Config.PRODUCTIONS_MASTER_DB)
    update_production_with_psl_id(notion, prod_page_id, new_psl_db_id, prod_db_obj.get("properties") or {})

    return {
        "production_page_id": prod_page_id,
        "production_id": production_id,
        "abbreviation": abbreviation,
        "psl_database_id": new_psl_db_id,
        "psl_database_url": notion_url_for_id(new_psl_db_id),
        "psl_database_name": new_name,
    }
