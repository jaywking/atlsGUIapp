# ATLSApp Canonical Layout Pattern (NiceGUI-Native)

## Purpose

This document defines a single, enforceable layout rule for ATLSApp that guarantees consistent horizontal alignment across all pages.
It eliminates header drift, padding mismatches, and nested layout inconsistencies by establishing a clear ownership model for spacing.

This pattern is NiceGUI-native and avoids CSS overrides or compensating hacks.

---

## Metadata

- Document Type: UI Architecture / Layout Standard
- Applies To: ATLSApp (NiceGUI + FastAPI)
- Status: Adopted Pattern
- Last Edited: 2025-12-30
- Maintainer: ATLSApp Project

---

## Core Principle

Only one component owns horizontal padding.

All other components must be width-100 and horizontally padding-neutral.

For ATLSApp, the main scrolling content column is the single owner of horizontal padding.

---

## Canonical Layout Hierarchy

```
Root Row
├── Sidebar (fixed width)
└── Main Content Column (scroll container + padding owner)
    ├── Global Header (no horizontal padding)
    └── Page Content
        ├── Page Header (no horizontal padding)
        └── Page Body (no horizontal padding)
```

This hierarchy must be preserved on all pages.

---

## Reference Implementation (NiceGUI)

### 1. Root Layout

```python
with ui.row().classes('w-full h-screen no-wrap'):
    build_sidebar()

with ui.column().classes(
        'flex-1 h-screen overflow-y-auto overflow-x-hidden pl-3 pr-5'
    ):
        build_global_header()
        build_page_content()
```

Rules:

- px-3 is defined only here
- This column establishes the canonical left edge for the entire app
- No other component may introduce horizontal padding
- Left and right gutters should feel balanced (use the layout owner to tune)

---

### 2. Global Header (Padding-Neutral)

```python
def build_global_header():
    with ui.row().classes(
        'w-full items-center justify-between '
        'py-4 border-b border-slate-200 '
        'bg-white dark:bg-slate-900 '
        'sticky top-0 z-10'
    ):
        ui.label('Admin Tools').classes(
            'text-2xl font-semibold'
        )

        with ui.row().classes('items-center gap-3'):
            ui.label('DEV').classes('text-sm text-slate-500')
            if settings.DEBUG_ADMIN:
                ui.label('DEBUG_ADMIN enabled').classes('text-sm text-slate-500')
            build_header_controls()
```

Constraints:

- No px-* classes
- Vertical padding allowed
- Sticky positioning allowed
- Horizontal alignment inherited from parent column

---

### 3. Page Header (Padding-Neutral)

```python
def build_page_header(title: str, subtitle: str | None = None):
    with ui.row().classes(
        'w-full items-center justify-between '
        'py-2.5 mb-4 '
        'min-h-[52px]'
    ):
        ui.label(title).classes(
            'text-xl font-semibold'
        )

        if subtitle:
            ui.label(subtitle).classes(
                'text-sm text-slate-500'
            )
```

Constraints:

- No px-* classes
- No nested padding containers
- Typography may differ from the global header
- Must align exactly with the global header text above

---

### 4. Page Body / Content Blocks

```python
with ui.column().classes('w-full gap-3'):
    build_page_components()
```

Constraints:

- No horizontal padding
- Content components expand naturally to full width
- Expansion panels, tables, and cards inherit alignment automatically

---

## Explicit Prohibitions

The following patterns are not allowed anywhere in the app:

- Applying px-* to global headers
- Applying px-* to page headers
- Adding compensating padding to fix perceived misalignment
- Nesting padded containers inside padded containers
- Per-page alignment overrides

Violations must be fixed at the layout-owner level.

---

## Data Table Page Standard (Search + Results)

For list/search pages like Productions, Locations, and Medical Facilities, use this consistent structure
in addition to the canonical padding rule.

Required structure:

- Global header (page title only; no duplicate content title)
- Search panel (full width, single row where possible)
- Advanced filters (collapsible, full width)
- Status + pagination row (single line, full width)
- Results table (full width, flat)

Behavioral notes:

- Search panel uses the full content width (inputs can flex).
- Do not repeat the page title inside the content area.
- Status + pagination sit on one row (status left, pager right).
- Avoid redundant page labels when numbered page buttons are shown.

---

### Example: Status + Pagination Row (Single Line)

```python
with ui.row().classes("items-center justify-between w-full gap-2"):
    status_label = ui.label("Returned 0 rows").classes("text-sm text-slate-500")
    with ui.row().classes("items-center gap-2"):
        prev_button = ui.button("Prev").classes("bg-slate-200 text-slate-700")
        page_numbers_container = ui.row().classes("items-center gap-2")
        next_button = ui.button("Next").classes("bg-slate-200 text-slate-700")
```

Notes:
- Use numbered buttons when paginating (avoid "Page 1 of 3" labels).
- Keep buttons compact to avoid wrapping.

---

## Codex Enforcement Rules

Provide the following verbatim to Codex:

```
ATLS Layout Rule:

- The main scrolling content column is the only element allowed to define horizontal padding.
- Global headers, page headers, and page body containers must be width-100 and horizontally padding-neutral.
- Never apply px-* classes to headers or inner content containers.
- Alignment issues must be resolved by adjusting the layout owner, not by compensating padding.
```

---

## What This Pattern Solves

- Global header vs page header misalignment
- Page-to-page horizontal drift
- Nested padding accumulation
- Visual inconsistency caused by defensive spacing
- Repeated manual fixes across pages

---

## Notes

This pattern is intentionally minimal and structural.
It relies on NiceGUI primitives behaving predictably and avoids reliance on global CSS overrides.

Any future layout changes must preserve the single padding owner principle.

---

## Change Log

- 2025-12-30: Initial version created and adopted
- 2025-12-30: Documented standard layout for data-table pages (search + results)
