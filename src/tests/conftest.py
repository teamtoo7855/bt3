import os
import sys
import types
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


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

    def create(self, data):
        self.store[self.key] = data

    def update(self, data):
        if self.key not in self.store:
            self.store[self.key] = {}
        self.store[self.key].update(data)

    def set(self, data, merge=False):
        if merge and self.key in self.store:
            self.store[self.key].update(data)
        else:
            self.store[self.key] = data


class FakeCollection:
    def __init__(self, store):
        self.store = store

    def document(self, key):
        return FakeDocumentRef(self.store, key)


class FakeFirestoreClient:
    def __init__(self):
        self.collections = {"profile": {}}

    def collection(self, name):
        if name not in self.collections:
            self.collections[name] = {}
        return FakeCollection(self.collections[name])


@pytest.fixture(scope="session", autouse=True)
def fake_external_modules():
    fake_keys = types.ModuleType("keys")
    fake_keys.translink_api_key = "fake-translink-key"
    fake_keys.firebase_apikey = "fake-firebase-key"
    fake_keys.mapbox_access_token = "fake-mapbox-key"

    sys.modules["keys"] = fake_keys
    sys.modules["src.keys"] = fake_keys

    fake_firebase_admin = types.ModuleType("firebase_admin")
    fake_firebase_admin._apps = []

    def initialize_app(cred):
        fake_firebase_admin._apps.append("initialized")
        return "fake-app"

    fake_firebase_admin.initialize_app = initialize_app

    fake_credentials = types.ModuleType("credentials")
    fake_credentials.Certificate = lambda path: {"path": path}

    fake_db = FakeFirestoreClient()

    fake_firestore = types.ModuleType("firestore")
    fake_firestore.client = lambda: fake_db

    fake_auth = types.ModuleType("auth")

    def verify_id_token(token):
        if token == "good-token":
            return {"uid": "test-uid"}
        raise Exception("invalid token")

    def create_user(email, password):
        return types.SimpleNamespace(uid="new-user", email=email)

    fake_auth.verify_id_token = verify_id_token
    fake_auth.create_user = create_user

    fake_firebase_admin.credentials = fake_credentials
    fake_firebase_admin.firestore = fake_firestore
    fake_firebase_admin.auth = fake_auth

    sys.modules["firebase_admin"] = fake_firebase_admin
    sys.modules["firebase_admin.credentials"] = fake_credentials
    sys.modules["firebase_admin.firestore"] = fake_firestore
    sys.modules["firebase_admin.auth"] = fake_auth


@pytest.fixture()
def app():
    from app import app as flask_app
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
    )
    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()