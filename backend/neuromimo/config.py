"""Global simulation and model configuration definitions for NeuroMIMO."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ModulationType(str, Enum):
    """Supported digital modulation schemes."""
    QPSK = "QPSK"
    QAM16 = "16QAM"


class ChannelModelType(str, Enum):
    """Supported wireless propagation channel models."""
    AWGN = "AWGN"
    RAYLEIGH = "RAYLEIGH"


class EstimationAlgorithm(str, Enum):
    """Supported channel estimation algorithms."""
    PERFECT = "PERFECT"
    LS = "LS"
    MMSE = "MMSE"
    DNN = "DNN"


class EqualizerType(str, Enum):
    """MIMO spatial equalization methods."""
    ZERO_FORCING = "ZF"
    MMSE = "MMSE"


@dataclass
class SimulationConfig:
    """Configurable MIMO-OFDM communication pipeline parameters."""
    num_tx: int = 2
    num_rx: int = 2
    fft_size: int = 64
    cp_length: int = 16
    pilot_spacing: int = 8  # Subcarrier spacing between pilots
    modulation: ModulationType = ModulationType.QPSK
    channel_model: ChannelModelType = ChannelModelType.RAYLEIGH
    snr_db: float = 20.0
    algorithm: EstimationAlgorithm = EstimationAlgorithm.LS
    num_channel_taps: int = 4
    num_ofdm_symbols: int = 14  # Standard LTE / 5G slot size
    random_seed: Optional[int] = 42

    @property
    def num_pilots(self) -> int:
        """Number of pilot subcarriers per OFDM symbol."""
        return self.fft_size // self.pilot_spacing

    @property
    def num_data_subcarriers(self) -> int:
        """Number of data-bearing subcarriers per OFDM symbol."""
        return self.fft_size - self.num_pilots


@dataclass
class ModelConfig:
    """Configuration for DNN channel estimation model."""
    input_dim: int = 64 * 2 * 2 * 2  # (subcarriers * complex (2) * tx * rx)
    hidden_dims: List[int] = field(default_factory=lambda: [256, 128, 256])
    output_dim: int = 64 * 2 * 2 * 2
    learning_rate: float = 1e-3
    batch_size: int = 64
    epochs: int = 50
    checkpoint_dir: str = "models"
    device: str = "cpu"
