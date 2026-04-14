from . import api_bp
from flask import jsonify, request
from google.transit import gtfs_realtime_pb2
from flask import current_app as app
import requests
import csv
import time
from firebase import db
from utils.profile import get_profile_data
from config import Config
from decorators.auth import require_jwt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
limiter = Limiter(get_remote_address, app=app)
from models import Models, get_stop_id_from_stop_code, get_route_id_from_short_name
from models import db as dba

#profile api
@api_bp.get("/profile")
@require_jwt
def api_get_profile(uid : str):
    profile_data = get_profile_data(uid)
    return jsonify ({"uid": uid, "profile_data": profile_data})

@api_bp.get("/next_arrival")
@limiter.limit("10 per minute")
def next_arrival():
    stop_code = request.args.get("stop_id", "").strip()
    bus_number = request.args.get("bus_number", "").strip()

    if not stop_code or not bus_number:
        return jsonify({"error": "stop_id and bus_number are required"}), 400

    stop_id = get_stop_id_from_stop_code(stop_code)
    if not stop_id:
        return jsonify({"error": f"unknown stop_code: {stop_code}"}), 400

    route_id_needed = get_route_id_from_short_name(bus_number)
    if not route_id_needed:
        return jsonify({"error": f"unknown route_short_name: {bus_number}"}), 400

    resp = requests.get(Config.GTFS_TRIP_URL, timeout=10)
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

# deprecate
@api_bp.get("/shape")
@limiter.limit("10 per minute")
def get_shape():
    stop_id = request.args.get("stop_id", "").strip()
    trip_id = request.args.get("trip_id", "").strip()
    direction = request.args.get("direction", "").strip()
    if stop_id:
        with open("./data/stop_times.txt", "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if str((row.get("stop_id")).strip()) == str(stop_id):
                    trip_id = (row.get("trip_id")).strip()
                    break

    with open("./data/trips.txt", "r", encoding="utf-8-sig", newline="") as f:
        shape_id = None;
        for row in csv.DictReader(f):
            if str((row.get("trip_id")).strip()) == str(trip_id):
                shape_id = (row.get("shape_id")).strip()
                with open("./data/shapes.txt", "r", encoding="utf-8-sig", newline="") as g:
                    shape_pts = []
                    for row in csv.DictReader(g):
                        if (row.get("shape_id") or "").strip() == shape_id:
                            seq = int((row.get("shape_pt_sequence") or "").strip())
                            lon = float((row.get("shape_pt_lon") or "").strip())
                            lat = float((row.get("shape_pt_lat") or "").strip())
                            shape_pts.append([seq, lon, lat])
                    shape_pts.sort()
                    for i in shape_pts:
                        i.pop(0)
                    # send features to json
                    return jsonify(
                        {
                            "type": "FeatureCollection",
                            "features": [{
                                "type": "Feature",
                                "geometry": {
                                    "type": "LineString",
                                    "coordinates": shape_pts,
                                },
                                "properties": {},
                            }],
                        }
                    )

@api_bp.get('/stop_code/<stop_code>/shapes')
def stop_code_shapes(stop_code):
    with app.app_context():
        Shape    = Models["shapes"].__table__
        Stop     = Models["stops"].__table__
        StopTime = Models["stop_times"].__table__
        Trip     = Models["trips"].__table__

        # Subquery — get distinct shape_ids for the stop_code
        subquery = (
            dba.select(Trip.c.shape_id)
            .distinct()
            .select_from(Stop)
            .join(StopTime, Stop.c.stop_id   == StopTime.c.stop_id)
            .join(Trip,     StopTime.c.trip_id == Trip.c.trip_id)
            .where(Stop.c.stop_code == stop_code)
            .subquery()
        )

        # Main query — get all shape points for those shape_ids
        stmt = (
            dba.select(
                Shape.c.shape_id,
                Shape.c.shape_pt_lat,
                Shape.c.shape_pt_lon,
                Shape.c.shape_pt_sequence
            )
            .where(Shape.c.shape_id.in_(dba.select(subquery)))
            .order_by(Shape.c.shape_id, Shape.c.shape_pt_sequence)
        )

        rows = dba.session.execute(stmt).all()

    # Group shape points by shape_id
    shapes = {}
    for row in rows:
        if row.shape_id not in shapes:
            shapes[row.shape_id] = []
        shapes[row.shape_id].append([row.shape_pt_lon, row.shape_pt_lat])

    # Build a GeoJSON feature per shape
    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "properties": {
                "shape_id": shape_id
            }
        }
        for shape_id, coordinates in shapes.items()
    ]

    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })

@api_bp.get('/trips/<trip_id>/shape')
def get_trip_shape(trip_id):
    with app.app_context():
        Shape = Models["shapes"].__table__
        Trip  = Models["trips"].__table__

        stmt = (
            dba.select(
                Shape.c.shape_pt_lat,
                Shape.c.shape_pt_lon,
                Shape.c.shape_pt_sequence
            )
            .join(Trip, Shape.c.shape_id == Trip.c.shape_id)
            .where(Trip.c.trip_id == trip_id)
            .order_by(Shape.c.shape_pt_sequence)
        )

        rows = dba.session.execute(stmt).all()

    coordinates = [[row.shape_pt_lon, row.shape_pt_lat] for row in rows]

    return jsonify({
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coordinates
        },
        "properties": {
            "trip_id": trip_id
        }
    })

