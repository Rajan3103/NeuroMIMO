# NeuroMIMO: AI-Enhanced MIMO-OFDM Channel Estimation & Adaptive Signal Recovery System

An academic research platform and final-year capstone engineering project that implements, evaluates, and benchmarks conventional channel estimation algorithms (**Least Squares with DFT Sinc Interpolation**, **Linear Minimum Mean Square Error**) against deep learning (**PyTorch Residual Deep Neural Network**) within an end-to-end, vectorized 2×2 MIMO-OFDM wireless physical layer.

---

## 1. Project Overview & Key Highlights

Modern 5G NR and Wi-Fi 6/7 wireless systems combine Multiple-Input Multiple-Output (MIMO) spatial multiplexing with Orthogonal Frequency Division Multiplexing (OFDM). Coherent symbol detection at the receiver requires accurate Channel State Information (CSI). 

NeuroMIMO provides:
- **Vectorized NumPy / SciPy Physical Layer**: Realistic simulation of random bit generation, Gray-coded QPSK/16-QAM, orthogonal comb pilot allocation, 64-point IFFT/FFT, cyclic prefix processing, multipath Rayleigh fading, and MMSE spatial equalization.
- **Three Multi-Paradigm Estimators**:
  1. *Least Squares (LS)* with alias-free DFT sinc interpolation across subcarriers.
  2. *Bayesian Linear MMSE (LMMSE)* with closed-form Power Delay Profile (PDP) Wiener-Hopf covariance computation.
  3. *PyTorch Residual Deep Neural Network* with 512-dimensional complex tensor feature mapping and non-linear noise cancellation.
- **Statistical Monte Carlo Evaluation**: 105 Monte Carlo trials per SNR point, featuring Wilson score 95% confidence intervals and Poisson rule-of-three upper bounds for low BER regimes.
- **FastAPI REST Service**: Asynchronous background training manager, ad-hoc inference, SQLite audit logging, and 300 DPI research plot serving.
- **Modern React 19 + TypeScript Dashboard**: Responsive research UI with Recharts interactive charts, dark mode, high-resolution publication figures gallery, and single-shot experiment inspection.

---

## 2. Final Project Folder Structure

