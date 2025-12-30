# Project Handbook - ATLS GUI App  
Last Updated: 2025-12-16  
Version: v0.9.4

This handbook defines how ATLSApp is developed using NiceGUI, FastAPI, and a structured workflow.

---

This project includes several guardrails and patterns that Codex must follow at all times. The authoritative rules live in DEV_NOTES.md (“Developer Tools & Guardrails”) and throughout PROJECT_HANDBOOK.md, but this section summarizes the key constraints for fast onboarding.

Core Development Rules

### NON-NEGOTIABLE

UI is built with NiceGUI, and this project uses a version that does not support lambda-based reactive class bindings.  
Never use .classes(lambda: …).  
Always use static class strings with Tailwind utilities.  
**Tailwind `dark:` variants are explicitly disallowed.**

Do not use @ui.expose, pywebview callbacks, or JS→Python bridges. These are not supported in this runtime.

Do not introduce custom global wrapper classes (e.g., app-header, app-content). All styling must use Tailwind classes or global CSS inside layout.py.

Do not place Python callables inside table columns, slots, or NiceGUI components. NiceGUI cannot serialize them.

Theme persistence must use localStorage only. No callbacks.

Maintain the global layout structure defined in app/ui/layout.py.  
Do not restructure the shell, sidebar, or header without explicit instruction.

Where Key Logic Lives

Global layout, dark mode CSS, typography, table styling, alignment rules, theme persistence, and UI-level CSS live in:  
app/ui/layout.py

