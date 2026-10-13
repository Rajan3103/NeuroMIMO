"""Linear Minimum Mean Square Error (LMMSE) Channel Estimation.

Minimizes the expected Bayesian squared estimation error by combining Least Squares
observations with explicitly defined second-order channel frequency statistics (autocorrelation
matrix R_HH derived from power delay profile) and calibrated noise variance sigma_n^2.

Mathematical Formulation:
    W_{MMSE, t} = R_{H, H_{P_t}} * (R_{H_{P_t}, H_{P_t}} + sigma_n^2 * I)^(-1)
    H_{MMSE, r, t} = W_{MMSE, t} * H_{LS, r, t}(P_t)
"""

from typing import Optional, Union, Dict
import numpy as np
from .base import BaseChannelEstimator


class MMSEEstimator(BaseChannelEstimator):
    """Linear MMSE channel estimator using explicit channel covariance and noise variance."""

    def __init__(
        self,
        channel_pdp: Optional[np.ndarray] = None,
        pdp_decay: float = 1.5,
        num_taps: int = 4,
    ) -> None:
        self.pdp_decay = pdp_decay
        self.num_taps = num_taps
        if channel_pdp is not None:
            self.channel_pdp = channel_pdp / np.sum(channel_pdp)
        else:
            taps = np.arange(num_taps)
            raw = np.exp(-taps / self.pdp_decay)
            self.channel_pdp = raw / np.sum(raw)

    def compute_frequency_correlation(
        self,
        indices_1: np.ndarray,
        indices_2: np.ndarray,
        fft_size: int,
    ) -> np.ndarray:
        """Computes theoretical frequency-domain correlation matrix R_{H1, H2} from PDP.

        Autocorrelation in frequency between subcarriers k and l:
            R(k, l) = sum_{m=0}^{L-1} PDP[m] * exp(-j * 2 * pi * (k - l) * m / N_fft)

        Args:
            indices_1: Shape (N1,) subcarrier indices.
            indices_2: Shape (N2,) subcarrier indices.
            fft_size: Total subcarriers in OFDM symbol.

        Returns:
            R: Shape (N1, N2) complex correlation matrix.
        """
        k_grid = indices_1[:, np.newaxis]
        l_grid = indices_2[np.newaxis, :]
        delta = k_grid - l_grid  # Shape (N1, N2)

        R = np.zeros(delta.shape, dtype=np.complex128)
        for m, power in enumerate(self.channel_pdp):
            R += power * np.exp(-1j * 2.0 * np.pi * delta * m / fft_size)

        return R

    def estimate(
        self,
        rx_pilots: Union[np.ndarray, Dict[int, np.ndarray]],
        tx_pilots: Union[np.ndarray, Dict[int, np.ndarray]],
        pilot_indices: Union[np.ndarray, Dict[int, np.ndarray]],
        fft_size: int,
        noise_var: Optional[float] = None,
        num_rx: Optional[int] = None,
        num_tx: Optional[int] = None,
        **kwargs,
    ) -> np.ndarray:
        """Computes optimal Linear MMSE channel estimate across all subcarriers.

        Args:
            rx_pilots: Dict of tx_idx -> (num_rx, n_pilots) or array (num_rx, num_tx, n_pilots).
            tx_pilots: Dict of tx_idx -> (n_pilots,) or array (num_tx, n_pilots).
            pilot_indices: Dict of tx_idx -> (n_pilots,) or array (n_pilots,).
            fft_size: Total subcarriers in OFDM symbol.
            noise_var: Noise variance sigma_n^2.
            num_rx: Number of receive antennas.
            num_tx: Number of transmit antennas.

        Returns:
            H_est: Shape (num_rx, num_tx, fft_size) complex estimated CFR.
        """
        if noise_var is None or noise_var <= 0.0:
            noise_var = 1e-4

        all_subcarriers = np.arange(fft_size, dtype=np.int32)

        if isinstance(rx_pilots, dict):
            n_tx = len(rx_pilots) if num_tx is None else num_tx
            n_rx = rx_pilots[0].shape[0] if num_rx is None else num_rx
            H_est = np.zeros((n_rx, n_tx, fft_size), dtype=np.complex128)

            for t in range(n_tx):
                p_ind = pilot_indices[t] if isinstance(pilot_indices, dict) else pilot_indices
                p_tx = tx_pilots[t] if isinstance(tx_pilots, dict) else tx_pilots[t]
                p_rx = rx_pilots[t]
                num_p = len(p_ind)

                # Cross-correlation between all subcarriers and antenna t pilots: (fft_size, num_p)
                R_H_Hp = self.compute_frequency_correlation(all_subcarriers, p_ind, fft_size)

                # Autocorrelation between antenna t pilots: (num_p, num_p)
                R_Hp_Hp = self.compute_frequency_correlation(p_ind, p_ind, fft_size)

                # MMSE Wiener weight matrix: W = R_H_Hp * (R_Hp_Hp + sigma_n^2 * I)^(-1)
                reg = noise_var * np.eye(num_p, dtype=np.complex128)
                inv_matrix = np.linalg.pinv(R_Hp_Hp + reg)
                W_mmse = np.matmul(R_H_Hp, inv_matrix)  # Shape (fft_size, num_p)

                for r in range(n_rx):
                    h_ls_p = p_rx[r, :] / (p_tx + 1e-12)
                    H_est[r, t, :] = np.matmul(W_mmse, h_ls_p)

            return H_est

        # Array format (num_rx, num_tx, num_pilots)
        n_rx, n_tx, num_p = rx_pilots.shape
        H_est = np.zeros((n_rx, n_tx, fft_size), dtype=np.complex128)
        p_ind = np.asarray(pilot_indices, dtype=np.int32)

        R_H_Hp = self.compute_frequency_correlation(all_subcarriers, p_ind, fft_size)
        R_Hp_Hp = self.compute_frequency_correlation(p_ind, p_ind, fft_size)
        reg = noise_var * np.eye(num_p, dtype=np.complex128)
        W_mmse = np.matmul(R_H_Hp, np.linalg.pinv(R_Hp_Hp + reg))

        for r in range(n_rx):
            for t in range(n_tx):
                h_ls_p = rx_pilots[r, t, :] / (tx_pilots[t, :] + 1e-12)
                H_est[r, t, :] = np.matmul(W_mmse, h_ls_p)

        return H_est
