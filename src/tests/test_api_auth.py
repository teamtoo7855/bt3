from unittest.mock import patch


def test_missing_auth_header_returns_401(client):
    response = client.get("/api/profile/stops")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Missing Authorization header"


def test_invalid_auth_format_returns_401(client):
    response = client.get(
        "/api/profile/stops",
        headers={"Authorization": "not-a-bearer-token"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid Authorization header format"


@patch("firebase_admin.auth.verify_id_token")
def test_invalid_token_returns_401(mock_verify, client):
    mock_verify.side_effect = Exception("bad token")

    response = client.get(
        "/api/profile/stops",
        headers={"Authorization": "Bearer badtoken"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid or expired token"


@patch("firebase_admin.auth.verify_id_token")
def test_valid_token_allows_access_to_protected_route(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.get(
        "/api/profile/stops",
        headers={"Authorization": "Bearer validtoken"},
    )

    assert response.status_code == 200
    assert response.get_json() == ["12345", "67890"]


@patch("firebase_admin.auth.verify_id_token")
def test_get_one_favorite_stop_returns_200(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.get(
        "/api/profile/stops/0",
        headers={"Authorization": "Bearer validtoken"},
    )

    assert response.status_code == 200
    assert response.get_json() == "12345"


@patch("firebase_admin.auth.verify_id_token")
def test_get_one_favorite_stop_bad_index_returns_400(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.get(
        "/api/profile/stops/99",
        headers={"Authorization": "Bearer validtoken"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "No stop at index"