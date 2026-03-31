def test_demo_redirects_home(client):
    response = client.post("/demo", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
