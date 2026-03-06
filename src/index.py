from flask import Flask, jsonify, render_template, request, flash, session, redirect, url_for
from google.transit import gtfs_realtime_pb2
import time
import requests
import pickle
import csv
import os
import keys
import re
from tools.fetch_types import fetch_types
from tools.fetch_gtfs_static import fetch_gtfs_static

import firebase_admin
from firebase_admin import credentials, firestore, auth

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

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

def is_demo():
    return True if session.get("demo") else False

def require_login_or_demo():
    """
    If user is logged in -> return uid
    If demo mode -> return "demo"
    Else -> None
    """
    uid = validate_jwt()
    if uid:
        return uid
    if is_demo():
        return "demo"
    return None

@app.route("/")
#get html page defined as index.html, also include mapbox token
def home():
    if not require_login_or_demo():
        return redirect(url_for("login"))
    return render_template("index.html", key=keys.mapbox_access_token)

# -----------------------------
# DEMO MODE
# -----------------------------
@app.post("/demo")
def demo():
    # demo means: user can access map, but no profile writes
    session.pop("token", None)
    session["demo"] = True
    flash("Demo mode enabled (guest).", category="Success")
    return redirect(url_for("home"))

# -----------------------------
# AUTH: SIGNUP
# -----------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == "POST":
        email = (request.form.get('email') or "").strip()
        if not validate_email(email):
            flash("Please enter a valid email.", category="Error")
            return render_template('signup.html', error=error)

        password = request.form.get('password') or ""
        password_confirm = request.form.get('password_confirm') or ""

        if not validate_password(password):
            flash("Password needs to be at least 6 characters long.", category="Error")
            return render_template('signup.html', error=error)

        if password != password_confirm:
            flash("Passwords don't match.", category="Error")
            return render_template('signup.html', error=error)

        # NEW: preferences (optional)
        favorite_route = (request.form.get("favorite_route") or "").strip()
        favorite_type = (request.form.get("favorite_type") or "").strip()
        theme = (request.form.get("theme") or "").strip()
        alerts = (request.form.get("alerts") or "").strip()  # "on"/"off"/""
        favorite_stop = (request.form.get("favorite_stop") or "").strip()

        # create auth account
        try:
            user = auth.create_user(email=email, password=password)
        except:
            flash("Error creating account. Email may already exist.", category="Error")
            return render_template('signup.html', error=error)

        # normalize alert value
        alerts_value = ""
        if alerts == "on":
            alerts_value = True
        elif alerts == "off":
            alerts_value = False

        user_data = {
            "created": time.time(),
            "email": email,
            "prefs": {
                "favorite_bus_types": [favorite_type] if favorite_type else [],
                "favorite_routes": [favorite_route] if favorite_route else [],
                "favorite_stops": [favorite_stop] if favorite_stop else [],
                "theme": theme,
                "alerts": alerts_value
            }
        }

        # store profile under uid
        doc_ref = db.collection('profile').document(user.uid)
        doc_ref.set(user_data)

        flash("Signed up successfully. Please log in.", category="Success")
        return redirect(url_for('login'))

    return render_template('signup.html', error=error)

# -----------------------------
# AUTH: LOGIN
# -----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == "POST":
        email = (request.form.get('email') or "").strip()
        password = request.form.get('password') or ""

        if not validate_email(email) or not validate_password(password):
            flash("Bad email or password.", category="Error")
            return render_template('login.html', error=error)

        payload = {"email": email, "password": password, "returnSecureToken": True}
        res = requests.post(FIREBASE_LOGIN, json=payload)

        if res.status_code == 200:
            session["demo"] = False  # exit demo if previously on
            session['token'] = res.json()["idToken"]
            uid = validate_jwt()
            if uid:
                curr_email = db.collection('profile').document(uid).get().to_dict().get('email', email)
                flash(f"Logged in as {curr_email}", category="Success")
            return redirect(url_for('profile'))
        else:
            flash("Bad email or password.", category="Error")

    return render_template('login.html', error=error)

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('token', None)
    session.pop('demo', None)
    flash("Logged out", category="Success")
    return redirect(url_for('login'))

