from unittest.mock import patch


def test_missing_token_returns_401(client):
    response = client.get("/api/profile/stops", follow_redirects=True)

    assert response.status_code == 401


def test_bad_format_token_returns_401(client):
    response = client.get(
        "/api/profile/stops",
        headers={"Authorization": "badtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 401


@patch("firebase_admin.auth.verify_id_token")
def test_invalid_token_returns_401(mock_verify, client):
    mock_verify.side_effect = Exception("invalid")

    response = client.get(
        "/api/profile/stops",
        headers={"Authorization": "Bearer bad"},
        follow_redirects=True,
    )

    assert response.status_code == 401