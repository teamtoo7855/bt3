import os
import firebase_admin
from firebase_admin import credentials, firestore

from config import Config


db = None

if not firebase_admin._apps:
    service_account_path = Config.SERVICE_ACCOUNT_PATH

    if os.path.exists(service_account_path):
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
else:
    db = firestore.client()