import pytest
from app import app as flask_app


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

    db.collection("profile").document("test_user").set({
        "prefs": {
            "favorite_stops": ["12345", "67890"]
        }
    })

    return db


@pytest.fixture
def client(fake_db, monkeypatch):
    flask_app.config["TESTING"] = True

    import firebase
    monkeypatch.setattr(firebase, "db", fake_db)

    import blueprints.api.routes as api_routes
    monkeypatch.setattr(api_routes, "db", fake_db)

    with flask_app.test_client() as test_client:
        yield test_client