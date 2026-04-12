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


def validate_profile_data(username, password, email, favorite_bus_types, favorite_routes, favorite_stops, theme, alerts, created):

    if not isinstance(username, str):
        return "username must be a string"
    if not isinstance(password, str):
        return "password must be a string"
    if not isinstance(email, str):
        return "email must be a string"
    if not isinstance(theme, str):
        return "theme must be a string"
    if not isinstance(alerts, str):
        return "alerts must be a string"
    if not isinstance(created, float):
        return "created must be a string"

    # lists of strings
    if not isinstance(favorite_bus_types, list):
        return "favorite_bus_types must be a list of strings"
    if not isinstance(favorite_routes, list):
        return "favorite_routes must be a list of strings"
    if not isinstance(favorite_stops, list):
        return "favorite_stops must be a list of strings"

    # ensure list items are strings
    for item in favorite_bus_types:
        if not isinstance(item, str):
            return "favorite_bus_types must contain only strings"

    for item in favorite_routes:
        if not isinstance(item, str):
            return "favorite_routes must contain only strings"

    for item in favorite_stops:
        if not isinstance(item, str):
            return "favorite_stops must contain only strings"


    username = username.strip()
    password = password.strip()
    email = email.strip()
    theme = theme.strip()
    alerts = alerts.strip()
    #created = created.strip()

    # normalize list values too
    favorite_bus_types = [x.strip() for x in favorite_bus_types]
    favorite_routes = [x.strip() for x in favorite_routes]
    favorite_stops = [x.strip() for x in favorite_stops]


    if email and not validate_email(email):
        return "invalid email address"

    if password and not validate_password(password):
        return "password must be at least 8 characters"


    for route in favorite_routes:
        if not validate_favorite_routes(route):
            return f"invalid route: {route}"

    for stop in favorite_stops:
        if not validate_favorite_stops(stop):
            return f"invalid stop: {stop}"

    return None


def require_json_content_type():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    return None