@api_bp.get("/stop_code/<stop_code>")
def stop_code_info(stop_code):
    with app.app_context():
        Stop     = Models["stops"].__table__
        StopTime = Models["stop_times"].__table__
        Trip     = Models["trips"].__table__
        Route    = Models["routes"].__table__

        stmt = (
            dba.select(
                Route.c.route_short_name,
                Route.c.route_long_name
            )
            .distinct()
            .select_from(Stop)
            .join(StopTime, Stop.c.stop_id     == StopTime.c.stop_id)
            .join(Trip,     StopTime.c.trip_id == Trip.c.trip_id)
            .join(Route,    Trip.c.route_id    == Route.c.route_id)
            .where(Stop.c.stop_code == stop_code)
        )

        rows = dba.session.execute(stmt).all()
        
        if not rows:
            return jsonify({"error": f"No routes found for stop '{stop_code}'"}), 404

        return jsonify([
            {
                "route_short_name": row.route_short_name,
                "route_long_name" : row.route_long_name,
            }
            for row in rows
        ])

@api_bp.route('/profile/stops', methods=['GET'])
@require_jwt
def api_profile_stops_get_all(uid: str):
    stops = db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops']
    return jsonify(stops)
    #uid = validate_jwt()
    #if uid:
     #   stops = db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops']
      #  return jsonify(stops)
    #return jsonify({"error": "Invalid login"}), 401

@api_bp.route('/profile/stops/<fav_idx>', methods=['GET'])
@require_jwt
def api_profile_stops_get_one(fav_idx, uid: str):
    stops = db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops']
    try:
        stop_n = stops[int(fav_idx)]
        return jsonify(stop_n)
    except:
        return jsonify({"error": "No stop at index"}), 400
    #uid = validate_jwt()
    #if uid:
     #   stops = db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops']
      #  try:
       #     stop_n = stops[int(fav_idx)]
        #    return jsonify(stop_n)
        #except:
         #   return jsonify({"error": "No stop at index"}), 400
    return jsonify({"error": "Invalid login"}), 401

@api_bp.route('/profile/stops', methods=['POST'])
@require_jwt
def api_profile_stops_post(uid: str):
    stop_number = request.form['stop_number']
    if not stop_number:
        return jsonify({"error": "Invalid stop number"}), 400
    doc_ref = db.collection('profile').document(uid)
    doc = doc_ref.get()
    data = doc.to_dict()
    stops = data["prefs"]["favorite_stops"]
    if not len(stops):
        stops.append(stop_number)
    else:
        if stop_number in stops:
            return jsonify(db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops'])
        if not stops[0]:
            stops[0] = stop_number
        else:
            stops.append(stop_number)
    doc_ref.update({"prefs": {"favorite_stops": stops}})
    return jsonify(db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops'])

    '''
    uid = validate_jwt()
    if uid:
        stop_number = request.form['stop_number']
        if not stop_number:
            return jsonify({"error": "Invalid stop number"}), 400
        doc_ref = db.collection('profile').document(uid)
        doc = doc_ref.get()
        data = doc.to_dict()
        stops = data["prefs"]["favorite_stops"]
        if not len(stops):
            stops.append(stop_number)
        else:
            if stop_number in stops:
                return jsonify(db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops'])
            if not stops[0]:
                stops[0] = stop_number
            else:
                stops.append(stop_number)
        doc_ref.update({"prefs": {"favorite_stops": stops}})
        return jsonify(db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops'])
    return jsonify({"error": "Invalid login"}), 401
    '''

@api_bp.route('/api/profile/stops/<fav_idx>', methods=['PUT', 'DELETE'])
@require_jwt
def api_profile_stops_put_del(fav_idx, uid : str):
    doc_ref = db.collection('profile').document(uid)
    doc = doc_ref.get()
    data = doc.to_dict()
    stops = data["prefs"]["favorite_stops"]
    if request.method == 'PUT':
        try:
            stop_number = request.form['stop_number']
            stops[int(fav_idx)] = stop_number;
            doc_ref.update({"prefs": {"favorite_stops": stops}})
            return jsonify(db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops'])
        except:
            return jsonify({"error": "No stop at index"}), 400
    if request.method == 'DELETE':
        try:
            stops.pop(int(fav_idx))
            doc_ref.update({"prefs": {"favorite_stops": stops}})
            return jsonify(db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops'])
        except:
            return jsonify({"error": "No stop at index"}), 400

    '''
    uid = validate_jwt()
    if uid:
        doc_ref = db.collection('profile').document(uid)
        doc = doc_ref.get()
        data = doc.to_dict()
        stops = data["prefs"]["favorite_stops"]
        if request.method == 'PUT':
            try:
                stop_number = request.form['stop_number']
                stops[int(fav_idx)] = stop_number;
                doc_ref.update({"prefs": {"favorite_stops": stops}})
                return jsonify(db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops'])
            except:
                return jsonify({"error": "No stop at index"}), 400
        if request.method == 'DELETE':
            try:
                stops.pop(int(fav_idx))
                doc_ref.update({"prefs": {"favorite_stops": stops}})
                return jsonify(db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops'])
            except:
                return jsonify({"error": "No stop at index"}), 400
    return jsonify({"error": "Invalid login"}), 401
    '''