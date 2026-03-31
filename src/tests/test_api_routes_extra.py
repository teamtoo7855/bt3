from unittest.mock import patch


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
def test_get_one_favorite_stop_invalid_index_returns_400(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.get(
        "/api/profile/stops/99",
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "No stop at index"


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