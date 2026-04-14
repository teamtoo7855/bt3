import pytest
from unittest.mock import MagicMock

# create test fixture with monkeypatch to mock firebase auth
@pytest.fixture
def mock_firebase_auth(monkeypatch):
    mock_verify = MagicMock(return_value={"uid": "dummy"})
    monkeypatch.setattr("firebase_admin.auth.verify_id_token", mock_verify)
    return mock_verify

# # create test fixture to mock logged in user
# @pytest.fixture
# def mock_logged_in_uid(monkeypatch):
#     mock_verify = MagicMock(return_value={"dummy"})
#     monkeypatch.setattr("utils.auth.get_current_user", mock_verify)
#     return mock_verify

# def test_profile_get_returns_200(client, mock_firebase_auth):
#     response = client.get(
#         "/api/profile",
#         headers={"Authorization": "Bearer validtoken"},
#         follow_redirects=True,
#     )

#     assert response.status_code == 200
#     assert b"profile_data" in response.data
#     assert b"dummy@localhost.lan" in response.data
#     mock_firebase_auth.assert_called_once()

# def test_profile_post_updates_fields(client, mock_logged_in_uid):
#     response = client.post(
#         "/profile",
#         data={
#             "theme": "Dark",
#             "alerts": "off",
#             "add_stop": "58501",
#         },
#         headers={"Authorization": "Bearer validtoken"},
#         follow_redirects=True,
#     )

#     assert response.status_code == 200
#     assert b"58501" in response.data
#     mock_logged_in_uid.assert_called_once()

# def test_profile_post_does_not_duplicate_stop(client, mock_logged_in_uid):
#     response = client.post(
#         "/profile",
#         data={"add_stop": "12345"},
#         headers={"Authorization": "Bearer validtoken"},
#         follow_redirects=True,
#     )

<<<<<<< HEAD
    assert response.status_code == 200
    assert b"Profile updated." in response.data
    assert b"55555" in response.data


@patch("firebase_admin.auth.verify_id_token")
def test_profile_post_does_not_duplicate_stop(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.post(
        "/profile",
        data={"add_stop": "12345"},
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert response.data.count(b"<li>12345</li>") == 1


@patch("firebase_admin.auth.verify_id_token")
def test_profile_post_sets_alerts_on(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.post(
        "/profile",
        data={"alerts": "on"},
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Profile updated." in response.data


@patch("firebase_admin.auth.verify_id_token")
def test_profile_post_sets_alerts_off(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.post(
        "/profile",
        data={"alerts": "off"},
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Profile updated." in response.data
=======
#     assert response.status_code == 200
#     assert response.data.count(b"<li>12345</li>") == 1
#     mock_logged_in_uid.assert_called_once()
>>>>>>> 53823fe2a62812c3e1d3370fa3cefa01ee2e7507
