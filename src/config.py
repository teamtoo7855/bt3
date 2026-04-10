import os
import keys
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    MAPBOX_ACCESS_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN")
    TRANSLINK_API_KEY = os.environ.get("TRANSLINK_API_KEY")
    FIREBASE_APIKEY = os.environ.get("FIREBASE_APIKEY")
    GTFS_VEHICLE_URL = f'https://gtfsapi.translink.ca/v3/gtfsposition?apikey={TRANSLINK_API_KEY}'
    GTFS_TRIP_URL = f"https://gtfsapi.translink.ca/v3/gtfsrealtime?apikey={TRANSLINK_API_KEY}"
    #WEB_API_KEY = keys.firebase_apikey
    #MAPBOX_ACCESS_TOKEN = keys.mapbox_access_token

    SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT", "serviceAccountKey.json")
    FIREBASE_LOGIN = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_APIKEY}"