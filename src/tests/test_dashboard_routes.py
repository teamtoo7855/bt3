from unittest.mock import patch


def test_demo_redirects_home(client):
    response = client.post("/demo", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


@patch("blueprints.dashboard.routes.require_login_or_demo")
def test_home_returns_index_when_logged_in_or_demo(mock_require, client):
    mock_require.return_value = "test_user"

    response = client.get("/", follow_redirects=True)
from unittest.mock import patch


def test_demo_redirects_home(client):
    response = client.post("/demo", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


@patch("blueprints.dashboard.routes.require_login_or_demo")
def test_home_returns_index_when_logged_in_or_demo(mock_require, client):
    mock_require.return_value = "test_user"

    response = client.get("/", follow_redirects=True)

    assert response.status_code == 200
    assert b"map" in response.data.lower()
    assert response.status_code == 200
    assert b"map" in response.data.lower()