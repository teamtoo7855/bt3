from io import StringIO
from unittest.mock import patch
import time


@patch("firebase_admin.auth.verify_id_token")
def test_get_one_favorite_stop_valid_index_returns_200(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.get(
        "/api/profile/stops/0",
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert response.get_json() == "12345"


@patch("firebase_admin.auth.verify_id_token")
def test_get_one_favorite_stop_invalid_index_returns_400(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.get(
        "/api/profile/stops/99",
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "No stop at index"


@patch("firebase_admin.auth.verify_id_token")
def test_post_profile_stop_missing_value_returns_400(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.post(
        "/api/profile/stops",
        data={"stop_number": ""},
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid stop number"


@patch("firebase_admin.auth.verify_id_token")
def test_post_profile_stop_adds_new_stop(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.post(
        "/api/profile/stops",
        data={"stop_number": "55555"},
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "55555" in response.get_json()


@patch("firebase_admin.auth.verify_id_token")
def test_post_profile_stop_duplicate_does_not_duplicate(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.post(
        "/api/profile/stops",
        data={"stop_number": "12345"},
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert response.get_json().count("12345") == 1


@patch("firebase_admin.auth.verify_id_token")
def test_put_profile_stop_updates_existing_stop(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.put(
        "/api/api/profile/stops/0",
        data={"stop_number": "99999"},
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert response.get_json()[0] == "99999"


@patch("firebase_admin.auth.verify_id_token")
def test_put_profile_stop_invalid_index_returns_400(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.put(
        "/api/api/profile/stops/99",
        data={"stop_number": "99999"},
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "No stop at index"


@patch("firebase_admin.auth.verify_id_token")
def test_delete_profile_stop_removes_stop(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.delete(
        "/api/api/profile/stops/0",
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "12345" not in response.get_json()


@patch("firebase_admin.auth.verify_id_token")
def test_delete_profile_stop_invalid_index_returns_400(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.delete(
        "/api/api/profile/stops/99",
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "No stop at index"


class FakeResp:
    content = b"fake"

    def raise_for_status(self):
        return None


class FakeArrival:
    def __init__(self, t):
        self.time = t


class FakeStopTimeUpdate:
    def __init__(self, stop_id, arrival_time):
        self.stop_id = stop_id
        self.arrival = FakeArrival(arrival_time)
        self.departure = FakeArrival(0)

    def HasField(self, field):
        return field in {"arrival", "departure"}


class FakeTripInfo:
    def __init__(self, route_id="R1", trip_id="trip1"):
        self.route_id = route_id
        self.trip_id = trip_id

    def HasField(self, field):
        return field in {"route_id", "trip_id"}


class FakeTripUpdate:
    def __init__(self, stop_id, arrival_time, route_id="R1", trip_id="trip1"):
        self.trip = FakeTripInfo(route_id=route_id, trip_id=trip_id)
        self.stop_time_update = [FakeStopTimeUpdate(stop_id, arrival_time)]


class FakeEntityForArrival:
    def __init__(self, stop_id, arrival_time, route_id="R1", trip_id="trip1"):
        self.trip_update = FakeTripUpdate(stop_id, arrival_time, route_id, trip_id)

    def HasField(self, field):
        return field == "trip_update"


class FakeFeedNoMatch:
    def __init__(self):
        self.entity = []

    def ParseFromString(self, content):
        pass


class FakeFeedMatch:
    def __init__(self, stop_id, arrival_time, route_id="R1", trip_id="trip1"):
        self.entity = [FakeEntityForArrival(stop_id, arrival_time, route_id, trip_id)]

    def ParseFromString(self, content):
        pass


@patch("blueprints.api.routes.requests.get")
@patch("blueprints.api.routes.gtfs_realtime_pb2.FeedMessage")
def test_next_arrival_returns_none_when_no_match(mock_feed_cls, mock_get, client, monkeypatch):
    import blueprints.api.routes as api_routes

    monkeypatch.setattr(api_routes, "STOPCODE_TO_STOPID", {"12345": "STOP1"})
    monkeypatch.setattr(api_routes, "SHORT_TO_ROUTEID", {"106": "R1"})

    mock_get.return_value = FakeResp()
    mock_feed_cls.return_value = FakeFeedNoMatch()

    response = client.get("/api/next_arrival?stop_id=12345&bus_number=106")

    assert response.status_code == 200
    assert response.get_json()["next_arrival"] is None


@patch("blueprints.api.routes.requests.get")
@patch("blueprints.api.routes.gtfs_realtime_pb2.FeedMessage")
def test_next_arrival_returns_eta_when_match_found(mock_feed_cls, mock_get, client, monkeypatch):
    import blueprints.api.routes as api_routes

    monkeypatch.setattr(api_routes, "STOPCODE_TO_STOPID", {"12345": "STOP1"})
    monkeypatch.setattr(api_routes, "SHORT_TO_ROUTEID", {"106": "R1"})

    future_time = int(time.time()) + 300
    mock_get.return_value = FakeResp()
    mock_feed_cls.return_value = FakeFeedMatch("STOP1", future_time, route_id="R1", trip_id="trip1")

    response = client.get("/api/next_arrival?stop_id=12345&bus_number=106")

    assert response.status_code == 200
    data = response.get_json()
    assert data["next_arrival"] is not None
    assert data["next_arrival"]["trip_id"] == "trip1"
    assert data["route_id"] == "R1"


def test_shape_returns_geojson_from_trip_id(client, monkeypatch):
    stop_times_csv = "trip_id,stop_id\ntrip1,STOP1\n"
    trips_csv = "trip_id,shape_id\ntrip1,shapeA\n"
    shapes_csv = (
        "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n"
        "shapeA,49.25,-123.10,2\n"
        "shapeA,49.24,-123.09,1\n"
    )

    def fake_open(path, *args, **kwargs):
        if "stop_times.txt" in path:
            return StringIO(stop_times_csv)
        if "trips.txt" in path:
            return StringIO(trips_csv)
        if "shapes.txt" in path:
            return StringIO(shapes_csv)
        raise FileNotFoundError(path)

    monkeypatch.setattr("builtins.open", fake_open)

    response = client.get("/api/shape?trip_id=trip1")

    assert response.status_code == 200
    data = response.get_json()
    assert data["type"] == "FeatureCollection"
    assert data["features"][0]["geometry"]["type"] == "LineString"
    assert len(data["features"][0]["geometry"]["coordinates"]) == 2


def test_shape_resolves_trip_id_from_stop_id(client, monkeypatch):
    stop_times_csv = "trip_id,stop_id\ntrip1,STOP1\n"
    trips_csv = "trip_id,shape_id\ntrip1,shapeA\n"
    shapes_csv = (
        "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n"
        "shapeA,49.25,-123.10,1\n"
    )

    def fake_open(path, *args, **kwargs):
        if "stop_times.txt" in path:
            return StringIO(stop_times_csv)
        if "trips.txt" in path:
            return StringIO(trips_csv)
        if "shapes.txt" in path:
            return StringIO(shapes_csv)
        raise FileNotFoundError(path)

    monkeypatch.setattr("builtins.open", fake_open)

    response = client.get("/api/shape?stop_id=STOP1")

    assert response.status_code == 200
    data = response.get_json()
    assert data["features"][0]["geometry"]["coordinates"] == [[-123.10, 49.25]]