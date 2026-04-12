from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
import re
import csv

def validate_email(email: str):
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return True
    return False

def validate_password(password: str):
    if (len(password) < 8):
        return False
    return True
#idk if this is important
'''
def validate_jwt():
    try:
        token = session['token']
        decoded_token = auth.verify_id_token(token)
        return decoded_token["uid"]
    except:
        return None
    '''
def validate_profile_data(username, password, email, favorite_bus_type,
                          favorite_bus_route, favorite_bus_stop_id, theme, alerts, created):
    if not username or not password:
        return "please enter your username and password"
    if not type(username) is str and type(password) is str:
        return "username must be a string."
    return None

def validate_favorite_stops(favorite_stop_id):
    with open("./data/stops.txt", "r", encoding="utf-8-sig", newline="") as f:
        stops = []

        for row in csv.DictReader(f):
            stops.append(row.get("stop_code"))
        print (favorite_stop_id)
        print (stops)
        if favorite_stop_id not in stops:
            return False
        return True
    ''' 
    invalid_stops = []
    for multi down the line
    for stop in favorite_stop_id:
        if stop not in stops:
            invalid_stops.append(stop)
    if len(invalid_stops) > 0:
        return invalid_stops
        '''

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

def require_json_content_type():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    return None
