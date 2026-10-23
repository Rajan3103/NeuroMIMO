import React, { useState } from 'react';
import {
  Play,
  BarChart3,
  Info,
  Activity,
  Sparkles,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  LineChart,
  Line,
} from 'recharts';
import { Badge } from '../components/common/Badge';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { api } from '../api/client';
import type { AlgorithmComparisonResult, ModelPredictResult } from '../types';

export const ChannelEstimationPage: React.FC = () => {
  const [snr, setSnr] = useState<number>(15);
  const [numRealizations, setNumRealizations] = useState<number>(10);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<AlgorithmComparisonResult[] | null>(null);

  // Single-channel realization inspection state
  const [inspectLoading, setInspectLoading] = useState<boolean>(false);
  const [inspectResult, setInspectResult] = useState<ModelPredictResult | null>(null);

  const handleCompare = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.compareEstimators({
        snr_db: snr,
        algorithms: ['LS', 'MMSE', 'DNN'],
        num_realizations: numRealizations,
      });
      setResults(res.results);
    } catch (err: any) {
      setError(err?.message || 'Benchmark comparison failed');
    } finally {
      setLoading(false);
    }
  };

  const handleInspectRealization = async () => {
    setInspectLoading(true);
    setError(null);
    try {
      const res = await api.predictChannel({
        snr_db: snr,
        channel_model: 'RAYLEIGH',
      });
      setInspectResult(res);
    } catch (err: any) {
      setError(err?.message || 'Channel inspection failed');
    } finally {
      setInspectLoading(false);
    }
  };

  // Prepare subcarrier response comparison for inspection line chart
  const subcarrierComparisonData = [];
  if (inspectResult?.h_true_real && inspectResult?.h_pred_real) {
    for (let k = 0; k < 64; k++) {
      const trueMag = Math.sqrt(
        Math.pow(inspectResult.h_true_real[k], 2) + Math.pow(inspectResult.h_true_imag?.[k] || 0, 2)
      );
      const predMag = Math.sqrt(
        Math.pow(inspectResult.h_pred_real[k], 2) + Math.pow(inspectResult.h_pred_imag[k], 2)
      );
      subcarrierComparisonData.push({
        subcarrier: k,
        trueChannel: Number(trueMag.toFixed(4)),
        dnnEstimated: Number(predMag.toFixed(4)),
      });
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-fg tracking-tight">Channel Estimation Lab</h2>
          <p className="text-xs text-slate-400">
            Compare conventional Least Squares (LS), Linear MMSE, and Deep Neural Network estimators.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5">
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-400">SNR:</span>
              <input
                type="number"
                min="0"
                max="30"
                step="5"
                value={snr}
                onChange={(e) => setSnr(Number(e.target.value))}
                className="w-12 bg-slate-800 border border-slate-700 rounded px-1.5 py-0.5 text-xs font-mono font-bold text-cyan-400 text-center"
              />
              <span className="text-xs text-slate-400 font-mono">dB</span>
            </div>
            <div className="w-[1px] h-4 bg-slate-800" />
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-400">Trials:</span>
              <input
                type="number"
                min="1"
                max="50"
                value={numRealizations}
                onChange={(e) => setNumRealizations(Math.max(1, Math.min(50, Number(e.target.value))))}
                className="w-12 bg-slate-800 border border-slate-700 rounded px-1.5 py-0.5 text-xs font-mono font-bold text-purple-400 text-center"
              />
            </div>
          </div>
          <button
            onClick={handleCompare}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold uppercase tracking-wider flex items-center gap-2 transition-all shadow-lg shadow-cyan-950/50 disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Benchmarking...' : 'Run Head-to-Head Benchmark'}</span>
          </button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      <div className="glass-panel p-5">
        <div className="flex items-start gap-3 text-xs text-slate-300">
          <Info className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            The same channel realization <strong className="text-fg">H</strong> and identical noisy pilot observations
            are evaluated by all algorithms simultaneously. This guarantees zero realization bias across comparisons.
          </p>
        </div>
      </div>

      {/* Estimators Architecture Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            name: 'Least Squares (LS)',
            formula: 'H_LS[p] = Y[p] / X[p]',
            pros: 'DFT sinc interpolation. Fast, no channel covariance prior needed.',
            cons: 'Noise enhancement at low SNR; error sensitive across pilot gaps.',
            tag: 'Baseline',
            color: 'cyan',
          },
          {
            name: 'Linear MMSE (LMMSE)',
            formula: 'W = R_H,Hp (R_Hp,Hp + σ² I)⁻¹',
            pros: 'Bayesian optimal linear estimator minimizing mean squared error.',
            cons: 'Requires known channel PDP statistics and matrix inversion.',
            tag: 'Optimal Bayesian',
            color: 'emerald',
          },
          {
            name: 'PyTorch Residual DNN',
            formula: 'H_DNN = H_LS + f_θ(H_LS)',
            pros: 'Learns non-linear multipath patterns and robust low-SNR denoising.',
            cons: 'Higher inference latency; high-SNR residual regression error floor.',
            tag: 'AI-Enhanced',
            color: 'purple',
          },
        ].map((algo) => (
          <div key={algo.name} className="glass-panel p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-fg">{algo.name}</h3>
              <Badge variant={algo.color as any}>{algo.tag}</Badge>
            </div>
            <div className="p-2.5 rounded bg-slate-900 border border-slate-800 font-mono text-[11px] text-cyan-300 text-center overflow-x-auto">
              {algo.formula}
            </div>
            <div className="space-y-2 text-xs">
              <div>
                <span className="text-slate-400 font-medium">Advantages: </span>
                <span className="text-slate-300">{algo.pros}</span>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Trade-offs: </span>
                <span className="text-slate-300">{algo.cons}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Loading state */}
      {loading && (
        <div className="glass-panel p-8">
          <LoadingSpinner label="Running comparative benchmark across estimators under identical realizations..." size="lg" />
        </div>
      )}

      {/* Benchmark Results */}
      {results && !loading && (
        <div className="space-y-6">
          <div className="glass-panel p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-fg uppercase tracking-wider flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-cyan-400" />
                <span>Head-to-Head Comparative Benchmark @ {snr} dB SNR</span>
              </h3>
              <Badge variant="cyan">Averaged over {numRealizations} realizations</Badge>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="pb-3 font-semibold">Algorithm</th>
                    <th className="pb-3 font-semibold">NMSE (dB)</th>
                    <th className="pb-3 font-semibold">Linear NMSE</th>
                    <th className="pb-3 font-semibold">Bit Error Rate (BER)</th>
                    <th className="pb-3 font-semibold">Symbol Error Rate (SER)</th>
                    <th className="pb-3 font-semibold">Inference Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {results.map((r) => (
                    <tr key={r.algorithm} className="text-slate-200 hover:bg-slate-800/30">
                      <td className="py-3 font-sans font-semibold text-fg">{r.algorithm}</td>
                      <td className="py-3 text-cyan-400 font-bold">{r.nmse_db.toFixed(2)} dB</td>
                      <td className="py-3 text-slate-300">{r.nmse.toExponential(3)}</td>
                      <td className="py-3 text-emerald-400">{r.ber.toExponential(3)}</td>
                      <td className="py-3 text-purple-400">{r.ser.toExponential(3)}</td>
                      <td className="py-3 text-slate-400">{r.execution_time_ms.toFixed(2)} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Recharts Bar Charts Comparison */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-4 border-t border-slate-800">
              {/* NMSE Bar Chart */}
              <div>
                <span className="text-xs font-bold text-slate-300 block mb-2">
                  Normalized Mean Squared Error (NMSE in dB)
                </span>
                <div className="h-60 w-full bg-slate-950 rounded-lg border border-slate-800 p-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={results} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                      <XAxis dataKey="algorithm" stroke="var(--chart-axis)" tick={{ fontSize: 11, fill: 'var(--chart-tick)' }} />
                      <YAxis stroke="var(--chart-axis)" tick={{ fontSize: 10 }} />
                      <Tooltip
                        content={({ payload }) => {
                          if (!payload || !payload.length) return null;
                          const r = payload[0].payload;
                          return (
                            <div className="p-2 bg-slate-900 border border-slate-700 rounded text-xs font-mono text-cyan-300">
                              {r.algorithm}: {r.nmse_db.toFixed(2)} dB (Linear: {r.nmse.toExponential(2)})
                            </div>
                          );
                        }}
                      />
                      <Bar dataKey="nmse_db" fill="#06b6d4" radius={[4, 4, 0, 0]} name="NMSE [dB]" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Latency Bar Chart */}
              <div>
                <span className="text-xs font-bold text-slate-300 block mb-2">
                  Per-Frame Execution Latency [milliseconds]
                </span>
                <div className="h-60 w-full bg-slate-950 rounded-lg border border-slate-800 p-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={results} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                      <XAxis dataKey="algorithm" stroke="var(--chart-axis)" tick={{ fontSize: 11, fill: 'var(--chart-tick)' }} />
                      <YAxis stroke="var(--chart-axis)" tick={{ fontSize: 10 }} />
                      <Tooltip
                        content={({ payload }) => {
                          if (!payload || !payload.length) return null;
                          const r = payload[0].payload;
                          return (
                            <div className="p-2 bg-slate-900 border border-slate-700 rounded text-xs font-mono text-purple-300">
                              {r.algorithm}: {r.execution_time_ms.toFixed(2)} ms
                            </div>
                          );
                        }}
                      />
                      <Bar dataKey="execution_time_ms" fill="#a855f7" radius={[4, 4, 0, 0]} name="Runtime [ms]" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Interactive Single-Realization Inspection Tool */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-fg uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>Real-Time Channel Frequency Response Inspection</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Generate a test realization and inspect True Channel |H[k]| vs. PyTorch DNN Predicted Channel across all 64 subcarriers.
            </p>
          </div>
          <button
            onClick={handleInspectRealization}
            disabled={inspectLoading}
            className="px-3.5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold uppercase tracking-wider flex items-center gap-2 transition-all shadow-lg shadow-purple-950/50 disabled:opacity-50 shrink-0"
          >
            <Activity className={`w-3.5 h-3.5 ${inspectLoading ? 'animate-spin' : ''}`} />
            <span>{inspectLoading ? 'Predicting...' : 'Simulate & Predict CFR'}</span>
          </button>
        </div>

        {inspectResult && (
          <div className="space-y-4 pt-2">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs font-mono">
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-slate-400 block mb-1">Prediction NMSE (dB):</span>
                <span className="text-cyan-400 font-bold text-sm">
                  {inspectResult.nmse_db !== undefined ? `${inspectResult.nmse_db.toFixed(2)} dB` : 'N/A'}
                </span>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-slate-400 block mb-1">Inference Latency:</span>
                <span className="text-emerald-400 font-bold text-sm">
                  {inspectResult.inference_time_ms.toFixed(2)} ms
                </span>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-slate-400 block mb-1">Tensors Estimated:</span>
                <span className="text-purple-400 font-bold text-sm">2x2 x 64 tones</span>
              </div>
            </div>

            <div className="h-64 w-full bg-slate-950 rounded-lg border border-slate-800 p-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={subcarrierComparisonData} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                  <XAxis
                    dataKey="subcarrier"
                    stroke="var(--chart-axis)"
                    tick={{ fontSize: 10 }}
                    label={{ value: 'Subcarrier Index k', position: 'insideBottom', offset: -5, fill: '#64748b', fontSize: 10 }}
                  />
                  <YAxis
                    stroke="var(--chart-axis)"
                    tick={{ fontSize: 10 }}
                    label={{ value: '|H[k]| Magnitude', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 10 }}
                  />
                  <Tooltip
                    content={({ payload }) => {
                      if (!payload || !payload.length) return null;
                      const d = payload[0].payload;
                      return (
                        <div className="p-2 bg-slate-900 border border-slate-700 rounded text-xs font-mono space-y-1">
                          <div className="text-slate-400">Subcarrier {d.subcarrier}</div>
                          <div className="text-emerald-400 font-bold">True: {d.trueChannel}</div>
                          <div className="text-purple-400 font-bold">DNN Pred: {d.dnnEstimated}</div>
                        </div>
                      );
                    }}
                  />
                  <Legend verticalAlign="top" height={36} iconType="circle" />
                  <Line
                    type="monotone"
                    dataKey="trueChannel"
                    name="Ground Truth |H_true[k]|"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="dnnEstimated"
                    name="PyTorch DNN Estimate |H_DNN[k]|"
                    stroke="#a855f7"
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