# -----------------------------
# PROFILE (GET + POST edit)
# -----------------------------
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    uid = validate_jwt()
    if not uid:
        return redirect(url_for("login"))

    doc_ref = db.collection('profile').document(uid)
    doc = doc_ref.get()
    user_data = doc.to_dict() if doc.exists else None

    if request.method == "POST":
        # Update preferences from form
        favorite_route = (request.form.get("favorite_route") or "").strip()
        favorite_type = (request.form.get("favorite_type") or "").strip()
        theme = (request.form.get("theme") or "").strip()
        alerts = (request.form.get("alerts") or "").strip()
        add_stop = (request.form.get("add_stop") or "").strip()

        prefs = (user_data or {}).get("prefs", {})
        favorite_routes = prefs.get("favorite_routes", []) or []
        favorite_types = prefs.get("favorite_bus_types", []) or []
        favorite_stops = prefs.get("favorite_stops", []) or []

        # single "main" values as index 0
        if favorite_route:
            if len(favorite_routes) == 0:
                favorite_routes = [favorite_route]
            else:
                favorite_routes[0] = favorite_route

        if favorite_type:
            if len(favorite_types) == 0:
                favorite_types = [favorite_type]
            else:
                favorite_types[0] = favorite_type

        # theme (string)
        prefs["theme"] = theme

        # alerts normalize
        if alerts == "on":
            prefs["alerts"] = True
        elif alerts == "off":
            prefs["alerts"] = False
        else:
            prefs["alerts"] = prefs.get("alerts", "")

        # add stop (append if new)
        if add_stop:
            if add_stop not in favorite_stops:
                favorite_stops.append(add_stop)

        prefs["favorite_routes"] = favorite_routes
        prefs["favorite_bus_types"] = favorite_types
        prefs["favorite_stops"] = favorite_stops

        doc_ref.update({"prefs": prefs})
        flash("Profile updated.", category="Success")

        # reload
        user_data = doc_ref.get().to_dict()

    return render_template('profile.html', user_data=user_data)

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

@app.get("/api/shape")
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

# @app.route('/profile', methods=['GET'])
# def profile():
#     uid = validate_jwt()
#     if uid:
#         user_data = db.collection('profile').document(uid).get().to_dict()
#         return render_template('profile.html', user_data=user_data)
#     return "not logged in", 401

# @app.route('/api/profile', methods=['GET'])
# def api_profile():
#     uid = validate_jwt()
#     if uid:
#         user_data = db.collection('profile').document(uid).get().to_dict()
#         return jsonify(user_data)
#     return "not logged in", 401

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

# @app.route('/signup', methods=['GET', 'POST'])
# def signup():
#     error = None
#     # assemble signup payload if POST
#     if request.method == "POST":
#         email = request.form['email']
#         # check if email is an email
#         if (validate_email(email)):
#             password = request.form['password']
#             password_confirm = request.form['password_confirm']
#             # check if password meets firebase requirements
#             if not validate_password(password):
#                 flash("Password needs to be at least 6 characters long")
#                 return render_template('signup.html', error=error)
#             # check if password is correctly entered twice
#             if not password == password_confirm:
#                 flash("Passwords don't match")
#                 return render_template('signup.html', error=error)
#             user = None;
#             # try to create auth account on firebase auth, catch exception for when
#             # email exists
#             try:
#                 user = auth.create_user(
#                     email=email,
#                     password=password
#                 )
#             except:
#                 flash("Error firebase auth. Does email already exist?", category="Error")
#                 return render_template('signup.html', error=error)
#             # initialize default user data fields
#             user_data = {
#                 "created": time.time(),
#                 "email": email,
#                 "prefs": {
#                     "favorite_bus_types": [],
#                     "favorite_routes": [],
#                     "favorite_stops": [],
#                     "theme": '',
#                     "alerts": ''
#                 }
#             }
#             # create new document based on uid
#             doc_ref = db.collection('profile').document(user.uid)
#             doc_ref.create(user_data)
#             flash("Signed up successfully. Log in with your email and password.", category="Success")
#             return redirect(url_for('login'))
#         else:
#             flash("Bad email", category="Error")
#     # show signup page otherwise
#     return render_template('signup.html', error=error)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     error = None
#     # assemble login payload if POST
#     if request.method == "POST":
#         email = request.form['email']
#         # check if email is email
#         if (validate_email(email)):
#             password = request.form['password']
#             # check if password meets firebase requirements
#             if not validate_password(password):
#                 flash("Password needs to be at least 6 characters long")
#                 return render_template('login.html', error=error)
#             payload = {
#             "email": email,
#             "password": password,
#             "returnSecureToken": True
#             }
#             res = requests.post(FIREBASE_LOGIN, json=payload)
#             if res.status_code == 200:
#                 # retrieve and save token in session cookies
#                 token = res.json()["idToken"]
#                 session['token'] = token
#                 # get logged in user's email
#                 curr_email = db.collection('profile').document(validate_jwt()).get().to_dict()['email']
#                 flash(f"Logged in as {curr_email}", category="Success")
#                 return redirect(url_for('profile'))
#             else:
#                 flash("Bad email or password", category="Error")
#         else:
#             flash("Bad email or password", category="Error")
#     # show login page otherwise
#     return render_template('login.html', error=error)

# @app.route('/logout', methods=['GET'])
# def logout():
#     error = None
#     session.pop('token', None)
#     flash("Logged out", category = "Success")
#     return redirect(url_for('login'))

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



if __name__ == "__main__":
    app.run(debug=True)