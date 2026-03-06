from flask import Flask, jsonify, render_template, request, flash, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Index
from sqlalchemy.exc import OperationalError
from google.transit import gtfs_realtime_pb2
import time
import requests
import pickle
import os
import keys
import re
import pandas
from tools.fetch_types import fetch_types
from tools.fetch_gtfs_static import fetch_gtfs_static

import firebase_admin
from firebase_admin import credentials, firestore, auth

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///static.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Replace this with your agency's GTFS-Realtime vehicle positions URL
GTFS_VEHICLE_URL = f'https://gtfsapi.translink.ca/v3/gtfsposition?apikey={keys.translink_api_key}'
GTFS_TRIP_URL = f"https://gtfsapi.translink.ca/v3/gtfsrealtime?apikey={keys.translink_api_key}"
WEB_API_KEY = keys.firebase_apikey
FIREBASE_LOGIN = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={WEB_API_KEY}"

# get bus type data if not already existing
try:
    with open('types.pkl', 'rb') as f:
        processed = pickle.load(f)
        print("types.pkl loaded")
except:
    print("types.pkl not found, fetching")
    fetch_types()

# get GTFS static data if not already existing
db_path = os.path.join(app.instance_path, "static.db")

if not os.path.isfile(db_path):
    print("Static data not found, fetching")
    fetch_gtfs_static(app.instance_path)
    with app.app_context():
        db.create_all()     # create database if not yet existing
        for f in os.listdir(app.instance_path):
            if f.endswith('.txt'):
                name = f.split('.')[0]
                path = os.path.join(app.instance_path, f)
                df = pandas.read_csv(path)
                df.to_sql(name, db.engine, if_exists="replace", index=False)
                os.remove(path)
                print(f'{f} imported into db')
else:
    print("Static data found")

Models = {}

def create_gtfs_indexes(engine):
    indexes = [
        # index for route lookup from stop code
        Index("idx_stop_times_stop_id", Models["stop_times"].__table__.c.stop_id),
        Index("idx_stop_times_trip_id", Models["stop_times"].__table__.c.trip_id),
        Index("idx_trips_route_id",     Models["trips"].__table__.c.route_id),

        # index for shape lookup from trip id
        Index("idx_trips_shape_id",  Models["trips"].__table__.c.shape_id),
        Index("idx_shapes_shape_id", Models["shapes"].__table__.c.shape_id),
    ]

    for idx in indexes:
        try:
            idx.create(engine)
            print(f"Indexed: {idx.name}")
        except OperationalError:
            print(f"Skipped: {idx.name} (exists)")

with app.app_context():
    db.reflect()
    for table_name, table in db.metadata.tables.items():
        pk_col = Column("rowid", Integer, primary_key=True)
        table.append_column(pk_col)

        model = type(
            table_name.capitalize(),
            (db.Model,),
            {"__table__": table}
        )
        Models[table_name] = model
        print(f"Model reflected: {table_name}")
    create_gtfs_indexes(db.engine)

# with sqlite3.connect(db_path) as con:
#     cur = con.cursor()
#     cur.execute('SELECT trip_id FROM stop_times WHERE stop_id=11088')
#     rows = cur.fetchall()
#     for row in rows:
#         print(row)
    # cur.execute('SELECT shape_pt_lat, shape_pt_lon FROM shapes WHERE shape_id=314725')
    # rows = cur.fetchall()
    # for row in rows:
    #     print(row)

# exit()

# def load_stopcode_to_stopid(stops_path: str) -> dict[str, str]:
#     m = {}
#     with open(stops_path, "r", encoding="utf-8-sig", newline="") as f:
#         for row in csv.DictReader(f):
#             sid = (row.get("stop_id") or "").strip()
#             code = (row.get("stop_code") or "").strip()
#             if sid and code:
#                 m[code] = sid
#     return m

# def load_short_to_routeid(routes_path: str) -> dict[str, str]:
#     m = {}
#     with open(routes_path, "r", encoding="utf-8-sig", newline="") as f:
#         for row in csv.DictReader(f):
#             rid = (row.get("route_id") or "").strip()
#             short = (row.get("route_short_name") or "").strip()
#             if rid and short and short not in m:
#                 m[short] = rid
#     return m

# STOPCODE_TO_STOPID = load_stopcode_to_stopid("./data/stops.txt")
# SHORT_TO_ROUTEID = load_short_to_routeid("./data/routes.txt")

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

def validate_email(email: str):
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return True
    return False

def validate_password(password: str):
    if (len(password) < 6):
        return False
    return True

def validate_jwt():
    try:
        token = session['token']
        decoded_token = auth.verify_id_token(token)
        return decoded_token["uid"]
    except:
        return None

@app.route("/")
#get html page defined as index.html, also include mapbox token
def home():
    return render_template("index.html", key=keys.mapbox_access_token)

# @app.get("/api/next_arrival")
# def next_arrival():
#     stop_code = request.args.get("stop_id", "").strip()
#     bus_number = request.args.get("bus_number", "").strip()

#     if not stop_code or not bus_number:
#         return jsonify({"error": "stop_id and bus_number are required"}), 400

