import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

    TRANSLINK_API_KEY = os.getenv("TRANSLINK_API_KEY", "test-translink-key")
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "test-firebase-api-key")
    MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN", "test-mapbox-token")

    GTFS_VEHICLE_URL = (
        f"https://gtfsapi.translink.ca/v3/gtfsposition?apikey={TRANSLINK_API_KEY}"
    )
    GTFS_TRIP_URL = (
        f"https://gtfsapi.translink.ca/v3/gtfsrealtime?apikey={TRANSLINK_API_KEY}"
    )
    WEB_API_KEY = FIREBASE_API_KEY
    SERVICE_ACCOUNT_PATH = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT",
        "serviceAccountKey.json",
    )
    FIREBASE_LOGIN = (
        "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
        f"?key={WEB_API_KEY}"
    )