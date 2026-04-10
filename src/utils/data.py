import pickle
import csv
import os
from tools.fetch_types import fetch_types
from tools.fetch_gtfs_static import fetch_gtfs_static


# get bus type data if not already existing
try:
    with open('types.pkl', 'rb') as f:
        processed = pickle.load(f)
        print("types.pkl loaded")
except:
    print("types.pkl not found, fetching")
    fetch_types()

# get GTFS static data if not already existing
data_dir = './data'
try:
    file_count = len(os.listdir(data_dir))
    if file_count != 16:
        raise Exception
    else:
        print("GTFS static data found")
except:
    print("GTFS static data not found, fetching")
    fetch_gtfs_static()

def load_stopcode_to_stopid(stops_path: str) -> dict[str, str]:
    m = {}
    with open(stops_path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sid = (row.get("stop_id") or "").strip()
            code = (row.get("stop_code") or "").strip()
            if sid and code:
                m[code] = sid
    return m

def load_short_to_routeid(routes_path: str) -> dict[str, str]:
    m = {}
    with open(routes_path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rid = (row.get("route_id") or "").strip()
            short = (row.get("route_short_name") or "").strip()
            if rid and short and short not in m:
                m[short] = rid
    return m

STOPCODE_TO_STOPID = load_stopcode_to_stopid("./data/stops.txt")
SHORT_TO_ROUTEID = load_short_to_routeid("./data/routes.txt")

def check_id(bus_id : int):
    with open('types.pkl', 'rb') as f:
        bus_name = None
        processed = pickle.load(f)
        for t in processed:
            for r in t['fn_range']:
                if len(r) % 2:
                    if bus_id == r[0]:
                        bus_name = f"{t['year']} {t['manufacturer']} {t['model']}"
                        break
                    else:
                        continue
                    break
                if bus_id in range(r[0], r[1]):
                    bus_name = f"{t['year']} {t['manufacturer']} {t['model']}"
                    break
        return bus_name