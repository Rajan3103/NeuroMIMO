import React, { useState } from 'react';
import {
  Radio,
  Cpu,
  Layers,
  Activity,
  Zap,
  BarChart2,
  ArrowRight,
  Play,
  CheckCircle2,
  Maximize2,
} from 'lucide-react';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { StatCard } from '../components/common/StatCard';
import { Badge } from '../components/common/Badge';
import { api } from '../api/client';
import type { HealthResponse, ModelStatus, SimulationResult } from '../types';
import type { NavTab } from '../components/layout/Sidebar';

interface OverviewPageProps {
  health: HealthResponse | null;
  modelStatus: ModelStatus | null;
  onNavigate: (tab: NavTab) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  health,
  modelStatus,
  onNavigate,
}) => {
  const [quickDemoLoading, setQuickDemoLoading] = useState<boolean>(false);
  const [demoResult, setDemoResult] = useState<SimulationResult | null>(null);

  const handleRunQuickDemo = async () => {
    setQuickDemoLoading(true);
    try {
      const res = await api.runSimulation({
        num_tx: 2,
        num_rx: 2,
        fft_size: 64,
        cp_length: 16,
        pilot_spacing: 8,
        modulation: 'QPSK',
        channel_model: 'RAYLEIGH',
        snr_db: 20.0,
        algorithm: 'LS',
        num_ofdm_symbols: 4,
        random_seed: 42,
      });
      setDemoResult(res);
    } catch (err) {
      console.error('Quick demo simulation failed:', err);
    } finally {
      setQuickDemoLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-panel p-6 sm:p-8 border-cyan-900/30 bg-gradient-to-r from-slate-900/90 via-panel/90 to-slate-900/90 relative overflow-hidden">
        <div className="relative z-10 max-w-3xl">
          <Badge variant="cyan" className="mb-3" dot>
            FINAL-YEAR ENGINEERING CAPSTONE
          </Badge>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight mb-2">
            AI-Enhanced MIMO-OFDM Channel Estimation & Signal Recovery
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed mb-5">
            A software-only wireless communication research platform comparing conventional
            channel estimators (<span className="text-cyan-400 font-semibold">Least Squares</span>,{' '}
            <span className="text-emerald-400 font-semibold">Linear MMSE</span>) with deep neural network architectures (
            <span className="text-purple-400 font-semibold">PyTorch Residual MLP</span>) in a 2×2 MIMO-OFDM physical layer.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate('simulator')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs tracking-wider uppercase transition-all shadow-lg shadow-cyan-950/50"
            >
              <span>Open Simulator</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={handleRunQuickDemo}
              disabled={quickDemoLoading}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs tracking-wider uppercase transition-all shadow-lg shadow-purple-950/50 disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${quickDemoLoading ? 'animate-spin' : ''}`} />
              <span>{quickDemoLoading ? 'Running Demo...' : '1-Click Interactive Demo (20 dB)'}</span>
            </button>
            <button
              onClick={() => onNavigate('estimation')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold text-xs tracking-wide uppercase transition-all"
            >
              <span>Compare Estimators</span>
            </button>
          </div>
        </div>
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-cyan-500/10 to-transparent pointer-events-none" />
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="MIMO Topology"
          value="2 x 2"
          subtitle="Spatial multiplexing streams"
          icon={Radio}
          variant="cyan"
          badgeText="Active"
        />
        <StatCard
          title="Modulation Scheme"
          value="QPSK / 16-QAM"
          subtitle="Gray mapped, unit energy"
          icon={Layers}
          variant="purple"
          badgeText="E[|s|²]=1.0"
        />
        <StatCard
          title="OFDM Waveform"
          value="64 FFT / 16 CP"
          subtitle="Comb-type orthogonal pilots"
          icon={Activity}
          variant="green"
          badgeText="FDM Grid"
        />
        <StatCard
          title="ML Channel Estimator"
          value={modelStatus?.trained ? 'Ready' : 'Untrained'}
          subtitle={
            modelStatus?.parameters_count
              ? `${modelStatus.parameters_count.toLocaleString()} parameters`
              : `PyTorch on ${health?.device?.toUpperCase() || 'CPU'}`
          }
          icon={Cpu}
          variant="amber"
          badgeText={modelStatus?.device?.toUpperCase() || 'CPU'}
        />
      </div>

      {/* 1-Click Demo Live Result Box */}
      {demoResult && (
        <div className="glass-panel p-6 border-cyan-500/40 bg-slate-900/90 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-cyan-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Live Simulation Output @ {demoResult.snr_db} dB SNR ({demoResult.algorithm})
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-400">
              Latency: {demoResult.execution_time_ms.toFixed(1)} ms
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <span className="text-slate-400 block mb-1">NMSE (dB):</span>
              <span className="text-cyan-400 text-base font-bold">{demoResult.nmse_db.toFixed(2)} dB</span>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <span className="text-slate-400 block mb-1">Bit Error Rate (BER):</span>
              <span className="text-emerald-400 text-base font-bold">{demoResult.ber.toExponential(3)}</span>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <span className="text-slate-400 block mb-1">Bit Errors / Total:</span>
              <span className="text-white text-base font-bold">{demoResult.bit_errors} / {demoResult.total_bits}</span>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
              <span className="text-slate-400 block mb-1">Symbol Errors / Total:</span>
              <span className="text-purple-400 text-base font-bold">{demoResult.symbol_errors} / {demoResult.total_symbols}</span>
            </div>
          </div>

          {/* Quick Constellation Scatter Plot */}
          <div className="pt-2">
            <span className="text-xs font-semibold text-slate-300 block mb-2">
              Recovered Symbol Constellation (IQ Plane)
            </span>
            <div className="h-44 w-full bg-slate-950 rounded-lg border border-slate-800 p-2">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                  <XAxis type="number" dataKey="i" domain={[-2, 2]} stroke="var(--chart-axis)" tick={{ fontSize: 9 }} />
                  <YAxis type="number" dataKey="q" domain={[-2, 2]} stroke="var(--chart-axis)" tick={{ fontSize: 9 }} />
                  <Tooltip
                    cursor={{ strokeDasharray: '3 3' }}
                    content={({ payload }) => {
                      if (!payload || !payload.length) return null;
                      const pt = payload[0].payload;
                      return (
                        <div className="p-2 bg-slate-900 border border-slate-700 rounded text-[10px] font-mono text-cyan-300">
                          I: {pt.i.toFixed(3)}, Q: {pt.q.toFixed(3)}
                        </div>
                      );
                    }}
                  />
                  <Scatter
                    name="Equalized Rx Symbols"
                    data={demoResult.rx_constellation_sample}
                    fill="#06b6d4"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Architecture Diagram */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-white">End-to-End Transceiver Pipeline</h3>
            <p className="text-xs text-slate-400">Signal processing flow from bit generator to recovered data bits</p>
          </div>
          <Badge variant="cyan">Deterministic Ground Truth</Badge>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          {[
            { step: '01', title: 'Bit Gen & Mod', desc: 'QPSK / 16-QAM Gray Mapping', color: 'border-cyan-500/30 text-cyan-400' },
            { step: '02', title: 'OFDM Modulation', desc: 'Comb Pilots + 64-IFFT + CP-16', color: 'border-blue-500/30 text-blue-400' },
            { step: '03', title: 'Wireless Channel', desc: 'Rayleigh 4-Tap PDP + AWGN', color: 'border-purple-500/30 text-purple-400' },
            { step: '04', title: 'OFDM Demod', desc: 'CP Removal + 64-FFT + Pilot Extraction', color: 'border-indigo-500/30 text-indigo-400' },
            { step: '05', title: 'Channel Estimation', desc: 'LS, MMSE or PyTorch DNN', color: 'border-emerald-500/30 text-emerald-400' },
            { step: '06', title: 'MIMO Equalizer', desc: 'Zero-Forcing / MMSE Symbol Rec.', color: 'border-amber-500/30 text-amber-400' },
          ].map((stage) => (
            <div key={stage.step} className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
              <span className={`text-[10px] font-mono font-bold ${stage.color}`}>{stage.step}</span>
              <h4 className="text-xs font-semibold text-white mt-1">{stage.title}</h4>
              <p className="text-[11px] text-slate-400 mt-1 leading-snug">{stage.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Verified Publication Results & Performance Highlights */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-cyan-400" />
              <h3 className="text-base font-semibold text-white">Empirical Research Results & Publication Curves</h3>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Comparative Monte Carlo evaluation across 105 channel realizations from 0 to 30 dB SNR.
            </p>
          </div>
          <button
            onClick={() => onNavigate('comparison')}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center gap-1 font-sans"
          >
            <span>Explore All 6 Figures &rarr;</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Card 1: NMSE Waterfall Screenshot */}
          <div
            onClick={() => onNavigate('comparison')}
            className="rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/50 p-4 transition-all cursor-pointer group flex flex-col justify-between"
          >
            <div className="aspect-[16/10] bg-slate-950 rounded-lg overflow-hidden flex items-center justify-center p-2 mb-3 relative">
              <img
                src="/results/nmse_vs_snr.png"
                alt="NMSE vs SNR Waterfall"
                className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-300"
              />
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1.5 text-white text-xs font-semibold">
                <Maximize2 className="w-3.5 h-3.5 text-cyan-400" />
                <span>Open in Comparison Suite</span>
              </div>
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-white group-hover:text-cyan-400 transition-colors">
                  Channel Estimation NMSE vs SNR
                </h4>
                <Badge variant="purple">0–30 dB Sweep</Badge>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                LMMSE is best at low SNR; the residual DNN slightly beats LS there without channel covariance knowledge, but levels off near -25 dB at high SNR.
              </p>
            </div>
          </div>

          {/* Card 2: BER Waterfall Screenshot */}
          <div
            onClick={() => onNavigate('comparison')}
            className="rounded-xl bg-slate-900/60 border border-slate-800 hover:border-emerald-500/50 p-4 transition-all cursor-pointer group flex flex-col justify-between"
          >
            <div className="aspect-[16/10] bg-slate-950 rounded-lg overflow-hidden flex items-center justify-center p-2 mb-3 relative">
              <img
                src="/results/ber_vs_snr.png"
                alt="BER vs SNR Waterfall"
                className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-300"
              />
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1.5 text-white text-xs font-semibold">
                <Maximize2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Open in Comparison Suite</span>
              </div>
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-white group-hover:text-emerald-400 transition-colors">
                  Bit Error Rate (BER) vs SNR
                </h4>
                <Badge variant="green">95% Wilson Intervals</Badge>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                End-to-end bit errors after MIMO equalization, with 95% Wilson confidence intervals. The DNN's high-SNR estimation floor raises its BER above LS at 25-30 dB.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          onClick={() => onNavigate('simulator')}
          className="glass-panel p-5 cursor-pointer hover:border-cyan-500/40 hover:bg-slate-900/80 transition-all group"
        >
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold text-white group-hover:text-cyan-400 transition-colors">
              Physical Layer Simulator
            </h4>
            <Zap className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-xs text-slate-400 leading-relaxed mb-3">
            Simulate MIMO-OFDM frames with configurable SNR, modulation, channel taps, and antenna counts.
          </p>
          <span className="text-xs text-cyan-400 font-medium inline-flex items-center gap-1">
            Open Simulator &rarr;
          </span>
        </div>

        <div
          onClick={() => onNavigate('training')}
          className="glass-panel p-5 cursor-pointer hover:border-purple-500/40 hover:bg-slate-900/80 transition-all group"
        >
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold text-white group-hover:text-purple-400 transition-colors">
              ML Model Studio
            </h4>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <p className="text-xs text-slate-400 leading-relaxed mb-3">
            Train the PyTorch channel estimation network with simulated channel realizations and inspect loss curves.
          </p>
          <span className="text-xs text-purple-400 font-medium inline-flex items-center gap-1">
            Train Network &rarr;
          </span>
        </div>

        <div
          onClick={() => onNavigate('comparison')}
          className="glass-panel p-5 cursor-pointer hover:border-emerald-500/40 hover:bg-slate-900/80 transition-all group"
        >
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold text-white group-hover:text-emerald-400 transition-colors">
              Performance Comparison
            </h4>
            <BarChart2 className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-xs text-slate-400 leading-relaxed mb-3">
            Plot NMSE vs SNR and BER vs SNR curves across LS, MMSE, and DNN on identical test channels.
          </p>
          <span className="text-xs text-emerald-400 font-medium inline-flex items-center gap-1">
            View Analytics &rarr;
          </span>
        </div>
      </div>
    </div>
  );
};
