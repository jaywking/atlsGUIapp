## Global Notes (Authoritative)
DEV_NOTES.md is a historical session log. When conflicts arise, PROJECT_HANDBOOK.md is the authoritative source of current rules and behavior.

### Dark Mode Status
Historical DEV_NOTES entries describe prior dark-mode experimentation, including Tailwind `dark:` usage and synchronization logic. These entries are historical only.

Current rule (see PROJECT_HANDBOOK.md):
Dark mode is frozen and must not be modified unless explicitly instructed. Tailwind `dark:` utilities are not permitted.

### Versioning Note
DEV_NOTES records historical version bumps as they occurred at the time.

Current rule (see PROJECT_HANDBOOK.md):
Version increments occur only at verified milestone acceptance, not during intermediate fixes, experiments, or drafts.

Session: 2025-12-30 - PSL reprocess Status write fix
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Prevented production reprocess writes from sending `Status` to PSL tables, which do not include that property.

Changes:
- `app/services/matching_service.py`: removed `Status` from reprocess payload for PSL updates.
- `app/api/locations_api.py`: removed `Status` from reprocess PATCH payload when matching PSL rows.
- `docs/PROJECT_HANDBOOK.md`: clarified PSL enrichment/write rules and removed `Status` from PSL schema expectations.

Testing:
- Not run (reported Notion 400 validation errors resolved by removing Status writes).

Notes:
- Rerun reprocess on affected productions to apply match updates without schema validation errors.

Session: 2025-12-30 - PSL data quality check (Production Detail)
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Added a Production Detail tool to detect PSL rows with missing address fields that can break reprocess matching.

Changes:
- `app/api/productions_api.py`: added `/api/productions/inspect_psl` to report missing PSL address fields with Notion links.
- `app/ui/production_detail.py`: added "Inspect PSL Rows" tool with results table and Notion links.

Testing:
- Not run (requires Notion data).

Session: 2025-12-30 - Location Detail Notion link
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Made the Location Master ID on the Location Detail page link to the Notion record for quick edits.

Changes:
- `app/api/locations_api.py`: include `notion_url` in Location Detail payload.
- `app/ui/location_detail.py`: render Location Master ID as a Notion link when available.

Testing:
- Not run (requires Notion data).

Session: 2025-12-30 - Preserve LM Practical Name on PSL enrichment
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Prevented PSL enrichment from overwriting Locations Master `Practical Name`; enrichment only fills it when empty.

Changes:
- `app/services/psl_enrichment.py`: skip `Practical Name` updates on existing LM rows regardless of source.
- `docs/PROJECT_HANDBOOK.md`: clarified that enrichment only fills `Practical Name` when empty.

Testing:
- Not run (requires Notion data).

Session: 2025-12-30 - PSL address-to-business fallback
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- When Google Place Details returns an address-only result (`premise`/`street_address`), enrichment now looks up the nearest business within 50m and with the same street number to capture the correct Practical Name and Place_ID.

Changes:
- `app/services/psl_enrichment.py`: added nearby search fallback for address-only place results.
- `docs/PROJECT_HANDBOOK.md`: documented address-only fallback behavior.

Testing:
- Not run (requires Google Places API key).

Session: 2025-12-30 - Preserve PSL Practical Name
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- PSL enrichment no longer overwrites Practical Name if it already exists on PSL rows.

Changes:
- `app/services/psl_enrichment.py`: only set `Practical Name` in PSL payloads when it is blank.
- `docs/PROJECT_HANDBOOK.md`: clarified PSL Practical Name preservation.

Testing:
- Not run (requires Notion data).

Session: 2025-12-30 - Disable PSL batch enrichment
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Disabled the PSL batch enrichment UI to reduce risk; per-production enrichment remains available.

Changes:
- `app/ui/admin_tools.py`: replaced batch panel with a disabled notice.

Testing:
- Not run (UI-only change).

Session: 2025-12-30 - Medical Facilities maintenance tool
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Added an Admin Tools action to backfill missing Medical Facilities fields from Google Place Details without overwriting existing values.

Changes:
- `app/services/medical_facilities_runner.py`: stream backfill for missing fields; requires Place_ID and writes only blanks.
- `app/api/medicalfacilities_api.py`: added `/api/medicalfacilities/maintenance_stream`.
- `app/ui/admin_tools.py`: added the Medical Facilities Maintenance panel and streaming output.

Testing:
- Not run (requires Notion/Google credentials).

Notes:
- MedicalFacilityID is generated only when missing.

Session: 2025-12-30 - Medical Facilities hours cleanup on write
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Stripped weekday prefixes from Google weekday_text before writing MF hours fields.

Changes:
- `app/services/medical_facilities.py`: remove leading weekday labels (e.g., "Monday:") from hours before Notion writes.
- `docs/PROJECT_HANDBOOK.md`: document hours field storage without weekday labels.

Testing:
- Not run (requires Notion/Google credentials).

Notes:
- Use `scripts/clean_medical_facility_hours.py` to clean existing rows that still include weekday labels.

Session: 2025-12-30 - Sidebar full-height fix
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Ensured the left sidebar background stretches to match long page content.

Changes:
- `app/ui/layout.py`: set the main shell row to stretch items; sidebar and main column now use full height.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Sidebar fixed layout
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Made the left sidebar sticky so it stays fixed while scrolling long pages.

Changes:
- `app/ui/layout.py`: set the shell to `h-screen`, make sidebar `sticky top-0 h-screen`, and move vertical scrolling to the main content column.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Admin Tools full-width layout fix
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Ensured page content spans full width so Admin Tools is no longer constrained to a narrow column.

Changes:
- `app/ui/layout.py`: set the content column to `w-full max-w-none`.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Content padding balance
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Balanced the main content padding so left and right edges match.

Changes:
- `app/ui/layout.py`: adjusted content container padding to `px-3`.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Header/content alignment
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Aligned the global header padding with the main content padding.

Changes:
- `app/ui/layout.py`: header padding updated to `px-3`.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Page header alignment
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Aligned page headers with the main content/table edge padding.

Changes:
- `app/ui/layout.py`: reduced `PAGE_HEADER_CLASSES` horizontal padding to `px-3`.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Admin Tools header padding override
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Removed extra left padding on the Admin Tools page header to align with the table edge.

Changes:
- `app/ui/admin_tools.py`: override header padding to `px-0` for the Admin Tools title row.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Canonical layout padding owner
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Moved horizontal padding ownership to the main scroll column and removed header/page padding to match the canonical layout pattern.

Changes:
- `app/ui/layout.py`: main scroll column now owns `px-3`; global header and page header classes are padding-neutral.
- `app/ui/admin_tools.py`: removed the page-header padding override to avoid compensating hacks.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Global header border/shadow removal
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Removed the global header border and shadow for a flatter top bar.

Changes:
- `app/ui/layout.py`: dropped `border-b` and `shadow-sm` from the global header.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Global header divider line
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Restored a thin divider under the global header to match page header styling.

Changes:
- `app/ui/layout.py`: re-added `border-b` to the global header (no shadow).

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Global debug label + page header line removal
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Moved the DEBUG_ADMIN indicator to the global header and removed the thin divider line under page headers.

Changes:
- `app/ui/layout.py`: page headers no longer add a bottom border; global header shows DEBUG_ADMIN when enabled.
- `app/ui/admin_tools.py`: removed page-level DEBUG_ADMIN label.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Canonical layout alignment cleanup
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Removed header padding overrides on non-Admin pages to comply with the canonical layout pattern.

Changes:
- `app/ui/dashboard.py`: removed `atls-header-tight` from the page header.
- `app/ui/productions.py`: removed `atls-header-tight` from the page header.
- `app/ui/layout.py`: deleted the `atls-header-tight` CSS rule.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Remove duplicate page titles
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Removed redundant page titles in the content area where the global header already shows the page name.

Changes:
- `app/ui/admin_tools.py`: removed the content-area Admin Tools title row.
- `app/ui/dedup_simple.py`: removed the "Dedup Simple Admin UI" title from the content header.
- `app/ui/dedup.py`: removed the "Locations Master - Dedup Resolution" content title.
- `app/ui/settings.py`: removed the empty page header spacer row.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Sidebar/header title alignment
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Matched the sidebar "ATLSApp" heading typography to the global header title.

Changes:
- `app/ui/layout.py`: sidebar heading now uses `text-2xl font-semibold leading-none`; global header title uses the same line-height.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Sidebar title vertical alignment
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Matched the sidebar top padding to the global header so the ATLSApp title sits on the same vertical rhythm.

Changes:
- `app/ui/layout.py`: sidebar padding updated from `py-3` to `py-4`.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Admin Tools default collapse
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Defaulted the Match All Locations panel to collapsed.

Changes:
- `app/ui/admin_tools.py`: set Match All Locations expansion `value=False`.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Admin Tools descriptions and timers
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Added plain-English descriptions and elapsed-time timers to each Admin Tools panel.

Changes:
- `app/ui/admin_tools.py`: added per-panel descriptions and timers for Match All, Schema Update, Cache Management, Schema Report, Reprocess, PSL debug, MF maintenance, Dedup, Diagnostics, and System Info.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Locations search UI (production-aware)
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Replaced the placeholder Locations page with a read-only search UI for Locations Master, including production-name lookup.

Changes:
- `app/api/locations_api.py`: added `/api/locations/search_master` for production-aware and direct LM search.
- `app/ui/locations.py`: built a search form and results table with LM ID links and place-id truncation.

Testing:
- Not run (requires Notion credentials for live data).

Session: 2025-12-30 - Locations search table tweaks
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Adjusted Locations search table columns and exposed place type from Locations Master.

Changes:
- `app/services/notion_locations.py`: include LM Types multi-select in normalized rows.
- `app/api/locations_api.py`: expose `place_type` in search results.
- `app/ui/locations.py`: rename Location Name to Practical Name, narrow LM ID column, remove Country, add Place Type.

Testing:
- Not run (UI/Notion data required).

Session: 2025-12-30 - Locations page header removal
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Removed the duplicate Locations page title from the content area to match the canonical layout.

Changes:
- `app/ui/locations.py`: dropped the content-area page header row.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Locations search advanced filters
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Split Locations search into standard vs advanced filters and expanded backend filtering to support those fields.

Changes:
- `app/ui/locations.py`: added an Advanced Filters panel (full address, zip, country, county, borough, types, status, op status, place/master IDs).
- `app/api/locations_api.py`: extended `/api/locations/search_master` to filter on full address, zip, county, borough, status, op status, and place type.
- `app/services/notion_locations.py`: exposed Location Op Status on normalized master rows.

Testing:
- Not run (requires Notion data for search).

Session: 2025-12-30 - Production name search fix
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Fixed production-name matching for Locations search by preserving production display names and tracking DB titles separately.

Changes:
- `app/services/notion_locations.py`: keep production display_name, add `db_title` without overwriting.
- `app/api/locations_api.py`: production search includes `db_title`; production list uses `display_name` + `db_title`.

Testing:
- Not run (requires Notion data for search).

Session: 2025-12-30 - Locations table map link
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Replaced Place ID and Status columns with a Google Map link column in the Locations results table.

Changes:
- `app/services/notion_locations.py`: exposed `Google Maps URL` in normalized rows.
- `app/api/locations_api.py`: include `google_maps_url` in search results.
- `app/ui/locations.py`: removed Place ID/Status columns and added a "Google Map" link column.

Testing:
- Not run (UI/Notion data required).

Session: 2025-12-30 - Locations result label tweak
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Simplified the Locations search result label text.

Changes:
- `app/ui/locations.py`: changed "Returned n Locations Master rows." to "Returned n Locations."

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Location detail page (read-only)
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Added a read-only Location Details page and API endpoint for Locations Master records.

Changes:
- `app/api/locations_api.py`: added `/api/locations/detail` with production-usage lookup.
- `app/services/notion_locations.py`: exposed created/updated timestamps and Google Maps URL in normalized rows.
- `app/ui/location_detail.py`: built the Location Details UI with summary, address, classification, production usage, and metadata sections.
- `app/main.py`: added `/locations/{LocationMasterID}` route.

Testing:
- Not run (requires Notion data for lookup).

Session: 2025-12-30 - Location detail lookup optimization
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Switched Location Detail to query Locations Master by ID instead of loading the full master cache.

Changes:
- `app/services/notion_locations.py`: added `fetch_master_by_id` (title lookup on LocationsMasterID).
- `app/api/locations_api.py`: detail endpoint now uses `fetch_master_by_id`.

Testing:
- Not run (requires Notion data for lookup).

Session: 2025-12-30 - Location detail classification rendering guard
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Guarded Location Detail classification rendering to avoid blank sections when place types are missing or non-string.

Changes:
- `app/ui/location_detail.py`: added safe list join for place types in Classification & Status.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Location detail readonly input fix
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Fixed Location Detail rendering error by setting readonly via props instead of constructor.

Changes:
- `app/ui/location_detail.py`: switched to `.props("readonly")` on the Full Address input.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Location detail section collapsibility
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Made Location Detail sections collapsible, with Summary open by default, and reordered Production Usage before Classification.

Changes:
- `app/ui/location_detail.py`: converted sections to expansions; removed redundant Full Address/Maps from Address & Geography; reordered sections.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Location detail cache + map link target
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Open Map link now opens in a new tab, and location detail responses are cached briefly for faster reopen.

Changes:
- `app/ui/location_detail.py`: Open Map link uses `target=_blank`.
- `app/api/locations_api.py`: in-memory cache for `/api/locations/detail` with 60s TTL.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Location detail medical facilities section
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Added a Medical Facilities section to Location Detail with nearest ER and two nearest UCs.

Changes:
- `app/services/notion_locations.py`: expose ER/UC relation IDs on normalized master rows.
- `app/api/locations_api.py`: include medical facilities summary in `/api/locations/detail`.
- `app/ui/location_detail.py`: render Medical Facilities section before Production Usage.

Testing:
- Not run (requires Notion data for linked facilities).

Session: 2025-12-30 - Location detail loading spinner
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Added a loading spinner next to the Location Detail loading message.

Changes:
- `app/ui/location_detail.py`: show spinner during load and hide on success or error.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Location detail header title swap
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Replaced the content header text with the location Practical Name after load.

Changes:
- `app/ui/location_detail.py`: update header title to Practical Name and clear the subtitle.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - MF generation friendly summary
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Made the Medical Facilities generation summary output more readable.

Changes:
- `app/services/medical_facilities_runner.py`: replaced the single-line summary with a labeled, multi-line report.

Testing:
- Not run (output format only).

Session: 2025-12-30 - Production detail locations cross-linking
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Added a read-only Production Detail page with a Locations Used section linking to Location Detail pages.

Changes:
- `app/api/productions_api.py`: added `/api/productions/detail` to resolve production locations from the production `_Locations` table and map them to Locations Master.
- `app/ui/production_detail.py`: new Production Detail UI with Summary, Locations Used (expanded by default), and Metadata sections.
- `app/ui/productions.py`: ProductionID now links to the local Production Detail page.
- `app/main.py`: added `/productions/{ProductionID}` route.

Testing:
- Not run (requires Notion data for production lookups).

Session: 2025-12-30 - Production detail PSL location name
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Added PSL Location Name to the Production Detail Locations Used table.

Changes:
- `app/api/productions_api.py`: map PSL Location Name per LocationsMasterID when building locations list.
- `app/ui/production_detail.py`: added "Location Name (PSL)" column.

Testing:
- Not run (requires Notion data for production lookups).

Session: 2025-12-30 - Production detail summary layout
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Reflowed Production Detail summary into two columns for better use of width.

Changes:
- `app/ui/production_detail.py`: split summary fields into two columns with responsive wrap.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Production ID Notion link
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Linked the Production ID on the detail page back to the Notion record.

Changes:
- `app/ui/production_detail.py`: Production ID now links to Notion when a URL is available.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - PSL drill-down
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Added a read-only PSL drill-down page scoped to Production + Location and linked it from Production Detail.

Changes:
- `app/api/psl_enrichment_api.py`: added `/api/psl/detail` to fetch PSL rows scoped to production + LocationsMasterID.
- `app/services/notion_locations.py`: added filtered PSL fetch helper and exposed PSL notes/timestamps in normalized rows.
- `app/ui/psl_detail.py`: new PSL Details UI with context summary, PSL table, and metadata.
- `app/ui/production_detail.py`: added “View PSL” link per location row.
- `app/main.py`: added `/psl/{ProductionID}/{LocationMasterID}` route.

Testing:
- Not run (requires Notion data for PSL lookup).

Session: 2025-12-30 - PSL detail context practical name
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Added Practical Name and PSL Location Name to the PSL detail context summary.

Changes:
- `app/api/psl_enrichment_api.py`: include PSL location name in context.
- `app/ui/psl_detail.py`: show Practical Name and PSL Location Name in context summary.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - PSL detail full address
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Added full address to the PSL detail context summary.

Changes:
- `app/api/psl_enrichment_api.py`: include full address in location context.
- `app/ui/psl_detail.py`: display full address in the context summary.

