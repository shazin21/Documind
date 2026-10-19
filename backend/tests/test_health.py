from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "DocuMind AI"
    assert "status" in data
    assert "version" in data
    assert "database" in data
    assert "embedding_model" in data
    assert data["embedding_model"]["dimension"] == 384
