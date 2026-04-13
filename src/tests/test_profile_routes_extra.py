from unittest.mock import patch


@patch("firebase_admin.auth.verify_id_token")
def test_profile_post_initializes_empty_route_and_type_lists(mock_verify, client, fake_db):
    fake_db.collection("profile").document("empty_user").set(
        {
            "email": "empty@example.com",
            "prefs": {
                "favorite_stops": [],
                "favorite_routes": [],
                "favorite_bus_types": [],
                "theme": "",
                "alerts": "",
            },
        }
    )

    mock_verify.return_value = {"uid": "empty_user"}

    response = client.post(
        "/profile",
        data={
            "favorite_route": "222",
            "favorite_type": "Electric",
        },
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"value=\"222\"" in response.data
    assert b"value=\"Electric\"" in response.data


@patch("firebase_admin.auth.verify_id_token")
def test_profile_post_keeps_existing_alerts_when_blank(mock_verify, client):
    mock_verify.return_value = {"uid": "test_user"}

    response = client.post(
        "/profile",
        data={
            "alerts": "",
        },
        headers={"Authorization": "Bearer validtoken"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Profile updated." in response.data