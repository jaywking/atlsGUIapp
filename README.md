# ATLS GUI App

**Above the Line Safety – ATLSApp / NiceGUI Prototype**

ATLS GUI App is the browser-based interface for the *ATLSApp* project — a unified toolset that supports production safety workflows such as location management, medical facility lookups, and risk assessment document generation. It’s built using **NiceGUI** and **FastAPI**, with a focus on clarity, speed, and compatibility with existing CLI scripts.

---

## 📁 Project Structure

app/
├─ main.py                # Entry point – launches FastAPI + NiceGUI app
└─ ui/
├─ layout.py          # Common layout (header + sidebar)
├─ productions.py     # Production dashboard (baseline view)
├─ locations.py       # Production locations table
├─ medicalfacilities.py  # Nearby medical facilities table + map
├─ jobs.py            # Background job / process monitor
└─ settings.py        # Environment config page

---

## 🚀 Run Locally

### Prerequisites
- Python 3.10+
- FastAPI + NiceGUI

Install dependencies:
```bash
pip install nicegui fastapi uvicorn

Run the app:

uvicorn app.main:fastapi_app --reload

Visit:

http://localhost:8080


⸻

🧩 Current Scope

This prototype focuses on:
	•	Managing Productions as the top-level organizing unit
	•	Viewing Locations linked to each production
	•	Displaying nearby Medical Facilities using Google Maps integration

Later iterations will incorporate:
	•	RASP & LHA generation
	•	Notion API sync
	•	Background job tracking and document previews

⸻

🧠 Notes

This repo currently includes layout-only NiceGUI pages.
Functional logic will be added by connecting existing ATLS scripts (e.g., process_new_locations.py, fetch_medical_facilities.py) via FastAPI service adapters.

⸻

Author: Jay King
Organization: Above the Line Safety LLC
Last Updated: November 2025

---
