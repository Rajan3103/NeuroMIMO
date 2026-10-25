```
 ╔═════════════════════════════════════════════════════════════════════════════════════════╗
 ║  ┌──(neuromimo㉿root)-[~/wireless-dsp]                                                  ║
 ║  └─$ ./launch_neuromimo.sh --mimo 2x2 --subcarriers 64 --estimator DNN-RESIDUAL         ║
 ║                                                                                         ║
 ║   ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ███╗   ███╗██╗███╗   ███╗ ██████╗         ║
 ║   ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗████╗ ████║██║████╗ ████║██╔═══██╗        ║
 ║   ██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║██╔████╔██║██║██╔████╔██║██║   ██║        ║
 ║   ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██║╚██╔╝██║██║██║╚██╔╝██║██║   ██║        ║
 ║   ██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝██║ ╚═╝ ██║██║██║ ╚═╝ ██║╚██████╔╝        ║
 ║   ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝     ╚═╝ ╚═════╝         ║
 ║                                                                                         ║
 ║   [SYSTEM INITIALIZED]: NeuroMIMO — AI-Enhanced MIMO-OFDM Channel Estimation Platform   ║
 ╚═════════════════════════════════════════════════════════════════════════════════════════╝
```

<div align="center">

[![FastAPI](https://img.shields.io/badge/⚡_Backend-FastAPI_0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/⚛️_Frontend-React_19_Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![PyTorch](https://img.shields.io/badge/🔥_Deep_Learning-PyTorch_2.0+-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![NumPy SciPy](https://img.shields.io/badge/📐_DSP_Engine-NumPy_&_SciPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![SQLite](https://img.shields.io/badge/🗄️_Database-SQLite3_Audit-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tailwind](https://img.shields.io/badge/🎨_UI_Theme-Tailwind_&_Recharts-38B2AC?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![MIMO-OFDM](https://img.shields.io/badge/📡_Physical_Layer-2x2_MIMO_OFDM-7289DA?style=for-the-badge)](https://github.com/Rajan3103/NeuroMIMO)

</div>

---

### 🖥️ `SYS_DIAGNOSTICS // SYSTEM STATUS`

```console
[root@neuromimo-transceiver ~]# systemctl status neuromimo-engine.service
● neuromimo-engine.service - NeuroMIMO 2x2 MIMO-OFDM & AI Estimation Core Engine
     Loaded: loaded (/etc/systemd/system/neuromimo-engine.service; enabled)
     Active: active (running) since Tue 2026-10-13 18:25:00 UTC; 12ms ago
   Main PID: 8000 (uvicorn-fastapi)
      Tasks: 18 (limit: 4915)
     Memory: 218.4M
        CPU: 142ms
     CGroup: /system.slice/neuromimo-engine.service
             ├─ 8000 python -m uvicorn neuromimo.api.main:app --host 0.0.0.0 --port 8000
             └─ 5173 node /frontend/node_modules/.bin/vite --host

[DSP_STREAM] Physical Layer 2x2 MIMO-OFDM (64-FFT, CP-16)... INITIALIZED.
[DSP_STREAM] Channel Models: AWGN & 4-Tap Rayleigh Multipath (Exp-PDP)... CALIBRATED.
[DSP_STREAM] PyTorch Residual Deep Neural Network (neuromimo_dnn.pt)... LOADED (362K Params).
[DSP_STREAM] Conventional Estimators: LS (DFT Sinc) & Bayesian LMMSE... READY.
[DSP_STREAM] SQLite Experiment Registry (backend/data/experiments.db)... CONNECTED.
[DSP_STREAM] Vite Frontend GUI (http://localhost:5173)... ONLINE.
```

---

### ⚡ `CAPABILITIES // CORE MODULES`

```bash
$ neuromimo-cli --list-modules

  [MOD-01] 📡 2×2 MIMO-OFDM VECTORIZED BASEBAND ENGINE
           └─ End-to-end transceiver implementing Gray-coded QPSK & 16-QAM symbol mapping.
           └─ 64-point IFFT/FFT modulation grid with 16-sample cyclic prefix (CP) for ISI mitigation.
           └─ Orthogonal comb pilot multiplexing (Tx0: {0,16,32,48}, Tx1: {8,24,40,56}) with zero pilot contamination.

  [MOD-02] 📐 LEAST SQUARES (LS) & OPTIMAL DFT SINC INTERPOLATION
           └─ Direct pilot tone de-rotation: H_LS[p] = Y[p] / X[p].
           └─ High-fidelity continuous CFR reconstruction via alias-free IDFT, phase de-rotation, and zero-padded FFT.
           └─ Achieves theoretical zero interpolation error in noiseless channel environments.

  [MOD-03] 🎯 BAYESIAN LINEAR MINIMUM MEAN SQUARE ERROR (LMMSE)
           └─ Closed-form Wiener-Hopf estimator: H_MMSE = R_HP (R_PP + σ² I)⁻¹ H_LS.
           └─ Exact channel autocorrelation derived from 4-tap exponential Power Delay Profile (PDP).
           └─ Optimal Bayesian noise suppression across low and medium SNR operating conditions.

  [MOD-04] 🧠 PYTORCH RESIDUAL DEEP NEURAL NETWORK (DNN)
           └─ 4-layer Fully Connected Residual MLP mapping 512-dimensional complex tensor features.
           └─ Residual learning formulation: H_DNN = H_LS + f_θ(H_LS) directly learns noise perturbation ΔH.
           └─ Leakage-free dataset splitting strictly partitioned by independent channel realization seeds.

  [MOD-05] 📶 SPATIAL EQUALIZATION & SIGNAL RECOVERY (ZF / MMSE)
           └─ De-correlates dual spatial data streams: W_eq = (H^H H + σ² I₂)⁻¹ H^H.
           └─ Soft Gray demapping calculating empirical Bit Error Rate (BER) and Symbol Error Rate (SER).

  [MOD-06] 📊 REPRODUCIBLE MONTE CARLO BENCHMARKING SUITE
           └─ Automated 105-trial Monte Carlo benchmark per SNR point (47,040 bits/point).
           └─ Wilson score 95% confidence intervals and Poisson rule-of-three upper bounds for zero-error regimes.
           └─ Publication-grade 300 DPI figures for NMSE vs SNR, BER vs SNR, AWGN vs Rayleigh, and latency profiling.

  [MOD-07] 💻 FULL-STACK RESEARCH DASHBOARD & RECHARTS LAB
           └─ Modern React 19 + TypeScript dashboard with dark-mode aesthetic and responsive navigation.
           └─ Interactive constellation diagrams, 64-tone CFR spectrum views, live telemetry cards, and SQLite run logs.
```

---

### 📁 `DIRECTORY_TREE // REPOSITORY MAP`

```console
NeuroMIMO/
├── 📄 README.md                        # Master project documentation, setup & report
├── 📄 requirements.txt                 # Backend Python package dependencies
├── 📄 .env.example                     # Environment configuration template
├── 📄 WMC.pdf                          # Wireless Mobile Communication syllabus & reference
├── 📁 backend/
│   ├── 📁 data/
│   │   └── 📄 experiments.db           # SQLite database for simulation audit trail
│   ├── 📁 models/
│   │   └── 📄 neuromimo_dnn.pt         # Pre-trained PyTorch Residual DNN checkpoint
│   ├── 📁 results/                     # High-res 300 DPI research figures & benchmark datasets
│   │   ├── 📊 ber_vs_snr.png           # BER waterfall curves (LS vs MMSE vs DNN vs Genie)
│   │   ├── 📊 nmse_vs_snr.png          # Channel estimation NMSE vs SNR (dB)
│   │   ├── 📊 channel_model_comparison.png # AWGN vs Multipath Rayleigh ablation
│   │   ├── 📊 generalization_evaluation.png # Out-of-distribution unseen seed test
│   │   ├── 📊 inference_runtime.png    # Millisecond execution latency comparison
│   │   ├── 📊 pilot_density_comparison.png # Pilot density sensitivity curves
│   │   └── 📄 snr_sweep_results.json   # Full benchmark experimental data
│   ├── 📁 neuromimo/                   # Core Python package
│   │   ├── 📄 config.py                # Simulation configuration & Pydantic schemas
│   │   ├── 📁 wireless/                # Physical layer: QPSK/QAM, OFDM, 4-tap Rayleigh, MMSE Eq
│   │   ├── 📁 estimation/              # Conventional LS, LMMSE, PyTorch DNN architecture & trainer
│   │   ├── 📁 evaluation/              # Monte Carlo engine, Wilson CI, 6 benchmark experiments
│   │   ├── 📁 storage/                 # SQLite ORM & run history logger
│   │   └── 📁 api/                     # FastAPI app, REST routers, async background jobs
│   └── 📁 tests/                       # 28 Pytest unit & integration tests
└── 📁 frontend/                        # React 19 + TypeScript + Vite + Tailwind CSS Dashboard
    ├── 📄 package.json                 # Node dependencies
    ├── 📄 vite.config.ts               # Vite bundler & API reverse proxy
    ├── 📄 tailwind.config.js           # Dark theme design system
    ├── 📁 public/results/              # Static publication plots gallery
    └── 📁 src/
        ├── 📁 api/client.ts            # Type-safe Axios REST API client
        ├── 📁 components/              # StatCard, Badge, Modal, Navbar, Sidebar
        ├── 📁 pages/                   # 8 Interactive Research Pages (Overview, Sim, Lab, Train, etc.)
        └── 📁 types/index.ts           # Shared TypeScript interfaces
```

---

### 🚀 `QUICKSTART // RUNNING NEUROMIMO`

#### 1️⃣ Clone & Configure Environment
```bash
$ git clone https://github.com/Rajan3103/NeuroMIMO.git
$ cd NeuroMIMO

# Copy example environment configuration
$ cp .env.example .env
```

#### 2️⃣ Launch Backend DSP Engine (Python 3.10+)
```bash
# Create and activate Python virtual environment
$ python -m venv .venv

# On Linux/macOS:
$ source .venv/bin/activate
# On Windows PowerShell:
$ .venv\Scripts\Activate.ps1

# Install physical layer & ML dependencies
$ pip install -r requirements.txt

# Run full test suite (83 unit and API tests)
$ pytest backend/tests/ -v

# Launch FastAPI core engine
$ uvicorn neuromimo.api.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload

# [OUTPUT]:
# INFO:     Started server process [8000]
# INFO:     Waiting for application startup.
# [Database] SQLite connected successfully to 'backend/data/experiments.db'.
# [Model] PyTorch Residual DNN loaded from 'backend/models/neuromimo_dnn.pt' (330,112 params).
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Swagger docs at /docs)
```

#### 3️⃣ Launch Frontend Research Dashboard (Node 18+)
```bash
$ cd frontend

# Install UI dependencies
$ npm install

# Build to verify TypeScript types
$ npm run build

# Start Vite development server
$ npm run dev

# [OUTPUT]:
#   VITE v6.4.1  ready in 180 ms
#   ➜  Local:   http://localhost:5173/
#   ➜  Network: use --host to expose
```

---

### 📊 `SCIENTIFIC_BENCHMARKS // EMPIRICAL VALIDATION`

All evaluations were executed over $15$ independent Monte Carlo channels per SNR test point ($47,040$ payload bits per evaluation point):

| Metric / Scenario | Least Squares (LS) | Linear MMSE | PyTorch Residual DNN | Genie (Perfect CSI) |
| :--- | :--- | :--- | :--- | :--- |
| **NMSE @ 0 dB SNR** | $-8.38\text{ dB}$ | $-9.05\text{ dB}$ | **$-8.67\text{ dB}$** | $-\infty$ |
| **NMSE @ 15 dB SNR** | $-23.09\text{ dB}$ | $-23.19\text{ dB}$ | **$-19.56\text{ dB}$** | $-\infty$ |
| **NMSE @ 30 dB SNR** | $-38.64\text{ dB}$ | $-38.64\text{ dB}$ | **$-25.96\text{ dB}$** (Floor) | $-\infty$ |
| **BER @ 0 dB SNR** | $0.2310$ (10,866 errs) | $0.2309$ (10,860 errs) | **$0.2316$ (10,893 errs)** | $0.2064$ (9,710 errs) |
| **BER @ 15 dB SNR** | $0.0307$ (1,443 errs) | $0.0306$ (1,438 errs) | **$0.0334$ (1,570 errs)** | $0.0259$ (1,219 errs) |
| **BER @ 25 dB SNR** | $0.0067$ (314 errs) | $0.0067$ (317 errs) | **$0.0108$ (506 errs)** | $0.0054$ (252 errs) |
| **BER @ 30 dB SNR** | $0.0018$ (85 errs) | $0.0018$ (85 errs) | **$0.0043$ (201 errs)** | $0.0017$ (82 errs) |
| **Inference Latency** | **$0.12\text{ ms}$** | **$0.40\text{ ms}$** | **$0.65\text{ ms}$** | N/A |

#### Key Scientific Takeaways:
1. **Low-SNR Behaviour**: LMMSE is best at 0 dB ($-9.05\text{ dB}$), as theory predicts. The PyTorch Residual DNN ($-8.67\text{ dB}$) is slightly better than LS ($-8.38\text{ dB}$) without requiring the channel covariance matrix $\mathbf{R}_{HH}$ or noise variance $\sigma_n^2$.
2. **Residual Regression Floor**: Because the DNN is trained across a wide dynamic range $[0, 30]\text{ dB}$ with a lightweight MLP ($330\text{k}$ parameters), it levels off around $-26.0\text{ dB}$ at $30\text{ dB}$ SNR, while classical DFT sinc interpolation reaches $-38.6\text{ dB}$.
3. **Statistical Confidence**: All zero-error regimes report 95% Wilson score confidence intervals and Poisson rule-of-three upper bounds ($3/N_{bits}$).

---

### 🛰️ `DEEPMIMO // RAY-TRACED CHANNELS`

Besides its built-in Rayleigh channels, NeuroMIMO can train and benchmark on ray-traced channels from [DeepMIMO](https://deepmimo.net).

1. Generate OFDM channels with DeepMIMO using **at least 2 antennas** at both the base station and the user, and **64 or more subcarriers**.
2. Save the channel array, shaped `(users, rx_antennas, tx_antennas, subcarriers)`:
   ```python
   import numpy as np
   # DeepMIMO v4:  channels = dataset.compute_channels(params)
   # DeepMIMO v3:  channels = dataset[0]['user']['channel']
   np.save("channels.npy", channels)
   ```
3. Benchmark LS, LMMSE, DNN and perfect CSI on those channels, or train a DNN on them:
   ```bash
   cd backend
   python -m neuromimo.evaluation.deepmimo_cli channels.npy --trials 15
   python -m neuromimo.estimation.train_cli --deepmimo channels.npy --output models/deepmimo_dnn.pt
   ```

The loader (`neuromimo/wireless/deepmimo.py`) keeps the first 2×2 antennas, picks 64 evenly spaced subcarriers, drops users with no propagation paths and normalises each channel to unit power. LMMSE uses the delay profile measured from the loaded channels, and training splits by user so no user appears in two splits. `.npz` and `.mat` files work too (`--key` picks the array).

> Ray-traced channels can be longer than the 4 pilots per antenna can resolve, so expect an NMSE floor for every estimator when the delay spread is large.

---

### 💻 `REST API // ENDPOINT CHEATSHEET`

```http
# System & Health
GET    /api/health                     --> System status, compute device (CUDA/CPU), PyTorch version
GET    /api/config                     --> Transceiver parameters (64-FFT, CP-16, modulation options)

# Physical Layer Simulation & Estimation Lab
POST   /api/simulation/run             --> Execute single-shot 2x2 MIMO-OFDM transmission
POST   /api/estimation/compare         --> Head-to-head estimator benchmark (LS vs MMSE vs DNN)

# Deep Learning Engine
POST   /api/model/train                --> Launch PyTorch DNN model training (sync or background)
GET    /api/model/status               --> Check checkpoint availability & parameter count
GET    /api/model/train/status         --> Live epoch loss tracking & background progress
POST   /api/model/predict              --> Execute raw DNN inference on channel features

# Experiment History & Research Figures
GET    /api/experiments                --> Query persisted SQLite simulation runs
GET    /api/experiments/{id}           --> Retrieve experiment configuration & metrics
GET    /api/experiments/latest/plots   --> List available 300 DPI research figures
GET    /api/experiments/latest/plots/{name} --> Stream high-res PNG figure
GET    /api/experiments/benchmark/snr-sweep --> Pre-computed 105-trial Monte Carlo dataset
```

---

### 📄 `LICENSE // MIT`

```console
Distributed under the MIT License. See LICENSE for details.
NeuroMIMO Research Platform © 2026. Built with Python, PyTorch, FastAPI, React 19 & Tailwind CSS.
```
