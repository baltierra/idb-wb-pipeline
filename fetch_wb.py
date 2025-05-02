import os, json
from dotenv import load_dotenv
from cachetools import TTLCache, cached
import httpx

# Load environment
load_dotenv()

WB_BASE = os.getenv("WB_API_BASE_URL")
COUNTRIES = os.getenv("COUNTRIES", "").split(",")
INDICATOR_CODES = os.getenv("INDICATORS", "").split(",")
START = os.getenv("START_YEAR")
END = os.getenv("END_YEAR")
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))

# Human‑readable names for each code
INDICATOR_NAME_MAP = {
    "NV.AGR.TOTL.ZS": "Agriculture, forestry, and fishing (% of GDP)",
    "GC.DOD.TOTL.GD.ZS": "Central government debt (% of GDP)",
    "NE.EXP.GNFS.ZS":  "Exports of goods and services (% of GDP)",
    "NY.GDP.PCAP.KD.ZG":"GDP per capita growth (annual %)",
    "NY.GDP.PCAP.PP.CD":"GDP per capita, PPP (current intl $)",
    "NE.IMP.GNFS.ZS":  "Imports of goods and services (% of GDP)",
    "FP.CPI.TOTL.ZG":  "Inflation, consumer prices (annual %)",
    "DT.ODA.ODAT.CD":"Net ODA received (current US$)",
    "GC.REV.XGRT.GD.ZS":"Revenue, excluding grants (% of GDP)"
}

# In‑memory TTL cache for API calls
cache = TTLCache(maxsize=500, ttl=CACHE_TTL)

@cached(cache)
def fetch_indicator_data(country_code: str, indicator_code: str):
    """
    Return the raw list of World Bank datapoints for one country/indicator.
    """
    url = f"{WB_BASE}/country/{country_code}/indicator/{indicator_code}"
    params = {
        "date": f"{START}:{END}",
        "format": "json",
        "per_page": 10000,
    }
    r = httpx.get(url, params=params, timeout=10)
    r.raise_for_status()
    payload = r.json()
    # payload[1] is the list of data points; payload[0] is paging info
    return payload[1] if isinstance(payload, list) and len(payload) > 1 else []

def build_pipeline_structure():
    """
    Assemble data into { country → year → INDICATOR: {...} } form.
    Missing years or null values are left as None.
    """
    output = {}

    for cc in COUNTRIES:
        year_map = {}
        # for each indicator, pull its data and slot into years
        for code in INDICATOR_CODES:
            name = INDICATOR_NAME_MAP.get(code, code)
            datapoints = fetch_indicator_data(cc, code)

            for dp in datapoints:
                year = dp.get("date")
                val  = dp.get("value")  # may be None
                # initialize nested dicts
                year_bucket = year_map.setdefault(year, {"INDICATOR": {}})
                year_bucket["INDICATOR"][name] = {
                    "NAME": name,
                    "CODE": code,
                    "VALUE": val
                }

        output[cc] = year_map

    return output

if __name__ == "__main__":
    data = build_pipeline_structure()
    # pretty‑print or write to file as you like
    print(json.dumps(data, indent=2))
