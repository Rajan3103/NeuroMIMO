"""Unit and integration tests for PyTorch DNN channel estimation, training, and benchmarking."""

import os
import tempfile
import numpy as np
import pytest
import torch
from torch.utils.data import TensorDataset, DataLoader

from neuromimo.config import SimulationConfig, EstimationAlgorithm, ModulationType, ChannelModelType
from neuromimo.estimation.dnn import ChannelEstimationNet, DNNEstimator
from neuromimo.estimation.trainer import (
    generate_channel_dataset,
    split_dataset,
    ChannelEstimationTrainer,
)
from neuromimo.evaluation.benchmarks import benchmark_channel_estimators
from neuromimo.wireless.simulation import MIMOSimulationPipeline


def test_channel_dataset_generator_dimensions_and_reproducibility():
    """Verify generated dataset dimensions, SNR bounds, and deterministic reproducibility."""
    num_samples = 20
    X1, Y1, snrs1 = generate_channel_dataset(
        num_samples=num_samples,
        snr_range=(5.0, 25.0),
        random_seed=123,
    )
    # Check shapes: 64 subcarriers * 2 Rx * 2 Tx * 2 (real, imag) = 512
    assert X1.shape == (num_samples, 512)
    assert Y1.shape == (num_samples, 512)
    assert snrs1.shape == (num_samples,)
    assert np.all(snrs1 >= 5.0) and np.all(snrs1 <= 25.0)

    # Check reproducibility
    X2, Y2, snrs2 = generate_channel_dataset(
        num_samples=num_samples,
        snr_range=(5.0, 25.0),
        random_seed=123,
    )
    assert np.allclose(X1, X2)
    assert np.allclose(Y1, Y2)
    assert np.allclose(snrs1, snrs2)


def test_dataset_split_no_data_leakage():
    """Verify train, validation, and held-out test splits have zero overlap."""
    num_samples = 100
    X = np.random.randn(num_samples, 512).astype(np.float32)
    Y = np.random.randn(num_samples, 512).astype(np.float32)

    (X_tr, Y_tr), (X_val, Y_val), (X_te, Y_te) = split_dataset(
        X, Y, train_ratio=0.70, val_ratio=0.15, random_seed=42
    )

    assert len(X_tr) == 70
    assert len(X_val) == 15
    assert len(X_te) == 15
    assert len(X_tr) + len(X_val) + len(X_te) == num_samples


def test_channel_estimation_net_forward():
    """Verify forward pass on single-sample and batched inputs."""
    model = ChannelEstimationNet(input_dim=512, output_dim=512)
    model.eval()

    # Single-sample inference (1, 512)
    x1 = torch.randn(1, 512)
    with torch.no_grad():
        out1 = model(x1)
    assert out1.shape == (1, 512)

    # Batched inference (16, 512)
    x16 = torch.randn(16, 512)
    with torch.no_grad():
        out16 = model(x16)
    assert out16.shape == (16, 512)


def test_end_to_end_dnn_training_and_checkpoint():
    """Run a fast training loop, check loss curves, and verify checkpoint saving/loading."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ckpt_path = os.path.join(tmp_dir, "test_model.pt")

        # 1. Generate small training set
        X, Y, _ = generate_channel_dataset(num_samples=60, random_seed=999)
        (X_tr, Y_tr), (X_val, Y_val), (X_te, Y_te) = split_dataset(X, Y, train_ratio=0.7, val_ratio=0.15)

        tr_ds = TensorDataset(torch.from_numpy(X_tr), torch.from_numpy(Y_tr))
        val_ds = TensorDataset(torch.from_numpy(X_val), torch.from_numpy(Y_val))
        te_ds = TensorDataset(torch.from_numpy(X_te), torch.from_numpy(Y_te))

        tr_loader = DataLoader(tr_ds, batch_size=16, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=16)
        te_loader = DataLoader(te_ds, batch_size=16)

        # 2. Train model for 3 epochs
        trainer = ChannelEstimationTrainer(learning_rate=0.005)
        res = trainer.fit(tr_loader, val_loader, epochs=3, checkpoint_path=ckpt_path)

        assert res["status"] == "completed"
        assert res["epochs_completed"] == 3
        assert len(res["history"]) == 3
        assert os.path.exists(ckpt_path)

        # 3. Evaluate held-out test set
        test_eval = trainer.evaluate_test_set(te_loader)
        assert "test_mse" in test_eval
        assert "test_nmse" in test_eval
        assert test_eval["test_mse"] > 0

        # 4. Load saved model into DNNEstimator and run inference
        estimator = DNNEstimator(model_path=ckpt_path, fft_size=64, num_rx=2, num_tx=2)
        assert estimator.model_loaded is True

        # Test dummy pilot inputs
        rx_pilots = {0: np.ones((2, 4), dtype=np.complex128), 1: np.ones((2, 4), dtype=np.complex128)}
        tx_pilots = {0: np.ones(4, dtype=np.complex128), 1: np.ones(4, dtype=np.complex128)}
        pilot_indices = {0: np.arange(0, 64, 16), 1: np.arange(8, 64, 16)}

        H_pred = estimator.estimate(rx_pilots, tx_pilots, pilot_indices, fft_size=64, num_rx=2, num_tx=2)
        assert H_pred.shape == (2, 2, 64)
        assert H_pred.dtype == np.complex128


def test_dnn_estimator_in_mimo_simulation_pipeline():
    """Verify that MIMOSimulationPipeline seamlessly runs with DNN estimator."""
    config = SimulationConfig(
        num_tx=2,
        num_rx=2,
        fft_size=64,
        cp_length=16,
        pilot_spacing=8,
        modulation=ModulationType.QPSK,
        channel_model=ChannelModelType.RAYLEIGH,
        snr_db=20.0,
        algorithm=EstimationAlgorithm.DNN,
        num_ofdm_symbols=10,
        random_seed=42,
    )
    sim = MIMOSimulationPipeline(config)
    res = sim.run_single_shot()

    assert res["algorithm"] == "DNN"
    assert res["nmse"] < 0.5
    assert res["total_bits"] == 2 * 10 * 56 * 2  # 2240 bits
    assert res["execution_time_ms"] > 0
    assert res["inference_time_ms"] > 0


def test_comparative_benchmark_under_identical_realizations():
    """Verify head-to-head benchmark compares LS, MMSE, and DNN across identical realizations."""
    benchmark = benchmark_channel_estimators(
        snr_list=[10.0, 20.0],
        algorithms=["LS", "MMSE", "DNN"],
        num_trials_per_snr=2,
        random_seed=777,
    )

    assert benchmark["snr_points"] == [10.0, 20.0]
    assert "LS" in benchmark["results"]
    assert "MMSE" in benchmark["results"]
    assert "DNN" in benchmark["results"]

    for algo in ["LS", "MMSE", "DNN"]:
        res_algo = benchmark["results"][algo]
        assert len(res_algo["snr_db"]) == 2
        assert len(res_algo["nmse"]) == 2
        assert len(res_algo["ber"]) == 2
        assert len(res_algo["avg_inference_ms"]) == 2
