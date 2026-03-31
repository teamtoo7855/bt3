from unittest.mock import patch


def test_signup_get_returns_200(client):
    response = client.get("/signup")

    assert response.status_code == 200
    assert b"Create your bt3 account" in response.data


def test_login_get_returns_200(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b"Sign in to bt3" in response.data


def test_signup_invalid_email_shows_error(client):
    response = client.post(
        "/signup",
        data={
            "email": "bademail",
            "password": "password123",
            "password_confirm": "password123",
            "favorite_stop": "12345",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Please enter a valid email." in response.data


def test_signup_short_password_shows_error(client):
    response = client.post(
        "/signup",
        data={
            "email": "test@example.com",
            "password": "short",
            "password_confirm": "short",
            "favorite_stop": "12345",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Password needs to be at least 8 characters long." in response.data


def test_signup_password_mismatch_shows_error(client):
    response = client.post(
        "/signup",
        data={
            "email": "test@example.com",
            "password": "password123",
            "password_confirm": "different123",
            "favorite_stop": "12345",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Passwords don&#39;t match." in response.data


@patch("blueprints.auth.routes.validate_favorite_stops")
def test_signup_invalid_favorite_stop_shows_error(mock_validate_stop, client):
    mock_validate_stop.return_value = False

    response = client.post(
        "/signup",
        data={
            "email": "test@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "favorite_stop": "99999",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"does not exist" in response.data


@patch("firebase_admin.auth.create_user")
@patch("blueprints.auth.routes.validate_favorite_stops")
def test_signup_success_redirects_to_login(mock_validate_stop, mock_create_user, client):
    class FakeUser:
        uid = "new_user"

    mock_validate_stop.return_value = True
    mock_create_user.return_value = FakeUser()

    response = client.post(
        "/signup",
        data={
            "email": "test@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "favorite_route": "106",
            "favorite_type": "Standard",
            "theme": "Light",
            "alerts": "on",
            "favorite_stop": "12345",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


@patch("blueprints.auth.routes.requests.post")
def test_login_invalid_email_or_password_returns_page(mock_post, client):
    response = client.post(
        "/login",
        data={
            "email": "bademail",
            "password": "short",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Bad email or password." in response.data
    mock_post.assert_not_called()


def test_logout_redirects_to_login(client):
    response = client.get("/logout", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]