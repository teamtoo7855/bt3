
#from app import app
from config import Config
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response, flash
from utils.auth import get_current_user
from utils.profile import get_profile_data

from decorators.auth import require_jwt
from . import dashboard_bp


def is_demo():
    return True if session.get("demo") else False

@require_jwt
def require_login_or_demo(uid: str):
    """
    If user is logged in -> return uid
    If demo mode -> return "demo"
    Else -> None
    """
    return uid
    if is_demo():
        return "demo"
    return None
# -----------------------------
# DEMO MODE
# -----------------------------
@dashboard_bp.post("/demo")
def demo():
    # demo means: user can access map, but no profile writes
    session.pop("token", None)
    session["demo"] = True
    flash("Demo mode enabled (guest).", category="Success")
    return redirect(url_for("dashboard.home"))

@dashboard_bp.route("/")
#get html page defined as index.html, also include mapbox token
def home():
    current_user = get_current_user()
    if current_user:
        profile_data = get_profile_data(current_user)
        return render_template("index.html", key=Config.MAPBOX_ACCESS_TOKEN,
                               profile_data=profile_data,
                               jwt_token=session.get("jwt_token"),
                               )
    return redirect(url_for("auth.login"))
    #return render_template("index.html", key=Config.MAPBOX_ACCESS_TOKEN)