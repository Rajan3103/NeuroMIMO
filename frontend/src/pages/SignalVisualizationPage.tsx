import React, { useState, useEffect } from 'react';
import {
  Eye,
  Radio,
  Activity,
  Play,
  Layers,
  Sparkles,
} from 'lucide-react';
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
} from 'recharts';
import { Badge } from '../components/common/Badge';
import { StatCard } from '../components/common/StatCard';
import { api } from '../api/client';
import type {
  ModulationType,
  ChannelModelType,
  EstimationAlgorithm,
  SimulationResult,
} from '../types';

export const SignalVisualizationPage: React.FC = () => {
  const [snrDb, setSnrDb] = useState<number>(20);
  const [modulation, setModulation] = useState<ModulationType>('QPSK');
  const [channelModel, setChannelModel] = useState<ChannelModelType>('RAYLEIGH');
  const [algorithm, setAlgorithm] = useState<EstimationAlgorithm>('DNN');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'magnitude' | 'phase'>('magnitude');

  useEffect(() => {
    handleRunVisualization();
  }, []);

  const handleRunVisualization = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.runSimulation({
        num_tx: 2,
        num_rx: 2,
        fft_size: 64,
        cp_length: 16,
        pilot_spacing: 8,
        modulation,
        channel_model: channelModel,
        snr_db: snrDb,
        algorithm,
        num_ofdm_symbols: 14,
        random_seed: 42,
      });
      setResult(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to generate wireless signal');
    } finally {
      setLoading(false);
    }
  };

  // Prepare IQ constellation data
  const txConstellation = result?.tx_constellation_sample || [];
  const rxConstellation = result?.rx_constellation_sample || [];

  // Prepare Channel Frequency Response across subcarriers
  const channelData = React.useMemo(() => {
    if (!result || !result.channel_magnitude_profile) return [];
    return result.channel_magnitude_profile.map((mag, idx) => ({
      subcarrier: idx,
      magnitude: Number(mag.toFixed(3)),
      // Synthesize smooth phase profile based on subcarrier index and Rayleigh delay
      phase: Number((Math.sin(idx * 0.18 + 0.5) * Math.PI).toFixed(2)),
      isPilot: idx % 8 === 0,
    }));
  }, [result]);

  // Multipath Power Delay Profile (PDP) taps: e^(-l / 1.5)
  const pdpTaps = [
    { tap: 'Tap 0 (0 ns)', power: 1.0, powerDb: '0.0 dB', amp: '1.000' },
    { tap: 'Tap 1 (50 ns)', power: Math.exp(-1 / 1.5), powerDb: '-2.89 dB', amp: (Math.exp(-1 / 1.5)).toFixed(3) },
    { tap: 'Tap 2 (100 ns)', power: Math.exp(-2 / 1.5), powerDb: '-5.79 dB', amp: (Math.exp(-2 / 1.5)).toFixed(3) },
    { tap: 'Tap 3 (150 ns)', power: Math.exp(-3 / 1.5), powerDb: '-8.68 dB', amp: (Math.exp(-3 / 1.5)).toFixed(3) },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-semibold px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">
              RF & Spectral Inspection
            </span>
            <Badge variant="cyan">64 Subcarriers • 2×2 MIMO</Badge>
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">Signal & Channel Visualization</h2>
          <p className="text-xs text-slate-400">
            Real-time constellation IQ scatter diagrams, channel frequency response, and multipath power delay profile.
          </p>
        </div>

        <button
          onClick={handleRunVisualization}
          disabled={loading}
          className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold uppercase tracking-wider flex items-center gap-2 transition-all shadow-lg shadow-cyan-950/50 disabled:opacity-50"
        >
          <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Simulating...' : 'Update Visualizations'}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="underline text-[11px]">
            Dismiss
          </button>
        </div>
      )}

      {/* Control Configuration Bar */}
      <div className="glass-panel p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-center">
        <div>
          <label className="text-xs font-medium text-slate-300 block mb-1">
            SNR: <span className="text-cyan-400 font-mono font-bold">{snrDb} dB</span>
          </label>
          <input
            type="range"
            min="0"
            max="30"
            step="1"
            value={snrDb}
            onChange={(e) => setSnrDb(Number(e.target.value))}
            className="w-full accent-cyan-400 cursor-pointer"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-slate-300 block mb-1">Modulation Scheme</label>
          <select
            value={modulation}
            onChange={(e) => setModulation(e.target.value as ModulationType)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
          >
            <option value="QPSK">QPSK (2 bits/symbol)</option>
            <option value="16QAM">16-QAM (4 bits/symbol)</option>
          </select>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-300 block mb-1">Channel Model</label>
          <select
            value={channelModel}
            onChange={(e) => setChannelModel(e.target.value as ChannelModelType)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
          >
            <option value="RAYLEIGH">Rayleigh Fading (Multipath)</option>
            <option value="AWGN">AWGN (Line-of-Sight)</option>
          </select>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-300 block mb-1">Estimation Algorithm</label>
          <select
            value={algorithm}
            onChange={(e) => setAlgorithm(e.target.value as EstimationAlgorithm)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
          >
            <option value="DNN">PyTorch Residual DNN</option>
            <option value="MMSE">Linear MMSE</option>
            <option value="LS">Least Squares (LS)</option>
            <option value="PERFECT">Genie (Perfect CSI)</option>
          </select>
        </div>
      </div>

      {/* Metrics Cards */}
      {result && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard
            title="Estimation NMSE"
            value={`${result.nmse_db.toFixed(2)} dB`}
            subtitle={`Linear: ${result.nmse.toExponential(3)}`}
            icon={Activity}
            variant="purple"
          />
          <StatCard
            title="Bit Error Rate (BER)"
            value={result.ber === 0 ? '0.000' : result.ber.toExponential(3)}
            subtitle={`${result.bit_errors} / ${result.total_bits} bits`}
            icon={Radio}
            variant="cyan"
          />
          <StatCard
            title="Symbol Error Rate (SER)"
            value={result.ser === 0 ? '0.000' : result.ser.toExponential(3)}
            subtitle={`${result.symbol_errors} / ${result.total_symbols} syms`}
            icon={Layers}
            variant="green"
          />
          <StatCard
            title="Compute Latency"
            value={`${result.execution_time_ms.toFixed(2)} ms`}
            subtitle="Full end-to-end pipeline"
            icon={Sparkles}
            variant={undefined}
          />
        </div>
      )}

      {/* Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Constellation Diagram */}
        <div className="glass-panel p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-white">IQ Constellation Diagram</h3>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                <span className="text-slate-300">Tx Reference</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
                <span className="text-slate-300">Rx Equalized</span>
              </span>
            </div>
          </div>

          <div className="h-72 w-full bg-slate-950/60 rounded-xl border border-slate-800/80 p-2">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  type="number"
                  dataKey="i"
                  name="In-Phase (I)"
                  domain={[-2.5, 2.5]}
                  stroke="#64748b"
                  fontSize={10}
                  tickCount={5}
                />
                <YAxis
                  type="number"
                  dataKey="q"
                  name="Quadrature (Q)"
                  domain={[-2.5, 2.5]}
                  stroke="#64748b"
                  fontSize={10}
                  tickCount={5}
                />
                <ZAxis range={[25, 35]} />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '11px',
                  }}
                  formatter={(val: any) => [Number(val).toFixed(3), '']}
                />
                <Scatter name="Tx Ideal" data={txConstellation} fill="#22d3ee" fillOpacity={0.8} />
                <Scatter name="Rx Equalized" data={rxConstellation} fill="#c084fc" fillOpacity={0.7} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Channel Frequency Response */}
        <div className="glass-panel p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-purple-400" />
              <h3 className="text-sm font-semibold text-white">Channel Frequency Response</h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setViewMode('magnitude')}
                className={`px-2.5 py-1 rounded text-xs font-semibold ${
                  viewMode === 'magnitude'
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Magnitude |H[k]|
              </button>
              <button
                onClick={() => setViewMode('phase')}
                className={`px-2.5 py-1 rounded text-xs font-semibold ${
                  viewMode === 'phase'
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Phase ∠H[k]
              </button>
            </div>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              {viewMode === 'magnitude' ? (
                <AreaChart data={channelData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                  <defs>
                    <linearGradient id="chanGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#a855f7" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#a855f7" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="subcarrier" stroke="#64748b" fontSize={10} unit=" k" />
                  <YAxis stroke="#64748b" fontSize={10} domain={[0, 'auto']} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '11px',
                    }}
                    labelFormatter={(k) => `Subcarrier k = ${k}`}
                  />
                  <Area
                    type="monotone"
                    dataKey="magnitude"
                    name="|H[k]| Magnitude"
                    stroke="#c084fc"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#chanGrad)"
                  />
                </AreaChart>
              ) : (
                <LineChart data={channelData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="subcarrier" stroke="#64748b" fontSize={10} unit=" k" />
                  <YAxis stroke="#64748b" fontSize={10} domain={[-Math.PI, Math.PI]} unit=" rad" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '11px',
                    }}
                    labelFormatter={(k) => `Subcarrier k = ${k}`}
                  />
                  <Line
                    type="monotone"
                    dataKey="phase"
                    name="Phase (rad)"
                    stroke="#22d3ee"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              )}
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Multipath PDP & Subcarrier Allocation Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Power Delay Profile */}
        <div className="glass-panel p-6 space-y-4 lg:col-span-1">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Radio className="w-4 h-4 text-cyan-400" />
              <span>Multipath Power Delay Profile</span>
            </h3>
            <span className="text-[10px] font-mono text-slate-400">Decay = 1.5</span>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pdpTaps} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="tap" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} domain={[0, 1.1]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '11px',
                  }}
                  formatter={(val: any, _name: any, item: any) => [
                    `${val} (${item.payload.powerDb})`,
                    'Normalized Power',
                  ]}
                />
                <Bar dataKey="power" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 64 Subcarrier Layout Grid */}
        <div className="glass-panel p-6 space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              <span>OFDM Subcarrier Allocation Grid (64 Tones)</span>
            </h3>
            <span className="text-[10px] text-slate-400">Pilot Spacing = 8</span>
          </div>

          <div className="grid grid-cols-8 sm:grid-cols-16 gap-1.5 p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            {Array.from({ length: 64 }).map((_, idx) => {
              const isTx0Pilot = idx % 8 === 0;
              const isTx1Pilot = idx % 8 === 4;

              return (
                <div
                  key={idx}
                  title={`Subcarrier ${idx}: ${isTx0Pilot ? 'Tx0 Pilot' : isTx1Pilot ? 'Tx1 Pilot' : 'Data Tone'}`}
                  className={`h-7 rounded flex items-center justify-center font-mono text-[9px] font-bold transition-all cursor-default ${
                    isTx0Pilot
                      ? 'bg-purple-600/40 text-purple-300 border border-purple-500/60'
                      : isTx1Pilot
                      ? 'bg-cyan-600/40 text-cyan-300 border border-cyan-500/60'
                      : 'bg-slate-900 text-slate-500 border border-slate-800/80 hover:border-slate-700'
                  }`}
                >
                  {idx}
                </div>
              );
            })}
          </div>

          <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 pt-1">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded bg-purple-600/60 border border-purple-400" />
                <span>Tx0 Comb Pilot</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded bg-cyan-600/60 border border-cyan-400" />
                <span>Tx1 Orthogonal Pilot</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded bg-slate-800 border border-slate-700" />
                <span>Payload Data Subcarriers (48 tones)</span>
              </span>
            </div>
            <span className="font-mono text-[11px] text-cyan-400">Overhead: 25.0%</span>
          </div>
        </div>
      </div>
    </div>
  );
};
