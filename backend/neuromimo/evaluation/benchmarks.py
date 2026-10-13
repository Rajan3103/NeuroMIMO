"""Comparative benchmarking engine evaluating LS, MMSE, and DNN estimators under identical channel realizations."""

import time
from typing import Dict, Any, List, Optional
import numpy as np

from ..config import (
    SimulationConfig,
    EstimationAlgorithm,
    ChannelModelType,
    ModulationType,
    EqualizerType,
)
from ..wireless.ofdm import OFDMPipeline
from ..wireless.channel import WirelessChannel
from ..wireless.modulation import get_modulator, generate_random_bits
from ..wireless.equalization import MIMOEqualizer
from ..estimation.ls import LSEstimator
from ..estimation.mmse import MMSEEstimator
from ..estimation.dnn import DNNEstimator, DEFAULT_CHECKPOINT_PATH
from ..evaluation.metrics import (
    calculate_mse,
    calculate_nmse,
    calculate_ber,
    calculate_ser,
)


def benchmark_channel_estimators(
    snr_list: Optional[List[float]] = None,
    algorithms: Optional[List[str]] = None,
    num_trials_per_snr: int = 10,
    config: Optional[SimulationConfig] = None,
    checkpoint_path: Optional[str] = None,
    random_seed: int = 42,
) -> Dict[str, Any]:
    """Evaluates channel estimators across SNRs using identical test realizations.

    Crucial Engineering Constraint:
    All algorithms (LS, MMSE, DNN) process the exact same transmitted frames,
    identical channel realizations H, and identical noise vectors W at each trial.
    This guarantees zero realization bias across comparisons.
    """
    if snr_list is None:
        snr_list = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
    if algorithms is None:
        algorithms = ["LS", "MMSE", "DNN"]
    if config is None:
        config = SimulationConfig(
            num_tx=2,
            num_rx=2,
            fft_size=64,
            cp_length=16,
            pilot_spacing=8,
            modulation=ModulationType.QPSK,
            channel_model=ChannelModelType.RAYLEIGH,
            num_channel_taps=4,
            num_ofdm_symbols=14,
            random_seed=random_seed,
        )

    # Initialize components
    ofdm = OFDMPipeline(
        num_tx=config.num_tx,
        fft_size=config.fft_size,
        cp_length=config.cp_length,
        pilot_spacing=config.pilot_spacing,
    )
    modulator = get_modulator(config.modulation)

    # Initialize estimators
    estimators: Dict[str, Any] = {}
    if "LS" in algorithms:
        estimators["LS"] = LSEstimator()
    if "MMSE" in algorithms:
        taps = np.arange(config.num_channel_taps)
        pdp = np.exp(-taps / 1.5)
        estimators["MMSE"] = MMSEEstimator(channel_pdp=pdp / np.sum(pdp))
    if "DNN" in algorithms:
        ckpt = checkpoint_path or DEFAULT_CHECKPOINT_PATH
        estimators["DNN"] = DNNEstimator(
            model_path=ckpt,
            fft_size=config.fft_size,
            num_rx=config.num_rx,
            num_tx=config.num_tx,
        )

    # Storage for accumulated results
    benchmark_data: Dict[str, Dict[str, List[float]]] = {
        algo: {
            "snr_db": [],
            "nmse": [],
            "nmse_db": [],
            "ber": [],
            "ser": [],
            "avg_inference_ms": [],
        }
        for algo in algorithms
    }

    num_symbols = config.num_ofdm_symbols
    total_data_symbols_per_tx = num_symbols * ofdm.num_data
    total_bits_per_tx = total_data_symbols_per_tx * modulator.bits_per_symbol

    for snr in snr_list:
        # Pre-seed trial RNG so all SNRs experience deterministic test sequences
        rng = np.random.RandomState(random_seed + int(snr * 10))

        algo_metrics: Dict[str, Dict[str, float]] = {
            algo: {"nmse": 0.0, "ber": 0.0, "ser": 0.0, "time_ms": 0.0}
            for algo in algorithms
        }

        for _ in range(num_trials_per_snr):
            # 1. Transmit payload
            tx_bits = np.zeros((config.num_tx, total_bits_per_tx), dtype=np.int32)
            tx_data_symbols = np.zeros(
                (config.num_tx, num_symbols, ofdm.num_data), dtype=np.complex128
            )
            for t in range(config.num_tx):
                tx_bits[t] = generate_random_bits(total_bits_per_tx, rng=rng)
                tx_data_symbols[t] = modulator.modulate(tx_bits[t]).reshape(
                    num_symbols, ofdm.num_data
                )

            tx_freq = ofdm.assemble_mimo_frame(tx_data_symbols)

            # 2. Independent channel realization
            channel = WirelessChannel(
                num_tx=config.num_tx,
                num_rx=config.num_rx,
                num_taps=config.num_channel_taps,
                fft_size=config.fft_size,
                channel_type=config.channel_model,
                random_seed=int(rng.randint(0, 1000000)),
            )
            _, H_freq_true = channel.generate_channel_response()

            # 3. Channel propagation with calibrated AWGN noise
            rx_freq, noise_var = channel.apply_channel(tx_freq, H_freq_true, snr_db=snr)

            # 4. Extract pilot observations and data tones
            rx_pilots_dict, rx_data = ofdm.extract_pilots_and_data(rx_freq)

            # 5. Run each algorithm on the EXACT same observations
            for algo in algorithms:
                t0 = time.perf_counter()
                if algo == "PERFECT":
                    H_est = H_freq_true.copy()
                elif algo == "LS":
                    H_est = estimators["LS"].estimate(
                        rx_pilots=rx_pilots_dict,
                        tx_pilots=ofdm.known_pilots_per_tx,
                        pilot_indices=ofdm.pilot_indices_per_tx,
                        fft_size=config.fft_size,
                        num_rx=config.num_rx,
                        num_tx=config.num_tx,
                    )
                elif algo == "MMSE":
                    H_est = estimators["MMSE"].estimate(
                        rx_pilots=rx_pilots_dict,
                        tx_pilots=ofdm.known_pilots_per_tx,
                        pilot_indices=ofdm.pilot_indices_per_tx,
                        fft_size=config.fft_size,
                        noise_var=noise_var,
                        num_rx=config.num_rx,
                        num_tx=config.num_tx,
                    )
                elif algo == "DNN":
                    H_est = estimators["DNN"].estimate(
                        rx_pilots=rx_pilots_dict,
                        tx_pilots=ofdm.known_pilots_per_tx,
                        pilot_indices=ofdm.pilot_indices_per_tx,
                        fft_size=config.fft_size,
                        noise_var=noise_var,
                        num_rx=config.num_rx,
                        num_tx=config.num_tx,
                    )
                inf_time = (time.perf_counter() - t0) * 1000.0

                # NMSE evaluation
                nmse = calculate_nmse(H_freq_true, H_est)

                # Equalization on data tones
                H_data_est = H_est[:, :, ofdm.data_indices]
                eq_method = EqualizerType.MMSE if snr < 15.0 else EqualizerType.ZERO_FORCING
                rx_eq = MIMOEqualizer.equalize(
                    rx_symbols=rx_data,
                    H_est=H_data_est,
                    noise_var=noise_var,
                    method=eq_method,
                )

                # Demodulation & BER evaluation
                rec_bits = np.zeros_like(tx_bits)
                for t in range(config.num_tx):
                    rec_bits[t] = modulator.demodulate(rx_eq[t].flatten())

                ber = calculate_ber(tx_bits, rec_bits)
                ser = calculate_ser(tx_data_symbols, rx_eq)

                algo_metrics[algo]["nmse"] += nmse
                algo_metrics[algo]["ber"] += ber
                algo_metrics[algo]["ser"] += ser
                algo_metrics[algo]["time_ms"] += inf_time

        # Record averaged metrics at this SNR point
        for algo in algorithms:
            avg_nmse = algo_metrics[algo]["nmse"] / num_trials_per_snr
            avg_ber = algo_metrics[algo]["ber"] / num_trials_per_snr
            avg_ser = algo_metrics[algo]["ser"] / num_trials_per_snr
            avg_time = algo_metrics[algo]["time_ms"] / num_trials_per_snr

            benchmark_data[algo]["snr_db"].append(float(snr))
            benchmark_data[algo]["nmse"].append(float(avg_nmse))
            benchmark_data[algo]["nmse_db"].append(
                float(10.0 * np.log10(max(avg_nmse, 1e-12)))
            )
            benchmark_data[algo]["ber"].append(float(avg_ber))
            benchmark_data[algo]["ser"].append(float(avg_ser))
            benchmark_data[algo]["avg_inference_ms"].append(float(avg_time))

    return {
        "snr_points": [float(s) for s in snr_list],
        "algorithms": algorithms,
        "results": benchmark_data,
    }