#     stop_id = STOPCODE_TO_STOPID.get(stop_code)
#     if not stop_id:
#         return jsonify({"error": f"unknown stop_code: {stop_code}"}), 400

#     route_id_needed = SHORT_TO_ROUTEID.get(bus_number)
#     if not route_id_needed:
#         return jsonify({"error": f"unknown route_short_name: {bus_number}"}), 400

#     resp = requests.get(GTFS_TRIP_URL, timeout=10)
#     resp.raise_for_status()

#     feed = gtfs_realtime_pb2.FeedMessage()
#     feed.ParseFromString(resp.content)

#     now = int(time.time())
#     best = None

#     for ent in feed.entity:
#         if not ent.HasField("trip_update"):
#             continue

#         tu = ent.trip_update
#         route_id = tu.trip.route_id if tu.trip.HasField("route_id") else None
#         if route_id != route_id_needed:
#             continue

#         trip_id = tu.trip.trip_id if tu.trip.HasField("trip_id") else None

#         for stu in tu.stop_time_update:
#             if stu.stop_id != stop_id:
#                 continue

#             eta_unix = None
#             if stu.HasField("arrival") and stu.arrival.time:
#                 eta_unix = int(stu.arrival.time)
#             elif stu.HasField("departure") and stu.departure.time:
#                 eta_unix = int(stu.departure.time)

#             if eta_unix is None or eta_unix < now:
#                 continue

#             if best is None or eta_unix < best[0]:
#                 best = (eta_unix, trip_id, route_id)

#     if best is None:
#         return jsonify({
#             "stop_code": stop_code,
#             "stop_id": stop_id,
#             "bus_number": bus_number,
#             "route_id": route_id_needed,
#             "next_arrival": None
#         })

#     eta_unix, trip_id, route_id = best
#     return jsonify({
#         "stop_code": stop_code,
#         "stop_id": stop_id,
#         "bus_number": bus_number,
#         "route_id": route_id_needed,
#         "next_arrival": {
#             "eta_unix": eta_unix,
#             "eta_seconds": eta_unix - now,
#             "eta_minutes": round((eta_unix - now) / 60.0, 1),
#             "trip_id": trip_id,
#             "route_id": route_id
#         }
#     })

@app.route('/trips/<trip_id>/shape')
def get_trip_shape(trip_id):
    with app.app_context():
        Shape = Models["shapes"].__table__
        Trip  = Models["trips"].__table__

        stmt = (
            db.select(
                Shape.c.shape_pt_lat,
                Shape.c.shape_pt_lon,
                Shape.c.shape_pt_sequence
            )
            .join(Trip, Shape.c.shape_id == Trip.c.shape_id)
            .where(Trip.c.trip_id == trip_id)
            .order_by(Shape.c.shape_pt_sequence)
        )

        rows = db.session.execute(stmt).all()

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

