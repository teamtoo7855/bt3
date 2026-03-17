
#from app import app
from config import Config
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from . import dashboard_bp



@dashboard_bp.route("/")
#get html page defined as index.html, also include mapbox token
def home():
    if not require_login_or_demo():
        return redirect(url_for("login"))
    return render_template("index.html", key=Config.MAPBOX_ACCESS_TOKEN)