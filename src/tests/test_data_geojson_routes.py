from unittest.mock import patch


class FakeVehiclePosition:
    def __init__(self):
        self.latitude = 49.25
        self.longitude = -123.10
        self.bearing = 90

    def HasField(self, field):
        return field in {"latitude", "bearing"}


class FakeVehicleInfo:
    def __init__(self):
        self.id = "1234"


class FakeTrip:
    def __init__(self):
        self.trip_id = "trip1"
        self.route_id = "R1"
        self.direction_id = 1

    def HasField(self, field):
        return True


class FakeVehicle:
    def __init__(self):
        self.position = FakeVehiclePosition()
        self.vehicle = FakeVehicleInfo()
        self.trip = FakeTrip()


class FakeEntity:
    def __init__(self):
        self.vehicle = FakeVehicle()

    def HasField(self, field):
        return field == "vehicle"


class FakeFeed:
    def __init__(self):
        self.entity = [FakeEntity()]

    def ParseFromString(self, content):
        pass


class FakeStop:
    def __init__(self, stop_id, stop_code, stop_name, stop_lat, stop_lon):
        self.stop_id = stop_id
        self.stop_code = stop_code
        self.stop_name = stop_name
        self.stop_lat = stop_lat
        self.stop_lon = stop_lon


@patch("blueprints.data_geojson.routes.check_id")
@patch("blueprints.data_geojson.routes.gtfs_realtime_pb2.FeedMessage")
@patch("blueprints.data_geojson.routes.requests.get")
def test_vehicles_geojson_returns_feature_collection(
    mock_get, mock_feed_cls, mock_check_id, client
):
    class FakeResponse:
        content = b"fake"

    mock_get.return_value = FakeResponse()
    mock_feed_cls.return_value = FakeFeed()
    mock_check_id.return_value = "2020 New Flyer"

    response = client.get("/vehicles.geojson")

    assert response.status_code == 200
    data = response.get_json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["vehicle_id"] == "1234"


@patch("blueprints.data_geojson.routes.db.session.execute")
def test_stops_geojson_returns_feature_collection(mock_execute, client):
    mock_execute.return_value.all.return_value = [
        FakeStop("1001", "12345", "Test Stop", 49.25, -123.10),
        FakeStop("1002", "67890", "Another Stop", 49.26, -123.11),
    ]

    response = client.get("/stops.geojson")

    assert response.status_code == 200
    data = response.get_json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 2
    assert data["features"][0]["properties"]["stop_code"] == "12345"
    assert data["features"][1]["properties"]["stop_name"] == "Another Stop"