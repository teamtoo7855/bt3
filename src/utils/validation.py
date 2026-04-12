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


def validate_favorite_stops(favorite_stop_id):
    with open("./data/stops.txt", "r", encoding="utf-8-sig", newline="") as f:
        stops = []

        for row in csv.DictReader(f):
            stops.append(row.get("stop_code"))
        if favorite_stop_id not in stops:
            return False
        return True
def validate_favorite_routes(favorite_route_id):
    with open("./data/routes.txt", "r", encoding="utf-8-sig", newline="") as f:
        routes = []
        for row in csv.DictReader(f):
            routes.append(row.get("route_short_name"))
        if favorite_route_id not in routes:
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
def normalize_profile_data(created, email, favorite_bus_types, favorite_routes, favorite_stops, theme, alerts):
    return {
        #required fields
        "created": created.strip(),  # date created if wanted to use
        #non-required fields
        "email": email.strip(),
        "prefs": {
            "favorite_bus_types": favorite_bus_types.strip(), #enter in a specified format
            "favorite_routes": favorite_routes.strip(), #would be an id of sorts, can visually make it easy to understand
            "favorite_stops": favorite_stops.strip(), #would be a number
            "theme": theme.strip(), #theme strings tbd
            "alerts": alerts.strip(), #a true/false that would allow alert notifs
        }
    }


def validate_profile_data(username, password, email, favorite_bus_types,
                          favorite_routes, favorite_stops, theme, alerts, created):
    # Check all fields are strings
    fields = {
        "username": username,
        "password": password,
        "email": email,
        "favorite_bus_types": favorite_bus_types,
        "favorite_routes": favorite_routes,
        "favorite_stops": favorite_stops,
        "theme": theme,
        "alerts": alerts,
        "created": created
    }

    for field_name, value in fields.items():
        if not isinstance(value, str):
            return f"{field_name} must be a string"

    # Normalize (strip whitespace)
    username = username.strip()
    password = password.strip()
    email = email.strip()
    favorite_bus_types = favorite_bus_types.strip()
    favorite_routes = favorite_routes.strip()
    favorite_stops = favorite_stops.strip()
    theme = theme.strip()
    alerts = alerts.strip()
    created = created.strip()

    # Required fields
    if email and not validate_email(email):
        return f"{email} must be a valid email address"
    if password and not validate_password(password):
        return f"{password} must be a valid password"
    if not username:
        return "please enter your username"

    # Validate route and stop using your helper functions
    if favorite_routes and not validate_favorite_routes(favorite_routes):
        return "invalid favorite bus route"

    if favorite_stops and not validate_favorite_stops(favorite_stops):
        return "invalid favorite bus stop id"

    return None


def require_json_content_type():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    return None