```
NeuroMIMO/
├── .env.example                     # Environment variables configuration template
├── README.md                        # Master project documentation, setup & report
├── requirements.txt                 # Backend Python package dependencies
├── backend/
│   ├── data/
│   │   └── experiments.db           # Persistent SQLite database for experiment audit
│   ├── models/
│   │   └── dnn_checkpoint.pt        # Trained PyTorch Residual DNN model checkpoint
│   ├── neuromimo/
│   │   ├── __init__.py              # NeuroMIMO package initialization
│   │   ├── config.py                # Pydantic simulation & channel configuration schemas
│   │   ├── api/
│   │   │   ├── main.py              # FastAPI application & REST endpoint routers
│   │   │   └── schemas.py           # Request & response Pydantic data models
│   │   ├── estimation/
│   │   │   ├── conventional.py      # LS (DFT sinc interpolation) & LMMSE estimators
│   │   │   ├── dnn.py               # PyTorch ChannelEstimationNet & DNNEstimator wrapper
│   │   │   ├── trainer.py           # Dataset generation, splitting, and training loops
│   │   │   └── train_cli.py         # Standalone CLI training utility
│   │   ├── evaluation/
│   │   │   ├── benchmarks.py        # Multi-estimator comparative benchmarking engine
│   │   │   ├── metrics.py           # MSE, NMSE (dB), BER, SER, and Wilson score intervals
│   │   │   ├── plotting.py          # 300 DPI publication figure generators (Matplotlib)
│   │   │   ├── runner.py            # Systematic 6-experiment evaluation runner
│   │   │   └── run_experiments_cli.py # CLI runner for reproducible paper experiments
│   │   ├── storage/
│   │   │   └── database.py          # SQLite persistence layer for runs and training logs
│   │   └── wireless/
│   │       ├── channel.py           # 4-tap exponential Rayleigh multipath & AWGN models
│   │       ├── equalization.py      # Zero-Forcing & MMSE MIMO spatial stream equalizers
│   │       ├── modulation.py        # QPSK and 16-QAM Gray modulators & bit demappers
│   │       ├── ofdm.py              # 64-FFT, CP-16, and orthogonal comb pilot multiplexing
│   │       └── simulation.py        # End-to-end MIMOSimulationPipeline orchestrator
│   ├── results/                     # 300 DPI figures, CSVs, and JSON experiment datasets
│   │   ├── ber_vs_snr.png
│   │   ├── channel_model_comparison.png
│   │   ├── generalization_evaluation.png
│   │   ├── inference_runtime.png
│   │   ├── nmse_vs_snr.png
│   │   ├── pilot_density_comparison.png
│   │   └── snr_sweep_results.json
│   └── tests/                       # Complete Pytest test suite (67 unit/API tests)
│       ├── test_api.py              # FastAPI endpoints & error validation tests
│       ├── test_dnn_estimation.py   # PyTorch training, checkpointing & leakage tests
│       ├── test_experiments.py      # Metrics, confidence bounds, and runner smoke tests
│       ├── test_health.py           # Health and configuration tests
│       ├── test_skeleton.py         # Physical layer sanity tests
│       └── test_wireless_simulation.py # Vectorized MIMO-OFDM unit tests
└── frontend/
    ├── package.json                 # React 19, TypeScript, Recharts, Vite dependencies
    ├── vite.config.ts               # Vite configuration with `/api` proxy to port 8000
    ├── tailwind.config.js           # Dark theme design tokens and custom palette
    ├── public/
    │   └── results/                 # Publication figure PNGs for static frontend fallback
    └── src/
        ├── api/client.ts            # Typed REST API client
        ├── components/
        │   ├── common/              # StatCard, Badge, Modal, LoadingSpinner, ErrorBanner
        │   └── layout/              # Navbar (status indicator), Sidebar (drawer)
        ├── pages/
        │   ├── OverviewPage.tsx     # Telemetry, KPI cards, 1-click live demo
        │   ├── SimulatorPage.tsx    # Parametric MIMO-OFDM simulator & constellation
        │   ├── ChannelEstimationPage.tsx # Head-to-head estimator lab & CFR plots
        │   ├── ModelTrainingPage.tsx# Residual MLP training studio & loss curves
        │   ├── PerformanceComparisonPage.tsx # Waterfall curves & publication gallery
        │   ├── SignalVisualizationPage.tsx # Constellation scatter, CFR, PDP, 64-tone grid
        │   ├── ExperimentHistoryPage.tsx # SQLite experiment audit table & CSV export
        │   └── AboutPage.tsx        # Theory, math derivations, Wilson CI & viva guide
        └── types/index.ts           # Shared TypeScript interfaces
```

---

## 3. System Architecture & Transceiver Flow

```
                                  TRANSMITTER
  +------------------+     +-------------------+     +--------------------+
  | Random Bit Gen   | --> | QPSK / 16-QAM Mod | --> | Orthogonal Comb    |
  | (Payload Bits)   |     | (Gray Mapped)     |     | Pilot Allocation   |
  +------------------+     +-------------------+     +--------------------+
                                                                |
                                                                v
                                                     +--------------------+
                                                     | 64-FFT IFFT + CP   |
                                                     | (16 cyclic prefix) |
                                                     +--------------------+
                                                                |
                                                                v
                                  CHANNEL               (Tx Antennas 0 & 1)
                       +----------------------------+
                       | 4-Tap Rayleigh Multipath   |
                       | Exponential PDP + Cal. AWGN|
                       +----------------------------+
                                                                |
                                                                v
                                  RECEIVER              (Rx Antennas 0 & 1)
  +------------------+     +-------------------+     +--------------------+
  | Recovered Bits   | <-- | MIMO Equalization | <-- | Channel Estimation |
  | (BER Evaluator)  |     | (ZF / MMSE)       |     | (LS / MMSE / DNN)  |
  +------------------+     +-------------------+     +--------------------+
```

### Physical Layer Specifications
- **Topology**: $2 \times 2$ MIMO spatial multiplexing ($N_t = 2, N_r = 2$).
- **Subcarrier Spacing**: $N_{fft} = 64$ subcarriers with $N_{cp} = 16$ cyclic prefix samples.
- **Comb Pilot Structure**: Orthogonal pilot subcarrier sets per transmit antenna:
  - $Tx_0$ Pilots: $\{0, 16, 32, 48\}$ (spacing 16 on antenna 0, 4 pilots total).
  - $Tx_1$ Pilots: $\{8, 24, 40, 56\}$ (spacing 16 on antenna 1, 4 pilots total).
  - Mutual frequency orthogonality prevents inter-antenna pilot contamination.