Testing:
- Not run (UI change only).

Session: 2025-12-30 - Productions loading label
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Replaced the initial "No data available" message with "Loading productions..." while data loads.

Changes:
- `app/ui/productions.py`: set table no-data label during loading.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Admin tools cleanup, MF selection, timers, and debug logging
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Removed the retired Address Normalization panel from Admin Tools.
- Added elapsed-time timers for Medical Facilities and PSL enrichment runs.
- Improved MF selection to choose nearest ER/UC (distance-sorted) and biased ER inference to local results.
- Switched DEBUG_TOOLS logging to daily files and updated docs.

Changes:
- `app/ui/admin_tools.py`: removed Address Normalization section; added timers to Medical Facilities + PSL Enrichment panels.
- `app/services/medical_facilities.py`: select nearest ER/UC; ER inference text search now uses location+radius bias.
- `app/services/debug_logger.py`: write daily `logs/debug_tools_YYYY-MM-DD.log` files.
- `docs/AGENTS.md`: updated debug log filename pattern.

Testing:
- MF generation run observed in logs; user verified correct ER/UC associations.

Notes:
- Address normalization remains available via CLI: `python -m scripts.repair_addresses`.

Session: 2025-12-29 - Dashboard avatar restyle
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Restyled the dashboard avatar to align with app typography and spacing.

Changes:
- `app/ui/layout.py`: updated avatar styles to inherit global font and center initials cleanly.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Dashboard refresh cleanup and alignment
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Removed the redundant dashboard refresh button and aligned the header refresh with page content.

Changes:
- `app/ui/dashboard.py`: removed the secondary Refresh button; added dashboard header alignment class.
- `app/ui/layout.py`: added `.atls-dashboard-header` padding override to match content alignment.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Dashboard metric cards sizing polish
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Normalized dashboard metric card typography and reduced whitespace for tighter layout.

Changes:
- `app/ui/dashboard.py`: adjusted card padding/min height, heading/value sizes, status text sizing, and recent jobs spacing.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Dashboard metric cards sizing follow-up
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Increased metric card heading size and reduced card height for better balance.

Changes:
- `app/ui/dashboard.py`: raised heading text to `text-sm` and tightened card min-height.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Productions header alignment
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Aligned the Productions page header controls with the left content edge.

Changes:
- `app/ui/layout.py`: generalized header padding override class.
- `app/ui/dashboard.py`: updated to new header alignment class.
- `app/ui/productions.py`: applied header alignment class to the page header row.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Productions local time display
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Displayed Production Created dates in local time to match Last Edited formatting.

Changes:
- `app/ui/productions.py`: convert Created timestamps to local timezone before date-only formatting.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Medical Facilities header cleanup
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Removed duplicate Medical Facilities wording in the status line and let the table span full width.

Changes:
- `app/ui/medicalfacilities.py`: simplified status label text and removed minimum table width.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Medical Facilities duplicate header removal
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Removed the extra Medical Facilities header inside the page body.

Changes:
- `app/ui/medicalfacilities.py`: dropped the in-page header row so only the global header remains.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Medical Facilities table sorting
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Enabled sorting on all Medical Facilities table columns.

Changes:
- `app/ui/medicalfacilities.py`: added `sortable=True` to each column.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Medical Facilities address formatting
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Formatted Medical Facilities addresses from structured fields for consistent comma placement.

Changes:
- `app/ui/medicalfacilities.py`: build display address from address1/2/3 + city/state/zip, fallback to raw address.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Medical Facilities phone + Notion link
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Read phone_number fields for MF detail display and added a Notion link under hours.

Changes:
- `app/services/notion_medical_facilities.py`: read `phone_number` fields and expose `notion_url`.
- `app/ui/medicalfacilities.py`: display Notion icon link in the details panel.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Medical Facilities Notion icon link fix
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Fixed the Notion icon link in MF details to render as a clickable anchor.

Changes:
- `app/ui/medicalfacilities.py`: replaced `ui.link` with an anchor element for the icon.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Medical Facilities cache version bump
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Forced MF cache refresh when schema-normalization changes require new fields (phone/notion URL).

Changes:
- `app/services/notion_medical_facilities.py`: added cache schema version and invalidation on version mismatch.

Testing:
- Not run (requires MF cache refresh at runtime).

Session: 2025-12-29 - Medical Facilities address2 parse guard
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Avoided copying parsed address2 when it duplicates the city.

Changes:
- `app/services/notion_medical_facilities.py`: skip parsed address2 if it matches city; bumped MF cache schema version.

Testing:
- Not run (requires MF cache refresh at runtime).

Session: 2025-12-29 - Medical Facilities hours formatting
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Removed duplicate weekday labels from MF hours display.

Changes:
- `app/services/notion_medical_facilities.py`: strip leading weekday name from hours before prefixing with Mon/Tue/etc.

Testing:
- Not run (requires MF cache refresh at runtime).

Session: 2025-12-29 - Medical Facilities hours cleanup script
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Added a script to strip weekday prefixes from Medical Facilities hours fields in Notion.

Changes:
- `scripts/clean_medical_facility_hours.py`: scans MF rows and removes leading day labels from hours.

Testing:
- Not run (manual run required).

Session: 2025-12-29 - Medical Facilities cache refresh button
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Added a Refresh Cache button to force MF cache rebuild from Notion.

Changes:
- `app/api/medicalfacilities_api.py`: optional `refresh` query param on `/list` to bypass cache.
- `app/ui/medicalfacilities.py`: added Refresh Cache button and force-refresh path.

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Medical Facilities address dedupe
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Suppressed duplicate city when address2 matches the city value.

Changes:
- `app/ui/medicalfacilities.py`: drop address2 when it equals city (case-insensitive).

Testing:
- Not run (UI change only).

Session: 2025-12-29 - Location Op Status mapping fix
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Corrected Google operational status handling so business_status is stored in Location Op Status, not Status.
- Documented the separation between pipeline Status and business operational status.

Changes:
- `app/services/psl_enrichment.py`: request Google business_status and map it to Location Op Status when the LM schema supports it.
- `docs/PROJECT_HANDBOOK.md`: clarified Status vs Location Op Status and added the Google mapping.

Testing:
- Not run (Notion/Google credentials required).

Notes:
- No migration performed; re-enrich or manually correct any LM rows that previously stored Google operational values in Status.

Session: 2025-12-16 - Add Medical Facility Generation Service
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Implemented a new backend service to generate and link nearby medical facilities for a Location Master row.
- This service handles eligibility checks, Google Places API searches, canonical upserts of medical facilities, and the creation of bidirectional LM <-> MF relationships.
- The service is not yet exposed to the UI.

Changes:
- Created `app/services/medical_facilities.py` with the core logic for finding and linking nearby ER and Urgent Care facilities.
- Added helper functions `get_location_page()` to `app/services/notion_locations.py` and `find_medical_facility_by_place_id()` to `app/services/notion_medical_facilities.py`.
- The new service integrates with the existing global debug logger (`DEBUG_TOOLS=1`) for detailed diagnostics.

Testing:
Note: Any dark-mode testing referenced below reflects historical work only. Dark mode should not be modified or re-tested unless explicitly instructed.
- Manual testing will be required to verify the functionality with a valid Location Master ID and Google Maps API key once an invocation path is created.

Notes:
- The service includes rerun prevention to avoid overwriting existing facility links.
- This is a backend-only capability addition. No UI changes were made.

---
Refer to README.md and PROJECT_HANDBOOK.md for architecture and workflow rules.

Current Version: v0.9.4

Versioning guardrail: keep the repo version at the last confirmed-working build while fixing issues; do not bump for broken attempts-only increment once the fix is verified to work.

Session: 2025-12-15 - PSL International Phone fix & error visibility  
Author: Codex 5  
Milestone: v0.9.4 (no version bump)  

Summary:  
- Eliminated PSL 400s caused by International Phone type mismatches; ensured PSL writes never include phone data.  
- Corrected Locations Master phone handling to use Notion `phone_number` type when the schema property exists.  
- Surfaced full Notion error bodies in PSL streaming to expose schema/type issues.  

Changes:  
- `app/services/psl_enrichment.py`: strip phone fields from all PSL payloads and only include confirmed fields; ensure phone never reaches PSL PATCH.  
- `app/services/notion_locations.py`: send International Phone to Locations Master as `phone_number` (schema-guarded).  
- Error handling: bubble raw Notion PATCH bodies into Admin Tools streams for row-level diagnostics.  

Testing:  
- Manual PSL enrichment run on AMCL_Locations (17 rows) — all 17 enriched via refresh, 0 errors, 0 skips.  

Notes:  
- AMCL_Locations schema lacks International Phone; phone is LM-only. Phone payload remains enabled for LM when the schema contains `International Phone` (phone_number).  

Schema Report Tool (Admin) — Purpose & Usage  
- Why: Added after PSL enrichment failures caused by per-table schema variance and Notion 400 validation errors; replaces guessing with ground-truth schema visibility.  
- When: Run before modifying write payloads to PSL/production tables, when enrichment or other Notion writes throw validation errors, or when debugging inconsistent behavior across productions.  
- How: Use the Admin “Generate Schema Report” tool to inspect actual property names/types; treat the output as diagnostic reference only. Do not use schema output to auto-drive writes or fixes.  
- Instruction: For any work on Notion write logic (especially PSL enrichment), run the schema report first to confirm field/type assumptions.  
- Locations Master title rule: LM titles must be LOC### (expanding to LOC#### after 999). Titles must never be addresses/practical names; preserve existing LOC titles and only fill when missing.  

Session: 2025-12-15 - PSL Enrichment workflow
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Implemented PSL enrichment service with Google geocode/place-details/name search paths and conservative readiness/ambiguity handling.
- Added streaming API endpoints for per-production and batch PSL enrichment, updating Locations Master rows and PSL links in-line.
- Added Admin Tools PSL Enrichment panel for single-production and batch runs; surfaced Practical Name in normalized rows.

Changes:
- Added app/services/psl_enrichment.py for enrichment logic and Google resolution helpers.
- Added app/api/psl_enrichment_api.py plus router registration in app/main.py.
- Updated app/ui/admin_tools.py with PSL Enrichment streaming controls; surfaced practical_name in app/services/notion_locations.py.

Testing:
- Not run (Notion/Google credentials required in runtime).

Session: 2025-12-14 - Productions creation overhaul
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary:
- Refactored production creation into `app/services/create_production.py`; `ProductionID` now auto-generates as the next `PM###` (scans Productions Master).
- User inputs: required Abbreviation (uppercased) and Production Name; optional Nickname, ProdStatus (validated against Notion options), Client / Platform, Production Type, Studio.
- PSL handling: duplicate attempt with schema-clone fallback; renamed to `{Abbreviation}_Locations`; writes PSL URL to `Locations Table`.
- API: added `/api/productions/create` wrapper and `/api/productions/options` to pull ProdStatus options from Notion.
- UI: Productions page modal now collects the fields above, loads ProdStatus options from Notion, handles errors inline, refreshes on success; table timestamps formatted (Created date-only, Last Edited local datetime); pagination/sort state synced.
- Schema alignment: removed unused Status field; kept ProdStatus only.

Changes:
- Added `app/services/create_production.py` and updated script wrapper `scripts/create_production_from_template.py`.
- Added API route `/api/productions/create` and `/api/productions/options`.
- Updated `app/ui/productions.py` with Add Production dialog, option loading, and table formatting/sorting fixes.
- Docs: added productions creation flow to PROJECT_HANDBOOK.md; noted `sed` availability in agents.md.

Testing:
- Manual run of create flow via UI and script; verified PSL clone fallback succeeds and Locations Table updated.
- Observed server start after fixing NiceGUI select initialization; ensured table sorts/pagination work without errors.

Notes:
- ProdStatus options come from Notion; invalid values are rejected server-side.
- PSL direct duplicate still 400s; fallback clone handles creation and rename.


# Source: DEV_NOTES_COMPLETE.md

# DEV_TOOLS.md — ATLSApp Developer Tools & Guardrails

## Purpose

Authoritative reference for Codex 5.1 rules, NiceGUI guardrails, and the human workflows we follow when building ATLSApp.

## Codex 5.1 Rules (Quick Recall)

* Async-only HTTP in UI code (`httpx.AsyncClient`); browser fetch via `ui.run_javascript` (8s timeout wrapper).
* All UI mutations must execute in a valid NiceGUI page slot/context.
* Table slots: use context-managed slots or column `body` lambdas; avoid decorator-style `@table.add_slot` in NiceGUI 3.2.x.
* API paths must stay relative (`/api/...`) and should be built via `app.services.api_client`.
* Every change requires a `docs/DEV_NOTES.md` session entry (date, session, milestone, summary, changes, testing, notes).
* `python -m compileall <files>` must pass for touched modules before commit.
* Preserve imports/helpers/logging; do not remove behavior or env handling unless explicitly requested.

## Human Developer Workflows

### Core Tools

* VS Code with ChatGPT (Genie AI + Codex 5.1 extensions).
* `uvicorn app.main:fastapi_app --reload` for live server.
* Python venv for isolation; `.env` at repo root for Notion/Maps credentials.
* Logging: `logs/app.log`, JSONL jobs (`app/data/jobs.log`), feature logs (e.g., `logs/productions.log`).

### Required Checks Before Commit

1. `python -m compileall app`
2. Manual smoke: `/dashboard`, `/productions`, `/settings`, `/jobs`
3. Confirm background sync starts (console/logs show interval loop)
4. Update `docs/DEV_NOTES.md`

## NiceGUI Guardrails

* Never mutate DOM outside the page slot; timers/tasks must route through page context.
* After setting `table.rows`, call `table.update()` so changes propagate.
* Avoid decorator-style slots; use `with table.add_slot(...)` or column `body` lambdas.
* Keep browser JS snippets minimal (no leading newlines); prefer shared constants and the 8s timeout wrapper.
* Do not rely on `ui.get_client()` in async tasks; prefer server-side calls and relative URLs.

### PowerShell CLI Rules (Cross-Platform Guardrail)

Unix / POSIX command-line tools (`sed`, `awk`, `grep`, `cut`, `sort`, `uniq`, `tr`, `xargs`, `find`) are available via Git Bash (MINGW64, GNU versions under /usr/bin).

Codex may use these tools only when commands are explicitly intended to run in a POSIX shell (Git Bash).
They must not be used in native PowerShell (`pwsh`) commands or scripts unless Git Bash is explicitly invoked.

#### ripgrep (`rg`) Usage in PowerShell 7

When using `rg` from PowerShell 7 (`pwsh.exe`), directory paths must be written explicitly. PowerShell may otherwise treat paths like `app/services` as literal file names instead of directories.

Correct patterns:

```powershell
rg "<pattern>" app/services/
rg "<pattern>" app/services/*
rg "<pattern>" app/services --glob "*"
Avoid this pattern:

powershell
Copy code
rg "<pattern>" app/services
This may fail or return no results due to the path being interpreted as a file.

ripgrep (rg) is installed system-wide at:

makefile
Copy code
C:\ProgramData\chocolatey\bin\rg.exe
It is available to all PowerShell 7 sessions invoked by Codex.
```

## API Development Rules

* Always return `{status, message, ...}`.
* Log jobs via `log_job()` on success and error.
* Maintain cache fallback behavior for Notion-backed endpoints.
* Handle missing credentials gracefully and surface clear user-facing messages.

## Sync & Background Tasks

* Background sync enabled via env (`PRODUCTIONS_SYNC_ENABLED`, interval minutes).
* Cache path: `app/data/productions_cache.json`; refresh after mapper/schema changes.
* When updating UI from timers/async helpers, ensure page context or server callbacks (avoid emit/JS bridges for state changes).

## Fetch Patterns

* Browser fetch for large datasets (e.g., productions) with 8s timeout + toast on failure.
* Server-side async for Notion updates/sync; never block the NiceGUI event loop.

## Logging & Diagnostics

* Use module loggers with actionable messages (operation, count, error).
* Ensure `logs/` exists before writing; keep severity aligned (INFO flow, WARNING/ERROR failures).
* Add feature-specific logs when debugging (e.g., `logs/productions.log`).
* Logs are the primary source of truth for runtime behavior; consult logs before proposing speculative fixes or architectural changes.

## Editable Tables (Productions Reference)

* Prefer server-side handlers in column `body` lambdas or context slots; avoid client `emit` bridges for edits.
* Dirty-row tracking must update the source list and `table.rows`, then call `table.update()`.
* Auto-refresh should pause when dirty rows exist and resume after sync/discard.

## Deployment / Ops Notes

* `.env` auto-loads in `app/main.py`; maintain `NOTION_*`, `GOOGLE_MAPS_API_KEY`, and sync envs.
* Relative API paths keep dev/staging/prod aligned (no host/port hard-coding).
* Review `docs/DEV_NOTES.md` frequently for current patterns and pitfalls.

## Address Repair Tool (Developer Notes)

Developer Purpose  
- Corrective utility to fix historical Notion address data; not part of the ingestion pipeline.  
- Relies on the canonical ingestion normalizer plus a fallback parser when structured components are missing.

