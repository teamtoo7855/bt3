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
    with app.app_context():
        Stop = Models["stops"].__table__

        stmt = db.select(
            Stop.c.stop_id,
            Stop.c.stop_code,
            Stop.c.stop_name,
            Stop.c.stop_lat,
            Stop.c.stop_lon
        )

        stops = db.session.execute(stmt).all()

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [stop.stop_lon, stop.stop_lat]
            },
            "properties": {
                "stop_id":   stop.stop_id,
                "stop_code": stop.stop_code,
                "stop_name": stop.stop_name
            }
        }
        for stop in stops
    ]

    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })