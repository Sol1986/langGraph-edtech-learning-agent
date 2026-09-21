def test_app_boots(client):
    assert client is not None


def test_health_is_ok_without_touching_redis(client, monkeypatch):
    from src import server

    def boom():
        raise AssertionError("/health must not call Redis")

    monkeypatch.setattr(server._health_redis, "ping", boom)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready_returns_200_when_redis_answers(client, monkeypatch):
    from src import server

    monkeypatch.setattr(server._health_redis, "ping", lambda: True)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "redis": "connected"}


def test_ready_returns_503_without_leaking_details_when_redis_is_down(client, monkeypatch):
    from src import server

    def boom():
        raise server.redis.ConnectionError("Error connecting to secret-host.example:1234")

    monkeypatch.setattr(server._health_redis, "ping", boom)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "redis": "unreachable"}
    assert "secret-host" not in response.text


def test_cors_headers_present_for_frontend_origin(client):
    response = client.options(
        "/api/summary",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_unhandled_exception_returns_structured_json(monkeypatch):
    from fastapi.testclient import TestClient

    from src import quiz_agent, server

    def boom(config):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(quiz_agent.graph, "get_state", boom)

    # Starlette's TestClient re-raises server exceptions by default even when
    # a handler produces a response -- turn that off since we're deliberately
    # exercising the 500 path here.
    no_raise_client = TestClient(server.app, raise_server_exceptions=False)
    response = no_raise_client.post(
        "/api/resume/some-thread", json={"human_analyst_feedback": None}
    )

    assert response.status_code == 500
    body = response.json()
    assert body["error"] == "RuntimeError"
    assert "simulated failure" in body["detail"]
