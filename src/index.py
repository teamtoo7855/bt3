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

GTFS_VEHICLE_URL = f'https://gtfsapi.translink.ca/v3/gtfsposition?apikey={keys.translink_api_key}'
GTFS_TRIP_URL = f"https://gtfsapi.translink.ca/v3/gtfsrealtime?apikey={keys.translink_api_key}"
WEB_API_KEY = keys.firebase_apikey
FIREBASE_LOGIN = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={WEB_API_KEY}"

# -----------------------------
# Startup: types.pkl + GTFS static
# -----------------------------
try:
    with open('types.pkl', 'rb') as f:
        processed = pickle.load(f)
        print("types.pkl loaded")
except:
    print("types.pkl not found, fetching")
    fetch_types()

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

def check_id(bus_id: int):
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

def validate_email(email: str):
    return True if re.match(r"[^@]+@[^@]+\.[^@]+", email or "") else False

def validate_password(password: str):
    return False if not password or len(password) < 6 else True

def validate_jwt():
    try:
        token = session.get('token')
        if not token:
            return None
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

# -----------------------------
# HOME (Map) - protected by login OR demo
# -----------------------------
@app.route("/")
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

# -----------------------------
# EXISTING API ENDPOINTS (keep yours)
# -----------------------------
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
    response = requests.get(GTFS_VEHICLE_URL, timeout=10)
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    features = []
    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        v = entity.vehicle
        if not v.position.HasField("latitude"):
            continue

        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [v.position.longitude, v.position.latitude]},
            "properties": {
                "vehicle_id": v.vehicle.id,
                "vehicle_name": check_id(int(v.vehicle.id)),
                "trip_id": v.trip.trip_id if v.trip.HasField("trip_id") else None,
                "route_id": v.trip.route_id if v.trip.HasField("route_id") else None,
                "direction_id": v.trip.direction_id if v.trip.HasField("direction_id") else None,
                "bearing": v.position.bearing if v.position.HasField("bearing") else 0
            }
        })

    return jsonify({"type": "FeatureCollection", "features": features})

@app.route("/stops.geojson")
def stops_geojson():
    with open("./data/stops.txt", "r", encoding="utf-8-sig", newline="") as f:
        features = []
        for row in csv.DictReader(f):
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [
                    (row.get("stop_lon") or "").strip(),
                    (row.get("stop_lat") or "").strip(),
                ]},
                "properties": {
                    "stop_id": (row.get("stop_id") or "").strip(),
                    "stop_code": (row.get("stop_code") or "").strip(),
                    "stop_name": (row.get("stop_name") or "").strip(),
                }
            })
        return jsonify({"type": "FeatureCollection", "features": features})

if __name__ == "__main__":
    app.run(debug=True)