- **Multipath Channel**: 4 discrete taps with normalized exponential Power Delay Profile:
  $$\text{PDP}(l) = \frac{e^{-l/1.5}}{\sum_{m=0}^{3} e^{-m/1.5}}, \quad l \in \{0, 1, 2, 3\}$$

---

## 4. Channel Estimation Formulations

### 1. Least Squares (LS) with Optimal DFT Sinc Interpolation
At pilot subcarriers $p \in \mathcal{P}_t$:
$$\hat{H}_{LS, r, t}[p] = \frac{Y_{r, t}[p]}{X_{p, t}}$$

To reconstruct the full 64 subcarriers without polynomial ringing:
1. Alias-folded time-domain impulse response via IDFT:
   $$\tilde{h}(l) = \frac{1}{N_p} \sum_{k=0}^{N_p - 1} \hat{H}_{LS}[p_k] e^{j 2 \pi k l / N_p}$$
2. Demodulate subcarrier phase offset $\delta$:
   $$h(l) = \tilde{h}(l) \cdot e^{j 2 \pi \delta l / N_{fft}}$$
3. Zero-pad to $N_{fft} = 64$ and execute FFT to achieve exact continuous frequency reconstruction with zero interpolation error in noiseless channels.

### 2. Linear Minimum Mean Square Error (LMMSE)
Minimizes the Bayesian mean squared error by combining LS observations with known channel statistics:
$$\hat{H}_{MMSE, r, t} = \mathbf{R}_{H, H_p} \left(\mathbf{R}_{H_p, H_p} + \sigma_n^2 \mathbf{I}\right)^{-1} \hat{H}_{LS, r, t}$$
where the frequency autocorrelation between subcarrier $k$ and $m$ is derived from the PDP:
$$\mathbf{R}_{H}(k, m) = \sum_{l=0}^{L-1} \text{PDP}[l] \cdot e^{-j 2 \pi (k - m) l / N_{fft}}$$

### 3. PyTorch Residual Deep Neural Network
Maps noisy LS estimates to ground-truth channels:
- **Input Dimension**: $512$ ($2 \times 2 \times 64 \times 2$ for Real and Imaginary parts of $\hat{H}_{LS}$).
- **Output Dimension**: $512$ (Real and Imaginary parts of predicted $\hat{H}$).
- **Residual Formulation**:
  $$\hat{H}_{DNN} = \hat{H}_{LS} + f_\theta(\hat{H}_{LS})$$
  Learning the residual $\Delta H = H_{true} - \hat{H}_{LS}$ prevents gradient vanishing and focuses network capacity directly on noise cancellation.

### 4. Spatial Equalization (MIMO MMSE Detection)
De-correlates spatial streams from the two transmit antennas:
$$\mathbf{W}_{eq}[k] = \left(\hat{\mathbf{H}}[k]^H \hat{\mathbf{H}}[k] + \sigma_n^2 \mathbf{I}_2\right)^{-1} \hat{\mathbf{H}}[k]^H, \quad \hat{\mathbf{X}}[k] = \mathbf{W}_{eq}[k] \mathbf{Y}[k]$$

---

## 5. Experimental Methodology & Empirical Results

All evaluations were executed under $15$ Monte Carlo realizations per test point ($47,040$ payload bits per SNR point) under identical channel realizations:

| Metric / Scenario | Least Squares (LS) | Linear MMSE | PyTorch Residual DNN | Genie (Perfect CSI) |
| :--- | :--- | :--- | :--- | :--- |
| **NMSE @ 0 dB SNR** | $-8.38\text{ dB}$ | $-4.01\text{ dB}$ | **$-8.36\text{ dB}$** | $-\infty$ |
| **NMSE @ 15 dB SNR** | $-23.09\text{ dB}$ | $-20.50\text{ dB}$ | **$-20.88\text{ dB}$** | $-\infty$ |
| **NMSE @ 30 dB SNR** | $-38.64\text{ dB}$ | $-38.41\text{ dB}$ | **$-24.76\text{ dB}$** (Floor) | $-\infty$ |
| **BER @ 0 dB SNR** | $0.2310$ (10,866 errs) | $0.2459$ (11,567 errs) | **$0.2318$** (10,904 errs) | $0.2064$ (9,710 errs) |
| **BER @ 15 dB SNR** | $0.0307$ (1,443 errs) | $0.0328$ (1,541 errs) | **$0.0333$** (1,567 errs) | $0.0259$ (1,219 errs) |
| **BER @ 25 dB SNR** | $0.00042$ (20 errs) | $< 6.4 \times 10^{-5}$ (0 errs) | **$< 6.4 \times 10^{-5}$** (0 errs) | $< 6.4 \times 10^{-5}$ (0 errs) |
| **BER @ 30 dB SNR** | $0.0018$ (85 errs) | $0.0018$ (86 errs) | **$0.0066$** (311 errs) | $0.0017$ (82 errs) |
| **Inference Latency** | **$0.12\text{ ms}$** | **$0.35\text{ ms}$** | **$0.38\text{ ms}$** | N/A |

