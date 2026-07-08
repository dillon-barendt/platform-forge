from fastapi.testclient import TestClient
from {{ cookiecutter.gateway_package }}.main import create_app


def test_health() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_provider_registry() -> None:
    client = TestClient(create_app())

    response = client.get("/providers")

    assert response.status_code == 200
    assert response.json()
