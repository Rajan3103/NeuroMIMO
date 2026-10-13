"""Unit and integration tests for the NeuroMIMO experimental evaluation module.

Tests metric calculations, statistical confidence intervals, and runs an end-to-end
smoke test of the ExperimentRunner across wireless environments and estimators.
"""

import os
import json
import csv
import tempfile
import numpy as np
import pytest

from neuromimo.config import ChannelModelType, ModulationType
from neuromimo.evaluation.metrics import (
    calculate_mse,
    calculate_nmse,
    calculate_nmse_db,
    calculate_ber,
    calculate_ser,
    compute_confidence_interval_ber,
    SimulationMetrics,
)
from neuromimo.evaluation.experiments import ExperimentRunner


# =============================================================================
# 1. Metric Calculation Unit Tests
# =============================================================================

class TestMetricCalculations:
    """Tests accuracy, boundary conditions, and edge cases of signal metrics."""

    def test_calculate_mse_identical(self):
        arr = np.array([1.0 + 2.0j, -0.5 + 0.5j])
        mse = calculate_mse(arr, arr)
        assert mse == 0.0

    def test_calculate_mse_known_difference(self):
        h_true = np.array([1.0, 2.0])
        h_est = np.array([2.0, 4.0])
        # Errors: [1, 2] -> Squared errors: [1, 4] -> Mean: 2.5
        mse = calculate_mse(h_true, h_est)
        assert np.isclose(mse, 2.5)

    def test_calculate_mse_complex_numbers(self):
        h_true = np.array([1.0 + 1.0j])
        h_est = np.array([2.0 + 2.0j])
        # Difference: 1 + 1j -> |1+1j|^2 = 1^2 + 1^2 = 2.0
        assert np.isclose(calculate_mse(h_true, h_est), 2.0)

    def test_calculate_nmse_zero_error(self):
        h_true = np.array([3.0 - 4.0j, 1.0 + 1.0j])
        nmse = calculate_nmse(h_true, h_true)
        assert nmse == 0.0

        nmse_db = calculate_nmse_db(h_true, h_true)
        # Clamped at 1e-12 (-120 dB)
        assert nmse_db <= -119.0

    def test_calculate_nmse_known_ratio(self):
        h_true = np.array([2.0 + 0.0j])
        h_est = np.array([1.0 + 0.0j])
        # Error energy = |1|^2 = 1.0, True energy = |2|^2 = 4.0 -> NMSE = 0.25 (-6.0206 dB)
        assert np.isclose(calculate_nmse(h_true, h_est), 0.25)
        assert np.isclose(calculate_nmse_db(h_true, h_est), 10.0 * np.log10(0.25))

    def test_calculate_nmse_zero_true_energy(self):
        h_true = np.zeros(5, dtype=np.complex128)
        h_est = np.ones(5, dtype=np.complex128)
        assert calculate_nmse(h_true, h_est) == 0.0

    def test_calculate_ber_identical(self):
        bits = np.array([0, 1, 1, 0, 1, 0])
        assert calculate_ber(bits, bits) == 0.0

    def test_calculate_ber_all_inverted(self):
        b1 = np.array([0, 0, 1, 1])
        b2 = np.array([1, 1, 0, 0])
        assert calculate_ber(b1, b2) == 1.0

    def test_calculate_ber_partial_errors(self):
        b1 = np.array([0, 1, 0, 1, 0, 1, 0, 1])
        b2 = np.array([0, 1, 1, 1, 0, 0, 0, 1])  # 2 errors out of 8 bits
        assert np.isclose(calculate_ber(b1, b2), 0.25)

    def test_calculate_ber_empty(self):
        assert calculate_ber(np.array([]), np.array([])) == 0.0

    def test_calculate_ser_identical(self):
        syms = np.array([0.707 + 0.707j, -0.707 + 0.707j])
        assert calculate_ser(syms, syms) == 0.0

    def test_calculate_ser_noise_within_threshold(self):
        syms = np.array([1.0 + 0.0j])
        noisy = np.array([1.0001 + 0.0001j])
        assert calculate_ser(syms, noisy, threshold=1e-2) == 0.0

    def test_calculate_ser_noise_outside_threshold(self):
        syms = np.array([1.0 + 0.0j, -1.0 + 0.0j])
        noisy = np.array([1.1 + 0.0j, -1.0 + 0.0j])
        assert np.isclose(calculate_ser(syms, noisy, threshold=1e-2), 0.5)

    def test_calculate_ser_empty(self):
        assert calculate_ser(np.array([]), np.array([])) == 0.0


class TestConfidenceIntervalCalculation:
    """Tests statistical confidence interval reporting for Monte Carlo BER estimation."""

    def test_zero_bits_transmitted(self):
        ci = compute_confidence_interval_ber(0, 0)
        assert ci["ber"] == 0.0
        assert ci["is_conclusive"] is False

    def test_zero_errors_small_sample(self):
        # 0 errors in 500 bits: not enough sample size for conclusive low BER
        ci = compute_confidence_interval_ber(0, 500)
        assert ci["ber"] == 0.0
        assert ci["is_conclusive"] is False
        assert np.isclose(ci["ci_upper"], 3.0 / 500)

    def test_zero_errors_large_sample(self):
        # 0 errors in 20,000 bits: rule of three guarantees < 1.5e-4
        ci = compute_confidence_interval_ber(0, 20000)
        assert ci["ber"] == 0.0
        assert ci["is_conclusive"] is True
        assert np.isclose(ci["ci_upper"], 3.0 / 20000)

    def test_few_errors_inconclusive(self):
        # 3 errors in 1000 bits: fewer than 10 error events
        ci = compute_confidence_interval_ber(3, 1000)
        assert ci["ber"] == 0.003
        assert ci["is_conclusive"] is False

    def test_sufficient_errors_conclusive(self):
        # 50 errors in 1000 bits: >= 10 error events
        ci = compute_confidence_interval_ber(50, 1000)
        assert ci["ber"] == 0.05
        assert ci["is_conclusive"] is True
        assert ci["ci_lower"] < 0.05 < ci["ci_upper"]


