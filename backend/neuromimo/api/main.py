"""FastAPI application entry point for NeuroMIMO.

Provides RESTful endpoints for:
- Health and environment capabilities
- Simulation configuration limits
- Single-shot MIMO-OFDM simulation runs
- Head-to-head estimator comparisons
- Supervised DNN model training (synchronous or background thread)
- Model status and checkpoint inspection
- Direct model inference / prediction
- Experiment history retrieval and publication research plot serving
"""

import os
import json
import uuid
import time
import asyncio
import threading
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

import numpy as np
import torch
from torch.utils.data import TensorDataset, DataLoader
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from ..config import (
    SimulationConfig,
    EstimationAlgorithm,
    ChannelModelType,
    ModulationType,
    EqualizerType,
)
from .schemas import (
    HealthResponse,
    ConfigResponse,
    SimulationRunRequest,
    SimulationRunResponse,
    EstimationCompareRequest,
    EstimationCompareResponse,
    AlgorithmComparisonResult,
    ModelTrainRequest,
    ModelTrainResponse,
    ModelStatusResponse,
    TrainingJobStatusResponse,
    ModelPredictRequest,
    ModelPredictResponse,
    ExperimentRecordResponse,
    ExperimentPlotsResponse,
    PlotItem,
)
from ..storage.database import (
    init_db,
    save_experiment,
    get_all_experiments,
    get_experiment_by_id,
    save_training_run,
    get_latest_training_run,
)
from ..wireless.simulation import MIMOSimulationPipeline
from ..wireless.channel import WirelessChannel
from ..wireless.ofdm import OFDMPipeline
from ..wireless.modulation import get_modulator
from ..evaluation.benchmarks import benchmark_channel_estimators
from ..evaluation.metrics import calculate_nmse, calculate_nmse_db
from ..estimation.dnn import (
    ChannelEstimationNet,
    DNNEstimator,
    DEFAULT_CHECKPOINT_PATH,
)
from ..estimation.trainer import (
    generate_channel_dataset,
    split_dataset,
    ChannelEstimationTrainer,
)

CHECKPOINT_PATH = os.path.abspath(DEFAULT_CHECKPOINT_PATH)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "NEUROMIMO_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]
RESULTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "results")
)


# =============================================================================
# Asynchronous Background Training Job Manager
# =============================================================================

