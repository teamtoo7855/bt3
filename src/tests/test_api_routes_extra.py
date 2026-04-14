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