@app.get("/api/stop_code/<stop_code>")
def stop_code_info(stop_code):
    with app.app_context():
        Stop     = Models["stops"].__table__
        StopTime = Models["stop_times"].__table__
        Trip     = Models["trips"].__table__
        Route    = Models["routes"].__table__

        stmt = (
            db.select(
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

        rows = db.session.execute(stmt).all()
        
        if not rows:
            return jsonify({"error": f"No routes found for stop '{stop_code}'"}), 404

        return jsonify([
            {
                "route_short_name": row.route_short_name,
                "route_long_name" : row.route_long_name,
            }
            for row in rows
        ])
        
@app.route('/api/stop_code/<stop_code>/shapes')
def stop_code_shapes(stop_code):
    with app.app_context():
        Shape    = Models["shapes"].__table__
        Stop     = Models["stops"].__table__
        StopTime = Models["stop_times"].__table__
        Trip     = Models["trips"].__table__

        # Subquery — get distinct shape_ids for the stop_code
        subquery = (
            db.select(Trip.c.shape_id)
            .distinct()
            .select_from(Stop)
            .join(StopTime, Stop.c.stop_id   == StopTime.c.stop_id)
            .join(Trip,     StopTime.c.trip_id == Trip.c.trip_id)
            .where(Stop.c.stop_code == stop_code)
            .subquery()
        )

        # Main query — get all shape points for those shape_ids
        stmt = (
            db.select(
                Shape.c.shape_id,
                Shape.c.shape_pt_lat,
                Shape.c.shape_pt_lon,
                Shape.c.shape_pt_sequence
            )
            .where(Shape.c.shape_id.in_(db.select(subquery)))
            .order_by(Shape.c.shape_id, Shape.c.shape_pt_sequence)
        )

        rows = db.session.execute(stmt).all()

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
'''
@app.route('api/profile', methods=['GET', 'POST'])
def profile(user):
    doc_ref = db.collection('profile').document(user)
    if request.method == 'GET':
        doc = doc_ref.get()
        if not doc.exists:
            return jsonify({"error": "Profile not found"}), 404
    if not request.is_json:
        return jsonify({"error": "Invalid request, Content-Type must be application/json"}), 415
    data = request.get_json()
'''

@app.route('/profile', methods=['GET'])
def profile():
    uid = validate_jwt()
    if uid:
        user_data = db.collection('profile').document(uid).get().to_dict()
        return render_template('profile.html', user_data=user_data)
    return "not logged in", 401

@app.route('/api/profile', methods=['GET'])
def api_profile():
    uid = validate_jwt()
    if uid:
        user_data = db.collection('profile').document(uid).get().to_dict()
        return jsonify(user_data)
    return "not logged in", 401

@app.route('/api/profile/stops', methods=['GET'])
def api_profile_stops_get_all():
    uid = validate_jwt()
    if uid:
        stops = db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops']
        return jsonify(stops)
    return jsonify({"error": "Invalid login"}), 401

@app.route('/api/profile/stops/<fav_idx>', methods=['GET'])
def api_profile_stops_get_one(fav_idx):
    uid = validate_jwt()
    if uid:
        stops = db.collection('profile').document(uid).get().to_dict()['prefs']['favorite_stops']
        try:
            stop_n = stops[int(fav_idx)]
            return jsonify(stop_n)
        except:
            return jsonify({"error": "No stop at index"}), 400
    return jsonify({"error": "Invalid login"}), 401

@app.route('/api/profile/stops', methods=['POST'])
def api_profile_stops_post():
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

@app.route('/api/profile/stops/<fav_idx>', methods=['PUT', 'DELETE'])
def api_profile_stops_put_del(fav_idx):
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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    # assemble signup payload if POST
    if request.method == "POST":
        email = request.form['email']
        # check if email is an email
        if (validate_email(email)):
            password = request.form['password']
            password_confirm = request.form['password_confirm']
            # check if password meets firebase requirements
            if not validate_password(password):
                flash("Password needs to be at least 6 characters long")
                return render_template('signup.html', error=error)
            # check if password is correctly entered twice
            if not password == password_confirm:
                flash("Passwords don't match")
                return render_template('signup.html', error=error)
            user = None;
            # try to create auth account on firebase auth, catch exception for when
            # email exists
            try:
                user = auth.create_user(
                    email=email,
                    password=password
                )
            except:
                flash("Error firebase auth. Does email already exist?", category="Error")
                return render_template('signup.html', error=error)
            # initialize default user data fields
            user_data = {
                "created": time.time(),
                "email": email,
                "prefs": {
                    "favorite_bus_types": [],
                    "favorite_routes": [],
                    "favorite_stops": [],
                    "theme": '',
                    "alerts": ''
                }
            }
            # create new document based on uid
            doc_ref = db.collection('profile').document(user.uid)
            doc_ref.create(user_data)
            flash("Signed up successfully. Log in with your email and password.", category="Success")
            return redirect(url_for('login'))
        else:
            flash("Bad email", category="Error")
    # show signup page otherwise
    return render_template('signup.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    # assemble login payload if POST
    if request.method == "POST":
        email = request.form['email']
        # check if email is email
        if (validate_email(email)):
            password = request.form['password']
            # check if password meets firebase requirements
            if not validate_password(password):
                flash("Password needs to be at least 6 characters long")
                return render_template('login.html', error=error)
            payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
            }
            res = requests.post(FIREBASE_LOGIN, json=payload)
            if res.status_code == 200:
                # retrieve and save token in session cookies
                token = res.json()["idToken"]
                session['token'] = token
                # get logged in user's email
                curr_email = db.collection('profile').document(validate_jwt()).get().to_dict()['email']
                flash(f"Logged in as {curr_email}", category="Success")
                return redirect(url_for('profile'))
            else:
                flash("Bad email or password", category="Error")
        else:
            flash("Bad email or password", category="Error")
    # show login page otherwise
    return render_template('login.html', error=error)

@app.route('/logout', methods=['GET'])
def logout():
    error = None
    session.pop('token', None)
    flash("Logged out", category = "Success")
    return redirect(url_for('login'))

#profile validation helper
def validate_profile_data(username, password, email, favorite_bus_type,
                          favorite_bus_route, favorite_bus_stop_id, theme, alerts, created):
    if not username or not password:
        return "please enter your username and password"
    if not type(username) is str and type(password) is str:
        return "username must be a string."
    return None

#profile data normalization
def normalize_profile_data(username, password, email, favorite_bus_type,
                           favorite_bus_route, favorite_bus_stop_id, theme, alerts, created):
    return {
        #required fields
        "username": username.strip(), #username
        "password": password.strip(), #password
        #non-required fields
        "email": email.strip(),
        "preferences": {
            "favorite_bus_type": favorite_bus_type.strip(), #enter in a specified format
            "favorite_bus_route": favorite_bus_route.strip(), #would be an id of sorts, can visually make it easy to understand
            "favorite_bus_stop_id": favorite_bus_stop_id.strip(), #would be a number
            "theme": theme.strip(), #theme strings tbd
            "alerts": alerts.strip(), #a true/false that would allow alert notifs
        },
        "created": created.strip() #date created if wanted to use
    }

@app.route("/stops.geojson")
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

if __name__ == "__main__":
    app.run(debug=True)