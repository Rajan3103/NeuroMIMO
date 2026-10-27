import React, { useState } from 'react';
import {
  Radio,
  Cpu,
  BrainCircuit,
  Terminal,
  BookOpen,
  TrendingDown,
  ShieldCheck,
  Image as ImageIcon,
  Maximize2,
  ExternalLink,
  CheckCircle2,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';

interface ResultFigure {
  id: string;
  title: string;
  filename: string;
  src: string;
  category: 'Accuracy' | 'Recovery' | 'Complexity';
  caption: string;
  takeaway: string;
  badge: string;
}

const RESULT_FIGURES: ResultFigure[] = [
  {
    id: 'nmse',
    title: 'NMSE vs SNR Waterfall Curve',
    filename: 'nmse_vs_snr.png',
    src: '/results/nmse_vs_snr.png',
    category: 'Accuracy',
    caption: 'Normalized Mean Squared Error comparison under multipath Rayleigh fading across SNR points 0 to 30 dB.',
    takeaway: 'At 0 dB LMMSE is best (-9.1 dB) and the DNN (-8.7 dB) slightly beats LS (-8.4 dB). Above 15 dB the DNN levels off near -25 dB while LS and LMMSE reach -38.6 dB at 30 dB.',
    badge: '105 Monte Carlo Trials',
  },
  {
    id: 'ber',
    title: 'Bit Error Rate (BER) Waterfall Curve',
    filename: 'ber_vs_snr.png',
    src: '/results/ber_vs_snr.png',
    category: 'Recovery',
    caption: 'End-to-end BER after channel estimation and 2×2 MMSE spatial equalization with QPSK modulation.',
    takeaway: 'LS and LMMSE reach BER 1.8 × 10⁻³ at 30 dB; the DNN high-SNR floor raises its BER to 4.3 × 10⁻³. Every point carries a 95% Wilson interval.',
    badge: 'Post-Equalization Recovery',
  },
  {
    id: 'channel_model',
    title: 'Channel Model Sensitivity Comparison',
    filename: 'channel_model_comparison.png',
    src: '/results/channel_model_comparison.png',
    category: 'Accuracy',
    caption: 'Performance comparison across frequency-flat AWGN versus 4-tap frequency-selective Rayleigh fading.',
    takeaway: 'On flat AWGN the DNN tracks LS closely (-35.5 dB vs -38.6 dB at 30 dB); Rayleigh multipath exposes its high-SNR floor.',
    badge: 'AWGN vs Rayleigh Multipath',
  },
  {
    id: 'generalization',
    title: 'Generalization & Parameter Mismatch',
    filename: 'generalization_evaluation.png',
    src: '/results/generalization_evaluation.png',
    category: 'Accuracy',
    caption: 'Evaluation on channel realizations excluded from training and perturbed power-delay profile decay constants.',
    takeaway: 'At 15 dB the DNN drops from -22.7 dB in-distribution to -18.5 dB when the delay-profile decay changes to 2.5, while LS and LMMSE stay near -24 dB.',
    badge: 'Held-Out Realizations',
  },
  {
    id: 'runtime',
    title: 'Inference Latency & Computational Cost',
    filename: 'inference_runtime.png',
    src: '/results/inference_runtime.png',
    category: 'Complexity',
    caption: 'Per-frame computational runtime benchmark comparing PyTorch tensor operations against LS and MMSE matrix inversion.',
    takeaway: 'Mean latency per frame on CPU: LS 0.12 ms, LMMSE 0.40 ms, DNN 0.65 ms, all within a 1 ms 5G NR slot.',
    badge: 'ms / OFDM Frame',
  },
  {
    id: 'pilot_density',
    title: 'Pilot-Density Scaling Analysis',
    filename: 'pilot_density_comparison.png',
    src: '/results/pilot_density_comparison.png',
    category: 'Complexity',
    caption: 'Estimation NMSE scaling as a function of comb pilot subcarrier spacing (4, 8, and 16 tones).',
    takeaway: 'With 2 pilots per antenna (spacing 16) every estimator fails (about -4 dB NMSE): a 4-tap channel needs at least 4 pilots.',
    badge: 'Overhead Trade-off',
  },
];

export const AboutPage: React.FC = () => {
  const [selectedFigure, setSelectedFigure] = useState<ResultFigure | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('ALL');

  const filteredFigures = RESULT_FIGURES.filter((fig) => {
    if (filterCategory === 'ALL') return true;
    return fig.category === filterCategory;
  });

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 mb-1.5">
          <Badge variant="cyan">ENGINEERING SPECIFICATION & METHODOLOGY</Badge>
          <span className="text-[10px] font-mono text-slate-400">IEEE 802.11ax / 3GPP 5G NR NR-MIMO</span>
        </div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Project Methodology & Theory</h2>
        <p className="text-sm text-slate-400 mt-1">
          Theoretical architecture, mathematical formulations, and empirical verification principles of NeuroMIMO.
        </p>
      </div>

      {/* Architecture Highlights Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="glass-panel p-5 space-y-3">
          <div className="flex items-center gap-2 text-cyan-400 font-semibold text-xs">
            <Radio className="w-4 h-4" />
            <span>2×2 MIMO-OFDM Physical Layer</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Combines spatial multiplexing across 2 transmit and 2 receive antennas with 64-point FFT OFDM and a 16-sample
            cyclic prefix to combat multipath delay spread.
          </p>
        </div>

        <div className="glass-panel p-5 space-y-3">
          <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs">
            <Cpu className="w-4 h-4" />
            <span>Multi-Paradigm Estimation</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Directly benchmarks conventional Least Squares (LS) and Bayesian Linear MMSE with a PyTorch Deep Residual Neural
            Network under identical test realizations.
          </p>
        </div>

        <div className="glass-panel p-5 space-y-3">
          <div className="flex items-center gap-2 text-purple-400 font-semibold text-xs">
            <BrainCircuit className="w-4 h-4" />
            <span>Residual Neural Learning</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Instead of predicting channel coefficients from scratch, the neural network learns a residual noise-cancellation
            filter applied directly to the LS pilot estimate.
          </p>
        </div>
      </div>

      {/* Detailed Formulations Section */}
      <div className="glass-panel p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-cyan-400" />
            <span>Mathematical Formulations</span>
          </h3>
          <span className="text-xs font-mono text-slate-400">Complex Baseband Equivalents</span>
        </div>

        <div className="space-y-6 text-xs text-slate-300">
          {/* 1. Baseband OFDM Model */}
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white">1. MIMO-OFDM Baseband Input-Output Model</span>
              <span className="font-mono text-[11px] text-cyan-400">Per-Subcarrier Decomposition</span>
            </div>
            <p className="text-slate-400">
              By prepending a cyclic prefix of duration T_cp &gt; tau_max, the circular convolution in the time
              domain transforms into scalar matrix multiplication in the frequency domain:
            </p>
            <div className="p-3 rounded-lg bg-slate-950 font-mono text-cyan-300 text-[12px] border border-slate-800/80">
              {'Y[k] = H[k] X[k] + W[k]   ∈ ℂ^(2 × 1)'}
            </div>
            <p className="text-[11px] text-slate-400">
              {'Where H[k] ∈ ℂ^(2×2) is the channel frequency response matrix at subcarrier k, X[k] ∈ ℂ^(2×1) is the transmitted symbol vector, and W[k] ~ CN(0, σ_w² I_2) is additive white Gaussian noise.'}
            </p>
          </div>

          {/* 2. Estimator Equations */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <span className="font-semibold text-orange-400 block">Least Squares (LS)</span>
              <div className="p-2 rounded bg-slate-950 font-mono text-[11px] text-orange-300 border border-slate-800">
                {'Ĥ_LS[p] = Y[p] / X_p'}
              </div>
              <p className="text-[11px] text-slate-400">
                Minimizes ||Y_p - H X_p||². Computationally cheap but severely suffers from noise enhancement at low SNR.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <span className="font-semibold text-emerald-400 block">Linear MMSE (LMMSE)</span>
              <div className="p-2 rounded bg-slate-950 font-mono text-[11px] text-emerald-300 border border-slate-800">
                {'W = R_HHp (R_Hp_Hp + σ² I)⁻¹'}
              </div>
              <p className="text-[11px] text-slate-400">
                Optimal linear Bayesian estimator. Requires known channel covariance matrix R_HH and real-time matrix inversion.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <span className="font-semibold text-purple-400 block">PyTorch Residual DNN</span>
              <div className="p-2 rounded bg-slate-950 font-mono text-[11px] text-purple-300 border border-slate-800">
                {'Ĥ_DNN = Ĥ_LS + f_θ(Ĥ_LS)'}
              </div>
              <p className="text-[11px] text-slate-400">
                Residual connection maps LS input 512 → 256 → 128 → 256 → 512, directly learning non-linear noise cancellation.
              </p>
            </div>
          </div>

          {/* 3. Spatial Equalization */}
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white">2. Spatial Multiplexing Equalization (MIMO Detection)</span>
              <span className="font-mono text-[11px] text-purple-400">MMSE Equalizer</span>
            </div>
            <p className="text-slate-400">
              Signals from the 2 transmit antennas are decoupled at the receiver using the estimated channel matrix H_hat[k]:
            </p>
            <div className="p-3 rounded-lg bg-slate-950 font-mono text-purple-300 text-[12px] border border-slate-800/80">
              {'W_eq[k] = (Ĥ[k]^H Ĥ[k] + σ_w^2 I_2)⁻¹ Ĥ[k]^H,    X̂[k] = W_eq[k] Y[k]'}
            </div>
          </div>
        </div>
      </div>

      {/* Experimental Methodology & Statistical Rigor */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Monte Carlo Statistical Rigor</span>
          </h3>
          <span className="text-xs font-mono text-slate-400">Wilson Score & Poisson Bound</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs text-slate-300">
          <div className="space-y-2">
            <h4 className="font-semibold text-white">Wilson Score Confidence Intervals</h4>
            <p className="text-slate-400 leading-relaxed">
              To guarantee statistical credibility for low BER regimes (&lt; 10⁻³), 95% confidence intervals are computed using
              the Wilson score interval:
            </p>
            <div className="p-2.5 rounded bg-slate-950 font-mono text-cyan-300 text-[11px] border border-slate-800">
              {'CI = (p̂ + z²/2n ± z √(p̂(1-p̂)/n + z²/4n²)) / (1 + z²/n)'}
            </div>
            <p className="text-[11px] text-slate-500">
              Where p̂ is empirical BER, n is total bits, and z = 1.96.
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="font-semibold text-white">Zero-Error Upper Bounds (Poisson Rule of Three)</h4>
            <p className="text-slate-400 leading-relaxed">
              When 0 bit errors are observed at high SNR (25 dB, 30 dB), standard standard-deviation formulas collapse
              to 0. NeuroMIMO applies the Poisson rule of three to report statistically honest bounds:
            </p>
            <div className="p-2.5 rounded bg-slate-950 font-mono text-emerald-300 text-[11px] border border-slate-800">
              {'BER_upper = 3 / N_transmitted_bits'}
            </div>
            <p className="text-[11px] text-slate-500">
              Ensures zero-error points are documented with formal statistical upper limits.
            </p>
          </div>
        </div>
      </div>

      {/* Empirical Findings Summary Table */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-purple-400" />
            <span>Summary of Key Empirical Findings</span>
          </h3>
          <span className="text-xs text-slate-400">Rayleigh Fading Benchmark</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="pb-2.5 font-semibold">Evaluation Metric</th>
                <th className="pb-2.5 font-semibold text-orange-400">Least Squares (LS)</th>
                <th className="pb-2.5 font-semibold text-emerald-400">Linear MMSE</th>
                <th className="pb-2.5 font-semibold text-purple-400">PyTorch Residual DNN</th>
              </tr>
            </thead>
            <tbody className="divide-y border-slate-800/60 font-mono text-[11px]">
              <tr className="text-slate-300">
                <td className="py-2.5 font-sans font-semibold text-white">NMSE at 20 dB SNR</td>
                <td className="py-2.5 text-orange-400">-28.95 dB</td>
                <td className="py-2.5 text-emerald-400">-28.93 dB</td>
                <td className="py-2.5 text-purple-400 font-bold">-25.31 dB</td>
              </tr>
              <tr className="text-slate-300">
                <td className="py-2.5 font-sans font-semibold text-white">Prior CSI Statistics Needed</td>
                <td className="py-2.5 text-slate-400">None</td>
                <td className="py-2.5 text-rose-400">Requires True R_HH</td>
                <td className="py-2.5 text-emerald-400">None (Learned implicitly)</td>
              </tr>
              <tr className="text-slate-300">
                <td className="py-2.5 font-sans font-semibold text-white">BER at 25 dB SNR (QPSK)</td>
                <td className="py-2.5 text-orange-400">6.7 × 10⁻³</td>
                <td className="py-2.5 text-emerald-400">6.7 × 10⁻³</td>
                <td className="py-2.5 text-purple-400 font-bold">1.1 × 10⁻²</td>
              </tr>
              <tr className="text-slate-300">
                <td className="py-2.5 font-sans font-semibold text-white">Inference Latency</td>
                <td className="py-2.5 text-slate-400">0.12 ms</td>
                <td className="py-2.5 text-slate-400">0.40 ms</td>
                <td className="py-2.5 text-slate-400">0.65 ms</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Research Result Figures & Screenshots Section */}
      <div className="glass-panel p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-white">
                Empirical Research Result Figures & Screenshots
              </h3>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              High-resolution 300 DPI Matplotlib figures and empirical experiment outputs from 105 Monte Carlo trials. Click to expand.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setFilterCategory('ALL')}
              className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
                filterCategory === 'ALL'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              All (6)
            </button>
            <button
              onClick={() => setFilterCategory('Accuracy')}
              className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
                filterCategory === 'Accuracy'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Accuracy
            </button>
            <button
              onClick={() => setFilterCategory('Recovery')}
              className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
                filterCategory === 'Recovery'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Recovery
            </button>
            <button
              onClick={() => setFilterCategory('Complexity')}
              className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
                filterCategory === 'Complexity'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Complexity
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredFigures.map((fig) => (
            <div
              key={fig.id}
              onClick={() => setSelectedFigure(fig)}
              className="rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-cyan-500/50 transition-all cursor-pointer group flex flex-col overflow-hidden"
            >
              {/* Figure Preview Thumbnail */}
              <div className="relative aspect-[4/3] bg-slate-950 flex items-center justify-center overflow-hidden border-b border-slate-800/60 p-2">
                <img
                  src={fig.src}
                  alt={fig.title}
                  className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-slate-950/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 text-white text-xs font-semibold">
                  <Maximize2 className="w-4 h-4 text-cyan-400" />
                  <span>Expand High-Res (300 DPI)</span>
                </div>
              </div>

              {/* Figure Metadata & Takeaway */}
              <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-mono text-cyan-400 font-semibold px-2 py-0.5 rounded bg-cyan-950/40 border border-cyan-500/20">
                      {fig.badge}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">{fig.filename}</span>
                  </div>
                  <h4 className="text-xs font-bold text-white group-hover:text-cyan-400 transition-colors pt-0.5">
                    {fig.title}
                  </h4>
                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                    {fig.caption}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-800/60 flex items-start gap-1.5 text-[11px] text-emerald-400 bg-emerald-950/10 p-2 rounded-lg">
                  <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  <span className="leading-tight">{fig.takeaway}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Fullscreen Figure Modal */}
      {selectedFigure && (
        <Modal
          isOpen={!!selectedFigure}
          onClose={() => setSelectedFigure(null)}
          title={selectedFigure.title}
          subtitle={`Verified Research Artifact: ${selectedFigure.filename} • 300 DPI Publication Vector`}
          maxWidth="4xl"
        >
          <div className="space-y-4">
            <div className="w-full rounded-xl bg-slate-950 border border-slate-800 overflow-hidden flex items-center justify-center p-3">
              <img
                src={selectedFigure.src}
                alt={selectedFigure.title}
                className="w-full max-h-[70vh] object-contain"
              />
            </div>
            <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white">{selectedFigure.title}</span>
                <span className="text-[11px] font-mono text-cyan-400">{selectedFigure.badge}</span>
              </div>
              <p className="text-slate-400 leading-relaxed text-[11px]">
                {selectedFigure.caption}
              </p>
              <div className="p-2 rounded bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 text-[11px] flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                <span><strong>Key Empirical Takeaway:</strong> {selectedFigure.takeaway}</span>
              </div>
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-1">
                <span>File: {selectedFigure.filename}</span>
                <a
                  href={selectedFigure.src}
                  target="_blank"
                  rel="noreferrer"
                  className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-sans"
                >
                  <span>Open Full-Res in New Tab</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Reproducibility CLI commands */}
      <div className="glass-panel p-6 space-y-3">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <span>CLI Reproduction Commands</span>
        </h3>
        <p className="text-xs text-slate-400">
          Reproduce all simulation suites and backend integration tests directly from the terminal:
        </p>
        <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1.5 font-mono text-[11px] text-cyan-300">
          <div>{'# Run complete unit and integration test suite (67 tests)'}</div>
          <div className="text-slate-200">{'.venv\\Scripts\\python -m pytest backend/tests/ -v'}</div>
          <div className="pt-2 text-slate-500">{'# Launch the FastAPI REST service'}</div>
          <div className="text-slate-200">{'uvicorn neuromimo.api.main:app --app-dir backend --reload --port 8000'}</div>
          <div className="pt-2 text-slate-500">{'# Execute standalone benchmark runner with figure generation'}</div>
          <div className="text-slate-200">{'.venv\\Scripts\\python -m neuromimo.experiments.run_experiments'}</div>
        </div>
      </div>
    </div>
  );
};