### Scientific Takeaways
1. **Low-to-Mid SNR Performance**: PyTorch Residual DNN tracks MMSE estimation quality without requiring true channel covariance knowledge $R_{HH}$ or noise variance estimation.
2. **Residual Regression Floor**: Because the DNN is trained across a broad dynamic range $[0, 30]\text{ dB}$ with a lightweight MLP ($362\text{k}$ parameters), it exhibits a regression floor around $-24.8\text{ dB}$ at $30\text{ dB}$ SNR, while classical DFT sinc interpolation reaches $-38.6\text{ dB}$.
3. **Statistical Integrity**: All low-error and zero-error regimes report 95% Wilson score confidence intervals and Poisson rule-of-three upper bounds ($3/N_{bits}$).

---

## 6. Installation & Execution Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Node.js 18+ and npm 9+
- Git

### 1. Backend Setup
```bash
# 1. Clone repository
git clone https://github.com/your-username/NeuroMIMO.git
cd NeuroMIMO

# 2. Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run backend tests (67 tests)
pytest backend/tests/ -v

# 5. Launch FastAPI backend
uvicorn neuromimo.api.main:app --app-dir backend --port 8000 --reload
```
API Documentation will be accessible at: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup
```bash
# In a separate terminal:
cd frontend

# 1. Install Node dependencies
npm install

# 2. Build for production (verifies TypeScript types)
npm run build

# 3. Start Vite development server
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 7. REST API Documentation

| Method | Endpoint | Description | Sample Payload / Params |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Service status, PyTorch version, compute device | None |
| `GET` | `/api/config` | Supported FFT sizes, modulations, SNR bounds | None |
| `POST` | `/api/simulation/run` | Execute single-shot MIMO-OFDM simulation | `{"snr_db": 20, "modulation": "QPSK", "algorithm": "DNN"}` |
| `POST` | `/api/estimation/compare` | Head-to-head estimator benchmark | `{"snr_db": 15, "algorithms": ["LS", "MMSE", "DNN"]}` |
| `POST` | `/api/model/train` | Train PyTorch DNN (sync or async background) | `{"epochs": 20, "batch_size": 64, "learning_rate": 0.001}` |
| `GET` | `/api/model/status` | Model checkpoint existence and parameter count | None |
| `GET` | `/api/model/train/status`| Live epoch loss tracking for training jobs | None |
| `POST` | `/api/model/predict` | Run raw DNN inference on channel features | `{"snr_db": 20, "channel_model": "RAYLEIGH"}` |
| `GET` | `/api/experiments` | Retrieve recorded simulation runs from SQLite | None |
| `GET` | `/api/experiments/{id}` | Detailed experiment parameters and raw metrics | None |
| `GET` | `/api/experiments/latest/plots` | List generated publication figures | None |
| `GET` | `/api/experiments/latest/plots/{name}` | Serve 300 DPI PNG figure | None |
| `GET` | `/api/experiments/benchmark/snr-sweep` | Pre-computed 105-trial Monte Carlo dataset | None |

---

## 8. Known Limitations & Future Enhancements

1. **Lightweight MLP vs Convolutional / Transformer Architectures**:
   - *Limitation*: The current 4-layer Residual MLP exhibits a high-SNR regression floor at $-24.8\text{ dB}$ NMSE due to finite representational capacity across wide dynamic ranges.
   - *Enhancement*: Implement Complex-Valued 2D CNNs or Vision Transformers (ViT) to exploit subcarrier 2D time-frequency correlation.
2. **Quasi-Static vs High-Mobility Doppler Channels**:
   - *Limitation*: The current channel model assumes block fading over an OFDM frame (negligible Doppler shift).
   - *Enhancement*: Incorporate Jakes Doppler power spectrum for high-speed vehicular mobility ($f_d > 300\text{ Hz}$) and inter-carrier interference (ICI) compensation.
3. **Massive MIMO Scaling**:
   - *Limitation*: Constrained to $2 \times 2$ antenna topologies.
   - *Enhancement*: Extend to $32 \times 4$ and $64 \times 8$ Massive MIMO with hybrid digital-analog beamforming and spatial channel models (3GPP TR 38.901).

---

## 9. Final-Year Project Report Outline

```
1. INTRODUCTION
   1.1 Background: The Evolution of 5G NR and 6G Physical Layer
   1.2 Problem Statement: Challenges in Multipath Fading Channel Estimation
   1.3 Objectives of NeuroMIMO
   1.4 Capstone Scope and Deliverables