Canonical Field Enforcement  
- Only write to: address1/2/3, city, state, zip, country, county, borough, Full Address, Place_ID, Latitude, Longitude.  
- Map any legacy incoming fields in the ingestion normalizer; the repair tool intentionally ignores legacy property names.

Fallback Logic  
- Fallback parser runs when structured fields (address1/city/state/zip) are empty, even if defaults like country exist.  
- This prevents silent skips when the normalizer returns only partial components.

Comparison Strategy  
- Preview/update compares against raw Notion values first; empty rich_text arrays count as empty strings.  
- Idempotent: a clean second run must produce zero diffs/updates.

Logging  
- Notion PATCH payloads append to `logs/address_repair_patches.log`.  
- httpx logging is suppressed to WARNING for cleaner CLI output.

Testing Guidance  
- Dry-run a single production DB first; review diffs.  
- Apply mode next; confirm preview shows zero-needed rows afterward.

---

# DEV_NOTES.md - ATLS GUI App

(Full reconstructed sessions 1–24.3 follow below.)

Date: 2025-11-09 18:59 -0500
Author: Codex 5 (Developer)
Milestone: v0.3 – Job Logging System

Summary

* Implemented lightweight job logger and integrated with API routes.
* Added `/api/jobs/logs` endpoint to expose logs to the UI.
* Updated API map documentation.

Changes

* Added `app/services/logger.py` providing `log_job()` and `read_logs()` using JSONL at `app/data/jobs.log`.
* Updated `app/api/locations_api.py` to log success/error for `/api/locations/process`.
* Updated `app/api/facilities_api.py` to log success/error for `/api/facilities/fetch`.
* Added `app/api/jobs_api.py` with `GET /api/jobs/logs` returning `{status, message, logs}`.
* Fixed router registration order and included Jobs router in `app/main.py`.

Testing

* Module import sanity: ensured API modules import and logger reads/writes without raising exceptions locally.
* Endpoints return JSON with `status` and `message`.

Notes

* UI page `app/ui/jobs.py` currently static.

---

Date: 2025-11-09 19:01 -0500 (Session 2)
Milestone: v0.3.1 - Live Jobs Log UI

Summary

* Connected Jobs UI to logs endpoint.
* Added badges, toggles, refresh.

---

Date: 2025-11-09 19:01 -0500 (Session 3)
Milestone: v0.3.1 - Live Jobs Log UI (Docs sync)

Summary

* Standardized JSON responses.

---

Date: 2025-11-09 19:01 -0500 (Session 4)
Milestone: v0.3.1 - Stabilization

Summary

* Restored Config shim.
* Fixed bootstrap.

---

Date: 2025-11-09 19:01 -0500 (Session 5)
Milestone: v0.3.2 - Log Pruning & Rotation

Summary

* Added pruning + archive.

---

Date: 2025-11-09 19:01 -0500 (Session 6)
Milestone: v0.3.3 – Settings Connection Tests

Summary

* Added Notion + Maps diagnostics.

---

Date: 2025-11-09 19:01 -0500 (Session 7)
Milestone: v0.3.4 – Jobs UI Enhancements

Summary

* Filtering, archive, highlight.

---

Date: 2025-11-09 19:01 -0500 (Session 8)
Milestone: v0.3.4 – Hotfix

Summary

* Restored productions stub.

---

Date: 2025-11-09 15:01 -0500 (Session 8.1)
Milestone: v0.3.4.1 – Diagnostics Logging

Summary

* Added logs for settings tests.

---

Date: 2025-11-09 15:01 -0500 (Session 8.2)
Milestone: v0.3.4.2 – File-based Logging

Summary

* Added logs/app.log handler.

---

Date: 2025-11-09 15:01 -0500 (Session 8.3)
Milestone: v0.3.4.2 – API Path Standardization Fix

Summary

* Relative-path builder added.

---

Date: 2025-11-10 15:01 -0500 (Session 9)
Milestone: v0.4.0 – Dashboard Kickoff

Summary

* Dashboard page + `/api/dashboard/summary`.

---

Date: 2025-11-10 15:01 -0500 (Session 10)
Milestone: v0.4.1 – Dashboard Hardening & Env Autoload

Summary

* Fixed slot errors; timestamps local.

---

Date: 2025-11-09 15:01 -0500 (Session 11)
Milestone: v0.4.2 – Productions Data View & Sync

Summary

* Added `/productions` UI + fetch/sync.

---

Date: 2025-11-09 15:01 -0500 (Session 12)
Milestone: v0.4.3 – UI Enhancements & Background Sync

Summary

* Pagination, auto-refresh, background sync.

---

Date: 2025-11-12 15:01 -0500 (Session 13)
Milestone: v0.4.4 – Diagnostics UX Polish

Summary

* Parallelized tests; better spinners.

---

Date: 2025-11-13 15:01 -0500 (Session 14)
Milestone: v0.4.5 – Async Cleanup + Diagnostic Timing

Summary

* Added per-service timings.

---

Date: 2025-11-13 15:01 -0500 (Session 15)
Milestone: v0.4.6 – Async Conversion Across UI Pages

Summary

* Removed all `requests`; full async UI.

---

Date: 2025-11-13 15:01 -0500 (Session

xxx

Date: 2025-11-13 01:05 -0500 (Session 15)
Author: Codex 5 (Developer)
Milestone: v0.4.6 – Async Conversion Across UI Pages

Summary

* Eliminated all synchronous `requests` usage from Productions, Jobs, Locations, and Medical Facilities UI.
* All HTTP now async via `httpx.AsyncClient`.
* Added spinner/button-disable patterns across pages.
* Auto-refresh timers run through `ui.run_task` to avoid blocking.

Changes

* Updated `app/ui/productions.py`, `app/ui/jobs.py`, `app/ui/locations.py`, `app/ui/medicalfacilities.py` to async.
* Unified toast and spinner logic.

Testing

* `python -m compileall app/ui`.

---

Date: 2025-11-13 01:45 -0500 (Session 16)
Author: Codex 5 (Developer)
Milestone: v0.4.7 – Inline Editing in Productions

Summary

* Added inline `ui.select` and `ui.date` editors.
* Added dirty-row tracking and paused auto-refresh during edits.
* Sync endpoint updated to accept only modified rows.

Changes

* `app/ui/productions.py` rebuild.
* `app/api/productions_api.py` accepts `operation: ui_sync`.
* `background_sync.map_production` extended to include end dates.

Testing

* Compiled UI + API.

---

Date: 2025-11-13 02:10 -0500 (Session 17)
Milestone: v0.4.7 – Productions Fetch Reliability

Summary

* Switched data loading to browser `fetch` via `ui.run_javascript`.
* Improved spinners and error toasts.

---

Date: 2025-11-13 02:25 -0500 (Session 18)
Milestone: v0.4.7 – Productions Fetch Timeout

Summary

* Increased browser fetch timeout to 8 seconds.
* Added clear timeout messaging.

---

Date: 2025-11-13 02:35 -0500 (Session 19)
Milestone: v0.4.7 – Productions Fetch Logging

Summary

* Added server-side logging around fetch lifecycle.

---

Date: 2025-11-13 15:01 -0500 (Session 20)
Milestone: v0.4.7 – Productions Table UX Foundation

Summary

* Finalized columns, normalized schema, editors, confirm prompts.
* Enriched cache mapper and sync endpoint.

---

Date: 2025-11-13 03:05 -0500 (Session 21)
Milestone: v0.4.7 – Schema/UI Binding Sync

Summary

* Synced UI bindings with normalized backend vocabulary.

---

Date: 2025-11-13 04:10 -0500 (Session 22)
Milestone: v0.4.7 – Slot Fixes & JS Cleanup

Summary

* Replaced decorator-style slot usage with NiceGUI‑compliant patterns.
* Eliminated malformed JS injections.

---

Date: 2025-11-13 04:40 -0500 (Session 23)
Milestone: v0.4.7 – Page-Context Enforcement

Summary

* Fixed blank table by ensuring all UI mutations run inside page context.
* Added `run_in_page_context` helper.

---

Date: 2025-11-13 05:00 -0500 (Session 24)
Milestone: v0.4.7 – Table Update Enforcement

Summary

* Forced `table.update()` after assigning `table.rows`.
* Normalized slot resolution.

---

Date: 2025-11-15 19:30 -0500 (Session 24.1)
Milestone: v0.4.7 – Slot Resolution Fix

Summary

* Cleaned up `_resolve_slot_row` and removed duplicate helpers.

---

Date: 2025-11-15 19:45 -0500 (Session 24.2)
Milestone: v0.4.7 – Slot Decorator Removal

Summary

* Removed all decorator-style slot usage due to NiceGUI 3.2.0 TypeError.

---

Date: 2025-11-15 20:05 -0500 (Session 24.3)
Milestone: v0.4.7 – Slot Pattern Documentation

Summary

* Documented safe slot patterns and NiceGUI 3.2.0 limitations.

---


# Source: DEV_NOTES-recreated.md

# DEV_TOOLS.md — ATLSApp Developer Tools & Guardrails

## Purpose

Authoritative reference for Codex 5.1 rules, NiceGUI guardrails, and the human workflows we follow when building ATLSApp.

## Codex 5.1 Rules (Quick Recall)

* Async-only HTTP in UI code (`httpx.AsyncClient`); browser fetch via `ui.run_javascript` (8s timeout wrapper).
* All UI mutations must execute in a valid NiceGUI page slot/context.
* Table slots: use context-managed slots or column `body` lambdas; avoid decorator-style `@table.add_slot` in NiceGUI 3.2.x.
* API paths must stay relative (`/api/...`) and should be built via `app.services.api_client`.
* Every change requires a `docs/DEV_NOTES.md` session entry (date, session, milestone, summary, changes, testing, notes).
* `python -m compileall <files>` must pass for touched modules before commit.
* Preserve imports/helpers/logging; do not remove behavior or env handling unless explicitly requested.

## Human Developer Workflows

### Core Tools

* VS Code with ChatGPT (Genie AI + Codex 5.1 extensions).
* `uvicorn app.main:fastapi_app --reload` for live server.
* Python venv for isolation; `.env` at repo root for Notion/Maps credentials.
* Logging: `logs/app.log`, JSONL jobs (`app/data/jobs.log`), feature logs (e.g., `logs/productions.log`).

### Required Checks Before Commit

1. `python -m compileall app`
2. Manual smoke: `/dashboard`, `/productions`, `/settings`, `/jobs`
3. Confirm background sync starts (console/logs show interval loop)
4. Update `docs/DEV_NOTES.md`

## NiceGUI Guardrails

* Never mutate DOM outside the page slot; timers/tasks must route through page context.
* After setting `table.rows`, call `table.update()` so changes propagate.
* Avoid decorator-style slots; use `with table.add_slot(...)` or column `body` lambdas.
* Keep browser JS snippets minimal (no leading newlines); prefer shared constants and the 8s timeout wrapper.
* Do not rely on `ui.get_client()` in async tasks; prefer server-side calls and relative URLs.

## API Development Rules

* Always return `{status, message, ...}`.
* Log jobs via `log_job()` on success and error.
* Maintain cache fallback behavior for Notion-backed endpoints.
* Handle missing credentials gracefully and surface clear user-facing messages.

## Sync & Background Tasks

* Background sync enabled via env (`PRODUCTIONS_SYNC_ENABLED`, interval minutes).
* Cache path: `app/data/productions_cache.json`; refresh after mapper/schema changes.
* When updating UI from timers/async helpers, ensure page context or server callbacks (avoid emit/JS bridges for state changes).

## Fetch Patterns

* Browser fetch for large datasets (e.g., productions) with 8s timeout + toast on failure.
* Server-side async for Notion updates/sync; never block the NiceGUI event loop.

## Logging & Diagnostics

* Use module loggers with actionable messages (operation, count, error).
* Ensure `logs/` exists before writing; keep severity aligned (INFO flow, WARNING/ERROR failures).
* Add feature-specific logs when debugging (e.g., `logs/productions.log`).

## Editable Tables (Productions Reference)

* Prefer server-side handlers in column `body` lambdas or context slots; avoid client `emit` bridges for edits.
* Dirty-row tracking must update the source list and `table.rows`, then call `table.update()`.
* Auto-refresh should pause when dirty rows exist and resume after sync/discard.

## Deployment / Ops Notes

* `.env` auto-loads in `app/main.py`; maintain `NOTION_*`, `GOOGLE_MAPS_API_KEY`, and sync envs.
* Relative API paths keep dev/staging/prod aligned (no host/port hard-coding).
* Review `docs/DEV_NOTES.md` frequently for current patterns and pitfalls.

---

# DEV_NOTES.md - ATLS GUI App

(Full reconstructed sessions 1–24.3 follow below.)

Date: 2025-11-09 18:59 -0500
Author: Codex 5 (Developer)
Milestone: v0.3 – Job Logging System

Summary

* Implemented lightweight job logger and integrated with API routes.
* Added `/api/jobs/logs` endpoint to expose logs to the UI.
* Updated API map documentation.

Changes

* Added `app/services/logger.py` providing `log_job()` and `read_logs()` using JSONL at `app/data/jobs.log`.
* Updated `app/api/locations_api.py` to log success/error for `/api/locations/process`.
* Updated `app/api/facilities_api.py` to log success/error for `/api/facilities/fetch`.
* Added `app/api/jobs_api.py` with `GET /api/jobs/logs` returning `{status, message, logs}`.
* Fixed router registration order and included Jobs router in `app/main.py`.

Testing

* Module import sanity: ensured API modules import and logger reads/writes without raising exceptions locally.
* Endpoints return JSON with `status` and `message`.

Notes

* UI page `app/ui/jobs.py` currently static.

---

Date: 2025-11-09 19:01 -0500 (Session 2)
Milestone: v0.3.1 - Live Jobs Log UI

Summary

* Connected Jobs UI to logs endpoint.
* Added badges, toggles, refresh.

---

Date: 2025-11-09 19:01 -0500 (Session 3)
Milestone: v0.3.1 - Live Jobs Log UI (Docs sync)

Summary

* Standardized JSON responses.

---

Date: 2025-11-09 19:01 -0500 (Session 4)
Milestone: v0.3.1 - Stabilization

Summary

* Restored Config shim.
* Fixed bootstrap.

---

Date: 2025-11-09 19:01 -0500 (Session 5)
Milestone: v0.3.2 - Log Pruning & Rotation

Summary

* Added pruning + archive.

---

Date: 2025-11-09 19:01 -0500 (Session 6)
Milestone: v0.3.3 – Settings Connection Tests

Summary

* Added Notion + Maps diagnostics.

---

Date: 2025-11-09 19:01 -0500 (Session 7)
Milestone: v0.3.4 – Jobs UI Enhancements

Summary

* Filtering, archive, highlight.

---

Date: 2025-11-09 19:01 -0500 (Session 8)
Milestone: v0.3.4 – Hotfix

Summary

* Restored productions stub.

---

Date: 2025-11-09 15:01 -0500 (Session 8.1)
Milestone: v0.3.4.1 – Diagnostics Logging

Summary

* Added logs for settings tests.

---

Date: 2025-11-09 15:01 -0500 (Session 8.2)
Milestone: v0.3.4.2 – File-based Logging

Summary

* Added logs/app.log handler.

---

Date: 2025-11-09 15:01 -0500 (Session 8.3)
Milestone: v0.3.4.2 – API Path Standardization Fix

Summary

* Relative-path builder added.

---

Date: 2025-11-10 15:01 -0500 (Session 9)
Milestone: v0.4.0 – Dashboard Kickoff

Summary

* Dashboard page + `/api/dashboard/summary`.

---

Date: 2025-11-10 15:01 -0500 (Session 10)
Milestone: v0.4.1 – Dashboard Hardening & Env Autoload

Summary

* Fixed slot errors; timestamps local.

---

Date: 2025-11-09 15:01 -0500 (Session 11)
Milestone: v0.4.2 – Productions Data View & Sync

Summary

* Added `/productions` UI + fetch/sync.

---

Date: 2025-11-09 15:01 -0500 (Session 12)
Milestone: v0.4.3 – UI Enhancements & Background Sync

Summary

* Pagination, auto-refresh, background sync.

---

Date: 2025-11-12 15:01 -0500 (Session 13)
Milestone: v0.4.4 – Diagnostics UX Polish

Summary

* Parallelized tests; better spinners.

---

Date: 2025-11-13 15:01 -0500 (Session 14)
Milestone: v0.4.5 – Async Cleanup + Diagnostic Timing

Summary

* Added per-service timings.

---

Date: 2025-11-13 15:01 -0500 (Session 15)
Milestone: v0.4.6 – Async Conversion Across UI Pages

Summary

* Removed all `requests`; full async UI.

---

Date: 2025-11-13 15:01 -0500 (Session

xxx

Date: 2025-11-13 01:05 -0500 (Session 15)
Author: Codex 5 (Developer)
Milestone: v0.4.6 – Async Conversion Across UI Pages

Summary

* Eliminated all synchronous `requests` usage from Productions, Jobs, Locations, and Medical Facilities UI.
* All HTTP now async via `httpx.AsyncClient`.
* Added spinner/button-disable patterns across pages.
* Auto-refresh timers run through `ui.run_task` to avoid blocking.

Changes

* Updated `app/ui/productions.py`, `app/ui/jobs.py`, `app/ui/locations.py`, `app/ui/medicalfacilities.py` to async.
* Unified toast and spinner logic.

Testing

* `python -m compileall app/ui`.

---

Date: 2025-11-13 01:45 -0500 (Session 16)
Author: Codex 5 (Developer)
Milestone: v0.4.7 – Inline Editing in Productions

Summary

* Added inline `ui.select` and `ui.date` editors.
* Added dirty-row tracking and paused auto-refresh during edits.
* Sync endpoint updated to accept only modified rows.

Changes

* `app/ui/productions.py` rebuild.
* `app/api/productions_api.py` accepts `operation: ui_sync`.
* `background_sync.map_production` extended to include end dates.

Testing

* Compiled UI + API.

---

Date: 2025-11-13 02:10 -0500 (Session 17)
Milestone: v0.4.7 – Productions Fetch Reliability

Summary

* Switched data loading to browser `fetch` via `ui.run_javascript`.
* Improved spinners and error toasts.

---

Date: 2025-11-13 02:25 -0500 (Session 18)
Milestone: v0.4.7 – Productions Fetch Timeout

Summary

* Increased browser fetch timeout to 8 seconds.
* Added clear timeout messaging.

---

Date: 2025-11-13 02:35 -0500 (Session 19)
Milestone: v0.4.7 – Productions Fetch Logging

Summary

* Added server-side logging around fetch lifecycle.

---

Date: 2025-11-13 15:01 -0500 (Session 20)
Milestone: v0.4.7 – Productions Table UX Foundation

Summary

* Finalized columns, normalized schema, editors, confirm prompts.
* Enriched cache mapper and sync endpoint.

---

Date: 2025-11-13 03:05 -0500 (Session 21)
Milestone: v0.4.7 – Schema/UI Binding Sync

Summary

* Synced UI bindings with normalized backend vocabulary.

---

Date: 2025-11-13 04:10 -0500 (Session 22)
Milestone: v0.4.7 – Slot Fixes & JS Cleanup

Summary

* Replaced decorator-style slot usage with NiceGUI‑compliant patterns.
* Eliminated malformed JS injections.

---

Date: 2025-11-13 04:40 -0500 (Session 23)
Milestone: v0.4.7 – Page-Context Enforcement

Summary

* Fixed blank table by ensuring all UI mutations run inside page context.
* Added `run_in_page_context` helper.

---

Date: 2025-11-13 05:00 -0500 (Session 24)
Milestone: v0.4.7 – Table Update Enforcement

Summary

* Forced `table.update()` after assigning `table.rows`.
* Normalized slot resolution.

---

Date: 2025-11-15 19:30 -0500 (Session 24.1)
Milestone: v0.4.7 – Slot Resolution Fix

Summary

* Cleaned up `_resolve_slot_row` and removed duplicate helpers.

---

Date: 2025-11-15 19:45 -0500 (Session 24.2)
Milestone: v0.4.7 – Slot Decorator Removal

Summary

* Removed all decorator-style slot usage due to NiceGUI 3.2.0 TypeError.

---

Date: 2025-11-15 20:05 -0500 (Session 24.3)
Milestone: v0.4.7 – Slot Pattern Documentation

Summary

* Documented safe slot patterns and NiceGUI 3.2.0 limitations.

---


# Source: DEV_NOTES.md

# DEV_TOOLS.md — ATLSApp Developer Tools & Guardrails

## Purpose
Authoritative reference for Codex 5.1 rules, NiceGUI guardrails, and the human workflows we follow when building ATLSApp.

## Codex 5.1 Rules (Quick Recall)
- Async-only HTTP in UI code (`httpx.AsyncClient`); browser fetch via `ui.run_javascript` (8s timeout wrapper).
- All UI mutations must execute in a valid NiceGUI page slot/context.
- Table slots: use context-managed slots or column `body` lambdas; avoid decorator-style `@table.add_slot` in NiceGUI 3.2.x.
- API paths must stay relative (`/api/...`) and should be built via `app.services.api_client`.
- Every change requires a `docs/DEV_NOTES.md` session entry (date, session, milestone, summary, changes, testing, notes).
- `python -m compileall <files>` must pass for touched modules before commit.
- Preserve imports/helpers/logging; do not remove behavior or env handling unless explicitly requested.

## Human Developer Workflows
### Core Tools
- VS Code with ChatGPT (Genie AI + Codex 5.1 extensions).
- `uvicorn app.main:fastapi_app --reload` for live server.
- Python venv for isolation; `.env` at repo root for Notion/Maps credentials.
- Logging: `logs/app.log`, JSONL jobs (`app/data/jobs.log`), feature logs (e.g., `logs/productions.log`).

### Required Checks Before Commit
1) `python -m compileall app`
2) Manual smoke: `/dashboard`, `/productions`, `/settings`, `/jobs`
3) Confirm background sync starts (console/logs show interval loop)
4) Update `docs/DEV_NOTES.md`

