from utils.auth import get_current_user
from utils.profile import get_profile_data, set_profile
from utils.validation import normalize_profile_data, validate_profile_data
#from app import app
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from . import profile_bp




# -----------------------------
# PROFILE (GET + POST edit)
# -----------------------------
@profile_bp.route('/profile', methods=['GET', 'POST'])
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