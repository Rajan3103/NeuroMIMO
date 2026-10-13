"""Digital modulation and demodulation with Gray mapping and unit average energy.

Supports QPSK (2 bits/symbol) and 16-QAM (4 bits/symbol) constellations,
both strictly normalized to unit average symbol energy (E[|s|^2] = 1.0).
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np
from ..config import ModulationType


def generate_random_bits(
    num_bits: int,
    rng: Optional[np.random.RandomState] = None,
) -> np.ndarray:
    """Generates an array of independent and identically distributed (i.i.d.) random bits {0, 1}.

    Args:
        num_bits: Total number of binary bits to generate.
        rng: Optional NumPy RandomState for reproducibility.

    Returns:
        1D NumPy array of integers with values in {0, 1}.
    """
    if rng is None:
        rng = np.random.RandomState()
    return rng.randint(0, 2, size=num_bits, dtype=np.int32)


class ModulationScheme(ABC):
    """Abstract base class for digital modulation schemes."""

    @property
    @abstractmethod
    def bits_per_symbol(self) -> int:
        """Number of bits carried by each complex modulation symbol."""
        pass

    @property
    @abstractmethod
    def constellation(self) -> np.ndarray:
        """Complex constellation points array normalized to unit average power."""
        pass

    @abstractmethod
    def modulate(self, bits: np.ndarray) -> np.ndarray:
        """Maps binary bit sequence into complex modulation symbols.

        Args:
            bits: 1D binary numpy array of integers {0, 1}.

        Returns:
            Complex symbols array normalized to unit average energy.
        """
        pass

    @abstractmethod
    def demodulate(self, symbols: np.ndarray) -> np.ndarray:
        """Demodulates complex symbols back into binary bits via minimum Euclidean distance.

        Args:
            symbols: Array of complex received symbols.

        Returns:
            Demodulated binary bits {0, 1}.
        """
        pass


class QPSKModulation(ModulationScheme):
    """Quadrature Phase Shift Keying (QPSK) with Gray code mapping.

    Bits per symbol: 2
    Constellation points: (±1 ± 1j) / sqrt(2)
    Gray mapping:
      00 -> ( 1 + 1j) / sqrt(2)
      01 -> (-1 + 1j) / sqrt(2)
      11 -> (-1 - 1j) / sqrt(2)
      10 -> ( 1 - 1j) / sqrt(2)

    Adjacent constellation points differ by exactly 1 bit (Hamming distance 1).
    Average energy: E[|s|^2] = 1.0.
    """

    def __init__(self) -> None:
        norm = 1.0 / np.sqrt(2.0)
        self._mapping = {
            (0, 0): (1.0 + 1.0j) * norm,
            (0, 1): (-1.0 + 1.0j) * norm,
            (1, 1): (-1.0 - 1.0j) * norm,
            (1, 0): (1.0 - 1.0j) * norm,
        }
        self._constellation_points = np.array(list(self._mapping.values()), dtype=np.complex128)
        self._bit_tuples = list(self._mapping.keys())

    @property
    def bits_per_symbol(self) -> int:
        return 2

    @property
    def constellation(self) -> np.ndarray:
        return self._constellation_points.copy()

    def modulate(self, bits: np.ndarray) -> np.ndarray:
        bits_flat = np.asarray(bits, dtype=np.int32).flatten()
        if len(bits_flat) % 2 != 0:
            raise ValueError(f"Bits length must be a multiple of 2 for QPSK, got {len(bits_flat)}")

        bit_pairs = bits_flat.reshape(-1, 2)
        symbols = np.zeros(len(bit_pairs), dtype=np.complex128)
        for b_tuple, pt in self._mapping.items():
            mask = (bit_pairs[:, 0] == b_tuple[0]) & (bit_pairs[:, 1] == b_tuple[1])
            symbols[mask] = pt
        return symbols

    def demodulate(self, symbols: np.ndarray) -> np.ndarray:
        symbols_flat = np.asarray(symbols, dtype=np.complex128).flatten()
        num_symbols = len(symbols_flat)
        if num_symbols == 0:
            return np.array([], dtype=np.int32)

        # Minimum Euclidean distance detection across normalized constellation
        dists = np.abs(symbols_flat[:, np.newaxis] - self._constellation_points[np.newaxis, :])
        min_indices = np.argmin(dists, axis=1)

        recovered_bits = np.zeros((num_symbols, 2), dtype=np.int32)
        for idx, bit_tuple in enumerate(self._bit_tuples):
            recovered_bits[min_indices == idx] = bit_tuple

        return recovered_bits.flatten()


class QAM16Modulation(ModulationScheme):
    """16-Quadrature Amplitude Modulation (16-QAM) with 2D Gray coding.

    Bits per symbol: 4 (2 in-phase bits, 2 quadrature bits)
    PAM4 Gray constellation: 00 -> -3, 01 -> -1, 11 -> +1, 10 -> +3
    Average PAM4 energy: ((-3)^2 + (-1)^2 + 1^2 + 3^2) / 4 = 5.0
    Average 2D 16-QAM energy: 5.0 + 5.0 = 10.0
    Normalization scale: 1.0 / sqrt(10.0) -> E[|s|^2] = 1.0
    """

    def __init__(self) -> None:
        self.norm = 1.0 / np.sqrt(10.0)
        pam4_map = {
            (0, 0): -3.0,
            (0, 1): -1.0,
            (1, 1): 1.0,
            (1, 0): 3.0,
        }
        self._mapping = {}
        for b_i, val_i in pam4_map.items():
            for b_q, val_q in pam4_map.items():
                bit_4tuple = (b_i[0], b_i[1], b_q[0], b_q[1])
                self._mapping[bit_4tuple] = (val_i + 1j * val_q) * self.norm

        self._constellation_points = np.array(list(self._mapping.values()), dtype=np.complex128)
        self._bit_tuples = list(self._mapping.keys())

    @property
    def bits_per_symbol(self) -> int:
        return 4

    @property
    def constellation(self) -> np.ndarray:
        return self._constellation_points.copy()

    def modulate(self, bits: np.ndarray) -> np.ndarray:
        bits_flat = np.asarray(bits, dtype=np.int32).flatten()
        if len(bits_flat) % 4 != 0:
            raise ValueError(f"Bits length must be a multiple of 4 for 16-QAM, got {len(bits_flat)}")

        bit_quads = bits_flat.reshape(-1, 4)
        symbols = np.zeros(len(bit_quads), dtype=np.complex128)
        for b_tuple, pt in self._mapping.items():
            mask = (
                (bit_quads[:, 0] == b_tuple[0])
                & (bit_quads[:, 1] == b_tuple[1])
                & (bit_quads[:, 2] == b_tuple[2])
                & (bit_quads[:, 3] == b_tuple[3])
            )
            symbols[mask] = pt
        return symbols

    def demodulate(self, symbols: np.ndarray) -> np.ndarray:
        symbols_flat = np.asarray(symbols, dtype=np.complex128).flatten()
        num_symbols = len(symbols_flat)
        if num_symbols == 0:
            return np.array([], dtype=np.int32)

        # Minimum Euclidean distance detection across 16 constellation points
        dists = np.abs(symbols_flat[:, np.newaxis] - self._constellation_points[np.newaxis, :])
        min_indices = np.argmin(dists, axis=1)

        recovered_bits = np.zeros((num_symbols, 4), dtype=np.int32)
        for idx, bit_tuple in enumerate(self._bit_tuples):
            recovered_bits[min_indices == idx] = bit_tuple

        return recovered_bits.flatten()


def get_modulator(mod_type: ModulationType) -> ModulationScheme:
    """Factory helper to obtain the requested digital modulator."""
    if mod_type == ModulationType.QPSK or mod_type == "QPSK":
        return QPSKModulation()
    elif mod_type == ModulationType.QAM16 or mod_type == "16QAM":
        return QAM16Modulation()
    raise ValueError(f"Unsupported modulation type: {mod_type}")
