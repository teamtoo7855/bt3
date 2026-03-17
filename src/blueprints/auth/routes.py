from firebase import db
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response, url_for, flash
from firebase_admin import credentials, firestore, auth
from config import Config
from . import auth_bp
import requests
import time
from config import Config
from utils.validation import validate_email, validate_password
from decorators.auth import require_jwt
FIREBASE_LOGIN = Config.FIREBASE_LOGIN
# -----------------------------
# AUTH: SIGNUP
# -----------------------------
@auth_bp.route('/signup', methods=['GET', 'POST'])
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
@auth_bp.route('/login', methods=['GET', 'POST'])
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

@auth_bp.route('/logout', methods=['GET'])
def logout():
    session.pop('token', None)
    session.pop('demo', None)
    flash("Logged out", category="Success")
    return redirect(url_for('login'))