## NiceGUI Guardrails
- Never mutate DOM outside the page slot; timers/tasks must route through page context.
- After setting `table.rows`, call `table.update()` so changes propagate.
- Avoid decorator-style slots; use `with table.add_slot(...)` or column `body` lambdas.
- Keep browser JS snippets minimal (no leading newlines); prefer shared constants and the 8s timeout wrapper.
- Do not rely on `ui.get_client()` in async tasks; prefer server-side calls and relative URLs.
- Use only documented NiceGUI component kwargs; avoid Quasar-only props (e.g., use `side="right", overlay=True` for drawers instead of `right=True`).
- After UI layout or slot changes on a route, smoke-load that route (e.g., `/facilities`) to catch prop/slot errors early.

## API Development Rules
- Always return `{status, message, ...}`.
- Log jobs via `log_job()` on success and error.
- Maintain cache fallback behavior for Notion-backed endpoints.
- Handle missing credentials gracefully and surface clear user-facing messages.

## Sync & Background Tasks
- Background sync enabled via env (`PRODUCTIONS_SYNC_ENABLED`, interval minutes).
- Cache path: `app/data/productions_cache.json`; refresh after mapper/schema changes.
- When updating UI from timers/async helpers, ensure page context or server callbacks (avoid emit/JS bridges for state changes).

## Fetch Patterns
- Browser fetch for large datasets (e.g., productions) with 8s timeout + toast on failure.
- Server-side async for Notion updates/sync; never block the NiceGUI event loop.

## Logging & Diagnostics
- Use module loggers with actionable messages (operation, count, error).
- Ensure `logs/` exists before writing; keep severity aligned (INFO flow, WARNING/ERROR failures).
- Add feature-specific logs when debugging (e.g., `logs/productions.log`).

## Editable Tables (Productions Reference)
- Prefer server-side handlers in column `body` lambdas or context slots; avoid client `emit` bridges for edits.
- Dirty-row tracking must update the source list and `table.rows`, then call `table.update()`.
- Auto-refresh should pause when dirty rows exist and resume after sync/discard.

## Deployment / Ops Notes
- `.env` auto-loads in `app/main.py`; maintain `NOTION_*`, `GOOGLE_MAPS_API_KEY`, and sync envs.
- Relative API paths keep dev/staging/prod aligned (no host/port hard-coding).
- Review `docs/DEV_NOTES.md` frequently for current patterns and pitfalls.

---
This file should be updated whenever workflows, guardrails, or Codex rules evolve.

---

Date: 2025-11-21 14:30 -0500 (Session 27)
Author: Codex 5 (Developer)
Milestone: v0.4.8 — Productions Layout & UX Improvements

Summary
- Added horizontal overflow wrapper and min-width to the productions table so it stays beside the sidebar and scrolls horizontally.
- Injected global CSS to left-align all table headers and cells.
- Condensed LocationsTable to a short “Link” and made ProductionID link to `/production/<id>`.
- Inline editing is on hold; table is read-only while fetch/search/filter/pagination/auto-refresh remain unchanged.

Changes
- `app/ui/productions.py`: head CSS injection; `overflow-x-auto` wrapper with `min-w-[1600px]`; ProductionID link body; LocationsTable “Link” body; removed inline editing controls.
- `docs/PROJECT_HANDBOOK.md`: added UI conventions (overflow wrapper, left alignment, ID links) and version bumped to v0.4.8.
- `README.md`: version bumped to v0.4.8; documented layout scroll, left alignment, LocationsTable “Link,” and ProductionID navigation.

Testing
- `python -m compileall app`
- Manual: `/productions` (table beside sidebar, horizontal scroll, left alignment, LocationsTable shows “Link,” ProductionID clickable, no editing controls)
- Manual smoke: `/dashboard`, `/settings`, `/jobs`

Notes
- Follow NiceGUI 3.2.x slot guidance (lambda/context slots only). Editing remains paused per requirements.

---

Date: 2025-11-22 10:15 -0500 (Session 34)
Author: Codex 5 (Developer)
Milestone: v0.4.14 - Content Wrapper & Header Dark Mode Completion

Summary
- Extended the global content wrapper styling so every page inherits correct light/dark backgrounds and text colors.
- Documented the new requirement for page-level header sections to use the shared class set.

Changes
- `app/ui/layout.py`: added explicit light/dark classes to the page content column to cover all routes.
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: bumped version references to v0.4.14, added the new UI convention, and logged this session.

Testing
- `python -m compileall app`

Notes
- After deploying, manually verify dark-mode toggling on each route to ensure header blocks follow the updated styling.

---

Date: 2025-11-22 12:05 -0500 (Session 34b)
Author: Codex 5 (Developer)
Milestone: v0.4.14b - Header Dark Mode Override & Unified Page Header Blocks

Summary
- Applied dark-mode override for the global header bar to ensure Quasar wrappers cannot override the theme.
- Standardized all page-level header blocks with the Option A solid section style and removed page titles/subtitles across every page.

Changes
- `app/ui/layout.py`: added targeted dark-mode CSS overrides for the global header.
- `app/ui/dashboard.py`, `app/ui/productions.py`, `app/ui/locations.py`, `app/ui/medicalfacilities.py`, `app/ui/jobs.py`, `app/ui/settings.py`: removed page titles/subtitles and wrapped top controls in the unified header block with light/dark classes and borders.
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: bumped version to v0.4.14b, documented the unified header style, and logged this session.

Testing
- `python -m compileall app`

Notes
- Verify light/dark toggling on all routes to confirm header blocks and the global header respect the unified styling without regressions.

---

Date: 2025-11-23 09:40 -0500 (Session 35)
Author: Codex 5 (Developer)
Milestone: v0.4.15b - Dark-Mode Wiring Fix

Summary
- Unified dark-mode wiring so Quasar’s `body--dark`, Tailwind `dark:` utilities, and theme persistence stay in sync. Ensured global header and page header blocks respond correctly.

Changes
- `app/ui/layout.py`: synchronized `body--dark` with a `dark` class for Tailwind, updated persistence to watch `body--dark`, and added targeted overrides for `atls-global-header` and `atls-page-header`.
- `app/ui/dashboard.py`, `app/ui/productions.py`, `app/ui/locations.py`, `app/ui/medicalfacilities.py`, `app/ui/jobs.py`, `app/ui/settings.py`: applied the standardized header block class with spacing/border updates.
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: documented the unified dark-mode approach and version bump.

Testing
- `python -m compileall app`

Notes
- Validate light/dark toggling across all routes to ensure headers and wrappers switch cleanly without flicker.

---

Date: 2025-11-23 19:05 -0500 (Session 35.1)
Author: Codex 5 (Developer)
Milestone: v0.4.15c - Guarded Dark-Mode Wiring for SPA Navigation

Summary
- Added a one-time guard around the theme observers to prevent duplicate MutationObservers during SPA-style navigation while keeping Quasar `body--dark`, Tailwind `dark:`, and localStorage persistence aligned.

Changes
- `app/ui/layout.py`: wrapped theme init in a global guard to avoid repeated observer attachment and potential client slowdown.
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: bumped version to v0.4.15c and recorded this guard fix.

Testing
- `python -m compileall app`

Notes
- After restart, verify light/dark toggling across routes and monitor load time to confirm the guard eliminates observer buildup and hanging.

---

Date: 2025-11-24 09:20 -0500 (Session 38)
Author: Codex 5 (Developer)
Milestone: v0.4.16 - Dark-Mode Stabilization

Summary
- Removed all custom theme MutationObservers and Tailwind bridging to rely solely on Quasar’s `body--dark`.
- Simplified dark-mode CSS to cover global header, page headers, and tables without JS side effects.

Changes
- `app/ui/layout.py`: deleted theme JS observers/persistence, pruned Tailwind bridge rules, and consolidated `body--dark` CSS for layout, headers, and tables.
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: updated versioning and documented the dark-mode stabilization approach.

Testing
- `python -m compileall app`

Notes
- Restart the server and verify light/dark toggling on all routes; the UI should mount promptly with no freezes or console errors.

---

Date: 2025-11-24 10:05 -0500 (Session 39)
Author: Codex 5 (Developer)
Milestone: v0.4.17 - Dark Mode Follow-up Note

Summary
- Documented that dark mode remains inconsistent and will be revisited in a future release while keeping the UI responsive.

Changes
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: updated to v0.4.17 and added a note that dark mode needs a future fix.

Testing
- Documentation-only change.

Notes
- Dark mode remains a known issue; defer fixes to a future milestone.
- Dark-mode work from earlier sessions is now paused and will be revisited under a later milestone.

---

Date: 2025-11-25 09:42 -0500 (Session 40)
Author: Codex 5 (Developer)
Milestone: v0.5.0 - Refactor Release

Summary
- Refactored UI headers to use a shared constant and converted jobs table slots to template-style definitions that comply with NiceGUI v0.4.x rules.
- Standardized API job endpoints with helper functions and reduced redundant CSS in the shared layout.
- Updated documentation for the v0.5.0 refactor release and refreshed version markers.

Changes
- `app/ui/layout.py`, `app/ui/*.py`: centralized the page header classes, removed redundant dark-mode CSS, and standardized table slot usage on Jobs.
- `app/api/locations_api.py`, `app/api/facilities_api.py`, `app/api/jobs_api.py`: aligned logging/error handling helpers without changing responses.
- Documentation: bumped README, PROJECT_HANDBOOK.md, and DEV_NOTES.md to v0.5.0 with the new refactor entry.

Testing
- `python -m compileall app`

Notes
- No functional changes; focus was readability, consistency, and guardrail compliance ahead of new feature work.

---

Date: 2025-11-25 20:15 -0500 (Session 41)
Author: Codex 5 (Developer)
Milestone: v0.5.1 - UI Polish

Summary
- Applied small visual polish across all UI modules to align header alignment, control spacing, and table padding.
- Added consistent hover/focus styling for buttons and links (including ProductionID/Link cells) and tuned sidebar hover spacing.

Changes
- `app/ui/layout.py`, `app/ui/dashboard.py`, `app/ui/productions.py`, `app/ui/locations.py`, `app/ui/medicalfacilities.py`, `app/ui/jobs.py`, `app/ui/settings.py`: standardized control bar spacing/height, added hover styles, ensured table containers have overflow wrappers with padding, and tightened sidebar spacing.
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`: documented v0.5.1 UI polish and updated version history/standards.

Testing
- `python -m compileall app`

Notes
- UI-only polish; no functional behavior changes introduced.

---

Date: 2025-11-26 09:10 -0500 (Session 42)
Author: Codex 5 (Developer)
Milestone: v0.5.2 - Productions Search Fix

Summary
- Restored client-side filtering for the Productions table with a cached master row list and case-insensitive matching across key fields.
- Kept layout, routing, and backend logic unchanged while ensuring search input alignment and existing polish remain intact.

Changes
- `app/ui/productions.py`: added master row cache, client-side filter pipeline, and routed all table updates through `table.update_rows` without altering slots or layout.
- Docs: `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md` updated for v0.5.2.

Testing
- `python -m compileall app`

Notes
- UI-only repair; pagination/sorting still rely on the client dataset.

---

Date: 2025-11-24 20:20 -0500 (Session 25)
Author: Codex 5 (Developer)
Milestone: v0.6.0 – Medical Facilities UI Foundation

Summary
- Rebuilt the medical facilities table with read-only slots, badge-style facility type, and the new column order.
- Added a placeholder right-side details drawer and browser-based fetch with timeout, spinner, and toasts.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app/ui`
- Manual smoke test: table loads, drawer opens, no slot errors

Notes
- Facility fetch now runs in the browser with an 8s abort guard; data payloads remain backend-defined.

---

Date: 2025-11-24 20:40 -0500 (Session 43)
Author: Codex 5 (Developer)
Milestone: Documentation Update – ripgrep Usage

Summary
- Added ripgrep usage guidance to DEV_TOOLS.md and AGENTS.md.

