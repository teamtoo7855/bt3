from flask import Flask, jsonify, render_template
import requests
from google.transit import gtfs_realtime_pb2
import keys
app = Flask(__name__)

# Replace this with your agency's GTFS-Realtime vehicle positions URL
GTFS_VEHICLE_URL = keys.position


@app.route("/")
#get html page defined as index.html, also include mapbox token
def home():
    return render_template("index.html", key=keys.mapbox_access_token)

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