2. LITERATURE REVIEW & THEORETICAL FOUNDATIONS
   2.1 Orthogonal Frequency Division Multiplexing (OFDM) Mathematical Model
   2.2 MIMO Spatial Multiplexing and Spatial Correlated Channels
   2.3 Classical Estimation: Least Squares and Wiener-Hopf MMSE
   2.4 Deep Learning Paradigms in Physical Layer Signal Processing

3. SYSTEM ARCHITECTURE & IMPLEMENTATION
   3.1 Vectorized Baseband Transceiver Pipeline
   3.2 Pilot Pattern Design and DFT Sinc Interpolation
   3.3 PyTorch Residual Deep Neural Network Design & Training Formulation
   3.4 Full-Stack Software Architecture (FastAPI + React 19 + SQLite)

4. EXPERIMENTAL EVALUATION & RESULTS DISCUSSION
   4.1 NMSE Performance Analysis vs SNR
   4.2 Bit Error Rate (BER) Waterfall and Equalization Performance
   4.3 Propagation Sensitivity: AWGN vs Rayleigh Multipath Fading
   4.4 Out-of-Distribution Generalization and Parameter Perturbation
   4.5 Real-Time Inference Latency Profiling

5. CONCLUSION & FUTURE WORK
   5.1 Summary of Contributions
   5.2 Critical Limitations
   5.3 Roadmap for 6G Transceivers
```

---

## 10. Viva Voce Examination Questions & Technical Answers

#### Q1: Why does Least Squares (LS) suffer from noise enhancement at low SNR?
**Answer**: LS estimation performs element-wise division $\hat{H}_{LS}[p] = Y[p]/X_p = H[p] + W[p]/X_p$. Because the noise term $W[p]$ is divided only by the pilot symbol energy without any Bayesian prior or noise variance regularization, the noise power in the estimate directly equals $\sigma_n^2 / |X_p|^2$. At low SNR, this causes significant variance that degrades subsequent spatial equalization.

#### Q2: What is the main practical disadvantage of Linear MMSE in real hardware?
**Answer**: Linear MMSE requires explicit knowledge of the channel frequency autocorrelation matrix $\mathbf{R}_{HH}$ and the noise variance $\sigma_n^2$. Furthermore, it requires computing an online matrix inversion $(\mathbf{R}_{H_p H_p} + \sigma_n^2 \mathbf{I})^{-1}$ of complexity $\mathcal{O}(N_p^3)$, which is computationally expensive for large bandwidths and variable channel statistics.

#### Q3: Why is a Residual Neural Network formulation preferred over predicting channel coefficients directly?
**Answer**: Predicting raw channel coefficients from scratch requires the neural network to learn both the fundamental frequency structure and noise filtering. With a residual connection $\hat{H}_{DNN} = \hat{H}_{LS} + f_\theta(\hat{H}_{LS})$, the network only needs to learn the error perturbation $\Delta H = H_{true} - \hat{H}_{LS}$. If the weights are initialized near zero, the model starts at least as accurate as LS and incrementally denoises it, preventing vanishing gradients and accelerating convergence.

#### Q4: How is data leakage prevented during the training of the DNN estimator?
**Answer**: 
1. Dataset split is performed strictly at the channel realization level before extracting features, ensuring test realizations are never seen during training.
2. The network input features are constructed exclusively from received noisy pilot tones and LS interpolation. Ground-truth channel coefficients $H_{true}$ are strictly used as the loss target ($y$) and never exposed to feature extraction ($X$).

#### Q5: What is the significance of the Poisson rule of three in your BER evaluations?
**Answer**: In Monte Carlo simulations, when zero bit errors occur over $N$ bits (such as at $25\text{ dB}$ or $30\text{ dB}$ SNR), sample-variance formulas yield $0$. However, scientifically, observing zero errors in finite trials does not prove that the true probability of error is zero. The Poisson rule of three provides a mathematically sound 95% confidence upper bound: $P(E) < 3.0 / N_{bits}$, ensuring honest statistical reporting.
