from unittest.mock import patch


@patch("firebase_admin.auth.verify_id_token")
def test_profile_get_returns_200(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.get(
        "/profile",
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Your Profile" in response.data
    assert b"test@example.com" in response.data


@patch("firebase_admin.auth.verify_id_token")
def test_profile_post_updates_fields(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.post(
        "/profile",
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