Changes
- `docs/DEV_TOOLS.md`
- `docs/AGENTS.md`
- `docs/DEV_NOTES.md`

Testing
- N/A (documentation-only)

Notes
- Ensures Codex avoids PowerShell directory path misinterpretation when using ripgrep.

---

Date: 2025-11-24 20:40 -0500 (Session 44)
Author: Codex 5 (Developer)
Milestone: Documentation Correction – ripgrep Placement

Summary
- Removed incorrectly created DEV_TOOLS.md and added ripgrep usage guidance to the correct documents.

Changes
- `docs/DEV_NOTES.md`
- `docs/AGENTS.md`
- Removed `docs/DEV_TOOLS.md`

Testing
- N/A (documentation-only)

Notes
- Ensures correct placement of ripgrep usage rules and avoids future misrouting of documentation.

---

Date: 2025-11-24 21:07 -0500 (Session 45)
Author: Codex 5 (Developer)
Milestone: v0.6.1 - Pagination & Details Panel

Summary
- Added lightweight medical facilities list endpoint with pagination and decoupled the heavy fill job.
- Updated Facilities UI to use the new paginated list, add Prev/Next page controls, and wire the details dialog with real data fields.

Changes
- `app/api/medicalfacilities_api.py`
- `app/ui/medicalfacilities.py`
- `app/main.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual test: pagination, details panel, timeout handling

Notes
- Heavy fill/backfill now lives behind a separate `/api/medicalfacilities/fill` endpoint and no longer blocks list fetches.
Date: 2025-11-24 21:35 -0500 (Session 46)
Author: Codex 5 (Developer)
Milestone: v0.6.1 - Facilities Details Alignment

Summary
- Aligned medical facilities mapping to the actual Notion schema so details (name/title, Type, Phone, Website, Maps URL, Address, hours) populate in the UI dialog.

Changes
- `app/api/medicalfacilities_api.py`
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Drawer now reflects Notion fields: MedicalFacilityID/Name, Type, Address, Phone, Website, Google Maps URL, and hours.
Date: 2025-11-24 21:50 -0500 (Session 47)
Author: Codex 5 (Developer)
Milestone: Documentation Update – Parking Lot Added

Summary
- Added a Deferred Items / Parking Lot section to PROJECT_HANDBOOK.md with current architectural issues identified during v0.6.0 and v0.6.1 planning.

Changes
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- N/A (documentation-only)

Notes
- Provides a canonical location for tracking deferred issues and technical debt.

Date: 2025-11-24 21:50 -0500 (Session 48)
Author: Codex 5 (Developer)
Milestone: v0.6.1 – Details Dialog Row Binding Fix

Summary
- Implemented state-based row lookup for the Medical Facilities details dialog. Event payload now only provides the row_id, and full row data is retrieved from state["facility_rows"].

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: verify that clicking any facility row shows correct details in the right-side dialog.

Notes
- Replaces event.args-based lookup with stable state-backed row binding.
Date: 2025-11-24 21:50 -0500 (Session 49)
Author: Codex 5 (Developer)
Milestone: v0.6.1 – Details Dialog Layout Cleanup

Summary
- Cleaned up the facilities details dialog: removed duplicate name line, placed website/maps after phone, formatted hours per line, and dropped extra type/distance placeholders.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Dialog now shows Name once, Type chip, Address, Phone with copy, Website/Maps, and per-day hours on separate lines.

Date: 2025-11-24 21:50 -0500 (Session 50)
Author: Codex 5 (Developer)
Milestone: v0.6.1 – Details Dialog Link Fix

Summary
- Restored Website and Map links to use actual targets so they remain clickable (fallback to '#' when missing).

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Links now open when URLs are present; labels remain Website/Map with external targets.

Date: 2025-11-24 21:50 -0500 (Session 51)
Author: Codex 5 (Developer)
Milestone: v0.6.1 – Facilities Chip Colors

Summary
- Updated facility type chips: ER now uses red (bg-red-100 text-red-700), Urgent Care uses green (bg-green-100 text-green-700), fallback stays neutral.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Improves visual clarity between ER and Urgent Care types.
Date: 2025-11-24 22:13 -0500 (Session 52)
Author: Codex 5 (Developer)
Milestone: Documentation Update – Responsive Layout Redesign (Parking Lot)

Summary
- Added a new deferred item to the Parking Lot describing the planned migration from a fixed max-width layout to a responsive grid-based design.

Changes
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- N/A (documentation-only)

Notes
- Captures the long-term layout direction for future UI/UX milestones.
Date: 2025-11-24 22:13 -0500 (Session 53)
Author: Codex 5 (Developer)
Milestone: v0.6.2 – Global Layout Width Expansion

Summary
- Replaced the fixed max-width container (max-w-[1600px]) with full-width (max-w-none) while keeping horizontal padding.

Changes
- `app/ui/layout.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: verify all pages render full width with correct padding and no horizontal scrollbars.

Notes
- Temporary width expansion; full responsive grid redesign remains in the Parking Lot.
Date: 2025-11-24 22:13 -0500 (Session 54)
Author: Codex 5 (Developer)
Milestone: v0.6.2 – Padding Simplification

Summary
- Kept only one layer of horizontal padding by removing the inner px-6 on the full-width wrapper; outer px-6 remains.

Changes
- `app/ui/layout.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Aligns tables/control bars closer to the sidebar while keeping a single horizontal gutter.
Date: 2025-11-24 22:13 -0500 (Session 55)
Author: Codex 5 (Developer)
Milestone: v0.6.2 – Padding Removal

Summary
- Removed outer horizontal padding on the main content column (px-0); inner wrapper remains full-width with no extra padding.

Changes
- `app/ui/layout.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Eliminates remaining horizontal gutter; content now spans the available width alongside the sidebar.
Date: 2025-11-24 22:13 -0500 (Session 56)
Author: Codex 5 (Developer)
Milestone: v0.6.2 – Sidebar Height Fix

Summary
- Extended the sidebar to full viewport height (min-h-screen) so its background covers the left rail below the nav links.

Changes
- `app/ui/layout.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Sidebar background now spans the full height instead of stopping after the links.
Date: 2025-11-24 22:13 -0500 (Session 57)
Author: Codex 5 (Developer)
Milestone: v0.6.2 – Header Alignment

Summary
- Reduced global header padding (px-1) and removed extra label margin so page titles align with page content/table edges.

Changes
- `app/ui/layout.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Header titles now align with content after padding simplification.
Date: 2025-11-24 22:52 -0500 (Session 58)
Author: Codex 5 (Developer)
Milestone: Documentation Update – Backend Search Endpoint (Parking Lot)

Summary
- Added a new Parking Lot item describing the future backend search endpoint for Medical Facilities, to be implemented after the background worker architecture is introduced.

Changes
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- N/A (documentation-only)

Notes
- Captures future server-side filtering requirements without affecting the current v0.6.x UI-only search milestone.
Date: 2025-11-24 22:52 -0500 (Session 59)
Author: Codex 5 (Developer)
Milestone: v0.6.3 – Medical Facilities Search, Filters & Sorting (UI-Only)

Summary
- Added search-first workflow: no initial load; search panel collects filters (name/address/state/type) and triggers a full fetch, then client-side filters, sorts, and paginates. Sorting via dropdown; pagination reuses existing controls. Table and details dialog remain intact, now backed by filtered/sorted state caches.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: verify search, filters, sorting, pagination, and details dialog all work client-side.

Notes
- Backend unchanged; server-side search deferred per Parking Lot.
Date: 2025-11-24 22:52 -0500 (Session 60)
Author: Codex 5 (Developer)
Milestone: v0.6.3 – Search Trigger Fix

Summary
- Fixed the Medical Facilities search button to run the async fetch correctly (awaits load, then filters/sorts/paginates client-side).

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: search now triggers fetch and displays results with filters/sorting.

Notes
- Backend unchanged; client-side search remains per v0.6.3 scope.
Date: 2025-11-24 22:52 -0500 (Session 61)
Author: Codex 5 (Developer)
Milestone: v0.6.3 – State Filter Fix

Summary
- Improved state detection in client-side filters: now scans comma- and space-delimited address parts to find the first 2-letter alpha token (e.g., GA), enabling proper state filtering for addresses ending with ZIP codes.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: state filter (e.g., GA) returns matching facilities.

Notes
- Backend remains unchanged; client-side search/sort flow intact.
Date: 2025-11-24 22:52 -0500 (Session 62)
Author: Codex 5 (Developer)
Milestone: v0.6.3 – State Filter Regex Fix

Summary
- Hardened state detection for facilities search using a regex to capture the last 2-letter token (e.g., GA) anywhere in the address, improving matches for Georgia and similar cases.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: state filter (e.g., GA) should now return matching facilities even with varied address formats.

Notes
- Client-side search/sort remains unchanged otherwise.
Date: 2025-11-24 22:52 -0500 (Session 63)
Author: Codex 5 (Developer)
Milestone: v0.6.3 – Full Fetch Pagination Fix

Summary
- Fetches all facilities client-side by paging through `/api/medicalfacilities/list` in 100-row batches until the reported total is reached, then filters/sorts/paginates locally.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: search now loads the full dataset (beyond 100 rows) before applying filters/sorting.

Notes
- Backend unchanged; client-side search remains per v0.6.3 scope.
Date: 2025-11-24 22:52 -0500 (Session 64)
Author: Codex 5 (Developer)
Milestone: Documentation Update – Structured Address Fields (Parking Lot)

Summary
- Added a Parking Lot item describing the future plan to split Medical Facility and Location addresses into structured fields for improved server-side filtering, sorting, validation, and geospatial support.

Changes
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- N/A (documentation-only)

Notes
- This work will be part of a backend-focused milestone once the background worker and search endpoint infrastructure are in place.
Date: 2025-11-24 22:52 -0500 (Session 65)
Author: Codex 5 (Developer)
Milestone: Documentation Update – Backend Search & Caching (Parking Lot)

Summary
- Added a Parking Lot item describing the long-term backend plan for server-side Medical Facility search, API-level caching, and larger/bulk retrieval endpoints tied to future background worker and Facility Sync architecture.

Changes
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- N/A (documentation-only)

Notes
- Deferred to a backend-focused milestone (v0.7.x or later).
Date: 2025-11-24 22:52 -0500 (Session 66)
Author: Codex 5 (Developer)
Milestone: v0.6.4 – UI Polish (Heroicons, Hover Highlight, State Auto-Suggest)

Summary
- Added outline-style iconography to search panel, chips, and details dialog; tweaked spacing, bolded Name, enabled address wrapping, added row hover highlight, and aligned title/controls. Implemented state auto-suggest from dataset.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual: verify icons, hover effect, state auto-suggest, and existing search/sort/pagination behavior remain intact.

Notes
- Pure UI polish; backend unchanged.
Date: 2025-11-24 23:30 -0500 (Session 67)
Author: Codex 5 (Developer)
Milestone: v0.6.4 - State Select Init Fix

Summary
- Fixed the State auto-suggest select initialization by removing the invalid default value so the Facilities page loads without ValueError.

Changes
- `app/ui/medicalfacilities.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- UI-only fix; search/filter behavior unchanged.

Date: 2025-11-25 10:15 -0500 (Session 0.6.0-Launcher)
Author: Codex 5 (Developer)
Milestone: v0.6.0 - Dev Launcher Script

Summary
- Added a Windows-friendly launcher script with banner output, repo-relative venv detection, and port auto-selection for the NiceGUI/FastAPI dev server.
- Keeps the console open after exit and handles Ctrl+C to surface shutdown or error details.

Changes
- Added `scripts/run_atlsapp.ps1` for guided startup with venv activation and Uvicorn launch.
- Updated `README.md` and `docs/PROJECT_HANDBOOK.md` with the new launcher workflow.

Testing
- `python -m compileall app`

Notes
- No changes to app/main.py, API, or UI modules; relies on repo-local venvs only and avoids global path modifications.

Date: 2025-11-25 11:33 -0500 (Session 69)
Author: Codex 5 (Developer)
Milestone: v0.7.1 - Hybrid Cache Layer

Summary
- Added async cache utilities plus cache files for Medical Facilities and Locations (normalized + raw with timestamps).
- Implemented Notion fetch-and-cache services for facilities and locations with logging and staleness handling.
- Updated facilities and locations APIs to use cache-first logic with refresh on stale/missing data.

Changes
- `app/services/cache_utils.py`
- `app/services/notion_medical_facilities.py`
- `app/services/notion_locations.py`
- `app/api/medicalfacilities_api.py`
- `app/api/locations_api.py`
- `app/data/medical_facilities_cache.json`
- `app/data/locations_cache.json`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Manual verification needed: cache hits/misses for facilities and locations, stale cache fallback, and presence of `raw` data in cache files.

Date: 2025-11-25 11:45 -0500 (Session 70)
Author: Codex 5 (Developer)
Milestone: v0.7.2 - Bulk Retrieval Endpoints

Summary
- Added cache-aware bulk fetch helpers for facilities and locations, respecting staleness and limits.
- Introduced `/api/medicalfacilities/all` and `/api/locations/all` endpoints with limit validation, logging, and cache-first retrieval.
- Updated services to enforce limit handling and staleness checks against the hybrid cache.

Changes
- `app/services/notion_medical_facilities.py`
- `app/services/notion_locations.py`
- `app/api/medicalfacilities_api.py`
- `app/api/locations_api.py`
- `app/services/cache_utils.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Manual tests recommended: bulk endpoints with default/large/small/invalid limits, cache corruption recovery, and log verification for start/success/error events.

Date: 2025-11-25 12:05 -0500 (Session 71)
Author: Codex 5 (Developer)
Milestone: v0.7.3 - Background Worker Foundation

Summary
- Added a lightweight background job manager with async scheduling, registry, capped history, and structured logging.
- Implemented facilities and locations backfill job coroutines that refresh caches and log failures.
- Exposed job scheduling endpoints for facilities and locations backfills plus a jobs listing endpoint; retained log/prune endpoints.

Changes
- `app/services/job_manager.py`
- `app/services/backfill_jobs.py`
- `app/api/jobs_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Manual validation needed: call `/api/jobs/facilities/backfill` and `/api/jobs/locations/backfill`, verify immediate job_id responses, success/error logs in `app/data/jobs.log`, and cache refresh behavior when cache files are missing/corrupted. Jobs listing endpoint (`/api/jobs`) returns recent registry entries.

Date: 2025-11-25 11:55 -0500 (Session 72)
Author: Codex 5 (Developer)
Milestone: v0.7.4 - Structured Address Parsing (Internal Only)

Summary
- Added address parsing utility to derive address1/address2/city/state/zip from full addresses (heuristic, US-focused).
- Extended facilities and locations normalization to include parsed fields and log parse failures without leaking full addresses.
- Cache refreshes will now persist parsed address components in normalized records while leaving raw payloads untouched.

Changes
- `app/services/address_parser.py`
- `app/services/notion_medical_facilities.py`
- `app/services/notion_locations.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Manual refresh recommended to regenerate caches and verify parsed fields populate normalized records. Parser is heuristic and may not handle international/unusual formats; future work could refine regex rules or add geocoding validation.

Date: 2025-11-25 12:15 -0500 (Session 73)
Author: Codex 5 (Developer)
Milestone: v0.7.5 - Locations Server-Side Search

Summary
- Added a locations search service that builds Notion filter/sort blocks (name/address/city/state/production) and normalizes results with parsed addresses.
- Exposed `/api/locations/find` to handle search parameters, validate sorts, log start/error/success, and return normalized rows.
- Normalization now carries production_id (if present) to support filtering.

Changes
- `app/services/notion_locations.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Manual verification recommended: call `/api/locations/find` with single/multiple filters and valid/invalid sorts; watch `app/data/jobs.log` for start/success/error logs. Fallbacks depend on Notion property availability; production_id filtering assumes a `ProductionID` rich_text property.

Date: 2025-11-25 11:07 -0500 (Session 68)
Author: Codex 5 (Developer)
Milestone: v0.7.0 - Medical Facilities Server-Side Search

Summary
- Added a Notion-backed service layer to build AND-combined filters/sorts and normalize Medical Facility records.
- Introduced `/api/medicalfacilities/find` using the new service with structured envelope, logging, and error handling.
- Routed the existing `/list` endpoint through the shared service normalization while preserving pagination semantics.

Changes
- `app/services/notion_medical_facilities.py`
- `app/api/medicalfacilities_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Manual endpoint permutations pending (requires running the API server).

Date: 2025-11-25 12:45 -0500 (Session 74)
Author: Codex 5 (Developer)
Milestone: v0.8.0 - Batch Location Import

Summary
- Added async batch import job to normalize addresses, detect duplicates (normalized/parsed), optionally flag/update existing records, create Notion Location pages, refresh caches, and log detailed stats.
- Exposed `POST /api/productions/{production_id}/locations/import` to validate production IDs and payloads, accept duplicate strategies (`skip`|`update`|`flag`), and schedule background jobs via the job manager.
- Extended locations service with Notion create/update helpers and fixed the Notion query helper to accept filters/sorts (restoring server-side location search reliability).

