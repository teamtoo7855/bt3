import pytest
from unittest.mock import MagicMock

# create test fixture with monkeypatch to mock firebase auth
@pytest.fixture
def mock_firebase_auth(monkeypatch):
    mock_verify = MagicMock(return_value={"uid": "dummy"})
    monkeypatch.setattr("firebase_admin.auth.verify_id_token", mock_verify)
    return mock_verify

@patch("firebase_admin.auth.verify_id_token")
def test_profile_get_returns_200(mock_verify, client):
    mock_verify.return_value = {"uid": "dummy"}

    response = client.get(
        "/api/profile",
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"profile_data" in response.data
    assert b"dummy@localhost.lan" in response.data
    mock_firebase_auth.assert_called_once()
    response = client.post(
        "/api/profile",
        data={
            "favorite_route": "222",
            "favorite_type": "Electric",
            "theme": "Dark",
            "alerts": "off",
            "add_stop": "55555",
        },
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    mock_firebase_auth.assert_called_once()
    response = client.post(
        "/api/profile",
        data={"add_stop": "12345"},
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert response.data.count(b"<li>12345</li>") == 1
    mock_firebase_auth.assert_called_once()