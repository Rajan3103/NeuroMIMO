"""Pydantic schemas for API request and response validation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """System health and environment status."""
    status: str = "ok"
    version: str = "0.1.0"
    device: str
    cuda_available: bool
    torch_version: str
    numpy_version: str


class ConfigResponse(BaseModel):
    """Default simulation parameters and allowed configuration ranges."""
    default_snr_db: float = 20.0
    min_snr_db: float = 0.0
    max_snr_db: float = 30.0
    fft_sizes: List[int] = [64, 128, 256]
    default_fft_size: int = 64
    cp_lengths: List[int] = [16, 32]
    pilot_spacings: List[int] = [4, 8, 16]
    supported_modulations: List[str] = ["QPSK", "16QAM"]
    supported_channel_models: List[str] = ["RAYLEIGH", "AWGN"]
    supported_algorithms: List[str] = ["PERFECT", "LS", "MMSE", "DNN"]
    supported_antennas: List[Dict[str, int]] = [
        {"tx": 2, "rx": 2},
        {"tx": 2, "rx": 4},
        {"tx": 4, "rx": 4},
    ]


class SimulationRunRequest(BaseModel):
    """Parameters for running a MIMO-OFDM simulation round."""
    num_tx: int = Field(default=2, ge=1, le=4, description="Transmit antennas")
    num_rx: int = Field(default=2, ge=1, le=4, description="Receive antennas")
    fft_size: int = Field(default=64, ge=16, le=512, description="FFT size (subcarriers)")
    cp_length: int = Field(default=16, ge=4, le=128, description="Cyclic prefix length")
    pilot_spacing: int = Field(default=8, ge=2, le=32, description="Comb pilot subcarrier spacing")
    modulation: str = Field(default="QPSK", description="QPSK or 16QAM")
    channel_model: str = Field(default="RAYLEIGH", description="RAYLEIGH or AWGN")
    snr_db: float = Field(default=20.0, ge=-10.0, le=40.0, description="Signal-to-Noise Ratio in dB")
    algorithm: str = Field(default="LS", description="PERFECT, LS, MMSE, or DNN")
    num_ofdm_symbols: int = Field(default=14, ge=1, le=100, description="OFDM symbols per frame")
    random_seed: Optional[int] = Field(default=42, description="RNG seed")


class ConstellationPoint(BaseModel):
    """A complex IQ constellation point."""
    i: float
    q: float


class SimulationRunResponse(BaseModel):
    """Result payload from simulation run."""
    id: Optional[str] = None
    mse: float
    nmse: float
    nmse_db: float
    ber: float
    ser: float
    total_bits: int
    bit_errors: int
    total_symbols: int
    symbol_errors: int
    snr_db: float
    algorithm: str
    execution_time_ms: float
    tx_constellation_sample: List[ConstellationPoint]
    rx_constellation_sample: List[ConstellationPoint]
    channel_magnitude_profile: List[float]


class AlgorithmComparisonResult(BaseModel):
    """Individual estimation algorithm performance metric."""
    algorithm: str
    nmse: float
    nmse_db: float
    ber: float
    ser: float
    execution_time_ms: float


class EstimationCompareRequest(BaseModel):
    """Request to benchmark multiple algorithms under the same channel realizations."""
    snr_db: float = Field(default=20.0, ge=-10.0, le=40.0)
    algorithms: List[str] = Field(default_factory=lambda: ["LS", "MMSE", "DNN"])
    num_realizations: int = Field(default=10, ge=1, le=100)
    fft_size: int = Field(default=64, ge=16, le=512)
    cp_length: int = Field(default=16, ge=4, le=128)
    modulation: str = Field(default="QPSK")


class EstimationCompareResponse(BaseModel):
    """Comparative benchmark results."""
    snr_db: float
    results: List[AlgorithmComparisonResult]


class ModelTrainRequest(BaseModel):
    """Hyperparameters for training the DNN channel estimator."""
    epochs: int = Field(default=20, ge=1, le=100)
    batch_size: int = Field(default=64, ge=8, le=256)
    learning_rate: float = Field(default=0.001, gt=0.0)
    num_samples: int = Field(default=1000, ge=50, le=10000)
    snr_range: List[float] = Field(default_factory=lambda: [0.0, 30.0])
    random_seed: int = 42
    background: bool = Field(default=False, description="Run training as an asynchronous background job")


class TrainingProgressPoint(BaseModel):
    """Loss tracking per training epoch."""
    epoch: int
    train_loss: float
    val_loss: float


class ModelTrainResponse(BaseModel):
    """Summary of training run."""
    status: str
    job_id: Optional[str] = None
    epochs_completed: int
    final_train_loss: float
    final_val_loss: float
    history: List[TrainingProgressPoint]
    checkpoint_saved: bool
    checkpoint_path: str


class TrainingJobStatusResponse(BaseModel):
    """Status of asynchronous training job."""
    job_id: str
    status: str  # idle, running, completed, failed
    epochs_completed: int
    total_epochs: int
    current_train_loss: Optional[float] = None
    current_val_loss: Optional[float] = None
    history: List[TrainingProgressPoint] = []
    error: Optional[str] = None


class ModelStatusResponse(BaseModel):
    """Current status of DNN checkpoint."""
    trained: bool
    checkpoint_exists: bool
    checkpoint_path: str
    parameters_count: int
    device: str
    active_job_id: Optional[str] = None
    training_status: Optional[str] = None


class ModelPredictRequest(BaseModel):
    """Input payload for raw DNN inference."""
    features: Optional[List[float]] = Field(
        default=None,
        description="512-dimensional float array [Re(H_LS), Im(H_LS)]. If omitted, a sample frame is simulated.",
    )
    snr_db: float = Field(default=20.0, ge=-10.0, le=40.0)
    modulation: str = Field(default="QPSK")
    channel_model: str = Field(default="RAYLEIGH")


class ModelPredictResponse(BaseModel):
    """Model inference channel estimation output."""
    status: str = "success"
    h_pred_real: List[float]
    h_pred_imag: List[float]
    h_true_real: Optional[List[float]] = None
    h_true_imag: Optional[List[float]] = None
    nmse: Optional[float] = None
    nmse_db: Optional[float] = None
    inference_time_ms: float
    shape: List[int] = [2, 2, 64]


class ExperimentRecordResponse(BaseModel):
    """Summary or detail of a stored simulation experiment."""
    id: str
    created_at: str
    name: str
    config: Dict[str, Any]
    algorithm: str
    snr_db: float
    nmse: float
    ber: float
    ser: float
    execution_time_ms: float
    results: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class PlotItem(BaseModel):
    """Reference to an experiment plot."""
    name: str
    filename: str
    url: str
    description: str


class ExperimentPlotsResponse(BaseModel):
    """List of plots associated with an experiment."""
    experiment_id: str
    plots: List[PlotItem]
