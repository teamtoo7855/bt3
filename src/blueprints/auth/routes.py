from firebase import db
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response, url_for, flash, make_response
from firebase_admin import credentials, firestore, auth
from config import Config
from . import auth_bp
import requests
import time
from config import Config
from utils.validation import validate_email, validate_password, validate_favorite_stops
from decorators.auth import require_jwt
FIREBASE_LOGIN = Config.FIREBASE_LOGIN
# -----------------------------
# AUTH: SIGNUP
# -----------------------------
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "GET":
        return render_template('signup.html')

    #error = None
    #if request.method == "POST":
    email = (request.form.get('email') or "").strip()
    if not validate_email(email):
        flash("Please enter a valid email.", category="Error")
        return render_template('signup.html', error=error)

    password = request.form.get('password') or ""
    password_confirm = request.form.get('password_confirm') or ""

    if not validate_password(password):
        flash("Password needs to be at least 8 characters long.", category="Error")
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
    if not validate_favorite_stops(favorite_stop):
        flash(f"The stop {favorite_stop} does not exist. Please enter a valid stop number", category="Error")
        return render_template('signup.html', error=error)
    '''
    for multi down the line
    favorite_stops = [stop.strip() for stop in favorite_stop.split(",") if stop.strip()]
    if not validate_favorite_stops(favorite_stops):
        flash(f"the following stops are invalid {validate_favorite_stops(favorite_stops)}", category="Error")
        return render_template('signup.html', error=error)
        '''
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
            "favorite_stops": [favorite_stop] if favorite_route else [],
            "theme": theme,
            "alerts": alerts_value
        }
    }
    # create auth account
    try:
        user = auth.create_user(email=email, password=password)
        db.collection("profile").document(user.uid).set(user_data)
        #doc_ref = db.collection('profile').document(user.uid)
        #doc_ref.set(user_data)
        flash("Signed up successfully. Please log in.", category="Success")
        return redirect(url_for('auth.login'))
    except:
        flash("Error creating account. Email may already exist.", category="Error")
        return render_template('signup.html', error=error)



    # store profile under uid




    return render_template('signup.html', error=error)

# -----------------------------
# AUTH: LOGIN
# -----------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
#@require_jwt
def login():
    if request.method == 'GET':
        return render_template('login.html')
    #error = None

    email = (request.form.get('email') or "").strip()
    password = request.form.get('password') or ""

    if not validate_email(email) or not validate_password(password):
        flash("Bad email or password.", category="Error")
        return render_template('login.html', error=error)
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={Config.FIREBASE_API_KEY}"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        res = requests.post(FIREBASE_LOGIN, json=payload)
        if res.status_code == 200:
            token_data = res.json()
            uid = token_data.get("localId")
            session["logged_in"] = True
            session["uid"] = uid
            session["email"] = email
            session["jwt_token"] = token_data.get("idToken")
            return redirect(url_for('dashboard.home'))
        error_data = res.json().get("error", {})
        error_msg = error_data.get("message", "Invalid credentials")
        if "INVALID_LOGIN_CREDENTIALS" in error_msg:
            error_msg = "invalid email or pass"
        return render_template('login.html', error=error_msg)
    except requests.RequestException:
        return render_template("login.html", error="Authentication service unavailable")
    '''
    if res.status_code == 200:
        session["demo"] = False  # exit demo if previously on
        session['token'] = res.json()["idToken"]
        curr_email = db.collection('profile').document(uid).get().to_dict().get('email', email)
        flash(f"Logged in as {curr_email}", category="Success")
        return redirect(url_for('auth.profile'))
    else:
        flash("Bad email or password.", category="Error")
        '''

    return render_template('login.html', error=error)

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    #session.pop('token', None)
    #session.pop('demo', None)
    response = make_response(redirect(url_for('auth.login')))
    response.delete_cookie('session')
    
    flash("Logged out", category="success")
    return response


@auth_bp.route("/error")
def error():
    status_code = request.args.get("status_code", 500)
    error_message = request.args.get("error_message", "Please try again.")

    return render_template(
        "error.html",
        status_code=status_code,
        error_message=error_message
    ), int(status_code)
