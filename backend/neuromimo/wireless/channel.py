"""Wireless propagation channel models (Rayleigh multipath fading and AWGN).

Generates reproducible channel impulse responses (CIR) with exponential power delay profiles,
computes deterministic ground truth Channel Frequency Responses (CFR) H[k],
and injects complex Additive White Gaussian Noise (AWGN) calibrated to target SNR.
"""

from typing import Tuple, Optional
import numpy as np
from ..config import ChannelModelType


class WirelessChannel:
    """Simulates multi-antenna MIMO wireless multipath fading and AWGN channels."""

    def __init__(
        self,
        num_tx: int = 2,
        num_rx: int = 2,
        num_taps: int = 4,
        fft_size: int = 64,
        channel_type: ChannelModelType = ChannelModelType.RAYLEIGH,
        pdp_decay: float = 1.5,
        random_seed: Optional[int] = None,
    ) -> None:
        self.num_tx = num_tx
        self.num_rx = num_rx
        self.num_taps = num_taps
        self.fft_size = fft_size
        self.channel_type = channel_type
        self.pdp_decay = pdp_decay
        self.rng = np.random.RandomState(random_seed)

        # Compute normalized Power Delay Profile (PDP)
        taps = np.arange(num_taps)
        pdp_raw = np.exp(-taps / self.pdp_decay)
        self.pdp = pdp_raw / np.sum(pdp_raw)  # Normalized total power per link = 1.0

    def generate_channel_response(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generates ground truth Channel Impulse Response (CIR) and Channel Frequency Response (CFR).

        Returns:
            Tuple:
                - h_time: Shape (num_rx, num_tx, num_taps) complex CIR
                - H_freq: Shape (num_rx, num_tx, fft_size) complex CFR (Deterministic Ground Truth)
        """
        if self.channel_type == ChannelModelType.AWGN:
            # Identity flat channel across antennas (spatial channels uncoupled)
            h_time = np.zeros((self.num_rx, self.num_tx, self.num_taps), dtype=np.complex128)
            for r in range(min(self.num_rx, self.num_tx)):
                h_time[r, r, 0] = 1.0 + 0.0j

            H_freq = np.fft.fft(h_time, n=self.fft_size, axis=-1)
            return h_time, H_freq

        # Rayleigh Multipath Fading:
        # Each link (r, t) has independent complex Gaussian taps h_{r, t}(l) ~ CN(0, PDP[l])
        h_time = np.zeros((self.num_rx, self.num_tx, self.num_taps), dtype=np.complex128)
        for rx in range(self.num_rx):
            for tx in range(self.num_tx):
                std_dev = np.sqrt(self.pdp / 2.0)
                re = self.rng.normal(0.0, std_dev, size=self.num_taps)
                im = self.rng.normal(0.0, std_dev, size=self.num_taps)
                h_time[rx, tx, :] = re + 1j * im

        # Ground truth CFR via FFT along tap dimension
        H_freq = np.fft.fft(h_time, n=self.fft_size, axis=-1)
        return h_time, H_freq

    def apply_channel(
        self,
        tx_freq: np.ndarray,
        H_freq: np.ndarray,
        snr_db: float,
    ) -> Tuple[np.ndarray, float]:
        """Applies spatial MIMO frequency response and calibrated complex AWGN noise.

        Mathematical model per subcarrier k and OFDM symbol s:
            Y[r, s, k] = sum_{t} H[r, t, k] * X[t, s, k] + W[r, s, k]

        Args:
            tx_freq: Shape (num_tx, num_symbols, fft_size) transmitted frequency symbols.
            H_freq: Shape (num_rx, num_tx, fft_size) ground truth channel frequency response.
            snr_db: Signal-to-Noise Ratio in decibels.

        Returns:
            Tuple of:
                - rx_freq: Shape (num_rx, num_symbols, fft_size) received noisy frequency symbols
                - noise_variance: Float sigma^2 noise power per complex dimension
        """
        # Vectorized spatial matrix multiplication across subcarriers:
        # H_freq is (Nr, Nt, K)
        # tx_freq is (Nt, Nsym, K)
        # Result rx_noiseless is (Nr, Nsym, K)
        rx_noiseless = np.einsum("rtk,tsk->rsk", H_freq, tx_freq)

        # Average received signal power per receive antenna
        signal_power = float(np.mean(np.abs(rx_noiseless) ** 2))

        # Handle noise power according to target SNR:
        # SNR_linear = P_signal / sigma^2
        snr_linear = 10.0 ** (snr_db / 10.0)
        noise_variance = signal_power / snr_linear

        # Complex AWGN noise: CN(0, sigma^2) = N(0, sigma^2/2) + j*N(0, sigma^2/2)
        noise_std = np.sqrt(noise_variance / 2.0)
        noise = self.rng.normal(0.0, noise_std, size=rx_noiseless.shape) + 1j * self.rng.normal(
            0.0, noise_std, size=rx_noiseless.shape
        )

        rx_freq = rx_noiseless + noise
        return rx_freq, noise_variance
