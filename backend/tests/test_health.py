"""Tests for NeuroMIMO FastAPI endpoints."""

from fastapi.testclient import TestClient
from neuromimo.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "torch_version" in data
    assert "numpy_version" in data


def test_config_endpoint():
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["default_fft_size"] == 64
    assert "QPSK" in data["supported_modulations"]
    assert "LS" in data["supported_algorithms"]


def test_model_status_endpoint():
    response = client.get("/api/model/status")
    assert response.status_code == 200
    data = response.json()
    assert "checkpoint_exists" in data
    assert "parameters_count" in data
    assert data["parameters_count"] > 0
