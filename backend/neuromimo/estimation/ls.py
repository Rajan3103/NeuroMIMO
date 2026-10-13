"""Least Squares (LS) Channel Estimation with Frequency-Domain Interpolation.

Estimates channel transfer function at pilot subcarriers via element-wise division:
    H_{LS}[p] = Y[p] / X[p]
and interpolates across all subcarriers using optimal discrete Fourier transform (DFT)
sinc interpolation or spline/linear interpolation.
"""

from typing import Optional, Union, Dict
import numpy as np
from scipy.interpolate import interp1d
from .base import BaseChannelEstimator


class LSEstimator(BaseChannelEstimator):
    """Computes Least Squares estimates at pilot subcarriers and interpolates to all data tones."""

    def __init__(self, interpolation_kind: str = "dft") -> None:
        self.interpolation_kind = interpolation_kind

    def _interpolate_channel(
        self,
        p_ind: np.ndarray,
        h_p: np.ndarray,
        fft_size: int,
    ) -> np.ndarray:
        """Interpolates discrete pilot channel estimates across the full OFDM bandwidth."""
        n_p = len(p_ind)
        # Check if pilots are uniformly spaced
        diffs = np.diff(p_ind)
        is_uniform = len(diffs) > 0 and np.all(diffs == diffs[0])

        if self.interpolation_kind == "dft" and is_uniform and (fft_size % n_p == 0):
            # Optimal DFT / IDFT sinc interpolation for OFDM
            spacing = int(diffs[0])
            delta = int(p_ind[0])
            
            # IDFT of pilot observations
            h_phase = np.fft.ifft(h_p)
            l_vec = np.arange(n_p)
            # Demodulate carrier phase shift
            h_time = h_phase * np.exp(1j * 2.0 * np.pi * delta * l_vec / fft_size)
            
            # Reconstruct full frequency response via zero-padded FFT
            return np.fft.fft(h_time, n=fft_size)

        # Fallback to linear / spline interpolation
        all_subcarriers = np.arange(fft_size, dtype=np.float64)
        p_coords = list(p_ind)
        h_vals = list(h_p)

        if p_coords[0] > 0:
            p_coords.insert(0, 0)
            h_vals.insert(0, h_p[0])
        if p_coords[-1] < fft_size - 1:
            p_coords.append(fft_size - 1)
            h_vals.append(h_p[-1])

        p_arr = np.array(p_coords, dtype=np.float64)
        h_arr = np.array(h_vals, dtype=np.complex128)

        kind = "linear" if self.interpolation_kind == "dft" else self.interpolation_kind
        interp_real = interp1d(
            p_arr,
            np.real(h_arr),
            kind=kind,
            fill_value="extrapolate",
            bounds_error=False,
        )
        interp_imag = interp1d(
            p_arr,
            np.imag(h_arr),
            kind=kind,
            fill_value="extrapolate",
            bounds_error=False,
        )
        return interp_real(all_subcarriers) + 1j * interp_imag(all_subcarriers)

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
        """Computes LS channel estimate H_LS = Y_p / X_p and interpolates across subcarriers.

        Args:
            rx_pilots: Dict of tx_idx -> (num_rx, n_pilots) or array (num_rx, num_tx, n_pilots).
            tx_pilots: Dict of tx_idx -> (n_pilots,) or array (num_tx, n_pilots).
            pilot_indices: Dict of tx_idx -> (n_pilots,) or array (n_pilots,).
            fft_size: Total subcarriers in OFDM symbol.
            noise_var: Unused for LS.
            num_rx: Number of receive antennas.
            num_tx: Number of transmit antennas.

        Returns:
            H_est: Shape (num_rx, num_tx, fft_size) complex estimated CFR.
        """
        if isinstance(rx_pilots, dict):
            n_tx = len(rx_pilots) if num_tx is None else num_tx
            n_rx = rx_pilots[0].shape[0] if num_rx is None else num_rx
            H_est = np.zeros((n_rx, n_tx, fft_size), dtype=np.complex128)

            for t in range(n_tx):
                p_ind = pilot_indices[t] if isinstance(pilot_indices, dict) else pilot_indices
                p_tx = tx_pilots[t] if isinstance(tx_pilots, dict) else tx_pilots[t]
                p_rx = rx_pilots[t]  # (n_rx, n_pilots)

                for r in range(n_rx):
                    h_p = p_rx[r, :] / (p_tx + 1e-12)
                    H_est[r, t, :] = self._interpolate_channel(p_ind, h_p, fft_size)

            return H_est

        # Array format (num_rx, num_tx, num_pilots)
        n_rx, n_tx, _ = rx_pilots.shape
        H_est = np.zeros((n_rx, n_tx, fft_size), dtype=np.complex128)
        p_ind = np.asarray(pilot_indices, dtype=np.int32)

        for r in range(n_rx):
            for t in range(n_tx):
                h_p = rx_pilots[r, t, :] / (tx_pilots[t, :] + 1e-12)
                H_est[r, t, :] = self._interpolate_channel(p_ind, h_p, fft_size)

        return H_est
