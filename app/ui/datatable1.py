from __future__ import annotations

from typing import Any, Dict, List

from nicegui import ui

from app.ui.layout import PAGE_HEADER_CLASSES


def page_content() -> None:
    rows: List[Dict[str, Any]] = [
        {
            "id": "ROW001",
            "name": "Amin Driving School",
            "type": "Business",
            "city": "Jersey City",
            "state": "NJ",
            "updated": "2025-01-18 10:12",
            "map_url": "https://maps.google.com/?q=3495+John+F.+Kennedy+Blvd+Jersey+City+NJ",
        },
        {
            "id": "ROW002",
            "name": "The Madison Hotel",
            "type": "Hotel",
            "city": "Morristown",
            "state": "NJ",
            "updated": "2025-01-18 11:20",
            "map_url": "https://maps.google.com/?q=1+Convent+Rd+Morristown+NJ",
        },
        {
            "id": "ROW003",
            "name": "Vitalis Pharmacy",
            "type": "Pharmacy",
            "city": "Jersey City",
            "state": "NJ",
            "updated": "2025-01-17 16:05",
            "map_url": "https://maps.google.com/?q=3495+John+F.+Kennedy+Blvd+Jersey+City+NJ",
        },
        {
            "id": "ROW004",
            "name": "Shoreline Charters",
            "type": "Business",
            "city": "Chicago",
            "state": "IL",
            "updated": "2025-01-16 09:41",
            "map_url": "https://maps.google.com/?q=474+N+Lake+Shore+Dr+Chicago+IL",
        },
        {
            "id": "ROW005",
            "name": "North Pier Apartments",
            "type": "Residential",
            "city": "Chicago",
            "state": "IL",
            "updated": "2025-01-15 14:33",
            "map_url": "https://maps.google.com/?q=474+N+Lake+Shore+Dr+Chicago+IL",
        },
        {
            "id": "ROW006",
            "name": "Carlos Fruits and Vegetables",
            "type": "Store",
            "city": "Jersey City",
            "state": "NJ",
            "updated": "2025-01-14 12:58",
            "map_url": "https://maps.google.com/?q=3495+John+F.+Kennedy+Blvd+Jersey+City+NJ",
        },
        {
            "id": "ROW007",
            "name": "SEI Consulting",
            "type": "Business",
            "city": "Chicago",
            "state": "IL",
            "updated": "2025-01-13 08:20",
            "map_url": "https://maps.google.com/?q=474+N+Lake+Shore+Dr+Chicago+IL",
        },
        {
            "id": "ROW008",
            "name": "MAT Action",
            "type": "Business",
            "city": "Chicago",
            "state": "IL",
            "updated": "2025-01-12 18:44",
            "map_url": "https://maps.google.com/?q=474+N+Lake+Shore+Dr+Chicago+IL",
        },
    ]

    state: Dict[str, Any] = {"rows": rows, "filtered": list(rows)}

    with ui.column().classes("w-full gap-3"):
        with ui.row().classes("items-end gap-2 flex-wrap w-full"):
            search_input = ui.input(label="Search name").props("dense clearable").classes("flex-1 min-w-[220px]")
            type_select = ui.select(
                ["All", "Business", "Hotel", "Pharmacy", "Residential", "Store"],
                value="All",
                label="Type",
            ).props("dense dropdown-icon=keyboard_arrow_down").classes("w-48")
            state_select = ui.select(
                ["All", "IL", "NJ"],
                value="All",
                label="State",
            ).props("dense dropdown-icon=keyboard_arrow_down").classes("w-28")
            search_button = ui.button("Search", icon="search").classes(
                "bg-blue-500 text-white hover:bg-blue-600"
            )
            clear_button = ui.button("Clear", icon="refresh").classes(
                "bg-slate-200 text-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800"
            )

        with ui.expansion("Advanced Filters", icon="tune", value=False).classes("w-full"):
            with ui.row().classes("items-end gap-2 flex-wrap w-full"):
                city_input = ui.input(label="City contains").props("dense clearable").classes("w-56")
                updated_input = ui.input(label="Updated after (YYYY-MM-DD)").props("dense clearable").classes("w-64")
                status_select = ui.select(
                    ["All", "Active", "Inactive"],
                    value="All",
                    label="Status",
                ).props("dense dropdown-icon=keyboard_arrow_down").classes("w-40")

        status_label = ui.label("Use the search controls to filter results.").classes("text-sm text-slate-500")

        columns = [
            {"name": "id", "label": "ID", "field": "id", "sortable": True},
            {"name": "name", "label": "Name", "field": "name", "sortable": True},
            {"name": "type", "label": "Type", "field": "type", "sortable": True},
            {"name": "city", "label": "City", "field": "city", "sortable": True},
            {"name": "state", "label": "State", "field": "state", "sortable": True},
            {"name": "updated", "label": "Last Updated", "field": "updated", "sortable": True},
            {"name": "map", "label": "Map", "field": "map_url", "sortable": False},
        ]

        table = (
            ui.table(columns=columns, rows=state["filtered"], row_key="id")
            .classes("w-full text-sm q-table--flat")
            .props('wrap-cells flat square separator="horizontal" no-data-label="No data available"')
        )

    table.add_slot(
        "body-cell-name",
        """
        <q-td :props="props">
          <span class="font-semibold">{{ props.row.name }}</span>
        </q-td>
        """,
    )

    table.add_slot(
        "body-cell-map",
        """
        <q-td :props="props">
              <a
                v-if="props.row.map_url"
                :href="props.row.map_url"
                target="_blank"
                class="px-2 py-1 rounded inline-flex items-center hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                Map
              </a>
              <span v-else class="px-2 py-1 text-slate-500">--</span>
            </q-td>
            """,
        )

    def apply_filters() -> None:
        term = (search_input.value or "").strip().lower()
        type_val = type_select.value or "All"
        state_val = state_select.value or "All"
        filtered = []
        for row in state["rows"]:
            if term and term not in row.get("name", "").lower():
                continue
            if type_val != "All" and row.get("type") != type_val:
                continue
            if state_val != "All" and row.get("state") != state_val:
                continue
            filtered.append(row)
        state["filtered"] = filtered
        table.rows = filtered
        table.update()
        status_label.set_text(f"Returned {len(filtered)} rows" if filtered else "No data available.")

    def clear_filters() -> None:
        search_input.value = ""
        type_select.value = "All"
        state_select.value = "All"
        apply_filters()

    search_button.on_click(lambda _: apply_filters())
    clear_button.on_click(lambda _: clear_filters())
    search_input.on("keydown.enter", lambda _: apply_filters())
