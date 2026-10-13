"""Abstract base class for channel estimators."""

from abc import ABC, abstractmethod
from typing import Optional, Union, Dict
import numpy as np


class BaseChannelEstimator(ABC):
    """Base interface for all MIMO-OFDM channel estimators."""

    @abstractmethod
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
        """Estimates full Channel Frequency Response (CFR) across all subcarriers.

        Args:
            rx_pilots: Received symbols at pilot locations (array or dict of tx_idx -> (num_rx, n_pilots)).
            tx_pilots: Known transmitted pilot symbols (array or dict of tx_idx -> (n_pilots,)).
            pilot_indices: Indices of pilot subcarriers (array or dict of tx_idx -> (n_pilots,)).
            fft_size: Total subcarriers in OFDM symbol.
            noise_var: Noise variance sigma^2 (used by MMSE/Bayesian methods).
            num_rx: Optional number of receive antennas.
            num_tx: Optional number of transmit antennas.

        Returns:
            H_est: Shape (num_rx, num_tx, fft_size) complex estimated CFR.
        """
        pass
