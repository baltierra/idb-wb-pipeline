# IDB World Bank Data Pipeline & Dashboard

A prototype dashboard that pulls key indicators from the World Bank API on‑the‑fly, caches them in‑memory, and displays them in an interactive Plotly Dash app. Built as part of the application for the IDB Data Scientist – Senior Associate position.

---
## 🔧 Technical Specifications
- **VM**: Jetstream2 Ubuntu 22.04, 6 GB RAM, 50 GB disk, Python 3.10  
- **Environment**: managed via [Poetry](https://python-poetry.org/) 2.1.2  
- **Libraries**:  
  - HTTP & caching: `httpx`, `cachetools`  
  - Config: `python-dotenv`  
  - Data: `pandas`, `pycountry`  
  - Dashboard: `dash`, `plotly`  
- **Data sources**:  
  - 26 Latin American & Caribbean countries (ISO3 codes in `.env`)  
  - 9 WB indicators (codes & common names in code)  
  - Years 2004–2023  
  - Real‑time API calls + in‑session TTL cache (default TTL 3600 s)
---
## ⚙️ Installation
1. **Clone** the repo and `cd` into it  
   ```bash
   git clone https://github.com/baltierra/idb-wb-pipeline.git
   cd idb-wb-pipeline
   ```
2. **Install** dependencies 
   ```bash
   poetry install
   ```
3. **Create your .env** (see .env.example)

   This project can utilize data from all countries available through the World Bank API and supports any indicator the user needs to analyze. The front end updates dynamically based on the selected parameters. The most important step is correctly configuring the .env file, which stores all the necessary information. **An example is provided below for reference**.

   This particular implementation only gathered information regarding the [26 IDB Borrowing Member Countries](https://www.iadb.org/en/who-we-are/how-we-are-organized/borrowing-member-countries) and 9 indicators of interest.
   ```dotenv
   WB_API_BASE_URL="https://api.worldbank.org/v2"
   COUNTRIES="ARG,BHS,BRB,BLZ,…,URY,VEN"
   INDICATORS="NV.AGR.TOTL.ZS,GC.DOD.TOTL.GD.ZS,…,GC.REV.XGRT.GD.ZS"
   START_YEAR=2004
   END_YEAR=2023
   CACHE_TTL=3600
   ```
---
## 🚀 Usage
1. **Fetch & inspect raw data**
   ```bash
   poetry run python fetch_wb.py > worldbank_data.json
   jq . worldbank_data.json | less
   ```
2. **Launch the dashboard** 
   ```bash
   poetry run python app.py
   ```
   Open your browser to `http://<your_localhost>:8050` (default port 8050).
---
## 📐 Dashboard Features
- **Country selector** (plain names)
- **Indicator selector** & real‑time **interactive line chart**
   - 2004–2023 smoothed spline + navy markers
   - Major grid at 2‑year ticks, minor grid at 1‑year ticks
   - Custom tooltip on interpolated points
- **Year picker & data table** beside the chart
   - Table sorted by original indicator order
- **Latest values tiles** below
- **Light/dark auto‑theme** via CSS vars & prefers-color-scheme
---
## 🛠️ Deployment Notes
- Consider fronting Dash with NGINX (80/443) and firewalling port 8050
- Use `systemd` to run `poetry run python app.py` as a service on boot
- Monitor via `journalctl -u your‑service`