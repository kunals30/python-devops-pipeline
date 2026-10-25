from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == (
        "Python CI/CD pipeline is running"
    )


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_add_endpoint():
    response = client.post(
        "/add",
        json={"a": 10, "b": 20}
    )
    assert response.status_code == 200
    assert response.json()["result"] == 30
