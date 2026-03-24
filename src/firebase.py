import firebase_admin
from firebase_admin import credentials, firestore
from config import Config

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(Config.SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)

# Export db instance to avoid circular imports
db = firestore.client()
