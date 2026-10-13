"""Comprehensive unit tests for the complete wireless communication simulation backend."""

import numpy as np
import pytest

from neuromimo.config import (
    SimulationConfig,
    ModulationType,
    ChannelModelType,
    EstimationAlgorithm,
    EqualizerType,
)
from neuromimo.wireless.modulation import (
    QPSKModulation,
    QAM16Modulation,
    generate_random_bits,
    get_modulator,
)
from neuromimo.wireless.ofdm import OFDMPipeline
from neuromimo.wireless.channel import WirelessChannel
from neuromimo.wireless.equalization import MIMOEqualizer
from neuromimo.estimation.ls import LSEstimator
from neuromimo.estimation.mmse import MMSEEstimator
from neuromimo.wireless.simulation import MIMOSimulationPipeline
from neuromimo.evaluation.metrics import (
    calculate_mse,
    calculate_nmse,
    calculate_ber,
    calculate_ser,
)


def test_random_bit_generation_and_reproducibility():
    """Verify bit generation values and reproducibility with fixed seeds."""
    rng1 = np.random.RandomState(1234)
    bits1 = generate_random_bits(100, rng=rng1)
    assert len(bits1) == 100
    assert set(np.unique(bits1)).issubset({0, 1})

    rng2 = np.random.RandomState(1234)
    bits2 = generate_random_bits(100, rng=rng2)
    assert np.array_equal(bits1, bits2)


def test_qpsk_properties_and_demodulation():
    """Verify QPSK constellation power = 1.0, 2 bits/symbol, and noise-free recovery."""
    qpsk = QPSKModulation()
    assert qpsk.bits_per_symbol == 2
    pts = qpsk.constellation
    assert len(pts) == 4
    # Check exact unit average power
    assert np.isclose(np.mean(np.abs(pts) ** 2), 1.0, atol=1e-7)

    # Demodulate every constellation point directly
    for b0 in [0, 1]:
        for b1 in [0, 1]:
            b_in = np.array([b0, b1], dtype=np.int32)
            sym = qpsk.modulate(b_in)
            b_out = qpsk.demodulate(sym)
            assert np.array_equal(b_in, b_out)


def test_qam16_properties_and_demodulation():
    """Verify 16-QAM average power = 1.0, 4 bits/symbol, and noise-free recovery."""
    qam = QAM16Modulation()
    assert qam.bits_per_symbol == 4
    pts = qam.constellation
    assert len(pts) == 16
    assert np.isclose(np.mean(np.abs(pts) ** 2), 1.0, atol=1e-7)

    bits = np.random.randint(0, 2, size=64)
    syms = qam.modulate(bits)
    assert len(syms) == 16
    rec = qam.demodulate(syms)
    assert np.array_equal(bits, rec)


def test_ofdm_multi_antenna_assembly_and_dimensions():
    """Verify orthogonal comb pilot allocation and frame assembly across 2 Tx antennas."""
    num_tx = 2
    fft_size = 64
    cp_length = 16
    pilot_spacing = 8
    ofdm = OFDMPipeline(
        num_tx=num_tx,
        fft_size=fft_size,
        cp_length=cp_length,
        pilot_spacing=pilot_spacing,
    )

    # Check total pilots and data subcarrier counts
    assert ofdm.num_total_pilots == 8
    assert ofdm.num_data == 56

    # Verify disjoint orthogonal pilot allocation between antennas
    p0 = ofdm.pilot_indices_per_tx[0]
    p1 = ofdm.pilot_indices_per_tx[1]
    assert len(p0) == 4
    assert len(p1) == 4
    assert len(np.intersect1d(p0, p1)) == 0  # Zero overlap
    assert len(np.intersect1d(p0, ofdm.data_indices)) == 0

    # Test assemble frame
    num_sym = 10
    data_payload = np.ones((num_tx, num_sym, ofdm.num_data), dtype=np.complex128)
    tx_freq = ofdm.assemble_mimo_frame(data_payload)
    assert tx_freq.shape == (num_tx, num_sym, fft_size)

    # Verify antenna 0 has zero power on antenna 1 pilot tones
    assert np.all(tx_freq[0, :, p1] == 0.0)
    assert np.all(tx_freq[1, :, p0] == 0.0)

    # Verify modulation and demodulation invertibility
    tx_time = ofdm.modulate(tx_freq)
    assert tx_time.shape == (num_tx, num_sym, fft_size + cp_length)
    rx_demod = ofdm.demodulate(tx_time)
    assert rx_demod.shape == (num_tx, num_sym, fft_size)
    assert np.allclose(tx_freq, rx_demod, atol=1e-6)


