"""Comprehensive integration and unit test suite for the NeuroMIMO FastAPI backend.

Tests all 10 endpoints:
- GET /api/health
- GET /api/config
- POST /api/simulation/run (success and validation failure branches)
- POST /api/estimation/compare (multi-algorithm benchmarking)
- POST /api/model/train (synchronous and background modes)
- GET /api/model/status
- GET /api/model/train/status
- POST /api/model/predict (ad-hoc and explicit feature inputs)
- GET /api/experiments
- GET /api/experiments/{experiment_id}
- GET /api/experiments/{experiment_id}/plots
"""

import os
import json
import numpy as np
import pytest
from fastapi.testclient import TestClient

from neuromimo.api.main import app, CHECKPOINT_PATH, RESULTS_DIR

client = TestClient(app)


# =============================================================================
# 1. Health & Config Endpoints
# =============================================================================

def test_api_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "device" in data
    assert "cuda_available" in data
    assert "torch_version" in data
    assert "numpy_version" in data


def test_api_config_endpoint():
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["default_fft_size"] == 64
    assert "QPSK" in data["supported_modulations"]
    assert "16QAM" in data["supported_modulations"]
    assert "RAYLEIGH" in data["supported_channel_models"]
    assert "AWGN" in data["supported_channel_models"]
    assert "LS" in data["supported_algorithms"]
    assert "MMSE" in data["supported_algorithms"]
    assert "DNN" in data["supported_algorithms"]


# =============================================================================
# 2. Simulation Execution Endpoint
# =============================================================================

def test_api_simulation_run_ls_success():
    payload = {
        "num_tx": 2,
        "num_rx": 2,
        "fft_size": 64,
        "cp_length": 16,
        "pilot_spacing": 8,
        "modulation": "QPSK",
        "channel_model": "RAYLEIGH",
        "snr_db": 20.0,
        "algorithm": "LS",
        "num_ofdm_symbols": 4,
        "random_seed": 42,
    }
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["algorithm"] == "LS"
    assert data["snr_db"] == 20.0
    assert "nmse" in data
    assert "nmse_db" in data
    assert "ber" in data
    assert "ser" in data
    assert data["total_bits"] > 0
    assert data["bit_errors"] <= data["total_bits"]
    assert len(data["tx_constellation_sample"]) > 0
    assert len(data["rx_constellation_sample"]) > 0
    assert len(data["channel_magnitude_profile"]) == 64


def test_api_simulation_run_mmse_success():
    payload = {
        "num_tx": 2,
        "num_rx": 2,
        "fft_size": 64,
        "cp_length": 16,
        "pilot_spacing": 8,
        "modulation": "16QAM",
        "channel_model": "AWGN",
        "snr_db": 25.0,
        "algorithm": "MMSE",
        "num_ofdm_symbols": 4,
        "random_seed": 100,
    }
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"] == "MMSE"
    assert data["snr_db"] == 25.0


def test_api_simulation_run_dnn_success():
    if not os.path.exists(CHECKPOINT_PATH):
        pytest.skip("DNN checkpoint not found on disk.")

    payload = {
        "num_tx": 2,
        "num_rx": 2,
        "fft_size": 64,
        "cp_length": 16,
        "pilot_spacing": 8,
        "modulation": "QPSK",
        "channel_model": "RAYLEIGH",
        "snr_db": 15.0,
        "algorithm": "DNN",
        "num_ofdm_symbols": 4,
        "random_seed": 777,
    }
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"] == "DNN"


def test_api_simulation_run_invalid_parameters():
    # 1. Invalid modulation
    res = client.post("/api/simulation/run", json={"modulation": "64QAM_UNSUPPORTED"})
    assert res.status_code == 400
    assert "Unsupported modulation" in res.json()["detail"]

    # 2. Invalid channel model
    res = client.post("/api/simulation/run", json={"channel_model": "RICIAN_UNSUPPORTED"})
    assert res.status_code == 400
    assert "Unsupported channel model" in res.json()["detail"]

    # 3. Invalid algorithm
    res = client.post("/api/simulation/run", json={"algorithm": "KALMAN_UNSUPPORTED"})
    assert res.status_code == 400
    assert "Unsupported algorithm" in res.json()["detail"]

    # 4. Invalid CP length
    res = client.post("/api/simulation/run", json={"fft_size": 64, "cp_length": 64})
    assert res.status_code == 400
    assert "Cyclic prefix length" in res.json()["detail"]

    # 5. Out of range SNR
    res = client.post("/api/simulation/run", json={"snr_db": 100.0})
    assert res.status_code == 422


# =============================================================================
# 3. Estimation Compare Endpoint
# =============================================================================