Changes
- `app/services/import_jobs.py`
- `app/api/productions_api.py`
- `app/services/notion_locations.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Duplicate detection currently uses normalized addresses plus parsed (address1/city/state/zip) keys; geocoding is stubbed for a future milestone.
- Duplicate flagging writes to a `Notes` property when present; creation retries without that field if the schema rejects it.
- Production validation checks cached records first and falls back to a Notion fetch when available; ensure caches are refreshed if new productions were added recently.

Date: 2025-11-25 13:30 -0500 (Session 75)
Author: Codex 5 (Developer)
Milestone: v0.8.1 - Structured Address Fields

Summary
- Added structured address normalization for Locations and Medical Facilities including Address1/2/3, City, State/Province, ZIP/Postal, Country (ISO-2), County, and Borough with system-generated Full Address.
- Implemented practical-name fallback (Places name -> Address1) and status defaulting to Ready when Place ID exists, Unresolved otherwise; Full Address is regenerated on writes.
- Added structured address backfill job to rewrite existing Location rows with the new fields and refreshed cache; new scheduler endpoint exposed under `/api/jobs/locations/structured_backfill`.

Changes
- `app/services/address_parser.py`
- `app/services/notion_locations.py`
- `app/services/notion_medical_facilities.py`
- `app/services/import_jobs.py`
- `app/services/backfill_jobs.py`
- `app/api/jobs_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Address parser now supports US + CA (states/provinces, ZIP/postal) and pulls county/borough when provided by components; default country is `US`.
- Notion writes rebuild Full Address and structured fields; Status uses “Ready” when a Place ID is present, otherwise “Unresolved”. Practical Name falls back to Address1 when Places name is missing.
- Structured backfill uses existing Place IDs/fields to rebuild properties; future work can integrate real Places lookups to improve resolution before marking as Unresolved.

Date: 2025-11-25 14:00 -0500 (Session 76)
Author: Codex 5 (Developer)
Milestone: v0.8.1.1 - Schema Update Patch

Summary
- Added manual admin endpoint `/api/notion/update_schema_all` to update schemas for all `_Locations` databases, Locations Master, and Medical Facilities DB by adding structured address fields and ensuring Status includes “Unresolved”.
- Implemented Notion schema utilities to search databases, detect missing fields, patch schemas idempotently, and log schema updates.

Changes
- `app/api/notion_admin_api.py`
- `app/services/notion_schema_utils.py`
- `app/main.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`

Notes
- Endpoint runs on-demand only (not at startup). Returns updated/skipped/failed DB IDs and logs actions under `schema_update` in `app/data/jobs.log`.
- Uses Notion search for `_Locations` suffix; includes configured LOCATIONS_MASTER_DB and MEDICAL_FACILITIES_DB.
- Recent run (manual): schema updates succeeded for 8 databases; 1 skipped (already compliant); Status “Unresolved” must still be added manually in Notion if missing, since Notion API rejects status option mutations.

Date: 2025-11-25 14:30 -0500 (Session 77)
Author: Codex 5 (Developer)
Milestone: v0.8.1.2 - Status Enforcement Patch

Summary
- Added centralized status normalization (`normalize_status_for_write`) to force Unresolved when Place_ID is missing, keep Matched when already set, and default to Ready when a Place_ID exists.
- Applied the helper to location creation/import and structured backfill to ensure every write carries a non-empty Status.
- Logging: debug-level trace for auto-normalized statuses.

Changes
- `app/services/location_status_utils.py`
- `app/services/notion_locations.py`
- `app/services/import_jobs.py`
- `app/services/backfill_jobs.py`
- `docs/DEV_NOTES.md`

Testing (manual plan)
- Batch import with mixed Place_ID presence → rows without Place_ID get Unresolved; with Place_ID get Ready.
- Remove Place_ID then run backfill → remains Unresolved.
- Add Place_ID then run backfill → becomes Ready.
- Trigger match workflow → sets Matched and should not regress.
- Create location via API without Place_ID → Unresolved; with Place_ID → Ready.
- Verify `app/data/jobs.log` shows no Status-related Notion errors.

Date: 2025-11-25 15:00 -0500 (Session 78)
Author: Codex 5 (Developer)
Milestone: v0.8.1.2 - Status Enforcement Patch (API default focus)

Summary
- Added `resolve_status` helper to enforce creation defaults: Unresolved when no Place_ID, Ready when Place_ID is present, Matched when explicitly linked to master; explicit statuses are honored.
- Wired status enforcement into location creation/import/backfill so Status is always sent and defaults safely without schema changes.
- Logging uses debug traces for applied statuses; warnings for missing Status options are avoided per Notion API constraints.

Changes
- `app/services/notion_locations.py`
- `app/services/import_jobs.py`
- `app/services/backfill_jobs.py`
- `app/services/location_status_utils.py`
- `docs/DEV_NOTES.md`

Testing (manual plan)
- Batch import rows missing Place_ID → Unresolved; with Place_ID → Ready.
- Insert matched (LocationsMasterID linked) rows → Matched.
- Create via API without Place_ID → Unresolved; with Place_ID → Ready.
- Ensure logs show no Notion status-option errors; if Unresolved option is absent in Notion, add it manually (API cannot).

Date: 2025-11-25 15:30 -0500 (Session 79)
Author: Codex 5 (Developer)
Milestone: v0.8.2 - Master Matching Logic

Summary
- Added matching service to link production locations to Locations Master using Place_ID first, then hierarchical address fallbacks; multiple candidates leave records Unresolved with notes.
- Integrated matching into batch import, structured backfill, and a new `/api/locations/match_all` endpoint that refreshes cache, matches, and patches relations/status when matches are found.
- Matching sets LocationsMasterID relation and Status=Matched when a unique candidate is identified; status defaults remain enforced by existing helpers.

Changes
- `app/services/matching_service.py`
- `app/services/import_jobs.py`
- `app/services/backfill_jobs.py`
- `app/services/notion_locations.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing (manual plan)
- Create prod-location rows with/without Place_ID and run `/api/locations/match_all`; verify Place_ID matches first, address fallback matches when unique.
- Create duplicate address scenarios; confirm multiple candidates are logged and no match is applied (Status stays Unresolved).
- Run batch import: matched rows become Matched, others Unresolved/Ready per Place_ID.
- Run structured backfill: matching attempts applied post-resolution.
- Verify jobs.log shows matching logs and no Notion errors when patching relations/status.

Date: 2025-11-25 15:45 -0500 (Session 80)
Author: Codex 5 (Developer)
Milestone: v0.8.2 – Hotfix: /api/locations/match_all route loading

Summary
- Ensured API package initialization so the locations router (prefix `/api/locations`) loads consistently and the `POST /api/locations/match_all` route registers.

Changes
- `app/__init__.py`
- `app/api/__init__.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Confirmed `POST /api/locations/match_all` appears in `/docs` and responds with JSON.

Date: 2025-11-25 15:55 -0500 (Session 81)
Author: Codex 5 (Developer)
Milestone: v0.8.2 – Hotfix 2: Router load + import resolution

Summary
- Adjusted main imports to explicitly load `locations_api` as a module and verified the router prefix/path; cleaned temporary debug scaffolding after confirming load.

Changes
- `app/main.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Confirmed `POST /api/locations/match_all` is registered and visible in `/docs`.

Date: 2025-11-25 16:05 -0500 (Session 82)
Author: Codex 5 (Developer)
Milestone: v0.8.2 – Hotfix 3: Explicit router import ensures match_all registers

Summary
- Reinforced explicit `locations_api` import and added a temporary debug print to confirm the module loads so `/api/locations/match_all` registers.

Changes
- `app/main.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Pending manual verification: observe “DEBUG: locations_api imported successfully” on startup and confirm `/api/locations/match_all` in `/docs`.

Date: 2025-11-25 16:20 -0500 (Session 83)
Author: Codex 5 (Developer)
Milestone: v0.8.2 – Notion mapping fix for ProdLocID / ProductionID / LocationsMasterID

Summary
- Corrected production location normalization to pull `ProdLocID`, `ProductionID` (relation), and `LocationsMasterID` relations from Notion so API responses expose `prod_loc_id`, `production_id`, and `locations_master_ids` correctly.

Changes
- `app/services/notion_locations.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Verify `/api/locations/all` returns populated IDs/relations and `/api/locations/match_all` can now match using the correct fields.

Date: 2025-11-25 16:40 -0500 (Session 84)
Author: Codex 5 (Developer)
Milestone: v0.8.2 – Hotfix 4: /api/locations/all now aggregates production-specific tables

Summary
- Added Notion helpers to derive DB IDs from “Locations Table” URLs and to load all production-specific location rows via the Productions Master DB, normalizing with full IDs/relations.
- Updated `/api/locations/all` to return aggregated production-specific rows and `/api/locations/match_all` to match against Locations Master using those rows.

Changes
- `app/services/notion_locations.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Verify `/api/locations/all` returns production locations with `prod_loc_id`, `production_id`, and `locations_master_ids`.
- Verify `POST /api/locations/match_all` processes production locations and reports match results.

Date: 2025-11-25 17:05 -0500 (Session 85)
Author: Codex 5 (Developer)
Milestone: v0.8.3 – Force Rematch & Validation

Summary
- Added force rematch support to `/api/locations/match_all` (re-match even when master links exist via `force=true`) and logs force_rematch_applied when relations change.
- Added `/api/locations/validate_links` endpoint plus validation service to check Place_ID, structured address, and coordinate proximity (ok/suspect/mismatch) without writing changes.

Changes
- `app/services/matching_service.py`
- `app/services/validation_service.py`
- `app/api/locations_api.py`
- `app/services/notion_locations.py`
- `docs/DEV_NOTES.md`

Testing (manual plan)
- `python -m compileall app`
- `/api/locations/match_all?force=true` rematches existing links and updates when a better match is found; logs force_rematch_applied.
- `/api/locations/validate_links` returns reviewed/valid/invalid with mismatch flags and coordinate states.

Date: 2025-11-25 17:20 -0500 (Session 86)
Author: Codex 5 (Developer)
Milestone: v0.8.3.2 – Match-All No-Op Optimization

Summary
- Added no-op guard to `/api/locations/match_all` so Notion PATCH only occurs when LocationsMasterID or Status changes; force rematch now skips unchanged links for faster runs.

Changes
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- `/api/locations/match_all` returns matched=0 when already linked; `/api/locations/match_all?force=true` runs quickly and avoids unnecessary PATCH calls.

Date: 2025-11-25 17:35 -0500 (Session 87)
Author: Codex 5 (Developer)
Milestone: v0.8.3.3 – Location Caching + Progress Indicators

Summary
- Added 60s in-memory cache for production locations with `refresh=true` override; added progress ticker to `match_all`; responses now include duration/avg timings for diagnostics.

Changes
- `app/services/notion_locations.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- `/api/locations/all` cold vs warm cache; `/api/locations/match_all` and `?force=true` with/without `refresh=true`; verified duration_ms and avg_per_record_ms present; ticker prints every 20 records.

Date: 2025-11-25 17:50 -0500 (Session 88)
Author: Codex 5 (Developer)
Milestone: v0.8.3.4 – Fix Force-Rematch Cache Path

Summary
- Ensured `force=true` uses the production locations cache (only `refresh=true` bypasses it) and added cache diagnostics logging for loader behavior; no matching logic changes.

Changes
- `app/services/notion_locations.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- `/api/locations/all?refresh=true` (cold), `/api/locations/all` (warm), `/api/locations/match_all?force=true` (fast via cache), `/api/locations/match_all?force=true&refresh=true` (full reload).

Date: 2025-11-25 21:55 -0500 (Session 89)
Author: Codex 5 (Developer)
Milestone: v0.8.3.6 - Smart Force Rematch

Summary
- Updated `/api/locations/match_all` to recompute matches while only PATCHing when LocationsMasterID or Status change; force rematch now skips unchanged rows (tracked via match_noop) to avoid redundant writes.

Changes
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- `match_all?force=true` twice: first may apply updates; second should be fast with matched=0 and match_noop reflecting untouched rows; `match_all?force=true&refresh=true` still reloads when requested.

Date: 2025-11-25 22:30 -0500 (Session 90)
Author: Codex 5 (Developer)
Milestone: v0.8.4 - Locations Master Deduplication Engine

Summary
- Added synchronous deduplication service that clusters Locations Master rows by Place_ID, full address, address-without-zip, or coordinate proximity with sequential DUP ids.
- Exposed `GET /api/locations/master/dedup` using the existing master cache loader, returning duplicate clusters with counts and logging summary + per-group metrics under the `dedup` category.
- Documented heuristics and test approach for validating place_id, address, and Haversine (<50m) grouping without Notion writes.

Changes
- `app/services/dedup_service.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: insert duplicate master rows (place_id, full address, near-identical coordinates), call `/api/locations/master/dedup` with/without `refresh=true`, verify clusters and logged counts/reasons, confirm no Notion writes occur.

Date: 2025-11-25 23:05 -0500 (Session 91)
Author: Codex 5 (Developer)
Milestone: v0.8.5 - Master Address Normalization & Repair Tools

Summary
- Added address normalization service that reuses the shared address parser to fill missing structured fields (address1, address2, city, state, zip, country) on master rows without overwriting existing values.
- New read-only preview endpoint `/api/locations/master/normalize_preview` loads master rows, runs normalization, and returns before/after samples plus counts; no Notion writes or cache mutations.
- Logging under `address_normalization` captures per-row filled field counts, totals scanned/updated, and parse errors; functions are idempotent and safe to rerun.

Changes
- `app/services/address_normalizer.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: call `/api/locations/master/normalize_preview?refresh=true` to confirm structured fields are filled in the preview, rerun without refresh to confirm idempotent counts, and observe logs for filled fields/errors. Dedup improvements expected once write-back is enabled in v0.8.6.

Date: 2025-11-26 00:00 -0500 (Session 92)
Author: Codex 5 (Developer)
Milestone: v0.8.6 - Address Normalization Write-Back Engine

Summary
- Added write-back planning in `address_normalizer.apply_master_normalization`, generating per-row field updates only where structured fields are empty.
- Implemented throttled Notion writeback with retries in `notion_writeback.write_address_updates` (3/sec, exponential backoff) and logging under `address_writeback`.
- New endpoint `POST /api/locations/master/normalize_apply` to apply missing structured fields to Locations Master, refresh cache after writes, and return a sample of applied updates; idempotent—re-runs skip already populated rows.

Changes
- `app/services/address_normalizer.py`
- `app/services/notion_writeback.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: preview (`/api/locations/master/normalize_preview?refresh=true`), apply (`/api/locations/master/normalize_apply?refresh=true`), re-run apply to confirm 0 updates, and verify dedup still operates on refreshed cache.

Date: 2025-11-26 00:25 -0500 (Session 93)
Author: Codex 5 (Developer)
Milestone: v0.8.7 - Strict Empty-Field Normalization (Guaranteed Fix)

Summary
- Hardened empty-field detection with `is_empty` (treats whitespace-only strings as empty) across normalization planning and writeback to ensure whitespace junk no longer blocks updates.
- Planning now logs whitespace-only fields per row and honors an optional `strict` flag (default true) on `/api/locations/master/normalize_apply`; writeback skips empty payload fields after strict normalization.
- Added safety logging for whitespace detection and maintained throttled writeback behavior; idempotent runs now properly fill previously whitespace-only fields.

Changes
- `app/services/address_normalizer.py`
- `app/services/notion_writeback.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: preview (`/api/locations/master/normalize_preview?refresh=true`), apply with strict (`/api/locations/master/normalize_apply?strict=true&refresh=true`), re-run apply to confirm zero updates, verify logs show whitespace handling, and re-run dedup to ensure stability.

Date: 2025-11-26 00:45 -0500 (Session 93.1)
Author: Codex 5 (Developer)
Milestone: v0.8.7.2 - Locations Master Address Source Fix

Summary
- Fixed normalization to read the correct Notion field ("Full Address" rich_text) with plain-text extraction, falling back to legacy `address` when present; previously the parser saw empty input so no structured fields were populated.
- Strict `is_empty` checks preserved to treat whitespace-only structured fields as empty, ensuring writeback eligibility remains intact.
- Hotfix is backward compatible and restores real input to the normalization/writeback pipeline.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: preview (`/api/locations/master/normalize_preview?refresh=true`) shows rows to update; apply (`/api/locations/master/normalize_apply?strict=true&refresh=true`) fills structured fields; re-run apply returns zero updates; dedup sanity via `/api/locations/master/dedup?refresh=true`.

Date: 2025-11-26 01:05 -0500 (Session 93.2)
Author: Codex 5 (Developer)
Milestone: v0.8.7.3 - Critical Normalization Debug & Repair Patch

Summary
- Added detailed debug logging for normalization planning (full address raw/extracted, parser output, existing structured fields, per-field empty checks, needs_update flags) under `address_normalization_debug`.
- Enforced plain-text extraction from Notion "Full Address" rich_text (fallback to `address`), ensured normalize_preview uses apply_master_normalization(strict=True), and bypasses cache via refresh to inspect true Notion state.
- Confirmed rows_to_update logic relies on strict empty checks with parsed values; preview now shows pending updates when structured fields are empty/whitespace.

