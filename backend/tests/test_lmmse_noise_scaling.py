"""Regression tests for the LMMSE noise level after pilot averaging."""

import numpy as np
import pytest

from neuromimo.config import EstimationAlgorithm, SimulationConfig
from neuromimo.wireless.ofdm import OFDMPipeline
from neuromimo.wireless.simulation import MIMOSimulationPipeline


def _mean_nmse_db(algorithm: EstimationAlgorithm, snr_db: float, trials: int = 30) -> float:
    pipeline = MIMOSimulationPipeline(SimulationConfig(algorithm=algorithm, snr_db=snr_db))
    pipeline.channel.rng = np.random.RandomState(42)
    nmse = [pipeline.run_single_shot()["nmse"] for _ in range(trials)]
    return float(10 * np.log10(np.mean(nmse)))


def test_pilot_noise_variance_accounts_for_symbol_averaging():
    assert OFDMPipeline.pilot_noise_variance(1.4, 14) == pytest.approx(0.1)


def test_lmmse_beats_ls_at_low_snr():
    # Theory: with correct noise statistics LMMSE is never worse than LS
    assert _mean_nmse_db(EstimationAlgorithm.MMSE, 0.0) < _mean_nmse_db(EstimationAlgorithm.LS, 0.0)


def test_lmmse_matches_ls_at_high_snr():
    gap = _mean_nmse_db(EstimationAlgorithm.MMSE, 30.0) - _mean_nmse_db(EstimationAlgorithm.LS, 30.0)
    assert abs(gap) < 0.5
