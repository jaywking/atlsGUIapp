# ATLS GUI App

**Above the Line Safety – ATLSApp / NiceGUI + FastAPI Prototype**

ATLS GUI App is a browser-based interface for production safety management.  
It consolidates existing *LocationSync* automation scripts into an integrated web tool for handling productions, locations, and medical facilities.  

This application is part of the broader **ATLSApp ecosystem**, providing a unified dashboard to manage location-based health & safety data, Notion synchronization, and automated risk assessment workflows.

---

## 🚀 Quick Start

### Requirements
- Python 3.10+
- FastAPI
- NiceGUI
- Uvicorn
- Requests

### Setup
```bash
git clone https://github.com/jaywking/atlsGUIapp.git
cd atlsGUIapp
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
