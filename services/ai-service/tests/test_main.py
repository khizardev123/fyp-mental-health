from fastapi.testclient import TestClient
from main import app 

# Use context manager to trigger lifespan events (model loading)
def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "ai-service"}

def test_analyze_journal():
    with TestClient(app) as client:
        # Mocking the model response would be better, but for integration:
        response = client.post("/analyze/journal", json={"text": "I am feeling very happy today!", "language": "en"})
        assert response.status_code == 200
        data = response.json()
        assert "emotion" in data
        assert "crisis" in data
        # Note: Model prediction might vary, so we check structure primarily
        assert "emotion" in data["emotion"]
        assert "confidence" in data["emotion"]

def test_crisis_detection():
    with TestClient(app) as client:
        response = client.post("/predict/crisis", json={"text": "I want to end it all"})
        assert response.status_code == 200
        data = response.json()
        # Crisis endpoint returns direct result (probability)
        assert "crisis_probability" in data
        # risk_level is calculated in analyze endpoint, not here

