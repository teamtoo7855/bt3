from unittest.mock import patch


def test_login_bad_email_returns_400(client):
    response = client.post(
        "/api/login",
        json={"email": "not-an-email", "password": "secret123"}
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_login_bad_password_returns_400(client):
    response = client.post(
        "/api/login",
        json={"email": "user@example.com", "password": "123"}
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_signup_passwords_do_not_match_returns_400(client):
    response = client.post(
        "/api/signup",
        json={
            "email": "user@example.com",
            "password": "secret123",
            "password_confirm": "different123",
            "favorite_route": "",
            "favorite_type": "",
            "theme": "",
            "alerts": "",
            "favorite_stop": ""
        }
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Passwords do not match"


def test_signup_bad_email_returns_400(client):
    response = client.post(
        "/api/signup",
        json={
            "email": "bad-email",
            "password": "secret123",
            "password_confirm": "secret123",
            "favorite_route": "",
            "favorite_type": "",
            "theme": "",
            "alerts": "",
            "favorite_stop": ""
        }
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


@patch("blueprints.api.routes.validate_favorite_stops", return_value=False)
def test_signup_bad_favorite_stop_returns_400(mock_validate_stop, client):
    response = client.post(
        "/api/signup",
        json={
            "email": "user@example.com",
            "password": "secret123",
            "password_confirm": "secret123",
            "favorite_route": "",
            "favorite_type": "",
            "theme": "",
            "alerts": "",
            "favorite_stop": "99999"
        }
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid favorite stop"


def test_profile_update_without_token_returns_401(client):
    response = client.put(
        "/api/profile",
        json={"favorite_route": "106"}
    )
    assert response.status_code == 401


@patch("blueprints.api.routes.db")
@patch("blueprints.api.routes.validate_favorite_stops", return_value=False)
def test_profile_update_filters_invalid_stops(mock_validate_stop, mock_db, client):
    fake_doc_ref = mock_db.collection.return_value.document.return_value
    fake_doc_ref.get.return_value.exists = True
    fake_doc_ref.get.return_value.to_dict.return_value = {
        "email": "test@example.com",
        "prefs": {
            "favorite_routes": [],
            "favorite_bus_types": [],
            "favorite_stops": [],
            "theme": "",
            "alerts": ""
        }
    }

    response = client.put(
        "/api/profile",
        headers={"Authorization": "Bearer good-token"},
        json={
            "favorite_route": "106",
            "favorite_type": "Electric",
            "theme": "Dark",
            "alerts": "on",
            "favorite_stops": ["99999"]
        }
    )

    assert response.status_code == 200
    updated_payload = fake_doc_ref.update.call_args[0][0]
    assert updated_payload["prefs"]["favorite_stops"] == []


@patch("blueprints.api.routes.validate_favorite_stops", return_value=False)
def test_add_profile_stop_bad_payload_returns_400(mock_validate_stop, client):
    response = client.post(
        "/api/profile/stops",
        headers={"Authorization": "Bearer good-token"},
        json={"stop_code": "99999"}
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid stop code"