from flask import session


def test_is_demo_false_by_default(client):
    import blueprints.dashboard.routes as dashboard_routes

    with client.application.test_request_context("/"):
        session.clear()
        assert dashboard_routes.is_demo() is False


def test_is_demo_true_when_session_set(client):
    import blueprints.dashboard.routes as dashboard_routes

    with client.application.test_request_context("/"):
        session["demo"] = True
        assert dashboard_routes.is_demo() is True


def test_home_redirects_when_require_login_or_demo_returns_none(client, monkeypatch):
    import blueprints.dashboard.routes as dashboard_routes

    monkeypatch.setattr(dashboard_routes, "require_login_or_demo", lambda: None)

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]