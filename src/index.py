from flask import Flask, jsonify, render_template, request
from google.transit import gtfs_realtime_pb2
import time
import requests
import pickle
import csv
import os
import keys
from tools.fetch_types import fetch_types
from tools.fetch_gtfs_static import fetch_gtfs_static
app = Flask(__name__)

# Replace this with your agency's GTFS-Realtime vehicle positions URL
GTFS_VEHICLE_URL = f'https://gtfsapi.translink.ca/v3/gtfsposition?apikey={keys.translink_api_key}'

GTFS_TRIP_URL = f"https://gtfsapi.translink.ca/v3/gtfsrealtime?apikey={keys.translink_api_key}"

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

STOPCODE_TO_STOPID = load_stopcode_to_stopid("stops.txt")
SHORT_TO_ROUTEID = load_short_to_routeid("routes.txt")

def check_id(bus_id : int):
    with open('types.pkl', 'rb') as f:
        bus_name = None
        processed = pickle.load(f)
        for t in processed:
            for r in t['fn_range']:
                if len(r) % 2:
                    if bus_id == r[0]:
                        bus_name = f'{t['year']} {t['manufacturer']} {t['model']}'
                        break
                    else:
                        continue
                    break
                if bus_id in range(r[0], r[1]):
                    bus_name = f'{t['year']} {t['manufacturer']} {t['model']}'
                    break
        return bus_name

# get bus type data if not already existing
try:
    with open('types.pkl', 'rb') as f:
        processed = pickle.load(f)
        print("types.pkl loaded")
except:
    print("types.pkl not found, fetching")
    fetch_types()

@app.route("/")
#get html page defined as index.html, also include mapbox token
def home():
    return render_template("index.html", key=keys.mapbox_access_token)

@app.get("/api/next_arrival")
def next_arrival():
    stop_code = request.args.get("stop_id", "").strip()
    bus_number = request.args.get("bus_number", "").strip()

    if not stop_code or not bus_number:
        return jsonify({"error": "stop_id and bus_number are required"}), 400

    stop_id = STOPCODE_TO_STOPID.get(stop_code)
    if not stop_id:
        return jsonify({"error": f"unknown stop_code: {stop_code}"}), 400

    route_id_needed = SHORT_TO_ROUTEID.get(bus_number)
    if not route_id_needed:
        return jsonify({"error": f"unknown route_short_name: {bus_number}"}), 400

    resp = requests.get(GTFS_TRIP_URL, timeout=10)
    resp.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)

    now = int(time.time())
    best = None

    for ent in feed.entity:
        if not ent.HasField("trip_update"):
            continue

        tu = ent.trip_update
        route_id = tu.trip.route_id if tu.trip.HasField("route_id") else None
        if route_id != route_id_needed:
            continue

        trip_id = tu.trip.trip_id if tu.trip.HasField("trip_id") else None

        for stu in tu.stop_time_update:
            if stu.stop_id != stop_id:
                continue

            eta_unix = None
            if stu.HasField("arrival") and stu.arrival.time:
                eta_unix = int(stu.arrival.time)
            elif stu.HasField("departure") and stu.departure.time:
                eta_unix = int(stu.departure.time)

            if eta_unix is None or eta_unix < now:
                continue

            if best is None or eta_unix < best[0]:
                best = (eta_unix, trip_id, route_id)

    if best is None:
        return jsonify({
            "stop_code": stop_code,
            "stop_id": stop_id,
            "bus_number": bus_number,
            "route_id": route_id_needed,
            "next_arrival": None
        })

    eta_unix, trip_id, route_id = best
    return jsonify({
        "stop_code": stop_code,
        "stop_id": stop_id,
        "bus_number": bus_number,
        "route_id": route_id_needed,
        "next_arrival": {
            "eta_unix": eta_unix,
            "eta_seconds": eta_unix - now,
            "eta_minutes": round((eta_unix - now) / 60.0, 1),
            "trip_id": trip_id,
            "route_id": route_id
        }
    })

@app.route("/vehicles.geojson")
def vehicles_geojson():
    #load the GTFS key info for vehicle positions
    response = requests.get(GTFS_VEHICLE_URL, timeout=10)

    #extract/parse the info from the .pb file
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    #variable to include all features wanted from the API
    features = []

    #looping through every vehicle in circulation currently
    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        #define vehicle variable for each item (highest in dict hierarchy)
        v = entity.vehicle

        if not v.position.HasField("latitude"):
            continue

        #add relevant variables to geojson (in geojson format)
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    v.position.longitude,
                    v.position.latitude
                ]
            },
            "properties": {
                "vehicle_id": v.vehicle.id,
                "vehicle_name": check_id(int(v.vehicle.id)),
                "trip_id": v.trip.trip_id if v.trip.HasField("trip_id") else None,
                "bearing": v.position.bearing if v.position.HasField("bearing") else 0
            }
        })
    #send features to json
    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })


if __name__ == "__main__":
    app.run(debug=True)