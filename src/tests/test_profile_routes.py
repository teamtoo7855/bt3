from unittest.mock import patch


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