from unittest.mock import patch


def test_profile_requires_auth_header(client):
    response = client.get("/api/profile")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Missing Authorization header"


def test_profile_rejects_bad_auth_format(client):
    response = client.get(
        "/api/profile",
        headers={"Authorization": "Token abc123"}
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid Authorization header format"


def test_profile_rejects_invalid_token(client):
    response = client.get(
        "/api/profile",
        headers={"Authorization": "Bearer bad-token"}
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid or expired token"


@patch("blueprints.api.routes.db")
def test_profile_accepts_valid_token(mock_db, client):
    fake_doc = mock_db.collection.return_value.document.return_value.get
    fake_doc.return_value.exists = True
    fake_doc.return_value.to_dict.return_value = {
        "email": "test@example.com",
        "prefs": {
            "favorite_routes": ["106"],
            "favorite_bus_types": ["Electric"],
            "favorite_stops": ["56934"],
            "theme": "Dark",
            "alerts": True,
        }
    }

    response = client.get(
        "/api/profile",
        headers={"Authorization": "Bearer good-token"}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["email"] == "test@example.com"
    assert data["prefs"]["favorite_routes"] == ["106"]