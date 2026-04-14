from unittest.mock import patch


@patch("firebase_admin.auth.create_user")
@patch("blueprints.auth.routes.validate_favorite_stops")
def test_signup_existing_email_shows_error(mock_validate_stop, mock_create_user, client):
    mock_validate_stop.return_value = True
    mock_create_user.side_effect = Exception("email exists")

    response = client.post(
        "/signup",
        data={
            "email": "test@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "favorite_stop": "12345",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Error creating account. Email may already exist." in response.data


@patch("blueprints.auth.routes.requests.post")
def test_login_valid_input_calls_firebase_login(mock_post, client):
    class FakeResponse:
        status_code = 400

        def json(self):
            return {}

    mock_post.return_value = FakeResponse()

    response = client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    mock_post.assert_called_once()

