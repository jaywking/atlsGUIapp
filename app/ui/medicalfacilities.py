from __future__ import annotations

import json
import math
import re
from typing import Any, Dict, List, Optional

from nicegui import ui

from app.ui.layout import PAGE_HEADER_CLASSES

US_STATE_CODES = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "DC",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "PR",
}

def page_content() -> None:
    """Medical Facilities page with client-side search, filters, sorting, and pagination."""

    state: Dict[str, Any] = {
        "all_facilities": [],
        "filtered_rows": [],
        "paginated_rows": [],
        "facility_rows": {},
        "page": 1,
        "limit": 25,
        "total": 0,
        "search_initiated": False,
        "filters": {"name": "", "address": "", "state": "", "facility_type": "All"},
        "sort": "name_asc",
    }

    # Subtle hover style for rows (global for this page)
    ui.add_head_html(
        """
<style>
.facilities-table .q-table__body tr:hover {
  background-color: #f9fafb !important;
}
.facilities-table .address-cell {
  white-space: normal !important;
  line-height: 1.25rem !important;
}
.facilities-table .name-cell {
  font-weight: 600 !important;
}
</style>
"""
    )

    # Search panel
    with ui.column().classes("w-full gap-1"):
        with ui.row().classes("items-end gap-2 flex-wrap"):
            name_input = ui.input(label="Name contains").props("dense clearable").classes("w-64")
            name_input.add_slot("prepend", '<q-icon name="search" size="18px" class="text-slate-500" />')

            address_input = ui.input(label="Address contains").props("dense clearable").classes("w-64")
            address_input.add_slot("prepend", '<q-icon name="search" size="18px" class="text-slate-500" />')

            state_input = ui.select(
                [],
                value=None,
                label="State",
            ).props("dense use-input fill-input hide-selected input-debounce=0 clearable dropdown-icon=keyboard_arrow_down").classes("w-28")

            facility_type_select = ui.select(
                ["All", "ER", "Urgent Care"],
                value="All",
                label="Facility Type",
            ).props("dense dropdown-icon=keyboard_arrow_down").classes("w-40")

            sort_select = ui.select(
                {
                    "name_asc": "Name (A→Z)",
                    "name_desc": "Name (Z→A)",
                    "type_order": "Facility Type (ER, Urgent Care)",
                    "state_asc": "State (A→Z)",
                    "state_desc": "State (Z→A)",
                },
                value="name_asc",
                label="Sort",
            ).props("dense").classes("w-48")
            sort_select.add_slot("prepend", '<q-icon name="sort" size="18px" class="text-slate-500" />')

            search_button = ui.button("Search", icon="search").classes(
                "bg-blue-500 text-white hover:bg-slate-100 dark:hover:bg-slate-800"
            )
            reset_button = ui.button("Reset", icon="refresh").classes(
                "bg-slate-200 text-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800"
            )
            refresh_button = ui.button("Refresh Cache", icon="cached").classes(
                "bg-slate-800 text-white hover:bg-slate-900 dark:hover:bg-slate-800"
            )
            spinner = ui.spinner(size="md").props("color=primary").style("display: none;")

    ui.separator().classes("w-full")

    status_label = ui.label("Use the search tool above to find facilities.").classes("text-sm text-slate-500")

    with ui.row().classes("items-center gap-2 flex-wrap w-full"):
        prev_button = ui.button("Prev").classes("bg-slate-200 text-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800")
        page_numbers_container = ui.row().classes("items-center gap-2")
        next_button = ui.button("Next").classes("bg-slate-200 text-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800")
        page_meta = ui.label("Page 1 of 1").classes("text-sm text-slate-500")

    columns = [
        {"name": "medical_facility_id", "label": "ID", "field": "medical_facility_id", "sortable": True},
        {"name": "name", "label": "Name", "field": "name", "sortable": True},
        {"name": "address", "label": "Address", "field": "address", "sortable": True},
        {"name": "facility_type", "label": "Type", "field": "facility_type", "sortable": True},
        {"name": "website", "label": "Website", "field": "website", "sortable": True},
    ]

    with ui.element("div").classes("w-full overflow-x-auto py-2").style("display: none;") as table_container:
        table = (
            ui.table(columns=columns, rows=[], row_key="row_id")
            .classes("w-full text-sm q-table--flat facilities-table")
            .props('wrap-cells flat square separator="horizontal"')
        )

        table.add_slot(
            "body-cell-facility_type",
            """
            <q-td :props="props">
              <div
                class="px-2 py-1 rounded text-xs font-semibold inline-flex items-center gap-1"
                :class="props.row.facility_type === 'ER'
                  ? 'bg-red-100 text-red-700'
                  : (props.row.facility_type === 'Urgent Care'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-slate-100 text-slate-600')"
              >
                <q-icon :name="props.row.facility_type === 'ER' ? 'local_hospital' : 'healing'" size="16px" class="q-mr-xs" />
                {{ props.row.facility_type || 'Unknown' }}
              </div>
            </q-td>
            """,
        )

        table.add_slot(
            "body-cell-website",
            """
            <q-td :props="props">
              <a
                v-if="props.row.website"
                :href="props.row.website"
                target="_blank"
                class="px-2 py-1 rounded inline-flex items-center hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                Link
              </a>
              <span v-else class="px-2 py-1 text-slate-500">--</span>
            </q-td>
            """,
        )

        table.add_slot(
            "body-cell-name",
            """
            <q-td :props="props">
              <span class="name-cell">{{ props.row.name }}</span>
            </q-td>
            """,
        )

        table.add_slot(
            "body-cell-address",
            """
            <q-td :props="props">
              <span class="address-cell">{{ props.row.address }}</span>
            </q-td>
            """,
        )

    details_dialog = ui.dialog().props('position="right" transition-show="none" transition-hide="none"').classes("w-[440px]")
    with details_dialog, ui.card().classes("w-full h-full shadow-lg"):
        with ui.column().classes("gap-3 p-4 h-full"):
            with ui.row().classes("items-center justify-between"):
                detail_title = ui.label("Facility Details").classes("text-lg font-semibold")
                ui.button(icon="close", on_click=details_dialog.close).props("flat round dense")
            ui.separator()
            with ui.row().classes("items-center gap-2"):
                ui.icon("healing").classes("text-slate-500")
                type_chip = ui.label("--").classes("px-2 py-1 rounded text-xs font-semibold bg-slate-100 text-slate-600")
            with ui.row().classes("items-start gap-2"):
                ui.icon("place").classes("text-slate-500")
                address_value = ui.label("--").classes("text-sm")
            with ui.row().classes("items-center gap-2"):
                ui.icon("phone").classes("text-slate-500")
                phone_value = ui.label("--").classes("text-sm")
                copy_button = ui.button(icon="content_copy").props("flat round dense")
            with ui.row().classes("items-center gap-2"):
                ui.icon("open_in_new").classes("text-slate-500")
                website_link = ui.link("Website", "#").classes("text-sm text-blue-600 dark:text-blue-300 underline").props("target=_blank")
            with ui.row().classes("items-center gap-2"):
                ui.icon("map").classes("text-slate-500")
                maps_link = ui.link("Map", "#").classes("text-sm text-blue-600 dark:text-blue-300 underline").props("target=_blank")
            with ui.row().classes("items-start gap-2"):
                ui.icon("schedule").classes("text-slate-500")
                hours_value = ui.column().classes("text-sm gap-1")
            with ui.row().classes("items-center gap-2"):
                notion_link = ui.element("a").classes("text-slate-500 hover:text-slate-800 dark:text-slate-300")
                notion_link.props("target=_blank aria-label='Open in Notion'")
                with notion_link:
                    ui.html(
                        "<svg viewBox=\"0 0 24 24\" width=\"18\" height=\"18\" fill=\"currentColor\" aria-hidden=\"true\">"
                        "<path d=\"M6.5 3.5h11c1.7 0 3 1.3 3 3v11c0 1.7-1.3 3-3 3h-11c-1.7 0-3-1.3-3-3v-11c0-1.7 1.3-3 3-3zm.6 3.5v10c0 .6.4 1 1 1h8.8c.6 0 1-.4 1-1v-10c0-.6-.4-1-1-1H8.1c-.6 0-1 .4-1 1zm2 .7h1.9l4.2 6.4V7.7h1.8v8.6h-1.9l-4.2-6.3v6.3H9.1V7.7z\"/>"
                        "</svg>",
                        sanitize=False,
                    )
            ui.space()
            ui.space()

    def set_loading(is_loading: bool) -> None:
        spinner.style("display: inline-block;" if is_loading else "display: none;")
        search_button.set_enabled(not is_loading)
        reset_button.set_enabled(not is_loading)
        refresh_button.set_enabled(not is_loading)

    def format_distance(raw: Any) -> str:
        if raw is None or raw == "":
            return "\u2013"
        try:
            return f"{float(raw):.1f} mi"
        except Exception:
            return str(raw)

    def _extract_state_code(address: str | None) -> Optional[str]:
        if not address:
            return None
        tokens = re.findall(r"\b([A-Za-z]{2})\b", address.upper())
        for token in reversed(tokens):
            if token in US_STATE_CODES:
                return token
        return None

    def _format_address(raw: Dict[str, Any]) -> str:
        address1 = (raw.get("address1") or "").strip()
        address2 = (raw.get("address2") or "").strip()
        address3 = (raw.get("address3") or "").strip()
        city = (raw.get("city") or "").strip()
        state = (raw.get("state") or "").strip()
        zip_code = (raw.get("zip") or "").strip()
        country = (raw.get("country") or "").strip()

        if address2 and city and address2.strip().lower() == city.strip().lower():
            address2 = ""

        parts = [p for p in [address1, address2, address3] if p]
        city_line = ""
        if city:
            city_line = city
        if state:
            city_line = f"{city_line}, {state}" if city_line else state
        if zip_code:
            city_line = f"{city_line} {zip_code}".strip()
        if city_line:
            parts.append(city_line)
        if country and country.upper() not in {"US", "USA"}:
            parts.append(country.upper())

        formatted = ", ".join(parts).strip()
        if formatted:
            return formatted
        return (raw.get("address") or "").strip()

    def normalize_row(raw: Dict[str, Any], idx: int) -> Dict[str, Any]:
        addr = _format_address(raw)
        state_code = (raw.get("state") or "").strip().upper() or _extract_state_code(addr)
        return {
            "row_id": raw.get("row_id") or raw.get("id") or f"facility-{idx}",
            "medical_facility_id": raw.get("medical_facility_id") or raw.get("MedicalFacilityID") or "",
            "name": raw.get("name") or raw.get("Name") or raw.get("MedicalFacilityID") or "Unnamed Facility",
            "facility_type": raw.get("facility_type") or "",
            "address": addr,
            "phone": raw.get("phone") or "",
            "hours": raw.get("hours") or "",
            "website": raw.get("website") or "",
            "google_maps_url": raw.get("google_maps_url") or "",
            "notion_url": raw.get("notion_url") or raw.get("url") or "",
            "distance": format_distance(raw.get("distance")),
            "place_types": raw.get("place_types") or [],
            "state_code": state_code or "",
        }

    def _page_window(total_pages: int, current: int) -> List[int]:
        if total_pages <= 3:
            return list(range(1, total_pages + 1))
        start = max(1, min(current - 1, total_pages - 2))
        return list(range(start, min(total_pages, start + 2) + 1))

    def refresh_pagination_controls() -> None:
        total_pages = max(1, math.ceil(state["total"] / state["limit"])) if state["total"] else max(
            1, math.ceil(len(state["filtered_rows"]) / state["limit"])
        )
        current_page = state["page"]
        page_meta.set_text(f"Page {current_page} of {total_pages}")
        prev_button.set_enabled(current_page > 1)
        next_button.set_enabled(current_page < total_pages)
        page_numbers_container.clear()
        pages = _page_window(total_pages, current_page)
        with page_numbers_container:
            for p in pages:
                btn_classes = "bg-slate-200 text-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800"
                if p == current_page:
                    btn_classes += " bg-blue-600 text-white hover:bg-blue-700"

                async def _go(_, target=p):
                    paginate_and_render(page=target)

                ui.button(str(p), on_click=_go).classes(btn_classes).props("flat dense")

    def apply_filters_and_sort() -> None:
        rows = list(state.get("all_facilities") or [])
        filters = state.get("filters") or {}
        name_term = (filters.get("name") or "").strip().lower()
        address_term = (filters.get("address") or "").strip().lower()
        state_term = (filters.get("state") or "").strip().upper()
        type_filter = (filters.get("facility_type") or "All").strip()

        filtered: List[Dict[str, Any]] = []
        for r in rows:
            name_val = (r.get("name") or "").lower()
            addr_val = (r.get("address") or "").lower()
            st = r.get("state_code") or _extract_state_code(r.get("address") or "")
            r_type = r.get("facility_type") or ""

            if name_term and name_term not in name_val:
                continue
            if address_term and address_term not in addr_val:
                continue
            if state_term and (not st or st != state_term):
                continue
            if type_filter and type_filter != "All" and r_type != type_filter:
                continue
            filtered.append(r)

        sort_key = state.get("sort") or "name_asc"
        if sort_key == "name_asc":
            filtered.sort(key=lambda x: (x.get("name") or "").lower())
        elif sort_key == "name_desc":
            filtered.sort(key=lambda x: (x.get("name") or "").lower(), reverse=True)
        elif sort_key == "type_order":
            order = {"ER": 0, "Urgent Care": 1}
            filtered.sort(key=lambda x: order.get(x.get("facility_type") or "", 99))
        elif sort_key == "state_asc":
            filtered.sort(key=lambda x: (x.get("state_code") or ""))
        elif sort_key == "state_desc":
            filtered.sort(key=lambda x: (x.get("state_code") or ""), reverse=True)

        state["filtered_rows"] = filtered
        state["total"] = len(filtered)

    def paginate_and_render(page: Optional[int] = None, show_toast: bool = False) -> None:
        if not state.get("filtered_rows"):
            table.rows = []
            table.update()
            status_label.set_text("No facilities found." if state.get("search_initiated") else "Use the search tool above to find facilities.")
            return

        if page is not None:
            state["page"] = page
        else:
            state["page"] = max(1, state.get("page") or 1)
        current = state["page"]
        limit = state.get("limit") or 25
        total = len(state["filtered_rows"])
        total_pages = max(1, math.ceil(total / limit)) if total else 1
        if current > total_pages:
            current = total_pages
            state["page"] = current
        start = (current - 1) * limit
        end = start + limit
        page_rows = state["filtered_rows"][start:end]
        state["paginated_rows"] = page_rows
        state["facility_rows"] = {r.get("medical_facility_id") or r.get("id") or r.get("row_id"): r for r in page_rows}
        table.rows = page_rows
        table.update()
        status_label.set_text(f"Returned {total} facilities (page {current} of {total_pages})")
        refresh_pagination_controls()
        if show_toast:
            ui.notify(status_label.text, type="positive")

    async def load_facilities(show_toast: bool = True, force_refresh: bool = False) -> None:
        set_loading(True)
        try:
            all_items: List[Dict[str, Any]] = []
            page_num = 1
            total_items: Optional[int] = None
            limit = 100  # API caps at 100 per call

            while True:
                refresh_flag = "true" if force_refresh and page_num == 1 else "false"
                script = (
                    "const controller = new AbortController();"
                    "const timer = setTimeout(() => controller.abort(), 8000);"
                    f"try {{ const response = await fetch('/api/medicalfacilities/list?page={page_num}&limit={limit}&refresh={refresh_flag}', {{ method: 'GET', signal: controller.signal }});"
                    "clearTimeout(timer);"
                    "if (!response.ok) { return { __error: `HTTP ${response.status}` }; }"
                    "return await response.json();"
                    "} catch (err) { clearTimeout(timer); return { __error: err?.message || 'Fetch failed' }; }"
                )
                result = await ui.run_javascript(script, timeout=9.0)
                if not isinstance(result, dict):
                    raise ValueError("Unexpected response from browser fetch")
                if result.get("__error"):
                    raise RuntimeError(result["__error"])
                if result.get("status") != "success":
                    raise RuntimeError(result.get("message") or "Unable to fetch facilities")

                payload = result.get("data") or {}
                if total_items is None:
                    total_items = payload.get("total") or 0
                raw_rows = payload.get("items") or []
                normalized = [normalize_row(r or {}, len(all_items) + idx) for idx, r in enumerate(raw_rows)]
                all_items.extend(normalized)

                if total_items and len(all_items) >= total_items:
                    break
                if not raw_rows:
                    break
                page_num += 1
                if page_num > 50:  # safety cap
                    break

            state["search_initiated"] = True
            state["all_facilities"] = all_items
            state["page"] = 1
            apply_filters_and_sort()
            paginate_and_render(page=1, show_toast=show_toast)
            table_container.style("display: block;")
            # populate state options from dataset (valid US codes only); fallback to full list if none found
            states = set()
            for r in state["all_facilities"]:
                st = r.get("state_code") or _extract_state_code(r.get("address") or "")
                if st and st in US_STATE_CODES:
                    states.add(st)
            if not states:
                states = set(US_STATE_CODES)
            state_options = sorted(states)
            state_input.options = state_options
            state_input.update()
            if not state["filtered_rows"]:
                status_label.set_text("No facilities found.")
        except Exception as exc:  # noqa: BLE001
            status_label.set_text(f"Facilities fetch failed: {exc}")
            ui.notify(f"Facilities fetch failed: {exc}", type="negative")
        finally:
            set_loading(False)

    def update_details(row: Dict[str, Any] | None) -> None:
        row = row or {}
        detail_title.set_text(row.get("name") or "Facility Details")
        type_chip.set_text(row.get("facility_type") or "Unknown")
        address_value.set_text(row.get("address") or "--")
        phone_text = row.get("phone") or "--"
        phone_value.set_text(phone_text)
        safe_phone = json.dumps(phone_text)
        copy_button.on_click(lambda _: ui.run_javascript(f"navigator.clipboard?.writeText({safe_phone});"))
        hours_value.clear()
        hours_text = row.get("hours") or ""
        parts = [p.strip() for p in hours_text.split(";") if p.strip()] if hours_text else []
        with hours_value:
            if parts:
                for part in parts:
                    ui.label(part)
            else:
                ui.label("--")
        website_url = row.get("website") or ""
        maps_url = row.get("google_maps_url") or ""
        notion_url = row.get("notion_url") or ""
        website_link.text = "Website" if website_url else "No website"
        website_link.props(f'href="{website_url or "#"}" target=_blank')
        website_link.update()
        maps_link.text = "Map" if maps_url else "No map link"
        maps_link.props(f'href="{maps_url or "#"}" target=_blank')
        maps_link.update()
        notion_link.props(f'href="{notion_url or "#"}" target=_blank')
        notion_link.update()

    async def handle_row_click(event) -> None:
        event_args = getattr(event, "args", None)
        row_id: str | None = None

        def _extract_id(obj: Dict[str, Any]) -> str | None:
            return obj.get("id") or obj.get("medical_facility_id") or obj.get("row_id") or obj.get("key")

        if isinstance(event_args, dict):
            row_id = _extract_id(event_args)
        elif isinstance(event_args, (list, tuple)) and event_args:
            for cand in event_args:
                if isinstance(cand, dict):
                    row_id = _extract_id(cand)
                    if row_id:
                        break

        row = None
        if row_id and isinstance(state.get("facility_rows"), dict):
            row = state["facility_rows"].get(row_id)

        update_details(row)
        details_dialog.open()

    async def on_search() -> None:
        filters = state["filters"]
        filters["name"] = (name_input.value or "").strip()
        filters["address"] = (address_input.value or "").strip()
        filters["state"] = (state_input.value or "").strip()
        filters["facility_type"] = facility_type_select.value or "All"
        state["sort"] = sort_select.value or "name_asc"
        if not state.get("search_initiated"):
            await load_facilities(show_toast=True)
        else:
            apply_filters_and_sort()
            paginate_and_render(page=1, show_toast=True)

    async def on_refresh_cache() -> None:
        await load_facilities(show_toast=True, force_refresh=True)

    def on_reset() -> None:
        state["filters"] = {"name": "", "address": "", "state": "", "facility_type": "All"}
        state["sort"] = "name_asc"
        name_input.value = ""
        address_input.value = ""
        state_input.value = ""
        facility_type_select.value = "All"
        sort_select.value = "name_asc"
        state["all_facilities"] = []
        state["filtered_rows"] = []
        state["paginated_rows"] = []
        state["facility_rows"] = {}
        state["page"] = 1
        state["total"] = 0
        state["search_initiated"] = False
        table_container.style("display: none;")
        table.rows = []
        table.update()
        status_label.set_text("Use the search tool above to find facilities.")

    prev_button.on_click(lambda _: paginate_and_render(page=state["page"] - 1))
    next_button.on_click(lambda _: paginate_and_render(page=state["page"] + 1))
    search_button.on_click(on_search)
    reset_button.on_click(on_reset)
    refresh_button.on_click(on_refresh_cache)
    sort_select.on("update:model-value", lambda e: (state.update({"sort": e.value or "name_asc"}), apply_filters_and_sort(), paginate_and_render(page=1)))
    name_input.on("keydown.enter", lambda _: on_search())
    address_input.on("keydown.enter", lambda _: on_search())
    state_input.on("keydown.enter", lambda _: on_search())
    table.on("row-click", handle_row_click)

    refresh_pagination_controls()
