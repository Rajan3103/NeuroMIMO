"""Orthogonal Frequency Division Multiplexing (OFDM) baseband processing for MIMO transceivers.

Handles orthogonal comb pilot subcarrier allocation across transmit antennas,
frequency-to-time IFFT modulation with cyclic prefix (CP) insertion,
and time-to-frequency CP removal with orthonormal FFT demodulation.
"""

from typing import Tuple, Dict, List, Union
import numpy as np


class OFDMPipeline:
    """Configurable MIMO-OFDM baseband modulation and demodulation transceiver pipeline."""

    def __init__(
        self,
        num_tx: int = 2,
        fft_size: int = 64,
        cp_length: int = 16,
        pilot_spacing: int = 8,
    ) -> None:
        self.num_tx = num_tx
        self.fft_size = fft_size
        self.cp_length = cp_length
        self.pilot_spacing = pilot_spacing

        # Total comb pilot subcarrier positions in the OFDM grid
        self.total_pilot_indices = np.arange(0, fft_size, pilot_spacing, dtype=np.int32)
        self.num_total_pilots = len(self.total_pilot_indices)

        # Backward compatibility properties
        self.pilot_indices = self.total_pilot_indices
        self.num_pilots = self.num_total_pilots

        # Assign disjoint orthogonal pilot subcarriers to each transmit antenna (FDM pilot pattern)
        # Antenna t uses indices total_pilot_indices[t::num_tx]
        self.pilot_indices_per_tx: Dict[int, np.ndarray] = {}
        for t in range(num_tx):
            self.pilot_indices_per_tx[t] = self.total_pilot_indices[t::num_tx]

        # Remaining subcarriers are dedicated to spatial multiplexing data payload
        all_indices = np.arange(fft_size, dtype=np.int32)
        self.data_indices = np.setdiff1d(all_indices, self.total_pilot_indices)
        self.num_data = len(self.data_indices)

        # Deterministic known unit-energy pilot symbol sequence (QPSK phases)
        # Transmitted pilot symbols are known to both transmitter and receiver
        rng = np.random.RandomState(4242)
        self.known_pilots_per_tx: Dict[int, np.ndarray] = {}
        for t in range(num_tx):
            n_p = len(self.pilot_indices_per_tx[t])
            phases = rng.choice([0.0, np.pi / 2, np.pi, 3 * np.pi / 2], size=n_p)
            self.known_pilots_per_tx[t] = np.exp(1j * phases).astype(np.complex128)

        # Legacy known pilots for single-stream references
        self.known_pilots = np.exp(
            1j * rng.choice([0.0, np.pi / 2, np.pi, 3 * np.pi / 2], size=self.num_total_pilots)
        ).astype(np.complex128)

    def assemble_mimo_frame(
        self,
        data_symbols: np.ndarray,
    ) -> np.ndarray:
        """Assembles MIMO frequency-domain OFDM frames across all transmit antennas.

        Args:
            data_symbols: Shape (num_tx, num_ofdm_symbols, num_data) complex data payload.

        Returns:
            tx_freq: Shape (num_tx, num_ofdm_symbols, fft_size) frequency-domain symbols.
        """
        num_tx, num_symbols, num_data = data_symbols.shape
        if num_tx != self.num_tx:
            raise ValueError(f"Expected {self.num_tx} transmit antennas, got {num_tx}")
        if num_data != self.num_data:
            raise ValueError(f"Expected {self.num_data} data subcarriers, got {num_data}")

        tx_freq = np.zeros((self.num_tx, num_symbols, self.fft_size), dtype=np.complex128)

        # Allocate data payload on data subcarriers for all antennas
        for idx, d_idx in enumerate(self.data_indices):
            tx_freq[:, :, d_idx] = data_symbols[:, :, idx]

        # Insert orthogonal pilots:
        # Antenna t inserts known pilots on its dedicated pilot subcarriers pilot_indices_per_tx[t]
        # and transmits 0 on other antennas' pilot subcarriers to ensure zero pilot contamination.
        for t in range(self.num_tx):
            p_indices = self.pilot_indices_per_tx[t]
            p_symbols = self.known_pilots_per_tx[t]
            for idx, p_idx in enumerate(p_indices):
                tx_freq[t, :, p_idx] = p_symbols[idx]

        return tx_freq

    def assemble_ofdm_frame(
        self,
        data_symbols: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Backward-compatible frame assembly for single-antenna or 2D payloads.

        Args:
            data_symbols: Shape (num_ofdm_symbols, num_data) complex data.

        Returns:
            Tuple of:
                - freq_frame: Shape (num_ofdm_symbols, fft_size)
                - pilot_symbols: Shape (num_pilots,) known pilot symbols
        """
        if data_symbols.ndim == 3:
            return self.assemble_mimo_frame(data_symbols), self.known_pilots

        num_symbols = data_symbols.shape[0]
        freq_frame = np.zeros((num_symbols, self.fft_size), dtype=np.complex128)
        for idx, p_idx in enumerate(self.total_pilot_indices):
            freq_frame[:, p_idx] = self.known_pilots[idx]
        for idx, d_idx in enumerate(self.data_indices):
            freq_frame[:, d_idx] = data_symbols[:, idx]
        return freq_frame, self.known_pilots.copy()

    def modulate(self, freq_signal: np.ndarray) -> np.ndarray:
        """Transforms frequency-domain OFDM symbols to time-domain with cyclic prefix.

        Uses unitary orthonormal IFFT scaling (norm="ortho") so energy is strictly preserved.

        Args:
            freq_signal: Shape (..., fft_size) complex frequency symbols.

        Returns:
            time_signal: Shape (..., fft_size + cp_length) time-domain OFDM samples with CP.
        """
        time_samples = np.fft.ifft(freq_signal, axis=-1, norm="ortho")
        cp = time_samples[..., -self.cp_length :]
        time_with_cp = np.concatenate([cp, time_samples], axis=-1)
        return time_with_cp

    def demodulate(self, time_signal: np.ndarray) -> np.ndarray:
        """Removes cyclic prefix and transforms time-domain signal back to frequency domain via FFT.

        Args:
            time_signal: Shape (..., fft_size + cp_length).

        Returns:
            freq_signal: Shape (..., fft_size).
        """
        time_samples = time_signal[..., self.cp_length :]
        freq_signal = np.fft.fft(time_samples, axis=-1, norm="ortho")
        return freq_signal

    def extract_pilots_and_data(
        self,
        rx_freq: np.ndarray,
    ) -> Tuple[Dict[int, np.ndarray], np.ndarray]:
        """Extracts pilot observations per transmit antenna and received data symbols.

        Args:
            rx_freq: Shape (num_rx, num_ofdm_symbols, fft_size) received frequency symbols.

        Returns:
            Tuple of:
                - rx_pilots_dict: Dict mapping tx_idx -> Shape (num_rx, num_pilots_t)
                  averaged across symbols
                - rx_data: Shape (num_rx, num_ofdm_symbols, num_data) received data payload
        """
        num_rx, num_symbols, _ = rx_freq.shape

        rx_pilots_dict: Dict[int, np.ndarray] = {}
        for t in range(self.num_tx):
            p_indices = self.pilot_indices_per_tx[t]
            rx_pilots_dict[t] = np.zeros((num_rx, len(p_indices)), dtype=np.complex128)
            for idx, p_idx in enumerate(p_indices):
                rx_pilots_dict[t][:, idx] = np.mean(rx_freq[:, :, p_idx], axis=1)

        rx_data = np.zeros((num_rx, num_symbols, len(self.data_indices)), dtype=np.complex128)
        for idx, d_idx in enumerate(self.data_indices):
            rx_data[:, :, idx] = rx_freq[:, :, d_idx]

        return rx_pilots_dict, rx_data