# =============================================================================
# 2. ExperimentRunner Smoke Test & Reproduction
# =============================================================================

class TestExperimentRunnerSmoke:
    """Verifies that ExperimentRunner executes all required evaluations and saves artifacts."""

    @pytest.fixture
    def temp_runner(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            runner = ExperimentRunner(output_dir=tmp_dir, random_seed=42)
            yield runner, tmp_dir

    def test_snr_sweep_execution_and_exports(self, temp_runner):
        runner, tmp_dir = temp_runner
        snr_list = [10.0, 20.0]
        algos = ["LS", "MMSE", "DNN", "PERFECT"]

        res = runner.run_snr_sweep_experiment(
            snr_list=snr_list,
            algorithms=algos,
            channel_type=ChannelModelType.RAYLEIGH,
            num_trials_per_snr=2,
            num_ofdm_symbols=4,
        )

        assert res["experiment_name"].startswith("snr_sweep")
        assert res["snr_points"] == snr_list
        for algo in algos:
            records = res["records"][algo]
            assert len(records) == len(snr_list)
            for r in records:
                if r.get("available") is not False:
                    assert "nmse" in r
                    assert "nmse_db" in r
                    assert "ber" in r
                    assert "bit_errors" in r
                    assert "total_bits" in r
                    assert r["total_bits"] > 0
                    assert r["bit_errors"] <= r["total_bits"]
                    assert "statistically_conclusive" in r

        # Test JSON and CSV persistence
        json_path = runner.save_results_to_json(res, "test_snr.json")
        assert os.path.exists(json_path)
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["experiment_name"] == res["experiment_name"]

        csv_path = runner.save_results_to_csv(res, "test_snr.csv")
        assert os.path.exists(csv_path)
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert "algorithm" in headers
            assert "nmse_db" in headers
            assert "ber" in headers
            rows = list(reader)
            assert len(rows) > 0

        # Test plot generation
        nmse_plot = runner.plot_nmse_vs_snr(res, "test_nmse.png")
        assert os.path.exists(nmse_plot)
        assert os.path.getsize(nmse_plot) > 1000  # Valid PNG file

        ber_plot = runner.plot_ber_vs_snr(res, "test_ber.png")
        assert os.path.exists(ber_plot)
        assert os.path.getsize(ber_plot) > 1000

    def test_channel_model_comparison_execution(self, temp_runner):
        runner, tmp_dir = temp_runner
        res = runner.run_channel_model_comparison_experiment(
            snr_list=[15.0],
            algorithms=["LS", "MMSE"],
            num_trials_per_snr=1,
        )

        assert "rayleigh_records" in res
        assert "awgn_records" in res
        plot_path = runner.plot_channel_model_comparison(res, "test_channel_comp.png")
        assert os.path.exists(plot_path)
        assert os.path.getsize(plot_path) > 1000

    def test_generalization_execution(self, temp_runner):
        runner, tmp_dir = temp_runner
        res = runner.run_generalization_experiment(
            snr_db=15.0,
            num_trials=1,
            pdp_decays=[0.8, 1.5],
            taps_list=[4],
        )

        assert "conditions" in res
        assert len(res["conditions"]) == 2
        for cond in res["conditions"]:
            assert "metrics" in cond
            assert "LS" in cond["metrics"]
            assert "MMSE" in cond["metrics"]

        plot_path = runner.plot_generalization_comparison(res, "test_gen.png")
        assert os.path.exists(plot_path)
        assert os.path.getsize(plot_path) > 1000

    def test_inference_time_profiling(self, temp_runner):
        runner, tmp_dir = temp_runner
        res = runner.run_inference_time_experiment(
            num_iterations=5,
            num_warmup=1,
        )

        assert "results" in res
        assert "LS" in res["results"]
        assert "MMSE" in res["results"]
        for algo, stats in res["results"].items():
            assert "mean_ms" in stats
            assert stats["mean_ms"] >= 0.0
            assert "throughput_fps" in stats

        plot_path = runner.plot_inference_runtime_comparison(res, "test_timing.png")
        assert os.path.exists(plot_path)
        assert os.path.getsize(plot_path) > 1000

    def test_pilot_density_execution(self, temp_runner):
        runner, tmp_dir = temp_runner
        res = runner.run_pilot_density_experiment(
            pilot_spacings=[4, 8],
            snr_db=15.0,
            algorithms=["LS", "MMSE"],
            num_trials=1,
        )

        assert "results" in res
        assert "LS" in res["results"]
        assert len(res["results"]["LS"]) == 2
        plot_path = runner.plot_pilot_density_comparison(res, "test_pilot_density.png")
        assert os.path.exists(plot_path)
        assert os.path.getsize(plot_path) > 1000
