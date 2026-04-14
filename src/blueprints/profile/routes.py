
#from app import app
from flask import render_template, request, redirect, url_for, flash
from utils.validation import normalize_profile_data, validate_profile_data
from utils.auth import get_current_user
from utils.profile import get_profile_data, set_profile
from utils.auth import get_current_user
from . import profile_bp
from decorators.auth import require_jwt
from firebase import db
import time

# -----------------------------
# PROFILE (GET + POST edit)
# -----------------------------
@profile_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    #uid = validate_jwt()
    #if not uid:
     #   return redirect(url_for("login"))
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('auth.login'))
    if request.method == "GET":
        profile_data = get_profile_data(current_user) or {}
        return render_template('profile.html', profile_data=profile_data, error=None)
    '''
    doc_ref = db.collection('profile').document(uid)
    doc = doc_ref.get()
    user_data = doc.to_dict() if doc.exists else None
'''

    profile_data = get_profile_data(current_user)
    prefs = (profile_data or {}).get("prefs", {})
    created = profile_data.get("created", time.time())
    email = (request.form.get("email") or "").strip()
    # Update preferences from form
    favorite_route = (request.form.get("favorite_route") or "").strip()
    favorite_type = (request.form.get("favorite_type") or "").strip()
    theme = (request.form.get("theme") or "").strip()
    alerts = (request.form.get("alerts") or "").strip()
    add_stop = (request.form.get("add_stop") or "").strip()



    favorite_routes = prefs.get("favorite_routes", []) or []
    favorite_types = prefs.get("favorite_bus_types", []) or []
    favorite_stops = prefs.get("favorite_stops", []) or []

    # single "main" values as index 0
    '''
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
'''
    if favorite_route:
        if favorite_routes:
            favorite_routes[0] = favorite_route
        else:
            favorite_routes = [favorite_route]

    if favorite_type:
        if favorite_types:
            favorite_types[0] = favorite_type
        else:
            favorite_types = [favorite_type]

        # add stop (append if new)
        '''
    if add_stop:
        if add_stop not in favorite_stops:
            favorite_stops.append(add_stop)
            '''
    if add_stop and add_stop not in favorite_stops:
        favorite_stops.append(add_stop)
    # theme (string)
    prefs["favorite_routes"] = favorite_routes
    prefs["favorite_bus_types"] = favorite_types
    prefs["favorite_stops"] = favorite_stops
    prefs["theme"] = theme

    # alerts normalize
    if alerts == "on":
        prefs["alerts"] = True
    elif alerts == "off":
        prefs["alerts"] = False
    else:
        prefs["alerts"] = prefs.get("alerts", "")

    profile_data["email"] = email
    profile_data["prefs"] = prefs
    # profile_data["created"] = created


    error = validate_profile_data(email, favorite_types,
                      favorite_routes, favorite_stops, theme, alerts)
    if error:
        flash(error, category="Error")
        return render_template("profile.html", profile_data=profile_data, error=error)


    #normalized = normalize_profile_data(created, email, favorite_types, favorite_routes, favorite_stops, theme, alerts)
    set_profile(current_user, profile_data, merge=False)
    return redirect(url_for("dashboard.home"))


        #doc_ref.update({"prefs": prefs})
        #flash("Profile updated.", category="Success")

        # reload
        #user_data = doc_ref.get().to_dict()