def test_channel_pdp_and_snr_calibration():
    """Verify Rayleigh channel power delay profile normalization and noise variance scaling."""
    num_tx = 2
    num_rx = 2
    num_taps = 4
    fft_size = 64
    channel = WirelessChannel(
        num_tx=num_tx,
        num_rx=num_rx,
        num_taps=num_taps,
        fft_size=fft_size,
        random_seed=777,
    )

    # Check PDP sum = 1.0
    assert np.isclose(np.sum(channel.pdp), 1.0, atol=1e-7)

    # Check CIR and CFR shapes
    h_time, H_freq = channel.generate_channel_response()
    assert h_time.shape == (num_rx, num_tx, num_taps)
    assert H_freq.shape == (num_rx, num_tx, fft_size)

    # Test noise variance scaling: 20 dB vs 10 dB should differ by ~10x
    tx_freq = np.ones((num_tx, 14, fft_size), dtype=np.complex128)
    _, var_20 = channel.apply_channel(tx_freq, H_freq, snr_db=20.0)
    _, var_10 = channel.apply_channel(tx_freq, H_freq, snr_db=10.0)
    ratio = var_10 / var_20
    assert np.isclose(ratio, 10.0, rtol=0.1)


def test_mimo_equalizer_noiseless_recovery():
    """Verify that Zero-Forcing and MMSE equalizers perfectly invert spatial channel when noiseless."""
    num_rx = 2
    num_tx = 2
    num_tones = 56
    num_symbols = 14

    # Generate random well-conditioned channel matrix per tone
    rng = np.random.RandomState(999)
    H = (rng.randn(num_rx, num_tx, num_tones) + 1j * rng.randn(num_rx, num_tx, num_tones)) / np.sqrt(2)

    # Generate transmitted symbols
    tx_symbols = (rng.choice([-1, 1], size=(num_tx, num_symbols, num_tones)) +
                  1j * rng.choice([-1, 1], size=(num_tx, num_symbols, num_tones))) / np.sqrt(2)

    # Noiseless channel application
    rx_symbols = np.einsum("rtk,tsk->rsk", H, tx_symbols)

    # Zero-Forcing equalization
    recovered_zf = MIMOEqualizer.equalize(rx_symbols, H, noise_var=0.0, method=EqualizerType.ZERO_FORCING)
    assert np.allclose(tx_symbols, recovered_zf, atol=1e-6)

    # MMSE equalization with small regularization
    recovered_mmse = MIMOEqualizer.equalize(rx_symbols, H, noise_var=1e-9, method=EqualizerType.MMSE)
    assert np.allclose(tx_symbols, recovered_mmse, atol=1e-5)


