from . import api_bp
from flask import Flask, jsonify, render_template, request, flash, session, redirect, url_for
from google.transit import gtfs_realtime_pb2
import requests
import csv
import time
from firebase_admin import credentials, firestore, auth
from firebase import db
import re
import json
from config import Config
from utils.data import STOPCODE_TO_STOPID, SHORT_TO_ROUTEID
from decorators.auth import require_jwt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import current_app as app
limiter = Limiter(get_remote_address, app=app)



GTFS_TRIP_URL = Config.GTFS_TRIP_URL

@api_bp.get("/next_arrival")
@limiter.limit("10 per minute")
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