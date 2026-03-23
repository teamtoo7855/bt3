from flask import Flask, jsonify, render_template, request, flash, session, redirect, url_for
from google.transit import gtfs_realtime_pb2
import time
import requests
import pickle
import csv
import os
import src.keys as keys
import re

from blueprints.data_geojson import data_geojson_bp
from tools.fetch_types import fetch_types
from tools.fetch_gtfs_static import fetch_gtfs_static

import firebase_admin
from firebase_admin import credentials, firestore, auth

'''
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
'''


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
