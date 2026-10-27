"""End-to-end MIMO-OFDM wireless simulation pipeline.

Executes complete transmission rounds:
1. Random bit generation
2. QPSK / 16-QAM Gray modulation
3. Multi-antenna comb pilot insertion and OFDM frame assembly
4. IFFT modulation and cyclic prefix (CP) insertion
5. Multipath Rayleigh fading or AWGN channel propagation
6. Calibrated AWGN noise injection based on SNR (dB)
7. CP removal and FFT demodulation
8. Pilot extraction and Channel Estimation (LS, MMSE, DNN, PERFECT)
9. Channel estimation evaluation (MSE, NMSE, NMSE_dB) against known ground truth
10. MIMO spatial equalization (Zero-Forcing or MMSE)
11. Symbol demodulation and bit recovery
12. Statistical evaluation (BER, SER, bit errors, runtime)
"""

import time
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import numpy as np

from ..config import (
    SimulationConfig,
    ModulationType,
    ChannelModelType,
    EstimationAlgorithm,
    EqualizerType,
)
from .modulation import get_modulator, generate_random_bits
from .ofdm import OFDMPipeline
from .channel import WirelessChannel
from .equalization import MIMOEqualizer
from ..estimation.ls import LSEstimator
from ..estimation.mmse import MMSEEstimator
from ..estimation.dnn import DNNEstimator
from ..evaluation.metrics import (
    calculate_mse,
    calculate_nmse,
    calculate_ber,
    calculate_ser,
    SimulationMetrics,
)

if TYPE_CHECKING:
    from .deepmimo import DeepMIMOChannelSet