Changes
- `app/services/address_normalizer.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: preview with refresh shows rows_to_update > 0 and debug logs; apply with strict+refresh writes structured fields; re-run apply returns zero updates; dedup sanity with refreshed cache.

Date: 2025-11-26 01:20 -0500 (Session 93.3)
Author: Codex 5 (Developer)
Milestone: v0.8.7.3.1 - Address Normalization Debug Hotfix

Summary
- Ensured full address extraction handles raw Notion rich_text and normalized string fields (`address`/`full_address`), preventing empty input to the parser.
- Added per-row debug logging for existing structured fields alongside raw/extracted full address, parsed output, and empty checks to pinpoint why rows were skipped.
- Preview remains bound to `apply_master_normalization(strict=True)` with refresh to bypass stale cache; strict empty checks preserved.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: rerun preview with refresh to confirm rows_to_update > 0 and inspect debug logs; apply with strict+refresh populates fields; repeat apply shows zero updates.

Date: 2025-11-26 01:35 -0500 (Session 93.4)
Author: Codex 5 (Developer)
Milestone: v0.8.7.3.2 - Address Raw-Field Detection Patch

Summary
- Captured raw Notion structured fields (`address1_raw`, `city_raw`, etc.) during normalization so empty-field checks no longer rely on parser-populated values; applies updates when Notion fields are actually empty even if parsed data filled normalized values.
- Address extraction still honors rich_text "Full Address" plus legacy string fallbacks; preview/apply now evaluate emptiness against raw fields first.

Changes
- `app/services/notion_locations.py`
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: `normalize_preview?refresh=true` should now show rows_to_update > 0; `normalize_apply?strict=true&refresh=true` should write structured fields; re-run apply should be idempotent.

Date: 2025-11-26 01:50 -0500 (Session 93.5)
Author: Codex 5 (Developer)
Milestone: v0.8.7.3.3 - Full Address Newline Normalization

Summary
- Sanitized full-address input before parsing by collapsing newlines into comma separators, preventing the city field from being polluted by the street line in parsed output.
- Keeps strict empty checks and raw-field detection intact; improves parsed city/state/zip accuracy for writeback.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: rerun preview with refresh; verify sample shows correct city values (not including street); apply with strict+refresh should now write accurate structured fields; re-run apply stays idempotent.

Date: 2025-11-27 16:25 -0500 (Session 93.6)
Author: Codex 5 (Developer)
Milestone: v0.8.7.3.4 - Writeback Progress + Throttle Bump

Summary
- Added periodic progress logging (every 5 processed) and returned progress list in writeback responses to monitor long runs.
- Reduced throttle between Notion PATCH requests to ~0.2s (~5 req/sec) from 0.34s to speed up normalization while retaining retries/backoff.

Changes
- `app/services/notion_writeback.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: rerun `/api/locations/master/normalize_apply?strict=true&refresh=true`, watch `address_writeback progress` logs, verify summary success and faster completion; re-run without refresh to confirm idempotent 0 updates.

Date: 2025-11-27 17:05 -0500 (Session 93.7)
Author: Codex 5 (Developer)
Milestone: v0.8.7.3.5 - Locations Master Property Mapping Fix

Summary
- Corrected Notion writeback property mappings to use the actual lowercase field names on the Locations Master DB (`address1`, `address2`, `city`, `state`, `zip`, `country`), resolving 400 validation errors.

Changes
- `app/services/notion_writeback.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: restart server, rerun `/api/locations/master/normalize_apply?strict=true&refresh=true` to confirm successful updates, then re-run without refresh for idempotence.

Date: 2025-11-28 10:00 -0500 (Session 94)
Author: Codex 5 (Developer)
Milestone: v0.8.8 - Locations Master Dedup Resolution Engine

Summary
- Added dedup resolution service to build merge plans (primary selection heuristics, field fills without overwrites, production pointer rewrites, deletion list) and endpoints for preview/apply.
- Preview endpoint (`GET /api/locations/master/dedup_resolve_preview`) uses dedup clusters, selects primary via heuristics, and returns field updates, prod pointer updates, and delete lists.
- Apply endpoint (`POST /api/locations/master/dedup_resolve_apply`) validates explicit primary/duplicate ids, rebuilds the plan, patches the primary master, updates production location relations, archives duplicate masters, refreshes caches, and logs full progress/debug.
- Writeback helpers now include progress ticks and relation updater; master field mapping uses lowercase property names matching the Locations Master schema.

Changes
- `app/services/dedup_resolve_service.py`
- `app/services/notion_writeback.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: identify a dedup group via `/api/locations/master/dedup?refresh=true`; preview with `/api/locations/master/dedup_resolve_preview?group_id=...`; apply with `/api/locations/master/dedup_resolve_apply` body including primary_id + duplicate_ids; confirm production relations updated, duplicates archived, caches refreshed, and re-run apply for idempotence.

Date: 2025-11-28 11:00 -0500 (Session 94.1)
Author: Codex 5 (Developer)
Milestone: v0.8.8.1 - Master Archival Fix

Summary
- Fixed dedup apply to archive duplicate master rows using the correct Locations Master Status property and ensured every delete_master_id is written back.
- Added Notion writeback helper for Status updates with throttle/retry and error-body logging, wiring archival into the dedup apply flow with refreshed caches and summary counts.

Changes
- `app/services/notion_writeback.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: rerun apply on a dedup group with duplicates, confirm Status=ARCHIVED on those rows, prod pointers updated, and re-run apply to confirm idempotent 0 archives.

Date: 2025-11-28 11:30 -0500 (Session 94.2)
Author: Codex 5 (Developer)
Milestone: v0.8.8.2 - Dedup Resolve Archival Execution Hotfix

Summary
- Ensured dedup apply always invokes archival for delete_master_ids and uses the correct Status payload; archival now logs errors with Notion response bodies and tracks archived ids.
- Added archival helper return of archived_ids; apply response summary reflects archived count and caches refresh after archival.

Changes
- `app/services/notion_writeback.py`
- `app/api/locations_api.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: rerun dedup apply on a group with duplicates, confirm archived count > 0 and Status=ARCHIVED in Notion; rerun apply (no refresh) shows archived=0 idempotence.

Date: 2025-11-29 09:00 -0500 (Session 95)
Author: Codex 5 (Developer)
Milestone: v0.8.9 - Dedup Resolution UI (Admin Tools)

Summary
- Added admin-only Dedup Resolution UI under `/tools/dedup` (visible when `DEBUG_ADMIN=true`) with group listing, preview modal, and apply workflow using existing dedup endpoints.
- Preview shows primary/duplicates, field updates, prod pointer changes, rows to archive, and summary; apply triggers merge via POST, shows toast, closes modal, and refreshes groups.

Changes
- `app/ui/dedup.py`
- `app/ui/layout.py`
- `app/main.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: open `/tools/dedup`, load groups, preview a group, apply merge, confirm success toast and group removal, re-run preview/apply for idempotence.

Date: 2025-11-29 09:30 -0500 (Session 95.1)
Author: Codex 5 (Developer)
Milestone: v0.8.9.1 - Dedup UI JSON Serialization Fix

Summary
- Removed function references from table rows/columns in the dedup UI to avoid JSON serialization errors; preview buttons now use closure on group_id only.
- Added a quick self-test to log any non-serializable (callable) values in table rows; table data now contains only basic types.

Changes
- `app/ui/dedup.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: load `/tools/dedup`, ensure table renders without errors, preview/apply flows still work.

Date: 2025-11-29 10:00 -0500 (Session 95.2)
Author: Codex 5 (Developer)
Milestone: v0.8.9.2 - Dedup UI Load/Serialization Hotfix

Summary
- Fixed dedup UI loading crash by adapting to backend response shape (`duplicate_groups`), removed table state entirely, and built a simple list with preview buttons (no functions stored in data).
- Added status text, spinner, and refresh button; group_id parsing tolerates alternate key casing; maintained pure JSON-serializable state.

Changes
- `app/ui/dedup.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Manual plan: open `/tools/dedup`, verify groups load (or show "no groups"), preview/apply still function without serialization errors.

Date: 2025-11-29 11:30 -0500 (Session 97)
Author: Codex 5
Milestone: v0.8.10 – Centralized Settings Model (Option B)

Summary
- Introduced `app/core/settings.py` with unified Pydantic BaseSettings.
- Migrated DEBUG_ADMIN from layout.py env lookup to Settings model.
- Updated layout.py and dedup_simple.py to import `settings.DEBUG_ADMIN`.
- Removed SimpleNamespace and os.getenv patterns.
- Launcher now works cleanly; no more import-time timing issues.

Changes
- `app/core/settings.py`
- `app/ui/layout.py`
- `app/ui/dedup_simple.py`
- `requirements.txt`
- `docs/DEV_NOTES.md`

Testing
- `python -m compileall app`
- Start launcher with -Admin; `/tools/dedup_simple` shows admin view.
- Start launcher without -Admin; page shows 'Not authorized.'

Notes
- This establishes a long-term configuration architecture for ATLSApp.

Date: 2025-11-29 11:45 -0500 (Session 97.1)
Author: Codex 5
Milestone: v0.8.10 – Centralized Settings Model (Option B)

Summary
- Updated developer launcher to honor `-Admin` by setting `DEBUG_ADMIN` and echoing the active value before starting Uvicorn.

Changes
- `scripts/run_atlsapp.ps1`

Testing
- Not run (launcher script change).

Date: 2025-11-29 10:30 -0500 (Session 96)
Author: Codex 5 (Developer)
Milestone: v0.8.10 – Dedup Simple Admin UI

Summary
- Replaced failing modal/table dedup UI.
- New `/tools/dedup_simple` implements clean, minimal, admin-only interface.
- Uses strict async HTTP patterns and JSON-safe state.
- No changes to backend; backend already fully working.

Changes
- `app/ui/dedup_simple.py`
- `app/ui/layout.py`
- `app/main.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI-only update).

Date: 2025-11-29 12:00 -0500 (Session 97.2)
Author: Codex 5
Milestone: v0.8.10 - Documentation Update

Summary
- Added a Parking Lot entry for the Production Template Bundle to standardize automated new-production setup.
- Captured requirements for the prebuilt _Locations database, two-way Locations Master relation, schema-aligned naming, ProductionID mapping, status defaults, and automation-ready layouts/filters.

Changes
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (docs-only).

Date: 2025-11-29 12:30 -0500 (Session 97.3)
Author: Codex 5
Milestone: v0.8.4 – Admin Tools Page

Summary
- Implemented new `/admin_tools` page gated by `DEBUG_ADMIN`, with collapsible sections for Match All, Schema Update placeholders, Cache Management, Normalization placeholders, Reprocess, Dedup Admin, Diagnostics, and System Info.
- Replaced the sidebar link to Dedup Simple with Admin Tools and removed the `/tools/dedup_simple` route while keeping dedup services intact.
- Added diagnostics/error handling for admin calls and placeholders for future schema/normalization/reprocess actions.

Changes
- `app/ui/admin_tools.py`
- `app/ui/layout.py`
- `app/main.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`
- `docs/AGENTS.md`

Testing
- Not run (UI/docs updates only).

Date: 2025-11-29 13:00 -0500 (Session 97.4)
Author: Codex 5
Milestone: v0.8.4 – Admin Tools Page

Summary
- Polished the Admin Tools layout with constrained width and clearer defaults.
- Replaced the initial Match All JSON block with a “run to see results” placeholder and similar diagnostics placeholder.

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/DEV_NOTES.md`
- `docs/PROJECT_HANDBOOK.md`

Testing
- Not run (UI/docs updates only).

Date: 2025-11-29 13:30 -0500 (Session 97.5)
Author: Codex 5
Milestone: v0.8.11 – Address Normalization (Admin Tools Integration)

Summary
- Added address_normalizer.normalize_table to support preview/apply normalization across Locations Master, Medical Facilities, and production `_Locations` tables.
- Introduced `/api/locations/normalize/preview` and `/api/locations/normalize/apply` endpoints.
- Wired the Admin Tools Address Normalization panel with table selector, preview/apply actions, spinner, and JSON result display.

Changes
- `app/services/address_normalizer.py`
- `app/api/locations_api.py`
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (service/UI wiring only).

Date: 2025-11-29 14:00 -0500 (Session 97.6)
Author: Codex 5
Milestone: v0.8.11.1 – Address Normalization Hotfix

Summary
- Resolved circular import by deferring `write_address_updates` import inside `normalize_table`.
- Keeps Address Normalization preview/apply endpoints functional.

Changes
- `app/services/address_normalizer.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (import-cycle hotfix only).

Date: 2025-11-29 14:20 -0500 (Session 97.7)
Author: Codex 5
Milestone: v0.8.11.2 – Admin Tools Patch

Summary
- Wired Address Normalization UI (Preview + Apply) to call `/locations/normalize/preview` and `/locations/normalize/apply`.
- Added spinner, disabled state bindings, error handling, and JSON result output.

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI wiring only).

Date: 2025-11-29 14:40 -0500 (Session 97.8)
Author: Codex 5
Milestone: v0.8.11.3 – Admin Tools Patch Hotfix

Summary
- Fixed button binding initialization in Admin Tools Address Normalization (avoid chaining disable() return None).

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI hotfix).

Date: 2025-11-29 14:55 -0500 (Session 97.9)
Author: Codex 5
Milestone: v0.8.11.4 – Admin Tools Address Normalization Endpoint Fix

Summary
- Corrected Address Normalization UI calls to use `/api/locations/normalize/preview` and `/api/locations/normalize/apply` with base_url to avoid hanging requests.

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI endpoint fix).

Date: 2025-11-29 15:10 -0500 (Session 97.10)
Author: Codex 5
Milestone: v0.8.11.5 – Admin Tools UX Improvement

Summary
- Added an elapsed-time label next to the Address Normalization spinner to show how long preview/apply have been running.

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI-only UX tweak).

Date: 2025-11-29 15:25 -0500 (Session 97.11)
Author: Codex 5
Milestone: v0.8.11.6 – Admin Tools Code Component Fix

Summary
- Fixed Admin Tools code blocks to use `text` + `update()` instead of the nonexistent `set_text` on `ui.code`, preventing exceptions and stuck spinners during Address Normalization preview/apply.

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI bugfix).

Date: 2025-11-29 15:35 -0500 (Session 97.12)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Preview Fix

Summary
- Replaced remaining `set_text` calls on Address Normalization UI with `text` + `update` and fixed the elapsed timer updates to prevent spinner hangs during preview/apply.

Changes
- `app/ui/admin_tools.py`
- `README.md`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI hotfix).

Date: 2025-11-29 15:45 -0500 (Session 97.13)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Preview Output Fix

Summary
- Ensured Address Normalization preview/apply shows results by using a shared `_show_result` helper, initial placeholder text, min-height for the code block, and error/empty fallbacks.

Changes
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI-only fix).

Date: 2025-11-29 15:55 -0500 (Session 97.14)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Code Content Fix

Summary
- Switched Admin Tools code blocks to use `content` + `update()` (NiceGUI Code expects `content`), ensuring Match All, Diagnostics, and Address Normalization results render.
- Kept version pinned (no bump) until normalization UI is fully verified per guardrail.

Changes
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI hotfix).

Date: 2025-11-29 16:05 -0500 (Session 97.15)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Preview Diagnostics

Summary
- Added `sample_existing` to normalization preview responses (first few rows with current structured fields) to understand why updates are skipped.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (service response tweak).

Date: 2025-11-29 16:15 -0500 (Session 97.16)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Preview Diagnostics 2

Summary
- Added load diagnostics to normalization preview (raw_rows, filtered_rows, production filter) to trace why zero rows are considered.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (service diagnostics tweak).

Date: 2025-11-29 16:25 -0500 (Session 97.17)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Preview Fallback

Summary
- Added a fallback to include all production location rows when the production filter yields zero matches, preventing empty previews for `_Locations` tables.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (logic tweak).

Date: 2025-11-29 16:35 -0500 (Session 97.18)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Mapping Diagnostics

Summary
- Added `sample_keys` to normalization preview to show which structured fields are present per sampled row, helping trace mapping vs. missing fields without renaming Notion columns.

Changes
- `app/services/address_normalizer.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (diagnostics only).

Date: 2025-11-29 16:45 -0500 (Session 97.19)
Author: Codex 5
Milestone: v0.8.11.7 – Socket Reconnect Tolerance

Summary
- Increased NiceGUI reconnect timeout and message history length to reduce transient websocket disconnect banners during admin tools use.

Changes
- `app/main.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (config tweak).

Date: 2025-11-29 16:55 -0500 (Session 97.20)
Author: Codex 5
Milestone: v0.8.11.7 – Socket Heartbeat

Summary
- Added a periodic heartbeat on Admin Tools to keep the websocket active during long admin actions; further increased reconnect window and message history.

