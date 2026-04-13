import os
import sys
import types
from unittest.mock import Mock

import pytest

# -------------------------
# Make tests CI-safe before importing the app
# -------------------------

os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key")
os.environ.setdefault("FIREBASE_SERVICE_ACCOUNT", "dummy-service-account.json")

fake_keys = types.SimpleNamespace(
    mapbox_access_token="test-mapbox-token",
    translink_api_key="test-translink-key",
    firebase_apikey="test-firebase-api-key",
)
sys.modules["keys"] = fake_keys
sys.modules["src.keys"] = fake_keys

# Stub Firebase Admin initialization before importing app
import firebase_admin
from firebase_admin import credentials, firestore

firebase_admin._apps = []
credentials.Certificate = Mock(return_value=object())
firebase_admin.initialize_app = Mock(return_value=object())
firestore.client = Mock(return_value=object())

# Provide a fake utils.data module so app import never touches local GTFS files
fake_utils_data = types.ModuleType("utils.data")
fake_utils_data.STOPCODE_TO_STOPID = {"12345": "STOP1", "67890": "STOP2"}
fake_utils_data.SHORT_TO_ROUTEID = {"106": "R1", "144": "R2"}

def fake_check_id(bus_id):
    return None

fake_utils_data.check_id = fake_check_id
sys.modules["utils.data"] = fake_utils_data

from app import app as flask_app


# -------------------------
# Block accidental real network calls
# -------------------------

@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    import requests.sessions

    def block(*args, **kwargs):
        raise AssertionError("Real network access is not allowed in tests")

    monkeypatch.setattr(requests.sessions.Session, "request", block)


# -------------------------
# Fake Firestore
# -------------------------

class FakeDocSnapshot:
    def __init__(self, data=None):
        self._data = data

    def to_dict(self):
        return self._data

    @property
    def exists(self):
        return self._data is not None


class FakeDocumentRef:
    def __init__(self, store, key):
        self.store = store
        self.key = key

    def get(self):
        return FakeDocSnapshot(self.store.get(self.key))

    def set(self, data):
        self.store[self.key] = data

    def update(self, data):
        if self.key not in self.store:
            self.store[self.key] = {}

        for k, v in data.items():
            if isinstance(v, dict) and isinstance(self.store[self.key].get(k), dict):
                self.store[self.key][k].update(v)
            else:
                self.store[self.key][k] = v


class FakeCollection:
    def __init__(self, root_store, name):
        self.root_store = root_store
        self.name = name
        if name not in self.root_store:
            self.root_store[name] = {}

    def document(self, key):
        return FakeDocumentRef(self.root_store[self.name], key)


class FakeDB:
    def __init__(self):
        self.store = {}

    def collection(self, name):
        return FakeCollection(self.store, name)


@pytest.fixture
def fake_db():
    db = FakeDB()

    db.collection("profile").document("test_user").set(
        {
            "email": "test@example.com",
            "prefs": {
                "favorite_stops": ["12345", "67890"],
                "favorite_routes": ["106"],
                "favorite_bus_types": ["Standard"],
                "theme": "Light",
                "alerts": True,
            },
        }
    )

    return db


@pytest.fixture
def client(fake_db, monkeypatch):
    flask_app.config["TESTING"] = True

    import firebase
    monkeypatch.setattr(firebase, "db", fake_db)

    import blueprints.api.routes as api_routes
    monkeypatch.setattr(api_routes, "db", fake_db)

    import blueprints.auth.routes as auth_routes
    monkeypatch.setattr(auth_routes, "db", fake_db)

    import blueprints.profile.routes as profile_routes
    monkeypatch.setattr(profile_routes, "db", fake_db)

    with flask_app.test_client() as test_client:
        yield test_client