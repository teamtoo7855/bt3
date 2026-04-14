from flask import jsonify
from google.transit import gtfs_realtime_pb2
import requests
from config import Config
from utils.data import check_id
from flask import current_app as app
from models import Models
from models import db
from . import data_geojson_bp

@data_geojson_bp.route("/vehicles.geojson")
def vehicles_geojson():
    #load the GTFS key info for vehicle positions
    response = requests.get(Config.GTFS_VEHICLE_URL, timeout=10)

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
                "route_id": v.trip.route_id if v.trip.HasField("route_id") else None,
                "direction_id": v.trip.direction_id if v.trip.HasField("direction_id") else None,
                "bearing": v.position.bearing if v.position.HasField("bearing") else 0
            }
        })
    #send features to json
    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })




@data_geojson_bp.route("/stops.geojson")
def stops_geojson():
    with open("./data/stops.txt", "r", encoding="utf-8-sig", newline="") as f:
        features = []
        for row in csv.DictReader(f):
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        (row.get("stop_lon") or "").strip(),
                        (row.get("stop_lat") or "").strip(),
                    ]
                },
                "properties": {
                    "stop_id": (row.get("stop_id") or "").strip(),
                    "stop_code": (row.get("stop_code") or "").strip(),
                    "stop_name": (row.get("stop_name") or "").strip(),
                }
            })
        #send features to json
        return jsonify({
            "type": "FeatureCollection",
            "features": features
        })