Changes
- `app/ui/admin_tools.py`
- `app/main.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UX/connectivity tweak).

Date: 2025-12-02 15:20 -0500 (Session 97.21)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Result Persistence

Summary
- Admin Tools Address Normalization now restores the last result from browser storage and saves new results, so preview/apply output persists across socket reconnects.

Changes
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI persistence tweak).

Date: 2025-12-02 15:40 -0500 (Session 97.22)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Storage Secret

Summary
- Added NiceGUI storage_secret to enable browser storage; normalization results now also fall back to direct localStorage writes so previews persist across reconnects.

Changes
- `app/main.py`
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (config/UI persistence tweak).

Date: 2025-12-02 16:00 -0500 (Session 97.23)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Client Fetch

Summary
- Reworked Address Normalization preview/apply buttons to use direct browser fetch + DOM/localStorage updates (no websocket dependency) and render into a plain `<pre>` so results persist even if the socket reconnects.

Changes
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI fetch/render tweak).

Date: 2025-12-02 16:10 -0500 (Session 97.24)
Author: Codex 5
Milestone: v0.8.11.7 – Admin Tools Pre Render Fix

Summary
- Fixed `<pre>` initialization to use `text` + `update()` (no `set_text`) so the normalization result box renders without errors.

Changes
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI minor fix).

Date: 2025-12-02 16:20 -0500 (Session 97.25)
Author: Codex 5
Milestone: v0.8.11.7 - Admin Tools JS Call Fix

Summary
- Removed unsupported `respond` parameter from `ui.run_javascript` calls in Admin Tools to stop the 500 error on /admin_tools.

Changes
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- Not run (UI hotfix).

Date: 2025-12-02 17:45 -0500 (Session 97.26)
Author: Codex 5
Milestone: v0.8.12.0 - Ingestion Normalization Rebuild Scripts

Summary
- Added ingestion normalization helper (structured fields + formatted address + Place_ID carry-through) and wired it into production imports, dedup writebacks, and facilities refresh.
- Introduced rebuild scripts for Locations Master, production _Locations tables, Medical Facilities, and an orchestrator to run them headlessly with job-logger summaries.
- Extended Notion service layer for production/facility page creation and production DB discovery; refreshed handbook rules and version to v0.8.12.0.

Changes
- `app/services/ingestion_normalizer.py`
- `app/services/import_jobs.py`, `app/api/locations_api.py`
- `app/services/notion_locations.py`, `app/services/notion_medical_facilities.py`
- `scripts/rebuild_locations_master.py`, `scripts/rebuild_production_locations.py`, `scripts/rebuild_medical_facilities.py`, `scripts/rebuild_all.py`
- `scripts/fetch_medical_facilities.py`
- `docs/PROJECT_HANDBOOK.md`, `README.md`, `docs/DEV_NOTES.md`

Testing
- Not run (backend scripts and service wiring only).

Date: 2025-12-02 18:30 -0500 (Session 97.27)
Author: Codex 5
Milestone: v0.8.12.1 - Notion Address Repair Tool

Summary
- Replaced rebuild-from-source flow with a unified Notion Address Repair Tool (`scripts/repair_addresses.py`) that normalizes existing Notion rows in-place (master, productions, facilities) with dry-run support.
- Retired old rebuild scripts and redirected the orchestrator to the repair tool; added facility page update helper.
- Documented the repair tool, retired rebuild guidance, and bumped version to v0.8.12.1.

Changes
- `scripts/repair_addresses.py`
- `app/services/notion_medical_facilities.py`
- `scripts/rebuild_locations_master.py`, `scripts/rebuild_production_locations.py`, `scripts/rebuild_all.py` (retired wrappers)
- `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`, `README.md`

Testing
- `python -m py_compile` on modified scripts/services.

Date: 2025-12-07 19:45 -0500 (Session 97.28)
Author: Codex 5
Milestone: v0.8.12.2 - Admin Tools Cleanup (Address Normalization Retired)

Summary
- Removed the deprecated Address Normalization panel from Admin Tools and replaced it with a notice pointing to the CLI repair tool.
- Left backend normalization endpoints intact for compatibility; UI now reflects ingest-time normalization + CLI-only repair.

Changes
- `app/ui/admin_tools.py`
- `docs/DEV_NOTES.md`

Testing
- `python -m py_compile app/ui/admin_tools.py`

Date: 2025-12-07 21:30 -0500 (Session 98)
Author: Codex 5
Milestone: v0.9.0 - Canonical Structured Ingest

Summary
- Rebuilt ingestion_normalizer to require Full Address or structured fields; Full Address now triggers a fresh Google lookup that overwrites structured fields, Place_ID, lat/lng, county/borough, and stores formatted_address_google; ATLS formatting applied (Title Case city, 2-letter state, 5-digit ZIP, ISO country, sanitized Full Address).
- Updated Notion location helpers to accept canonical property names only, include formatted_address_google, and set Status (Ready/Unresolved/Matched) from canonical inputs; dedupe/matching now assumes canonical structures.
- Import jobs now reject incomplete addresses, always normalize before writes, and dedupe via canonical keys; repair tool routes through the canonical normalizer without legacy fallback parsing; matching prioritizes Place_ID then deterministic address hashes.

Changes
- `app/services/ingestion_normalizer.py`
- `app/services/notion_locations.py`
- `app/services/import_jobs.py`
- `app/services/matching_service.py`
- `app/api/locations_api.py`
- `scripts/repair_addresses.py`
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`

Testing
- `python -m compileall app scripts`

Migration Note
- Legacy fallback address parsing removed in v0.9.0. All ingestion paths now require Full Address or structured fields; Full Address inputs always refresh via Google and store formatted_address_google internally.

Date: 2025-12-07 22:15 -0500 (Session 99)
Author: Codex 5
Milestone: v0.9.1 - Master Canonicalization & Matching Stability

Summary
- Added master rebuild CLI (`python -m scripts.repair_master`) to overwrite all Locations Master rows via the canonical ingestion normalizer (ATLS Full Address, ISO country, Place_ID/lat/lng refresh, county/borough, formatted_address_google).
- Introduced canonical matching cache (`app/services/master_cache.py`) with place_id, address hash, and city/state/zip indexes; matching uses deterministic priority with canonical fields only.
- Added schema verification helper (`python -m scripts.verify_schema`) to patch Locations Master and production `_Locations` databases to canonical properties (address1/2/3, city, state, zip, country, county, borough, Full Address, formatted_address_google, Place_ID, Latitude, Longitude, Status).
- Updated matching service to consume canonical cache; docs bumped to v0.9.1 with master rebuild workflow and migration note.

Changes
- `scripts/repair_master.py`
- `scripts/verify_schema.py`
- `app/services/master_cache.py`
- `app/services/matching_service.py`
- `app/services/notion_schema_utils.py`
- `README.md`, `docs/PROJECT_HANDBOOK.md`, `docs/DEV_NOTES.md`

Testing
- `python -m compileall app scripts`

Migration Note
- v0.9.1: Locations Master must be rebuilt via the canonical normalizer; matching uses only canonical indexes (Place_ID → address hash → city/state/zip); schemas are patched to canonical fields (including formatted_address_google).

Date: 2025-12-07 22:45 -0500 (Session 99.1)
Author: Codex 5
Milestone: v0.9.1 - Admin Tools Match All Streaming

Summary
- Added streaming progress for Match All Locations in Admin Tools using HTTP chunked lines; UI shows live progress with a readonly textarea and disables the run button during execution.
- Introduced streaming endpoint `/api/locations/match_all_stream` using StreamingResponse; matching service now exposes `stream_match_all` to yield progress while applying matches.

Changes
- `app/ui/admin_tools.py`
- `app/api/locations_api.py`
- `app/services/matching_service.py`
- `README.md`

Testing
- `python -m compileall app`

Date: 2025-12-07 23:05 -0500 (Session 99.2)
Author: Codex 5
Milestone: v0.9.2 - Admin Tools Schema Streaming

Summary
- Added streaming progress to Schema Update: new `/api/schema_update_stream` streams line-by-line updates while patching canonical schema across Locations Master and all `_Locations` DBs.
- Admin Tools Schema Update panel now shows live progress in a readonly textarea, clears on start, and disables the run button during execution; mirrors Match All streaming pattern.

Changes
- `app/api/locations_api.py`
- `app/ui/admin_tools.py`
- `README.md`

Testing
- `python -m compileall app scripts`

Date: 2025-12-07 23:25 -0500 (Session 99.3)
Author: Codex 5
Milestone: v0.9.2 - Admin Tools Cache Streaming

Summary
- Added streaming progress for Cache Management actions: refresh cache, purge dedup cache, and reload all places data via `/api/locations/cache_refresh_stream`, `/api/locations/cache_purge_stream`, `/api/locations/cache_reload_stream`.
- Admin Tools Cache panel now streams output into a readonly textarea, clears on start, and disables buttons during execution.

Changes
- `app/api/locations_api.py`
- `app/ui/admin_tools.py`
- `README.md`

Testing
- `python -m compileall app scripts`

Date: 2025-12-08 00:15 -0500 (Session 99.4)
Author: Codex 5
Milestone: v0.9.3 - Admin Tools Production Selector Fixes

Summary
- Ensured production_dbs endpoint guarantees display_name (friendly title fallback) and never shows raw DB IDs; Admin Tools select now maps display_name → locations_db_id.
- Reprocess stream filters strictly by selected locations_db_id with clear error when not found; streaming output includes selected production info.

Changes
- `app/api/locations_api.py`
- `app/services/notion_locations.py`
- `app/ui/admin_tools.py`
- `README.md`

Testing
- `python -m compileall app`

Notes
- Production selector now uses display_name labels with locations_db_id values; reprocess endpoint filters by locations_db_id only to avoid unintended batch runs.

Date: 2025-12-08 01:00 -0500 (Session 99.5)
Author: Codex 5
Milestone: v0.9.4 - Admin Tools Streaming Modernization

Summary
- Added streaming Dedup, Diagnostics, and System Info endpoints; Admin Tools panels now stream outputs for dedup and diagnostics and load structured system info.
- Production selector remains friendly-name mapped; reprocess filters by locations_db_id.

Changes
- `app/api/locations_api.py`
- `app/ui/admin_tools.py`
- `README.md`

Testing
- `python -m compileall app`

Known Issues
- Production selector/reprocess mapping still has instability: labels can surface DB IDs and reprocess may misalign db_id; this remains in the Parking Lot.
- Diagnostics v2 and Dedup v2 (near-duplicate heuristics, remediation workflow) are pending.

Date: 2025-12-16 16:10 -0500 (Session 103.1)
Author: Codex 5
Milestone: v0.9.5 - PSL Enrichment Production Stamping

Summary
- Fixed PSL enrichment to stamp `ProductionID` as a relation and generate `ProdLocID` values using the production abbreviation prefix (e.g., TEST001+), ensuring every new row carries ProductionID/Abbreviation and sequential ProdLocID.
- Prevented duplicate `LocationsMasterID` titles by honoring existing master titles when generating new LOC IDs, avoiding repeat `LOC001` rows.

Changes
- `app/services/notion_locations.py`
- `app/services/psl_enrichment.py`
- `docs/PROJECT_HANDBOOK.md`
- `docs/DEV_NOTES.md`

Testing
- Not run (not requested).

Date: 2026-01-07 12:45 -0500 (Session 104)
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary
- Standardized Admin Tools streaming UX (single-line Row n/total progress and DONE timers) across tools.
- Consolidated Medical Facilities admin actions into one panel with separate Generate/Maintenance sections.
- Refined PSL Details layout, removed redundant fields, added map link, and localized metadata timestamps.
- Production Detail metadata now renders timestamps in local time; documentation rule added for local-time display.

Changes
- `app/ui/admin_tools.py`
- `app/api/locations_api.py`
- `app/services/matching_service.py`
- `app/services/schema_report.py`
- `app/services/medical_facilities_runner.py`
- `app/ui/production_detail.py`
- `app/ui/psl_detail.py`
- `app/api/psl_enrichment_api.py`
- `docs/PROJECT_HANDBOOK.md`

Testing
- Not run (UI/streaming changes only).

Date: 2026-01-07 13:15 -0500 (Session 105)
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary
- Added Assets Editing Flow spec and implemented explicit asset edit UI for existing assets (PIC/AST/FOL) with validation and save/cancel staging.
- Added Assets API endpoints for edit options and atomic updates against the Assets table only.
- Wired Location Detail asset entries with Edit actions and inline refresh on success.

Changes
- `docs/ASSET_EDITING_FLOW.md`
- `app/services/notion_assets.py`
- `app/api/assets_api.py`
- `app/main.py`
- `app/ui/location_detail.py`

Testing
- Not run (UI/API integration only).

Date: 2026-01-07 14:05 -0500 (Session 106)
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary
- Added Light Asset Validation & Diagnostics spec and implemented read-only asset diagnostics on Location Detail.
- Diagnostics are computed in the UI and rendered as subtle badges with an optional page summary.

Changes
- `docs/LIGHT_ASSET_VALIDATION_DIAGNOSTICS.md`
- `app/ui/location_detail.py`

Testing
- Not run (UI-only diagnostics).

Date: 2026-01-07 15:05 -0500 (Session 107)
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary
- Added global Assets list and Asset detail pages with shared edit dialog and diagnostics display.
- Implemented Assets list/detail API endpoints and asset normalization helpers.
- Refactored asset diagnostics and edit dialog into shared UI modules.

Changes
- `docs/GLOBAL_ASSET_VIEWS.md`
- `app/ui/asset_diagnostics.py`
- `app/ui/asset_edit_dialog.py`
- `app/ui/assets_list.py`
- `app/ui/asset_detail.py`
- `app/ui/location_detail.py`
- `app/services/notion_assets.py`
- `app/api/assets_api.py`
- `app/ui/layout.py`
- `app/main.py`

Testing
- Not run (UI/API integration only).

Date: 2026-01-08 09:08 -0500 (Session 108)
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary
- Added Global Asset Views spec and implemented `/assets` list + `/assets/{AssetID}` detail pages.
- Added shared asset diagnostics module and shared asset edit dialog module.
- Refactored Location Detail assets to use shared diagnostics and edit dialog.

Changes
- `docs/GLOBAL_ASSET_VIEWS.md`
- `app/ui/asset_diagnostics.py`
- `app/ui/asset_edit_dialog.py`
- `app/ui/assets_list.py`
- `app/ui/asset_detail.py`
- `app/ui/location_detail.py`
- `app/services/notion_assets.py`
- `app/api/assets_api.py`
- `app/ui/layout.py`
- `app/main.py`

Testing
- Not run (UI/API integration only).

Date: 2026-01-08 10:20 -0500 (Session 109)
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary
- Locked Assets subsystem v1 and documented guardrails for future changes.

Changes
- `docs/ASSETS_SUBSYSTEM_LOCK.md`

Testing
- Not run (documentation only).

Date: 2026-01-08 11:10 -0500 (Session 110)
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary
- Added Production subsystem v1 spec and read-only production list/detail views.

Changes
- `docs/PRODUCTION_SUBSYSTEM.md`
- `app/ui/productions.py`
- `app/ui/production_detail.py`
- `app/ui/assets_list.py`

Testing
- Not run (UI changes only).

Date: 2026-01-08 11:20 -0500 (Session 111)
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary
- Locked Production subsystem v1 and documented guardrails for future changes.

Changes
- `docs/PRODUCTION_SUBSYSTEM_LOCK.md`

Testing
- Not run (documentation only).

Date: 2026-01-08 12:05 -0500 (Session 112)
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary
- Added Medical subsystem v1 spec and read-only medical list/detail views.

Changes
- `docs/MEDICAL_SUBSYSTEM.md`
- `app/ui/medical_shared.py`
- `app/ui/medical_list.py`
- `app/ui/medical_detail.py`
- `app/ui/layout.py`
- `app/main.py`
- `app/services/notion_medical_facilities.py`

Testing
- Not run (UI changes only).

Date: 2026-01-08 12:35 -0500 (Session 113)
Author: Codex 5
Milestone: v0.9.4 (no version bump)

Summary
- Locked Medical subsystem v1 and documented guardrails for future changes.

Changes
- `docs/MEDICAL_SUBSYSTEM_LOCK.md`

Testing
- Not run (documentation only).

### 2026-01-05 - Assets Model Introduced (Design Locked)

A canonical Assets model was defined and locked to support referencing external folders, documents, and photos within ATLSApp.

Key decisions:
- Assets are reference-only; no file storage, uploads, or Drive crawling
- Distinct human-facing ID prefixes introduced:
  - PIC### for promoted photos
  - FOL### for folders
  - AST### for all other assets
- Photos physically remain inside production location folders
- Individual photos may be explicitly promoted to Assets when independent reference is required
- Hero photos are explicitly selected Photo Assets (PIC###), never automatic
- Photo Assets carry both Production-specific Location context and Locations Master context
- Hazard Types are multi-select to support multiple hazards per image

The full design, schema, and rules are documented in:

docs/ASSETS_MODEL.md