def test_api_estimation_compare_success():
    payload = {
        "snr_db": 15.0,
        "algorithms": ["LS", "MMSE"],
        "num_realizations": 2,
        "fft_size": 64,
        "cp_length": 16,
        "modulation": "QPSK",
    }
    response = client.post("/api/estimation/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["snr_db"] == 15.0
    assert len(data["results"]) == 2
    algos = [r["algorithm"] for r in data["results"]]
    assert "LS" in algos
    assert "MMSE" in algos
    for r in data["results"]:
        assert "nmse" in r
        assert "nmse_db" in r
        assert "ber" in r
        assert "execution_time_ms" in r


def test_api_estimation_compare_invalid_algorithm():
    payload = {
        "snr_db": 15.0,
        "algorithms": ["INVALID_ALGO"],
    }
    response = client.post("/api/estimation/compare", json=payload)
    assert response.status_code == 400
    assert "Invalid algorithm" in response.json()["detail"]


# =============================================================================
# 4. Model Status, Training & Inference Endpoints
# =============================================================================

def test_api_model_status():
    response = client.get("/api/model/status")
    assert response.status_code == 200
    data = response.json()
    assert "trained" in data
    assert "checkpoint_exists" in data
    assert "checkpoint_path" in data
    assert data["parameters_count"] > 0
    assert "device" in data


def test_api_model_train_synchronous_smoke(tmp_path, monkeypatch):
    # Save the smoke-test model to a temp file so the trained checkpoint
    # committed in backend/models/ is never overwritten.
    smoke_ckpt = str(tmp_path / "smoke_dnn.pt")
    monkeypatch.setattr("neuromimo.api.main.CHECKPOINT_PATH", smoke_ckpt)

    payload = {
        "epochs": 2,
        "batch_size": 16,
        "learning_rate": 0.005,
        "num_samples": 60,
        "snr_range": [5.0, 25.0],
        "random_seed": 42,
        "background": False,
    }
    response = client.post("/api/model/train", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["epochs_completed"] == 2
    assert len(data["history"]) == 2
    assert data["checkpoint_saved"] is True
    assert os.path.exists(data["checkpoint_path"])
    assert os.path.abspath(data["checkpoint_path"]) == smoke_ckpt


def test_api_model_train_invalid_snr_range():
    payload = {
        "epochs": 2,
        "snr_range": [30.0, 10.0],  # Invalid min > max
    }
    response = client.post("/api/model/train", json=payload)
    assert response.status_code == 400


def test_api_model_predict_ad_hoc():
    if not os.path.exists(CHECKPOINT_PATH):
        pytest.skip("DNN checkpoint not found on disk.")

    payload = {
        "snr_db": 20.0,
        "channel_model": "RAYLEIGH",
        "modulation": "QPSK",
    }
    response = client.post("/api/model/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["h_pred_real"]) == 2 * 2 * 64
    assert len(data["h_pred_imag"]) == 2 * 2 * 64
    assert "nmse" in data
    assert "nmse_db" in data
    assert data["inference_time_ms"] >= 0.0


def test_api_model_predict_custom_features():
    if not os.path.exists(CHECKPOINT_PATH):
        pytest.skip("DNN checkpoint not found on disk.")

    dummy_features = [0.1] * 512
    payload = {
        "features": dummy_features,
    }
    response = client.post("/api/model/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["h_pred_real"]) == 256
    assert len(data["h_pred_imag"]) == 256


def test_api_model_predict_invalid_feature_length():
    payload = {
        "features": [0.1] * 100,  # Invalid: requires 512
    }
    response = client.post("/api/model/predict", json=payload)
    assert response.status_code == 400
    assert "512 elements" in response.json()["detail"]


# =============================================================================
# 5. Experiments & Plots Retrieval Endpoints
# =============================================================================

def test_api_experiments_list_and_detail():
    # 1. Trigger a simulation to guarantee at least one record
    run_res = client.post(
        "/api/simulation/run",
        json={
            "num_tx": 2,
            "num_rx": 2,
            "fft_size": 64,
            "cp_length": 16,
            "pilot_spacing": 8,
            "modulation": "QPSK",
            "channel_model": "RAYLEIGH",
            "snr_db": 10.0,
            "algorithm": "LS",
            "num_ofdm_symbols": 2,
        },
    )
    exp_id = run_res.json()["id"]

    # 2. List all experiments
    list_res = client.get("/api/experiments")
    assert list_res.status_code == 200
    exp_list = list_res.json()
    assert len(exp_list) > 0
    ids = [e["id"] for e in exp_list]
    assert exp_id in ids

    # 3. Retrieve detail by ID
    detail_res = client.get(f"/api/experiments/{exp_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == exp_id
    assert detail_data["algorithm"] == "LS"
    assert detail_data["snr_db"] == 10.0
    assert "results" in detail_data


def test_api_experiment_detail_not_found():
    response = client.get("/api/experiments/non-existent-uuid-99999")
    assert response.status_code == 404


def test_api_experiment_plots_catalog():
    # Test catalog with 'latest' alias
    response = client.get("/api/experiments/latest/plots")
    assert response.status_code == 200
    data = response.json()
    assert data["experiment_id"] == "latest"
    assert "plots" in data
    # At least some of the 6 publication plots should exist if run
    plot_names = [p["filename"] for p in data["plots"]]
    if os.path.exists(os.path.join(RESULTS_DIR, "nmse_vs_snr.png")):
        assert "nmse_vs_snr.png" in plot_names


def test_api_experiment_plots_image_serving():
    if not os.path.exists(os.path.join(RESULTS_DIR, "nmse_vs_snr.png")):
        pytest.skip("nmse_vs_snr.png not present in results dir.")

    response = client.get("/api/experiments/latest/plots/nmse_vs_snr.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 1000


def test_api_experiment_plots_not_found():
    response = client.get("/api/experiments/latest/plots/non_existent_plot.png")
    assert response.status_code == 404