class MIMOSimulationPipeline:
    """Orchestrates end-to-end physical-layer MIMO-OFDM simulation rounds."""

    def __init__(
        self,
        config: SimulationConfig,
        channel_set: Optional["DeepMIMOChannelSet"] = None,
    ) -> None:
        """Args:
            config: Simulation parameters.
            channel_set: Optional DeepMIMO channels that replace the synthetic channel model.
        """
        self.config = config
        self.ofdm = OFDMPipeline(
            num_tx=config.num_tx,
            fft_size=config.fft_size,
            cp_length=config.cp_length,
            pilot_spacing=config.pilot_spacing,
        )
        self.channel = WirelessChannel(
            num_tx=config.num_tx,
            num_rx=config.num_rx,
            num_taps=config.num_channel_taps,
            fft_size=config.fft_size,
            channel_type=config.channel_model,
            random_seed=config.random_seed,
            channel_set=channel_set,
        )
        self.modulator = get_modulator(config.modulation)
        self._init_estimator(config.algorithm)

    def _init_estimator(self, algo: EstimationAlgorithm) -> None:
        """Initializes requested channel estimation engine."""
        self.algorithm = algo
        if algo == EstimationAlgorithm.LS or algo == "LS":
            self.estimator = LSEstimator()
        elif algo == EstimationAlgorithm.MMSE or algo == "MMSE":
            self.estimator = MMSEEstimator(
                channel_pdp=self.channel.pdp,
                num_taps=len(self.channel.pdp),
            )
        elif algo == EstimationAlgorithm.DNN or algo == "DNN":
            self.estimator = DNNEstimator(
                fft_size=self.config.fft_size,
                num_rx=self.config.num_rx,
                num_tx=self.config.num_tx,
            )
        else:
            self.estimator = None  # PERFECT CSI

    def run_single_shot(self) -> Dict[str, Any]:
        """Runs a complete end-to-end transmission slot and evaluates performance."""
        start_time = time.perf_counter()

        num_tx = self.config.num_tx
        num_rx = self.config.num_rx
        num_symbols = self.config.num_ofdm_symbols
        num_data_tones = self.ofdm.num_data
        bits_per_sym = self.modulator.bits_per_symbol

        # Step 1: Bit Generation
        total_data_symbols_per_tx = num_symbols * num_data_tones
        total_bits_per_tx = total_data_symbols_per_tx * bits_per_sym
        total_bits = num_tx * total_bits_per_tx

        tx_bits = np.zeros((num_tx, total_bits_per_tx), dtype=np.int32)
        for t in range(num_tx):
            tx_bits[t] = generate_random_bits(total_bits_per_tx, rng=self.channel.rng)

        # Step 2: Digital Modulation (QPSK / 16-QAM)
        tx_data_symbols = np.zeros((num_tx, num_symbols, num_data_tones), dtype=np.complex128)
        for t in range(num_tx):
            mod_syms = self.modulator.modulate(tx_bits[t])
            tx_data_symbols[t] = mod_syms.reshape(num_symbols, num_data_tones)

        # Step 3: MIMO-OFDM Frame Assembly with Orthogonal Comb Pilots
        tx_freq = self.ofdm.assemble_mimo_frame(tx_data_symbols)

        # Step 4: IFFT Modulation + Cyclic Prefix Insertion (Time-domain signal)
        tx_time = self.ofdm.modulate(tx_freq)

        # Step 5: Channel Generation (CIR & CFR Ground Truth)
        h_time, H_freq_true = self.channel.generate_channel_response()

        # Step 6: Channel Propagation + Calibrated AWGN Noise
        rx_freq, noise_var = self.channel.apply_channel(
            tx_freq=tx_freq,
            H_freq=H_freq_true,
            snr_db=self.config.snr_db,
        )

        # Step 7: Pilot Extraction
        rx_pilots_dict, rx_data = self.ofdm.extract_pilots_and_data(rx_freq)
        pilot_noise_var = self.ofdm.pilot_noise_variance(noise_var, rx_freq.shape[1])

        # Step 8: Channel Estimation
        est_start = time.perf_counter()
        if self.algorithm == EstimationAlgorithm.PERFECT or self.algorithm == "PERFECT":
            H_freq_est = H_freq_true.copy()
        elif self.algorithm == EstimationAlgorithm.LS or self.algorithm == "LS":
            H_freq_est = self.estimator.estimate(
                rx_pilots=rx_pilots_dict,
                tx_pilots=self.ofdm.known_pilots_per_tx,
                pilot_indices=self.ofdm.pilot_indices_per_tx,
                fft_size=self.config.fft_size,
                noise_var=pilot_noise_var,
                num_rx=num_rx,
                num_tx=num_tx,
            )
        elif self.algorithm == EstimationAlgorithm.MMSE or self.algorithm == "MMSE":
            H_freq_est = self.estimator.estimate(
                rx_pilots=rx_pilots_dict,
                tx_pilots=self.ofdm.known_pilots_per_tx,
                pilot_indices=self.ofdm.pilot_indices_per_tx,
                fft_size=self.config.fft_size,
                noise_var=pilot_noise_var,
                num_rx=num_rx,
                num_tx=num_tx,
            )
        elif self.algorithm == EstimationAlgorithm.DNN or self.algorithm == "DNN":
            H_freq_est = self.estimator.estimate(
                rx_pilots=rx_pilots_dict,
                tx_pilots=self.ofdm.known_pilots_per_tx,
                pilot_indices=self.ofdm.pilot_indices_per_tx,
                fft_size=self.config.fft_size,
                noise_var=pilot_noise_var,
                num_rx=num_rx,
                num_tx=num_tx,
            )
        else:
            raise ValueError(f"Unknown estimation algorithm: {self.algorithm}")
        est_time_ms = (time.perf_counter() - est_start) * 1000.0

        # Step 9: Channel Estimation Error Metrics
        mse = calculate_mse(H_freq_true, H_freq_est)
        nmse = calculate_nmse(H_freq_true, H_freq_est)
        nmse_db = float(10.0 * np.log10(max(nmse, 1e-12)))

        # Step 10: MIMO Spatial Equalization on Data Subcarriers
        # Slice estimated channel onto data subcarriers:
        H_data_est = H_freq_est[:, :, self.ofdm.data_indices]
        equalizer_type = (
            EqualizerType.MMSE
            if self.config.snr_db < 15.0
            else EqualizerType.ZERO_FORCING
        )
        equalized_data_symbols = MIMOEqualizer.equalize(
            rx_symbols=rx_data,
            H_est=H_data_est,
            noise_var=noise_var,
            method=equalizer_type,
        )

        # Step 11: Symbol Demodulation & Bit Recovery
        recovered_bits = np.zeros_like(tx_bits)
        for t in range(num_tx):
            recovered_bits[t] = self.modulator.demodulate(equalized_data_symbols[t].flatten())

        # Step 12: Recovery Metrics (BER & SER)
        ber = calculate_ber(tx_bits, recovered_bits)
        bit_errors = int(np.count_nonzero(tx_bits.flatten() != recovered_bits.flatten()))

        ser = calculate_ser(tx_data_symbols, equalized_data_symbols)
        symbol_errors = int(
            np.count_nonzero(
                np.abs(tx_data_symbols.flatten() - equalized_data_symbols.flatten()) > 0.5
            )
        )
        total_symbols = tx_data_symbols.size

        exec_time_ms = (time.perf_counter() - start_time) * 1000.0

        # Step 13: Extract Constellation Samples for Frontend Visualization
        num_sample_pts = min(120, total_data_symbols_per_tx)
        tx_pts_sample = tx_data_symbols[0].flatten()[:num_sample_pts]
        rx_pts_sample = equalized_data_symbols[0].flatten()[:num_sample_pts]

        tx_constellation = [
            {"i": float(np.real(pt)), "q": float(np.imag(pt))} for pt in tx_pts_sample
        ]
        rx_constellation = [
            {"i": float(np.real(pt)), "q": float(np.imag(pt))} for pt in rx_pts_sample
        ]

        # Step 14: Channel Magnitude Response Profile across Subcarriers
        channel_magnitude = [
            float(np.abs(H_freq_true[0, 0, k])) for k in range(self.config.fft_size)
        ]

        return {
            "mse": float(mse),
            "nmse": float(nmse),
            "nmse_db": float(nmse_db),
            "ber": float(ber),
            "ser": float(ser),
            "total_bits": int(total_bits),
            "bit_errors": int(bit_errors),
            "total_symbols": int(total_symbols),
            "symbol_errors": int(symbol_errors),
            "snr_db": float(self.config.snr_db),
            "algorithm": str(self.algorithm.value if hasattr(self.algorithm, "value") else self.algorithm),
            "execution_time_ms": float(exec_time_ms),
            "inference_time_ms": float(est_time_ms),
            "tx_constellation_sample": tx_constellation,
            "rx_constellation_sample": rx_constellation,
            "channel_magnitude_profile": channel_magnitude,
        }

    def sweep_snr(
        self,
        snr_list: List[float],
        num_trials_per_snr: int = 5,
    ) -> List[Dict[str, Any]]:
        """Runs SNR sweep across multiple independent channel realizations."""
        results = []
        original_snr = self.config.snr_db
        base_seed = self.config.random_seed or 42
        try:
            for snr in snr_list:
                self.config.snr_db = snr
                self.channel.rng = np.random.RandomState(base_seed)
                ber_acc = 0.0
                nmse_acc = 0.0
                time_acc = 0.0
                for _ in range(num_trials_per_snr):
                    res = self.run_single_shot()
                    ber_acc += res["ber"]
                    nmse_acc += res["nmse"]
                    time_acc += res["execution_time_ms"]

                avg_ber = ber_acc / num_trials_per_snr
                avg_nmse = nmse_acc / num_trials_per_snr
                results.append(
                    {
                        "snr_db": float(snr),
                        "algorithm": str(self.algorithm.value if hasattr(self.algorithm, "value") else self.algorithm),
                        "ber": float(avg_ber),
                        "nmse": float(avg_nmse),
                        "nmse_db": float(10.0 * np.log10(max(avg_nmse, 1e-12))),
                        "execution_time_ms": float(time_acc / num_trials_per_snr),
                    }
                )
        finally:
            self.config.snr_db = original_snr

        return results
