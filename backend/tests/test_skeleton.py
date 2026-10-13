"""Unit tests for wireless simulation building blocks."""

import numpy as np
import pytest
from neuromimo.config import ModulationType, ChannelModelType
from neuromimo.wireless.modulation import QPSKModulation, QAM16Modulation
from neuromimo.wireless.ofdm import OFDMPipeline
from neuromimo.wireless.channel import WirelessChannel
from neuromimo.wireless.equalization import MIMOEqualizer
from neuromimo.estimation.ls import LSEstimator
from neuromimo.estimation.mmse import MMSEEstimator
from neuromimo.estimation.dnn import DNNEstimator, ChannelEstimationNet
from neuromimo.evaluation.metrics import calculate_ber, calculate_nmse


def test_qpsk_modulation_and_demodulation():
    mod = QPSKModulation()
    assert mod.bits_per_symbol == 2
    # Transmit test bits
    bits = np.array([0, 0, 0, 1, 1, 1, 1, 0], dtype=np.int32)
    symbols = mod.modulate(bits)
    assert len(symbols) == 4
    # Check unit average power
    power = np.mean(np.abs(symbols) ** 2)
    assert np.isclose(power, 1.0, atol=1e-3)
    # Demodulate without noise
    recovered = mod.demodulate(symbols)
    assert np.array_equal(bits, recovered)


def test_qam16_modulation_and_demodulation():
    mod = QAM16Modulation()
    assert mod.bits_per_symbol == 4
    # Full constellation average power must be exactly 1.0
    const_power = np.mean(np.abs(mod.constellation) ** 2)
    assert np.isclose(const_power, 1.0, atol=1e-6)

    # Test bit recovery without noise
    bits = np.random.randint(0, 2, size=64)
    symbols = mod.modulate(bits)
    assert len(symbols) == 16
    recovered = mod.demodulate(symbols)
    assert np.array_equal(bits, recovered)


def test_ofdm_pipeline_dimensions():
    fft_size = 64
    cp_length = 16
    pilot_spacing = 8
    ofdm = OFDMPipeline(fft_size=fft_size, cp_length=cp_length, pilot_spacing=pilot_spacing)
    
    assert ofdm.num_pilots == 8
    assert ofdm.num_data == 56

    # Test assemble and cyclic prefix insertion/removal
    num_symbols = 4
    data_payload = np.ones((num_symbols, ofdm.num_data), dtype=np.complex128)
    freq_frame, pilots = ofdm.assemble_ofdm_frame(data_payload)
    assert freq_frame.shape == (num_symbols, fft_size)

    time_signal = ofdm.modulate(freq_frame)
    assert time_signal.shape == (num_symbols, fft_size + cp_length)

    freq_rx = ofdm.demodulate(time_signal)
    assert freq_rx.shape == (num_symbols, fft_size)
    assert np.allclose(freq_frame, freq_rx, atol=1e-6)


def test_wireless_channel_and_estimation_shapes():
    num_tx = 2
    num_rx = 2
    fft_size = 64
    channel = WirelessChannel(num_tx=num_tx, num_rx=num_rx, num_taps=4, fft_size=fft_size, random_seed=42)
    
    h_time, H_freq = channel.generate_channel_response()
    assert h_time.shape == (num_rx, num_tx, 4)
    assert H_freq.shape == (num_rx, num_tx, fft_size)

    # Test LS and MMSE estimation output dimensions
    num_pilots = 8
    pilot_indices = np.arange(0, fft_size, 8)
    tx_pilots = np.ones((num_tx, num_pilots), dtype=np.complex128)
    rx_pilots = np.ones((num_rx, num_tx, num_pilots), dtype=np.complex128)

    ls_est = LSEstimator()
    H_ls = ls_est.estimate(rx_pilots, tx_pilots, pilot_indices, fft_size)
    assert H_ls.shape == (num_rx, num_tx, fft_size)

    mmse_est = MMSEEstimator()
    H_mmse = mmse_est.estimate(rx_pilots, tx_pilots, pilot_indices, fft_size, noise_var=0.01)
    assert H_mmse.shape == (num_rx, num_tx, fft_size)

    dnn_est = DNNEstimator(fft_size=fft_size, num_rx=num_rx, num_tx=num_tx)
    H_dnn = dnn_est.estimate(rx_pilots, tx_pilots, pilot_indices, fft_size)
    assert H_dnn.shape == (num_rx, num_tx, fft_size)


def test_metrics_calculation():
    b_true = np.array([0, 1, 1, 0, 1])
    b_pred = np.array([0, 1, 0, 0, 1])
    ber = calculate_ber(b_true, b_pred)
    assert np.isclose(ber, 0.2)

    H_true = np.ones((2, 2, 64), dtype=np.complex128)
    H_pred = np.ones((2, 2, 64), dtype=np.complex128)
    nmse = calculate_nmse(H_true, H_pred)
    assert nmse == 0.0