Per-page content and table definitions live in the corresponding app/ui/*.py files.

All developer guardrails, Codex rules, and NiceGUI patterns live in:  
docs/DEV_NOTES.md

Architecture guidelines, versioning, naming, and workflow rules live in:  
docs/PROJECT_HANDBOOK.md

Versioning Expectations

### NON-NEGOTIABLE

Each verified milestone increments the version in:  
README.md, PROJECT_HANDBOOK.md, and DEV_NOTES.md.

Add a new Session entry in DEV_NOTES.md summarizing the work.

Follow the existing v0.4.x structure for UI and layout improvements.

Never Modify

### NON-NEGOTIABLE

API route behavior unless specifically requested.

Background sync logic or service architecture.

Table column definitions or editing logic unless the task explicitly requires it.

What Every Codex Session Must Do

### NON-NEGOTIABLE

Read: PROJECT_HANDBOOK.md, DEV_NOTES.md, layout.py.

Adhere strictly to NiceGUI rules listed above.

Use static class strings + global CSS, never lambda-wrapped classes.

Do not introduce Tailwind `dark:` utilities.

Ensure any UI changes remain consistent across all pages (/dashboard, /productions, /locations, /facilities, /jobs, /settings).

Update documentation (version bump + notes) as part of every verified milestone.

---

# 1. Purpose

ATLSApp consolidates LocationSync, Medical Facility tools, Notion workflows, and diagnostic utilities into a unified browser interface.

---

# 2. Folder Structure

```
atlsGUIapp/
├ app/
│  ├ main.py
│  ├ ui/
│  ├ api/
│  ├ services/
│  ├ data/
├ scripts/
├ docs/
├ .env
├ requirements.txt
```

UI, API, and service layers must remain cleanly separated.

---

# 3. File Naming & Conventions

| Category | Convention | Example |
|----------|-----------|---------|
| UI pages | lowercase nouns | productions.py |
| API routers | <feature>_api.py | settings_api.py |
| Services | descriptive modules | background_sync.py |
| Docs | SCREAMING_SNAKE_CASE | PROJECT_HANDBOOK.md |

---

# 4. Code Style

### NON-NEGOTIABLE

- Async-first (`async def`, `await`, `httpx`)  
- Type hints required  
- PEP 8 formatting  
- No blocking operations  
- UI must call only relative API paths  
- API responses must follow:

```
{ "status": "success" | "error", "message": "...", "data": {...} }
```

- No secrets logged or shown in UI

---

# 6. Productions Creation Flow (UI / API / Service)

- Endpoint: `POST /api/productions/create` → calls `app.services.create_production.create_production`.
- ProductionID is auto-generated as the next `PM###` (scans Productions Master for the highest PM### and increments). Users do not enter ProductionID.
- Required user inputs: Abbreviation (uppercased) and Production Name.
- Optional user inputs (passed through to Notion when present): Nickname, ProdStatus (must match Notion options), Client / Platform, Production Type, Studio.
- Production page write: ProductionID (title) = generated PM###; Name = user value; Abbreviation = user value; optional fields above; ProdStatus/Status left blank if not provided.
- PSL handling: attempts Notion duplicate of the PSL template; if blocked, clones the schema and renames the new DB to `{Abbreviation}_Locations`, then writes the PSL URL to `Locations Table` on the production page.
- PSL enrichment: when Enrich PSL runs against a production locations DB, it now stamps `ProductionID` as a relation to the production page, applies the production Abbreviation as the `ProdLocID` prefix (e.g., `TEST001`), and auto-increments per production. LOC generation in Locations Master now respects existing master titles to avoid reusing `LOC001`.
- UI (app/ui/productions.py): “Add Production” dialog prompts for required Abbreviation/Name plus optional fields, fetches ProdStatus options from Notion, disables controls during submit, shows inline errors, and refreshes the table on success. Created/Last Edited timestamps are formatted (date-only for Created, local datetime for Last Edited).

# Data Models & External Source Mappings

This chapter is the authoritative contract for where data in PSL, LM, and MF comes from, and which system is allowed to write each field.

## 1. PSL Schema → Source, Derived Fields & External Alignment

### PSL Role & Scope
- PSL represents production-specific usage of a location.
- PSL rows are not canonical locations.
- PSL captures story/production/operational context.
- Canonical location identity and normalization live in Locations Master (LM).
- PSL may temporarily store Google-derived data during enrichment, but LM is authoritative.

### Identifier Rules (Non-Negotiable)
- **ProdLocID**
  - Identifier for PSL rows.
  - Derived from production abbreviation + zero-padded sequence (e.g., `TEST001`).
  - Unique within a production.
  - Generated during PSL enrichment; never user-entered; never free-form.
- **LocationsMasterID**
  - Identifier for LM; globally unique across all LM rows.
  - PSL may reference it via relation.
  - PSL must never generate or modify this value.

### PSL Field Categories & Write Authority
- **User-Authored Fields**
  - `Location Name`: Always user-entered; production-facing label (e.g., “Bad Guys Hangout”); must never be populated or overwritten by Google data.
  - `Practical Name`
  - `Notes`
- **Production-Derived Fields**
  - `ProductionID` (relation)
  - `Abbreviation` (rollup)
- **Derived Identifiers**
  - `ProdLocID`
- **Externally Populated Fields**
  - Address and coordinate fields written during enrichment (see Google alignment).
- **Relation Fields**
  - PSL → LM (`LocationsMasterID`)

### External Data → PSL Field Alignment (MANDATORY)
- **Google → PSL Alignment**
  - `place_id` → `Place_ID`
  - `geometry.location.lat` → `Latitude`
  - `geometry.location.lng` → `Longitude`
  - `url` → `Google Maps URL`
  - `formatted_address` → `formatted_address_google`
  - `formatted_address` → `Full Address`
- **Address Components**
  - `street_number` + `route` → `address1`
  - `subpremise` → `address2`
  - (no reliable Google source) → `address3`
  - `locality` → `city`
  - `administrative_area_level_1` → `state`
  - `postal_code` → `zip`
  - `country` → `country`
  - `administrative_area_level_2` → `county`
  - `sublocality_level_1` → `borough` (when present)
- **Explicit Non-Mappings**
  - Google `name` must not map to `Location Name` or `Practical Name`.
  - `Location Name` is always user-entered and must never be overwritten.
  - PSL must not infer or fabricate missing address components.

### Overwrite & Preservation Rules
- **May overwrite (by enrichment):** Structured address fields, `Full Address`, `formatted_address_google`, `Place_ID`, `Latitude`, `Longitude`, `LocationsMasterID`, `ProductionID`, `ProdLocID` (when missing/wrong prefix), `Status` per matching rules.
- **Must preserve:** `Location Name`, `Practical Name`, `Notes`, user-set `Status` outside enrichment, and any field not present in the PSL schema. Enrichment must never erase production intent.

## 2. Locations Master (LM) Schema → Canonical & External Source Mapping

### LM Role & Scope
- LM is the canonical location table.
- One LM row represents one real-world place.
- Multiple PSL rows may reference the same LM row.
- LM is authoritative for normalized address data, coordinates, `Place_ID`, and Google-derived location identity.
- Downstream systems (PSL, MF, safety, reporting) must treat LM as the source of truth.

### Identifier Rules (Non-Negotiable)
- **LocationsMasterID**
  - Identifier for LM rows; format `LOC###`.
  - Globally unique across the entire LM table.
  - Generated by the system; never user-entered; never reused; never derived from PSL.
- Google `place_id` is used for deduplication and upsert; no two LM rows may share the same `place_id`.

### LM Field Categories & Write Authority
- **Canonical Identifiers:** `LocationsMasterID`, `Place_ID`.
- **Externally Populated (Google) Fields:** Address fields, coordinates, `Google Maps URL`, `Types`.
- **User / Operational Fields:** `Name`, `Practical Name`, `Notes`.
- **Pipeline Status:** `Status` is reserved for pipeline state only (`Ready`, `Unresolved`, `Matched`).
- **Business Operational Status:** `Location Op Status` stores Google operational state (`business_status`) and must never write to `Status`.
- **System / Relation Fields:** `Productions Used In`, `ProductionID` (if present), medical facility relations (ER / UC fields).

### External Data → LM Field Alignment (MANDATORY)
- **Core Identity & Location**
  - `place_id` → `Place_ID`
  - `geometry.location.lat` → `Latitude`
  - `geometry.location.lng` → `Longitude`
  - `url` → `Google Maps URL`
- **Address (Formatted + Components)**
  - `formatted_address` → `formatted_address_google`
  - `formatted_address` → `Full Address`
  - `street_number` + `route` → `address1`
  - `subpremise` → `address2`
  - (no reliable Google source) → `address3`
  - `locality` → `city`
  - `administrative_area_level_1` → `state`
  - `postal_code` → `zip`
  - `country` → `country`
  - `administrative_area_level_2` → `county`
  - `sublocality_level_1` → `borough` (when present)
- **Classification**
  - `types[]` → `Types` (multi-select)
- **Operational State**
  - `business_status` → `Location Op Status`
- **Explicit Non-Mappings**
  - Google `name` does not overwrite `Name` or `Practical Name`.
  - Google `business_status` must not map to `Status` (pipeline only).
  - LM does not infer or fabricate missing address components.
  - Missing Google data results in empty LM fields.

### Overwrite, Deduplication & Preservation Rules
- LM rows are created or updated via `place_id` upsert.
- Address and coordinate fields may be overwritten on re-enrichment.
- User-authored fields (`Name`, `Practical Name`, `Notes`) must be preserved.
- `LocationsMasterID` must never change once assigned.
- LM canonical values take precedence over PSL copies.

## 3. Medical Facilities (MF) Schema → Google Places API Mapping

MF is populated exclusively from Google Places Nearby Search + Place Details. This mapping is the complete and authoritative alignment between Google field names and MF Notion fields. Any MF field not populated after enrichment is empty by design unless Google provides the data. Downstream consumers must not infer or fabricate MF data.

---

## Medical Facilities Database
Source: `env::NOTION_MEDICAL_DB_ID`

---

## 1. Identity / Core Fields

| MF Field | Google Places Field |
|--------|---------------------|
| MedicalFacilityID (title) | Internal only (not from Google) |
| Name | `name` |
| Place_ID | `place_id` |
| Type | Derived from `types` + name inspection (classification logic) |

**Type rules (summary):**
- ER → `types` includes `hospital` AND explicit emergency indicators
- Urgent Care → urgent care indicators
- Do not classify health systems, clinics, or offices as ER

---

## 2. Coordinates / Geometry

| MF Field | Google Places Field |
|--------|---------------------|
| Latitude | `geometry.location.lat` |
| Longitude | `geometry.location.lng` |

---

## 3. Address (Raw)

| MF Field | Google Places Field |
|--------|---------------------|
| formatted_address_google | `formatted_address` |
| Full Address | `formatted_address` |

---

## 4. Address (Parsed from `address_components[]`)

All fields below are derived from `address_components[]`.  
If a component does not exist, leave the MF field empty.

| MF Field | Google Address Component |
|--------|--------------------------|
| address1 | `street_number` + `route` |
| address2 | `subpremise` |
| address3 | Explicit component only (otherwise empty) |
| city | `locality` |
| borough | `sublocality` or `sublocality_level_1` |
| county | `administrative_area_level_2` |
| state | `administrative_area_level_1` (short_name) |
| zip | `postal_code` |
| country | `country` (short_name or long_name per app convention) |

---

## 5. Contact / Web

Populate only when Google returns the value.

| MF Field | Google Places Field |
|--------|---------------------|
| Phone | `formatted_phone_number` |
| International Phone | `international_phone_number` |
| Website | `website` |
| Google Maps URL | `url` |

---

## 6. Hours of Operation

Derived from `opening_hours.weekday_text[]`.  
Store times only (strip the leading weekday label like "Monday:").

| MF Field | Google Places Field |
|--------|---------------------|
| Monday Hours | `opening_hours.weekday_text[0]` |
| Tuesday Hours | `opening_hours.weekday_text[1]` |
| Wednesday Hours | `opening_hours.weekday_text[2]` |
| Thursday Hours | `opening_hours.weekday_text[3]` |
| Friday Hours | `opening_hours.weekday_text[4]` |
| Saturday Hours | `opening_hours.weekday_text[5]` |
| Sunday Hours | `opening_hours.weekday_text[6]` |

If `opening_hours` or `weekday_text` is missing → leave all day fields empty.

---

## 7. Relations / System-Managed Fields

| MF Field | Source |
|--------|--------|
| LocationsMasterID | Internal relation (LM → MF bidirectional write) |
| Notes | Not populated automatically |
| Created Time | Managed by Notion |
| Updated | Managed by Notion |

---

## 8. Required Google Place Details `fields` Parameter

To populate the MF schema correctly, the Place Details request **must explicitly include**:

```
place_id,
name,
formatted_address,
address_components,
geometry/location,
formatted_phone_number,
international_phone_number,
website,
opening_hours/weekday_text,
types,
url
```

If a field is not requested here, Google will **not return it**, even if data exists.

---

## 9. Key Constraints (Non-Negotiable)

- Do not infer missing data
- Do not fabricate hours, addresses, or contact info
- Leave fields empty if Google does not provide them
- Do not modify schema or field names
- MF completeness depends entirely on Place Details response

---

## 10. Validation Checklist

After implementation:
- MF rows populate all available fields from Google
- Empty fields correspond only to missing Google data
- No schema fields are silently ignored
- Debug logs clearly show populated vs missing fields

This mapping is authoritative for MF population logic.

### Field Completeness & Expected Google Data Gaps
- Nearby Search does not return formatted address, address components, hours, phone numbers, or website.
- Place Details may return these fields, but they are often missing.
- MF fields may legitimately remain empty when opening hours are unpublished, phone numbers are not provided, website is absent, or address components are incomplete.
- Empty MF fields do not indicate an error if Google did not return the data.

### Classification Authority (ER vs Urgent Care)
- MF `Type` is derived from Google `types[]` plus explicit hospital/emergency department signals.
- Only true hospital emergency departments qualify as `ER`.
- Clinics, physician offices, and non-hospital facilities must never be classified as `ER`.
- Misclassification of `Type` is a data integrity bug.

### Identifier Rules
- **MedicalFacilityID (MF###):** internal MF identifier; system-generated; globally unique.
- **Place_ID:** external canonical identifier; used for deduplication and upsert; no two MF rows may share the same `Place_ID`.

---

# 7. Medical Facilities Generation Flow

The Medical Facilities generation service is designed to find nearby hospitals and urgent care centers for a given location in the Locations Master. This is a key step in preparing location data for production use.

The relationship between Locations Master (LM) and Medical Facilities (MF) is bidirectional and must be explicitly maintained:
-   **LM → MF:** A location in the Locations Master has specific, ordered relation fields (`ER`, `UC1`, `UC2`, `UC3`) to link to its selected medical facilities. These are single-use fields, each holding a relation to exactly one medical facility. This represents a curated list of the most relevant facilities for that location.
-   **MF → LM:** A medical facility can serve multiple locations. Therefore, the `LocationsMasterID` field on a Medical Facility row is a multi-relation field that links back to all the Location Master rows that rely on it.

When the generation service runs, it performs Google Places searches to find nearby facilities, creates or updates them in the Medical Facilities database, and then writes the relationship in **both directions** to ensure data integrity.

---

# 8. Environment & Secrets

`.env` at the repo root, loaded automatically on app startup.

Example keys:

```
NOTION_TOKEN
NOTION_LOCATIONS_DB_ID
NOTION_PRODUCTIONS_DB_ID
GOOGLE_MAPS_API_KEY
PRODUCTIONS_CACHE_PATH
LOG_PATH
PRODUCTIONS_SYNC_INTERVAL
LOG_ROTATE_DAYS
LOG_MAX_ENTRIES
```

Logs and caches must never contain secret values.

---

# 9. Development Workflow

## Step 1 - Branch  
Each feature uses its own branch.

## Step 2 - Implement  
- UI remains thin  
- Logic lives in services  
- Use async and relative paths  
- Keep code modular and testable  

## Step 3 - Test  
- Local browser test  
- `python -m compileall`  
- Manual API verification  

## Step 4 - Commit  
Semantic messages:

- feat:  
- fix:  
- refactor:  
- docs:  

## Step 5 - Document  
Add to `DEV_NOTES.md`:

- Date  
- Milestone  
- Summary  
- Changes  
- Testing  
- Notes  
- Next recommendations  

## Step 6 - Sync/Share  
Short milestone summary posted back to ChatGPT to align PM + Dev agent context.

### Starting the Dev Server via run_atlsapp.ps1
- Double-click `scripts/run_atlsapp.ps1` to launch the dev server with a guided banner.
- The script auto-detects the repo venv (`.venv`, `venv`, or any sibling directory under the repo containing `Scripts\Activate.ps1`) and activates it.
- Port 8000 is preferred; if busy, the script auto-selects the next open port up to 8010 and reports the chosen port.
- If dependencies break, reactivate the venv then run `pip install -r requirements.txt` to reinstall packages.
- To regenerate the venv, run `python -m venv .venv`, reinstall requirements, and re-run `scripts/run_atlsapp.ps1` (it will reconnect to the new activation path automatically).

---

# 10. Dashboard Overview

- Metrics: Notion + Maps + job summary  
- Local-time conversion  
- Spinners during async loads  
- `/api/dashboard/summary` is the authoritative source of system state

---

# 11. UI Conventions

### GUIDANCE

- Wide tables must be wrapped in an `overflow-x-auto` container so they remain beside the sidebar and allow horizontal scroll.
- Default table text alignment is left (headers and cells) via global CSS.
- Entity ID columns (e.g., `ProductionID`) should link to a detail/edit page instead of relying on inline editing.
- When linking to authoritative sources (e.g., Notion pages), use the built-in `url` provided by the API response; do not generate or modify Notion URLs manually.
- Root layout rows should use `ui.row(no-wrap)` to prevent sidebar wrapping; sidebars should use `shrink-0`; main content should use `flex-1` with `overflow-x-auto`; sticky headers should use `sticky top-0 z-10`; optional `max-w` wrappers improve readability on very wide screens.
- All tables share a unified Material-style header row; theme toggling is global via `ui.dark_mode()`. Avoid per-page table CSS; use the global theme block to adjust header background, borders, and text for light/dark modes.
- All table styling and alignment overrides live in `app/ui/layout.py`; target Quasar utility classes (e.g., `.text-right`, `.text-center`, `justify-*`) there. Do not add per-table or per-page alignment CSS.
- Header and sidebar classes must be static (not lambda-based); typography standard is Inter/Segoe UI/Arial at 15px.
- Control bars: keep controls left-aligned with consistent gaps (gap-2), minimum height around 52px, and keep controls on one line until the viewport forces wrap.
- Table containers: wrap each table in an `overflow-x-auto` block with light vertical padding to keep spacing consistent.
- Hover/focus: use `hover:bg-slate-100` on buttons and links for consistent feedback.
- New Admin Tools page (v0.8.4): replaces Dedup Simple in the sidebar, centralizes admin/debug/maintenance operations, is visible only when `DEBUG_ADMIN=true`, and uses collapsible sections for each tool.
- Address Normalization UI is retired; normalization now runs only during ingestion (imports/repair pipelines). Do not re-enable the panel.
- Medical Facilities Maintenance (Admin Tools): backfills missing MF fields from Google Place Details, fills blanks only (no overwrites), and requires `Place_ID`.
- All ingestion paths (master, productions, facilities, dedup writebacks) must call the canonical ingestion normalizer before Notion writes; no post-hoc bulk normalization.
- Notion Address Repair Tool (backend-only, headless): `scripts/repair_addresses.py` (targets: master, productions, facilities, or all). It performs in-place normalization of existing Notion rows, never deletes or recreates pages, and preserves identifiers/relations/status values.

## Canonical Ingestion Workflow (v0.9.0)

### NON-NEGOTIABLE

This section is the authoritative specification for all ingestion-time address normalization across the system.

- Inputs: Require either Full Address or structured fields (address1, city, state, zip, country). Missing both rejects ingestion with an explicit error.
- Full Address path: Always perform a fresh Google Places lookup. Overwrite structured fields, Full Address, Place_ID, latitude/longitude, county, and borough from Google data. Store Google `formatted_address` internally as `formatted_address_google`. Produce ATLS-formatted Full Address `{address1}, {city}, {state} {zip}` (+ `, {country}` when not US).
- Structured-only path: Normalize components (Title Case city, uppercase 2-letter state, ISO 3166-1 alpha-2 country, 5-digit ZIP) and build ATLS Full Address.
- Place_ID-only path (no Full Address): Optionally refresh structured fields via Google; otherwise rely on provided canonical structured fields.
- Notion payloads: Canonical property names only (address1/2/3, city, state, zip, country, county, borough, Full Address, Place_ID, Latitude, Longitude, formatted_address_google). Status: Ready when Place_ID exists, Unresolved when missing, Matched when linked.
- Matching priority: Place_ID → address hash (address1/city/state/zip/country) → city/state/zip; assumes canonical completeness.

## Master Rebuild Workflow (v0.9.1)

- Run `python -m scripts.repair_master` to canonicalize every Locations Master row via the ingestion normalizer.
- Overwrites structured fields, ATLS Full Address, Place_ID (when available), Latitude/Longitude, county/borough, and stores `formatted_address_google`.
- Ensures address hashes and component keys reflect canonical values; assumes schema already includes canonical fields.
- Run `python -m scripts.verify_schema` to ensure Locations Master and all production `_Locations` databases have canonical properties (address1/2/3, city, state, zip, country, county, borough, Full Address, formatted_address_google, Place_ID, Latitude, Longitude, Status).

## Address Repair Tool

Purpose  
- `scripts/repair_addresses.py` performs in-place normalization of existing Notion address data across production _Locations tables, Locations Master, and Medical Facilities.  
- It corrects and standardizes existing rows; it does not replace the ingestion-time normalization pipeline.

When to Use  
- After schema corrections, ingestion bugs, or data migrations that left inconsistent or legacy address fields.  
- When a production table, Locations Master, or Facilities table shows mixed/legacy property names or inconsistent formatting.  
- Not part of routine ingestion; use as a corrective/cleanup tool.

Canonical Address Schema  
- Properties: address1, address2, address3, city, state, zip, country, county, borough, Full Address, Place_ID, Latitude, Longitude.  
- All writes must target these names. Legacy fields (e.g., "Address 1", "City", "ZIP / Postal Code") are intentionally ignored by the repair tool.

How It Works  
- Loads rows from Notion (productions, master, facilities).  
- Extracts existing values and runs the ingestion normalizer to derive structured components.  
- If structured components are missing but Full Address exists, applies a fallback parser to derive address lines/city/state/zip.  
- Builds a canonical update dict and writes only changed fields back to the same Notion rows.  
- Idempotent: rerunning after a clean pass should produce zero updates.

How to Run  
- Interactive (recommended):  
  ```
  python -m scripts.repair_addresses
  ```  
  - Shows a menu of available databases.  
  - "Dry run only" prints per-row diffs.  
  - "Apply updates" writes changes to Notion.  
  - Returns to the menu after each database is processed.  
- Non-interactive:  
  ```
  python -m scripts.repair_addresses --target productions --dry-run
  python -m scripts.repair_addresses --target master
  python -m scripts.repair_addresses --target facilities
  python -m scripts.repair_addresses --target all
  ```  
  - Summary only; no per-row diffs.

Logging  
- All Notion PATCH operations are logged to `logs/address_repair_patches.log` with timestamp, database label, row ID, and JSON payload.

Normalized Ingest Requirement  
- All future address writes (imports, dedup writebacks, facility refresh, UI/admin tools) must normalize on ingest using the canonical ingestion normalizer.  
- The Address Repair Tool is a corrective utility for historical inconsistencies, not a replacement for proper ingestion-time normalization.

### Dark Mode Source of Truth
- Quasar/NiceGUI's `body--dark` class is authoritative.
- Page header blocks must include the `atls-page-header` class so shared CSS can target them.
- **Tailwind `dark:` variants are not permitted.**

### Dark Mode Architecture
- Quasar controls dark mode using `body--dark`.
- Dark-mode visuals (layout, global header, page headers, tables) are handled via CSS keyed on `body--dark`; no Tailwind `.dark` class, `dark:` utilities, or JS toggles are used.
- Page Header Blocks and Global Header use `atls-page-header` and `atls-global-header` for reliable dark-mode overrides.

### Dark Mode Status
Dark mode rules in this document describe the current implementation and must be respected; however, dark mode behavior is frozen and must not be modified unless explicitly instructed. Dark mode is currently unstable and deferred for a later milestone.

---

# 12. Testing Guidelines

### API  
- Validate structured JSON  
- Confirm error paths  
- Check timeouts for external services  

### UI  
- Verify all buttons  
- Ensure spinners show  
- Test Settings diagnostics with/without `.env`  

### Services  
- Background sync timing  
- Log rotation/archiving  
- Cache read/write paths  

---

# 13. Documentation Rules

- README.md — User-facing summary  
- PROJECT_HANDBOOK.md — Architecture + workflow  
- DEV_NOTES.md — Session-by-session progress  
- AGENTS.md — Team roles  
- Project Framework — Master reference  

Every new feature or endpoint must be documented.

---

# 14. Versioning

Semantic versioning:

```
v0.4.0 - Dashboard
v0.4.1 - Hardening & Env Autoload
v0.4.2 - Productions + Sync
v0.4.3 - UI Enhancements + Background Sync
v0.4.4 - Diagnostics UX Polish
v0.4.5 - Async Diagnostics Timing
v0.4.6 - Full Async Conversion
v0.4.7 - Productions Table UX & Slot Fixes
v0.4.8 - Productions Layout & UX Improvements
v0.4.9 - Productions Notion Link Integration
v0.4.10 - Global Layout Improvements
v0.4.11 - Global Theme + Material Table Styles
v0.4.12 - Final Table Header Alignment & CSS Consolidation
v0.4.13 - Dark Mode Polish, Persistent Theme, Typography
v0.4.14 - Content Wrapper & Header Dark Mode Completion
v0.4.14b - Header Dark Mode Override & Unified Page Header Blocks
v0.4.15b - Unified Dark-Mode Alignment & Theme Persistence Fix
v0.4.16 - Dark-Mode Stabilization
v0.4.17 - Dark Mode Follow-up Needed
v0.5.0 - Refactor Release: codebase cleaned and reorganized for clarity and maintainability; UI modules standardized; API and service modules consolidated and de-duplicated; no functional changes (structural quality improvements only)
v0.5.1 - UI Polish: standardized header alignment, control spacing, table padding, and hover/focus styling; no functional changes
v0.5.2 - Productions Search Fix: restored client-side search on /productions with case-insensitive filtering; no layout or backend changes
v1.0.0 - Production release
```

Versioning guardrail: keep the version at the last known-good state while fixing issues; only bump after the fix is verified to work so we avoid trails of non-working “versions.”

---

## 15. Deferred Items / Parking Lot

This section tracks known issues, architectural concerns, or improvements that must be revisited in future milestones. Items here are not part of the current milestone but require planned review.

12.x Admin Tools - Production Selector & Reprocess Stability  
- Production dropdown still showing raw locations_db_id values and occasional "DB not found" errors during reprocess.  
- Future fix: enforce friendly labels with deterministic label/value mapping, add server-side validation/logging for selection vs. returned list, and prevent multi-table runs when a single db_id is chosen.

## Migration Note (v0.9.0)

Legacy fallback address parsing is removed. All ingestion paths now require Full Address or structured fields, and Full Address inputs always re-query Google to overwrite structured fields while storing `formatted_address_google` internally.

## Migration Note (v0.9.1)

Master canonicalization and matching stability: Locations Master rows must be rebuilt via the canonical normalizer; matching now uses only canonical indexes (Place_ID → address hash → city/state/zip); schema verification helper patches all `_Locations` databases to canonical fields.

## v0.9.4 – Admin Tools Modernization

### Streaming Architecture
- Dedup, Diagnostics, Cache, Schema Update, and Match All share a consistent streaming model via FastAPI `StreamingResponse`.
- UI panels disable buttons during runs, clear output, and stream lines into read-only textareas.

### Dedup Tool Behavior
- Scans Locations Master and Production `_Locations` tables.
- Duplicate detection hierarchy: identical Place_ID, identical canonical hash, identical ATLS Full Address (when available).
- Output streams grouped duplicates and recommendations; no auto-merge is performed.

### Diagnostics Behavior
- Health checks include: master row count, missing Place_ID detection, cache index sizes, Notion/Maps credential availability, and production table summaries.
- Output streams live; this is a surface-level check. Canonical drift/schema drift audits are deferred (v2 planned).

### System Info
- Structured JSON: application version, OS/Python, NiceGUI/FastAPI, cache sizes/refresh, credential presence, production DB summary.

### Known Limitations (Parking Lot)
- Production Selector / Reprocess mapping: Labels can still show DB IDs; value resolution to `locations_db_id` can misalign. Needs focused UI/value-binding review and logging.
- Diagnostics depth: Current diagnostics are shallow; full canonical drift and schema audits deferred to v0.9.5.
- Dedup coverage: Current dedup handles Place_ID and canonical hash; near-duplicate heuristics and remediation workflow are deferred.

### 12.1 Current Deferred Items

1. **Architectural redesign needed for long-running Medical Facilities fill/backfill job**  
   - v0.6.1 removes the heavy job from the GET endpoint, fixing the immediate UI timeout.  
   - However, the underlying fill/backfill process is still a synchronous, long-running operation tied to the main FastAPI worker.  
   - A future milestone should migrate this to a proper background job system (task queue, async worker, or scheduled service) with progress reporting and non-blocking execution.

2. **Argparse exit mitigation (API invoking CLI script)**  
   - The backend currently calls a CLI-style script, requiring temporary modification of `sys.argv`.  
   - Long-term fix: replace with a proper async service module and remove CLI/argparse dependencies from API flows.

3. **config.py inconsistencies and missing Notion ID handling**  
   - Some Notion database IDs required by facility scripts were missing or mismatched.  
   - A full review and alignment of config.py with the other ATLSApp config modules is needed.

4. **Drawer → Dialog fallback due to NiceGUI prop limitations**  
   - NiceGUI’s drawer props (e.g., `right=True`) were not stable, requiring fallback to a right-side dialog.  
   - Revisit once NiceGUI stabilizes drawer parameters in future releases.

5. **Scaling of Facility Sync (full data pull may exceed current architecture)**  
   - As Medical Facilities grow, the heavy fill/backfill job may need to be moved to a dedicated process with caching or incremental updates.  
   - Evaluate in a backend-focused milestone (v0.7.x or later).

6. **Responsive Layout Redesign (Replace Global max-width with Grid-Based Layout)**  
   - The current layout uses a fixed `max-w-[1600px]` container, centered with `mx-auto`, which limits width on large displays.  
   - In a future milestone, replace this with a responsive grid-based shell to allow tables and data-heavy pages to use more screen width while preserving readability on smaller viewports.

7. **Medical Facilities – Backend Search Endpoint (Server-Side Filtering)**  
   - The v0.6.x implementation uses client-side filtering after a single bulk fetch, which is appropriate for the current dataset size (~300–400 facilities).  
   - A future milestone (v0.7.x or later) should introduce a dedicated backend search endpoint using Notion filters and caching.

8. **Medical Facilities - Server-Side Search, Caching & Bulk Retrieval**  
   - Introduce API-level caching and bulk retrieval to reduce Notion round-trips.  
   - Depends on background job architecture and Facility Sync service.

9. **Production Template Bundle (Automated New-Production Setup)**  
   - Standardized production template with schema, relations, naming, and defaults.

10. **Enforce Unique Production Name (Validation at Create/Edit)**  
    - Prevent exact duplicate Production Name values in Productions Master.

---

# 16. Collaboration Roles

- Jay - Owner  
- ChatGPT - Project Manager  
- Codex 5 - Developer  

---

# 17. Notes for Codex 5

- Avoid blocking the UI event loop  
- Use async httpx for network calls  
- Always wrap external calls with try/except  
- Keep changes modular  
- Update `DEV_NOTES.md` every session  
- Follow this Handbook and the Project Framework
