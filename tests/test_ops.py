from fastapi.testclient import TestClient


def test_liveness_does_not_depend_on_database(client: TestClient) -> None:
    response = client.get("/livez")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_unavailable_database(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "checks": {"database": "fail"}}


def test_metrics_exposes_http_server_metrics(client: TestClient) -> None:
    client.get("/v1/does-not-exist")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "http_server_" in response.text


def test_ops_endpoints_are_hidden_from_openapi(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert not {"/livez", "/readyz", "/metrics"} & paths.keys()
