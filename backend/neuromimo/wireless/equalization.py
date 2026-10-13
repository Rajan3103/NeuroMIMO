"""MIMO spatial equalization techniques (Zero-Forcing and MMSE).

Recovers transmitted spatial multiplexing streams from multi-antenna received observations
using estimated or ground-truth channel matrices H_k per subcarrier.
"""

from typing import Optional
import numpy as np
from ..config import EqualizerType


class MIMOEqualizer:
    """Equalizes spatial interference across transmit antennas per subcarrier."""

    @staticmethod
    def equalize(
        rx_symbols: np.ndarray,
        H_est: np.ndarray,
        noise_var: float = 1e-4,
        method: EqualizerType = EqualizerType.ZERO_FORCING,
    ) -> np.ndarray:
        """Equalizes received MIMO frequency-domain signals.

        Mathematical formulations at subcarrier k:
            Zero-Forcing (ZF):
                W_{ZF, k} = (H_k^H H_k)^(-1) H_k^H
                X_hat_k = W_{ZF, k} Y_k

            Linear MMSE:
                W_{MMSE, k} = (H_k^H H_k + sigma_n^2 I)^(-1) H_k^H
                X_hat_k = W_{MMSE, k} Y_k

        Args:
            rx_symbols: Shape (num_rx, num_symbols, num_tones) received complex observations.
            H_est: Shape (num_rx, num_tx, num_tones) estimated channel matrix.
            noise_var: Noise variance sigma^2 (used for MMSE equalizer regularization).
            method: EqualizerType.ZERO_FORCING or EqualizerType.MMSE.

        Returns:
            recovered_tx: Shape (num_tx, num_symbols, num_tones) equalized transmit symbols.
        """
        num_rx, num_symbols, num_tones = rx_symbols.shape
        _, num_tx, h_tones = H_est.shape
        if num_tones != h_tones:
            raise ValueError(f"Tone mismatch: rx_symbols has {num_tones}, H_est has {h_tones}")

        recovered_tx = np.zeros((num_tx, num_symbols, num_tones), dtype=np.complex128)

        # Transpose H_est to (num_tones, num_rx, num_tx) for subcarrier-wise processing
        H_k = np.transpose(H_est, (2, 0, 1))  # (K, Nr, Nt)
        H_H = np.conjugate(np.transpose(H_k, (0, 2, 1)))  # (K, Nt, Nr)

        # Grammian matrix H^H * H: Shape (K, Nt, Nt)
        grammian = np.matmul(H_H, H_k)

        if method == EqualizerType.MMSE or method == "MMSE":
            # MMSE regularization: sigma_n^2 * I
            reg = max(noise_var, 1e-8) * np.eye(num_tx, dtype=np.complex128)[np.newaxis, :, :]
            inv_matrix = np.linalg.pinv(grammian + reg)
        else:  # ZERO_FORCING
            # Small 1e-12 regularizer for condition stability
            reg = 1e-12 * np.eye(num_tx, dtype=np.complex128)[np.newaxis, :, :]
            inv_matrix = np.linalg.pinv(grammian + reg)

        # Weight matrix W_k: (K, Nt, Nr) = (H^H H + reg)^(-1) H^H
        W_k = np.matmul(inv_matrix, H_H)

        # Apply spatial filter per subcarrier:
        # W_k[k] is (Nt, Nr), rx_symbols[:, :, k] is (Nr, Nsym)
        # recovered_tx[:, :, k] = W_k[k] @ rx_symbols[:, :, k]
        for k in range(num_tones):
            recovered_tx[:, :, k] = np.matmul(W_k[k], rx_symbols[:, :, k])

        return recovered_tx