def test_ls_and_mmse_estimators_high_snr():
    """Test LS and MMSE channel estimation accuracy under high SNR."""
    config = SimulationConfig(
        num_tx=2,
        num_rx=2,
        fft_size=64,
        cp_length=16,
        pilot_spacing=8,
        snr_db=30.0,
        random_seed=42,
    )
    ofdm = OFDMPipeline(num_tx=2, fft_size=64, pilot_spacing=8)
    channel = WirelessChannel(num_tx=2, num_rx=2, fft_size=64, random_seed=42)

    tx_payload = np.ones((2, 14, ofdm.num_data), dtype=np.complex128)
    tx_freq = ofdm.assemble_mimo_frame(tx_payload)
    _, H_true = channel.generate_channel_response()
    rx_freq, noise_var = channel.apply_channel(tx_freq, H_true, snr_db=30.0)
    rx_pilots_dict, _ = ofdm.extract_pilots_and_data(rx_freq)

    # LS estimation
    ls_est = LSEstimator()
    H_ls = ls_est.estimate(
        rx_pilots_dict,
        ofdm.known_pilots_per_tx,
        ofdm.pilot_indices_per_tx,
        fft_size=64,
    )
    assert H_ls.shape == (2, 2, 64)
    nmse_ls = calculate_nmse(H_true, H_ls)
    # Under 30 dB, NMSE should be low (< 0.1)
    assert nmse_ls < 0.1

    # MMSE estimation
    mmse_est = MMSEEstimator(channel_pdp=channel.pdp)
    H_mmse = mmse_est.estimate(
        rx_pilots_dict,
        ofdm.known_pilots_per_tx,
        ofdm.pilot_indices_per_tx,
        fft_size=64,
        noise_var=noise_var,
    )
    assert H_mmse.shape == (2, 2, 64)
    nmse_mmse = calculate_nmse(H_true, H_mmse)
    assert nmse_mmse < 0.1


def test_end_to_end_simulation_perfect_csi():
    """Verify that with Perfect CSI and high SNR (30 dB), BER is minimal (< 0.005)."""
    config = SimulationConfig(
        num_tx=2,
        num_rx=2,
        fft_size=64,
        cp_length=16,
        pilot_spacing=8,
        modulation=ModulationType.QPSK,
        channel_model=ChannelModelType.RAYLEIGH,
        snr_db=30.0,
        algorithm=EstimationAlgorithm.PERFECT,
        num_ofdm_symbols=14,
        random_seed=101,
    )
    pipeline = MIMOSimulationPipeline(config)
    res = pipeline.run_single_shot()

    assert res["total_bits"] == 2 * 14 * 56 * 2  # 3136 bits
    assert res["nmse"] == 0.0  # Perfect CSI
    assert res["ber"] < 0.005  # High SNR with perfect channel inversion
    assert res["execution_time_ms"] > 0


def test_end_to_end_simulation_with_ls_and_mmse():
    """Verify single shot simulation execution for LS and MMSE estimators."""
    for algo in [EstimationAlgorithm.LS, EstimationAlgorithm.MMSE]:
        config = SimulationConfig(
            num_tx=2,
            num_rx=2,
            fft_size=64,
            cp_length=16,
            pilot_spacing=8,
            modulation=ModulationType.QPSK,
            channel_model=ChannelModelType.RAYLEIGH,
            snr_db=25.0,
            algorithm=algo,
            num_ofdm_symbols=14,
            random_seed=202,
        )
        pipeline = MIMOSimulationPipeline(config)
        res = pipeline.run_single_shot()

        assert res["total_bits"] > 0
        assert res["nmse"] < 0.25
        assert res["ber"] < 0.15
        assert len(res["tx_constellation_sample"]) > 0
        assert len(res["rx_constellation_sample"]) > 0
        assert len(res["channel_magnitude_profile"]) == 64


def test_snr_sweep_monotonicity():
    """Verify that average NMSE monotonically decreases as SNR increases."""
    config = SimulationConfig(
        num_tx=2,
        num_rx=2,
        fft_size=64,
        cp_length=16,
        pilot_spacing=8,
        modulation=ModulationType.QPSK,
        channel_model=ChannelModelType.RAYLEIGH,
        snr_db=10.0,
        algorithm=EstimationAlgorithm.LS,
        num_ofdm_symbols=10,
        random_seed=303,
    )
    pipeline = MIMOSimulationPipeline(config)
    sweep_results = pipeline.sweep_snr(snr_list=[5.0, 15.0, 25.0], num_trials_per_snr=3)

    assert len(sweep_results) == 3
    nmse_5 = sweep_results[0]["nmse"]
    nmse_15 = sweep_results[1]["nmse"]
    nmse_25 = sweep_results[2]["nmse"]

    # Higher SNR must yield lower NMSE
    assert nmse_5 > nmse_15
    assert nmse_15 > nmse_25
