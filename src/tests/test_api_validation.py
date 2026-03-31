def test_missing_all_params_returns_400(client):
    response = client.get("/api/next_arrival")

    assert response.status_code == 400


def test_missing_stop_id_returns_400(client):
    response = client.get("/api/next_arrival?bus_number=106")

    assert response.status_code == 400


def test_missing_bus_number_returns_400(client):
    response = client.get("/api/next_arrival?stop_id=12345")

    assert response.status_code == 400


def test_invalid_stop_code_returns_400(client):
    response = client.get("/api/next_arrival?stop_id=INVALID&bus_number=106")

    assert response.status_code == 400


def test_invalid_route_returns_400(client):
    response = client.get("/api/next_arrival?stop_id=12345&bus_number=INVALID")

    assert response.status_code == 400