class TrainingJobManager:
    """Manages thread-safe asynchronous model training jobs without blocking API loops."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.current_job: Optional[Dict[str, Any]] = None

    def get_job_status(self) -> Dict[str, Any]:
        with self._lock:
            if not self.current_job:
                return {"job_id": "", "status": "idle", "epochs_completed": 0, "total_epochs": 0}
            return dict(self.current_job)

    def start_job(self, req: ModelTrainRequest, checkpoint_path: str) -> str:
        with self._lock:
            if self.current_job and self.current_job.get("status") == "running":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A model training job is already in progress. Please wait for completion.",
                )
            job_id = str(uuid.uuid4())
            self.current_job = {
                "job_id": job_id,
                "status": "running",
                "epochs_completed": 0,
                "total_epochs": req.epochs,
                "current_train_loss": None,
                "current_val_loss": None,
                "history": [],
                "error": None,
                "final_train_loss": 0.0,
                "final_val_loss": 0.0,
                "checkpoint_saved": False,
                "checkpoint_path": checkpoint_path,
            }

        worker = threading.Thread(
            target=self._execute_training,
            args=(job_id, req, checkpoint_path),
            daemon=True,
        )
        worker.start()
        return job_id

    def _execute_training(
        self,
        job_id: str,
        req: ModelTrainRequest,
        checkpoint_path: str,
    ) -> None:
        try:
            config = SimulationConfig(random_seed=req.random_seed)
            X, Y, snrs = generate_channel_dataset(
                num_samples=req.num_samples,
                config=config,
                snr_range=(req.snr_range[0], req.snr_range[1]),
                random_seed=req.random_seed,
            )
            train_set, val_set, test_set = split_dataset(
                X, Y, train_ratio=0.70, val_ratio=0.15, random_seed=req.random_seed
            )

            trainer = ChannelEstimationTrainer(learning_rate=req.learning_rate)

            train_dataset = TensorDataset(
                torch.from_numpy(train_set[0]), torch.from_numpy(train_set[1])
            )
            train_loader = DataLoader(train_dataset, batch_size=req.batch_size, shuffle=True)
            val_dataset = TensorDataset(
                torch.from_numpy(val_set[0]), torch.from_numpy(val_set[1])
            )
            val_loader = DataLoader(val_dataset, batch_size=req.batch_size, shuffle=False)

            best_val_loss = float("inf")
            best_state = None

            for epoch in range(1, req.epochs + 1):
                # Training phase
                trainer.model.train()
                train_loss_acc = 0.0
                num_train = 0
                for bx, by in train_loader:
                    bx, by = bx.to(trainer.device), by.to(trainer.device)
                    trainer.optimizer.zero_grad()
                    pred = trainer.model(bx)
                    loss = trainer.criterion(pred, by)
                    loss.backward()
                    trainer.optimizer.step()
                    train_loss_acc += float(loss.item())
                    num_train += 1

                epoch_train_loss = train_loss_acc / max(1, num_train)

                # Validation phase
                trainer.model.eval()
                val_loss_acc = 0.0
                num_val = 0
                with torch.no_grad():
                    for vx, vy in val_loader:
                        vx, vy = vx.to(trainer.device), vy.to(trainer.device)
                        v_loss = trainer.criterion(trainer.model(vx), vy)
                        val_loss_acc += float(v_loss.item())
                        num_val += 1

                epoch_val_loss = val_loss_acc / max(1, num_val)
                trainer.scheduler.step(epoch_val_loss)

                if epoch_val_loss < best_val_loss:
                    best_val_loss = epoch_val_loss
                    best_state = {k: v.cpu().clone() for k, v in trainer.model.state_dict().items()}

                point = {
                    "epoch": epoch,
                    "train_loss": float(epoch_train_loss),
                    "val_loss": float(epoch_val_loss),
                }

                with self._lock:
                    if self.current_job and self.current_job["job_id"] == job_id:
                        self.current_job["epochs_completed"] = epoch
                        self.current_job["current_train_loss"] = float(epoch_train_loss)
                        self.current_job["current_val_loss"] = float(epoch_val_loss)
                        self.current_job["history"].append(point)

            if best_state is not None:
                trainer.model.load_state_dict(best_state)

            save_path = checkpoint_path or DEFAULT_CHECKPOINT_PATH
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            torch.save(
                {
                    "model_state_dict": trainer.model.state_dict(),
                    "epochs": req.epochs,
                    "final_train_loss": float(self.current_job["current_train_loss"]),
                    "final_val_loss": float(best_val_loss),
                    "history": self.current_job["history"],
                },
                save_path,
            )

            save_training_run(
                run_id=job_id,
                epochs=req.epochs,
                final_train_loss=float(self.current_job["current_train_loss"]),
                final_val_loss=float(best_val_loss),
                checkpoint_path=save_path,
                history=self.current_job["history"],
            )

            with self._lock:
                if self.current_job and self.current_job["job_id"] == job_id:
                    self.current_job["status"] = "completed"
                    self.current_job["checkpoint_saved"] = True
                    self.current_job["final_train_loss"] = float(self.current_job["current_train_loss"])
                    self.current_job["final_val_loss"] = float(best_val_loss)

        except Exception as exc:
            with self._lock:
                if self.current_job and self.current_job["job_id"] == job_id:
                    self.current_job["status"] = "failed"
                    self.current_job["error"] = str(exc)


training_manager = TrainingJobManager()


# =============================================================================
# FastAPI Application & Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes persistence database and model directory on startup."""
    init_db()
    os.makedirs(os.path.dirname(os.path.abspath(CHECKPOINT_PATH)), exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="NeuroMIMO Wireless & ML Engine API",
    description=(
        "Comprehensive REST API for physical-layer 2x2 MIMO-OFDM simulation, "
        "reproducible LS/MMSE/DNN channel estimation benchmarks, and real-time PyTorch inference."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# 1. Health & Config Endpoints
# =============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def get_health() -> HealthResponse:
    """Returns system status, device capabilities (CPU/CUDA), and library versions."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return HealthResponse(
        status="ok",
        version="1.0.0",
        device=device,
        cuda_available=torch.cuda.is_available(),
        torch_version=torch.__version__,
        numpy_version=np.__version__,
    )


@app.get("/api/config", response_model=ConfigResponse, tags=["System"])
def get_config() -> ConfigResponse:
    """Returns default parameters and supported ranges for MIMO-OFDM simulation."""
    return ConfigResponse()


# =============================================================================
# 2. Simulation Execution
# =============================================================================

@app.post("/api/simulation/run", response_model=SimulationRunResponse, tags=["Simulation"])
async def run_simulation(request: SimulationRunRequest) -> SimulationRunResponse:
    """Executes a single-slot MIMO-OFDM wireless transmission round.

    Validates parameters, runs channel propagation with calibrated noise,
    performs channel estimation, applies spatial equalization, and returns
    BER, SER, and constellation scatter samples.
    """
    # 1. Parameter Validation
    mod_str = request.modulation.upper()
    if mod_str not in ("QPSK", "16QAM"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported modulation '{request.modulation}'. Supported: QPSK, 16QAM.",
        )

    chan_str = request.channel_model.upper()
    if chan_str not in ("RAYLEIGH", "AWGN"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported channel model '{request.channel_model}'. Supported: RAYLEIGH, AWGN.",
        )

    algo_str = request.algorithm.upper()
    if algo_str not in ("PERFECT", "LS", "MMSE", "DNN"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported algorithm '{request.algorithm}'. Supported: PERFECT, LS, MMSE, DNN.",
        )

    if algo_str == "DNN" and not os.path.exists(CHECKPOINT_PATH):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Trained DNN model checkpoint not found. "
                "Please train the model via POST /api/model/train or choose LS / MMSE."
            ),
        )

    if request.cp_length >= request.fft_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cyclic prefix length ({request.cp_length}) must be less than FFT size ({request.fft_size}).",
        )

    # 2. Construct Simulation Configuration
    sim_config = SimulationConfig(
        num_tx=request.num_tx,
        num_rx=request.num_rx,
        fft_size=request.fft_size,
        cp_length=request.cp_length,
        pilot_spacing=request.pilot_spacing,
        modulation=ModulationType(mod_str),
        channel_model=ChannelModelType(chan_str),
        snr_db=request.snr_db,
        algorithm=EstimationAlgorithm(algo_str),
        num_ofdm_symbols=request.num_ofdm_symbols,
        random_seed=request.random_seed,
    )

    # 3. Execute Simulation (Offload to thread pool to preserve async responsiveness)
    pipeline = MIMOSimulationPipeline(sim_config)
    result = await asyncio.to_thread(pipeline.run_single_shot)

    # 4. Save to Database
    exp_id = str(uuid.uuid4())
    save_experiment(
        exp_id=exp_id,
        name=f"{algo_str} at {request.snr_db:.1f} dB ({chan_str})",
        config=request.model_dump(),
        algorithm=algo_str,
        snr_db=request.snr_db,
        nmse=result["nmse"],
        ber=result["ber"],
        ser=result["ser"],
        execution_time_ms=result["execution_time_ms"],
        results=result,
    )

    return SimulationRunResponse(id=exp_id, **result)


# =============================================================================
# 3. Estimation Comparison
# =============================================================================

@app.post("/api/estimation/compare", response_model=EstimationCompareResponse, tags=["Estimation"])
async def compare_estimation_algorithms(
    request: EstimationCompareRequest,
) -> EstimationCompareResponse:
    """Compares LS, MMSE, and DNN channel estimation algorithms under IDENTICAL channel realizations."""
    # 1. Validation
    valid_algos = {"PERFECT", "LS", "MMSE", "DNN"}
    for a in request.algorithms:
        if a.upper() not in valid_algos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid algorithm '{a}'. Allowed: {list(valid_algos)}",
            )

    normalized_algos = [a.upper() for a in request.algorithms]

    if "DNN" in normalized_algos and not os.path.exists(CHECKPOINT_PATH):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trained DNN model checkpoint not found. Please train the model or benchmark LS/MMSE only.",
        )

    mod_str = request.modulation.upper()
    if mod_str not in ("QPSK", "16QAM"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported modulation '{request.modulation}'. Supported: QPSK, 16QAM.",
        )

    # 2. Execute Comparative Benchmark in thread pool
    bench_data = await asyncio.to_thread(
        benchmark_channel_estimators,
        snr_list=[request.snr_db],
        algorithms=normalized_algos,
        num_trials_per_snr=request.num_realizations,
        checkpoint_path=CHECKPOINT_PATH,
    )

    raw_results = bench_data.get("results", {})
    results: List[AlgorithmComparisonResult] = []
    for algo in normalized_algos:
        if algo in raw_results:
            d = raw_results[algo]
            results.append(
                AlgorithmComparisonResult(
                    algorithm=algo,
                    nmse=d["nmse"][0],
                    nmse_db=d["nmse_db"][0],
                    ber=d["ber"][0],
                    ser=d["ser"][0],
                    execution_time_ms=d["avg_inference_ms"][0],
                )
            )

    return EstimationCompareResponse(snr_db=request.snr_db, results=results)


# =============================================================================
# 4. DNN Model Training & Status
# =============================================================================

@app.get("/api/model/status", response_model=ModelStatusResponse, tags=["Model"])
def get_model_status() -> ModelStatusResponse:
    """Returns training readiness, checkpoint existence, parameter count, and compute device."""
    checkpoint_exists = os.path.exists(CHECKPOINT_PATH)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    net = ChannelEstimationNet()
    total_params = sum(p.numel() for p in net.parameters())

    job_info = training_manager.get_job_status()

    return ModelStatusResponse(
        trained=checkpoint_exists,
        checkpoint_exists=checkpoint_exists,
        checkpoint_path=CHECKPOINT_PATH,
        parameters_count=total_params,
        device=device,
        active_job_id=job_info.get("job_id"),
        training_status=job_info.get("status"),
    )


@app.get("/api/model/train/status", response_model=TrainingJobStatusResponse, tags=["Model"])
def get_training_job_status() -> TrainingJobStatusResponse:
    """Returns live epoch-by-epoch loss tracking for active or completed training jobs."""
    info = training_manager.get_job_status()
    if info.get("status") in ("idle", ""):
        latest = get_latest_training_run()
        if latest:
            return TrainingJobStatusResponse(
                job_id=latest["id"],
                status="completed",
                epochs_completed=latest["epochs"],
                total_epochs=latest["epochs"],
                current_train_loss=latest["final_train_loss"],
                current_val_loss=latest["final_val_loss"],
                history=latest.get("history", []),
            )
    return TrainingJobStatusResponse(**info)


@app.post("/api/model/train", response_model=ModelTrainResponse, tags=["Model"])
async def train_model(request: ModelTrainRequest) -> ModelTrainResponse:
    """Trains the PyTorch ChannelEstimationNet using synthetic MIMO-OFDM realizations.

    Supports asynchronous execution via `background=true` or synchronous execution.
    """
    if len(request.snr_range) != 2 or request.snr_range[0] >= request.snr_range[1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="snr_range must be [min_snr, max_snr] with min_snr < max_snr.",
        )

    # Background Job Mode
    if request.background:
        job_id = training_manager.start_job(request, CHECKPOINT_PATH)
        return ModelTrainResponse(
            status="running",
            job_id=job_id,
            epochs_completed=0,
            final_train_loss=0.0,
            final_val_loss=0.0,
            history=[],
            checkpoint_saved=False,
            checkpoint_path=CHECKPOINT_PATH,
        )

    # Synchronous Mode (executed in worker thread to prevent event loop starvation)
    job_id = training_manager.start_job(request, CHECKPOINT_PATH)

    # Wait for completion asynchronously
    while True:
        await asyncio.sleep(0.5)
        status_info = training_manager.get_job_status()
        if status_info.get("status") in ("completed", "failed"):
            break

    if status_info.get("status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training job failed: {status_info.get('error')}",
        )

    return ModelTrainResponse(
        status="completed",
        job_id=job_id,
        epochs_completed=status_info["epochs_completed"],
        final_train_loss=status_info.get("final_train_loss", 0.0),
        final_val_loss=status_info.get("final_val_loss", 0.0),
        history=status_info.get("history", []),
        checkpoint_saved=status_info.get("checkpoint_saved", True),
        checkpoint_path=CHECKPOINT_PATH,
    )


# =============================================================================
# 5. Direct Model Prediction / Inference
# =============================================================================

@app.post("/api/model/predict", response_model=ModelPredictResponse, tags=["Model"])
async def predict_channel(request: ModelPredictRequest) -> ModelPredictResponse:
    """Performs raw DNN model inference on input features or generates an ad-hoc test sample."""
    if not os.path.exists(CHECKPOINT_PATH):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trained DNN model checkpoint not found. Please train the model via POST /api/model/train first.",
        )

    estimator = DNNEstimator(model_path=CHECKPOINT_PATH)

    # Case A: User supplied raw 512-dim features [Re(H_LS), Im(H_LS)]
    if request.features is not None:
        if len(request.features) != 512:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input features array must have exactly 512 elements (received {len(request.features)}).",
            )
        tensor_in = torch.tensor(request.features, dtype=torch.float32).unsqueeze(0).to(estimator.device)
        t0 = time.perf_counter()
        estimator.model.eval()
        with torch.no_grad():
            preds = estimator.model(tensor_in).cpu().squeeze(0).numpy()
        inf_time = (time.perf_counter() - t0) * 1000.0

        half = len(preds) // 2
        return ModelPredictResponse(
            status="success",
            h_pred_real=preds[:half].tolist(),
            h_pred_imag=preds[half:].tolist(),
            inference_time_ms=float(inf_time),
            shape=[2, 2, 64],
        )

    # Case B: Simulate an ad-hoc channel realization at requested SNR
    chan_type = (
        ChannelModelType.RAYLEIGH
        if request.channel_model.upper() == "RAYLEIGH"
        else ChannelModelType.AWGN
    )
    ofdm = OFDMPipeline(num_tx=2, fft_size=64, cp_length=16, pilot_spacing=8)
    channel = WirelessChannel(
        num_tx=2,
        num_rx=2,
        num_taps=4,
        fft_size=64,
        channel_type=chan_type,
    )
    _, H_true = channel.generate_channel_response()

    # Known pilots transmission
    dummy_payload = np.zeros((2, 1, ofdm.num_data), dtype=np.complex128)
    tx_freq = ofdm.assemble_mimo_frame(dummy_payload)
    rx_freq, noise_var = channel.apply_channel(tx_freq, H_true, snr_db=request.snr_db)
    rx_pilots_dict, _ = ofdm.extract_pilots_and_data(rx_freq)
    pilot_noise_var = ofdm.pilot_noise_variance(noise_var, rx_freq.shape[1])

    t0 = time.perf_counter()
    H_est = estimator.estimate(
        rx_pilots=rx_pilots_dict,
        tx_pilots=ofdm.known_pilots_per_tx,
        pilot_indices=ofdm.pilot_indices_per_tx,
        fft_size=64,
        noise_var=pilot_noise_var,
        num_rx=2,
        num_tx=2,
    )
    inf_time = (time.perf_counter() - t0) * 1000.0

    nmse = calculate_nmse(H_true, H_est)
    nmse_db = calculate_nmse_db(H_true, H_est)

    return ModelPredictResponse(
        status="success",
        h_pred_real=np.real(H_est).flatten().tolist(),
        h_pred_imag=np.imag(H_est).flatten().tolist(),
        h_true_real=np.real(H_true).flatten().tolist(),
        h_true_imag=np.imag(H_true).flatten().tolist(),
        nmse=float(nmse),
        nmse_db=float(nmse_db),
        inference_time_ms=float(inf_time),
        shape=[2, 2, 64],
    )


# =============================================================================
# 6. Experiments History & Research Plot Artifacts
# =============================================================================

@app.get("/api/experiments", response_model=List[Dict[str, Any]], tags=["Experiments"])
def list_experiments() -> List[Dict[str, Any]]:
    """Returns list of recorded simulation runs stored in the SQLite database."""
    return get_all_experiments()


@app.get("/api/experiments/benchmark/snr-sweep", tags=["Experiments"])
def get_benchmark_snr_sweep() -> Dict[str, Any]:
    """Returns the pre-calculated benchmark SNR sweep dataset with Monte Carlo statistics."""
    file_path = os.path.join(RESULTS_DIR, "snr_sweep_results.json")
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benchmark SNR sweep dataset not found on server.",
        )
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/experiments/{experiment_id}", response_model=Dict[str, Any], tags=["Experiments"])
def get_experiment_details(experiment_id: str) -> Dict[str, Any]:
    """Retrieves full details and metrics of a single experiment by ID."""
    exp = get_experiment_by_id(experiment_id)
    if not exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with ID '{experiment_id}' was not found.",
        )
    return exp


@app.get(
    "/api/experiments/{experiment_id}/plots",
    response_model=ExperimentPlotsResponse,
    tags=["Experiments"],
)
def get_experiment_plots(experiment_id: str) -> ExperimentPlotsResponse:
    """Lists research plots associated with an experiment or system benchmarks."""
    # Check if experiment exists or is the 'latest' / 'research' alias
    if experiment_id not in ("latest", "research", "all"):
        exp = get_experiment_by_id(experiment_id)
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment with ID '{experiment_id}' was not found.",
            )

    plots_catalog = [
        {
            "name": "NMSE vs SNR Waterfall",
            "filename": "nmse_vs_snr.png",
            "description": "Normalized Mean Squared Error vs SNR in Rayleigh multipath fading",
        },
        {
            "name": "BER vs SNR Waterfall",
            "filename": "ber_vs_snr.png",
            "description": "Bit Error Rate vs SNR after channel estimation and spatial equalization",
        },
        {
            "name": "Channel Model Comparison",
            "filename": "channel_model_comparison.png",
            "description": "Comparative performance under frequency-flat AWGN vs frequency-selective Rayleigh fading",
        },
        {
            "name": "Generalization & Parameter Mismatch",
            "filename": "generalization_evaluation.png",
            "description": "Performance on unseen channel realizations and PDP decay/tap dispersion shifts",
        },
        {
            "name": "Computational Runtime",
            "filename": "inference_runtime.png",
            "description": "Per-frame estimation latency and throughput benchmark across estimators",
        },
        {
            "name": "Pilot-Density Scaling",
            "filename": "pilot_density_comparison.png",
            "description": "Estimation NMSE scaling as a function of comb pilot subcarrier spacing",
        },
    ]

    items = []
    for p in plots_catalog:
        file_path = os.path.join(RESULTS_DIR, p["filename"])
        if os.path.exists(file_path):
            items.append(
                PlotItem(
                    name=p["name"],
                    filename=p["filename"],
                    url=f"/api/experiments/{experiment_id}/plots/{p['filename']}",
                    description=p["description"],
                )
            )

    return ExperimentPlotsResponse(experiment_id=experiment_id, plots=items)


@app.get("/api/experiments/{experiment_id}/plots/{plot_name}", tags=["Experiments"])
def get_plot_image(experiment_id: str, plot_name: str):
    """Serves high-resolution (300 DPI) research figures as PNG images."""
    file_path = os.path.join(RESULTS_DIR, plot_name)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plot '{plot_name}' not found for experiment '{experiment_id}'.",
        )
    return FileResponse(file_path, media_type="image/png")
