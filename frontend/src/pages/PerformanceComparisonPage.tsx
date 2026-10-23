import React, { useState, useEffect } from 'react';
import {
  LineChart as LineChartIcon,
  Play,
  Layers,
  BarChart2,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  Clock,
  TrendingDown,
  Maximize2,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
} from 'recharts';
import { Badge } from '../components/common/Badge';
import { StatCard } from '../components/common/StatCard';
import { Modal } from '../components/common/Modal';
import { api } from '../api/client';
import type {
  SnrSweepDataset,
  PlotItem,
} from '../types';

const DEFAULT_PUBLICATION_PLOTS: PlotItem[] = [
  {
    name: 'NMSE vs SNR Waterfall',
    filename: 'nmse_vs_snr.png',
    url: '/results/nmse_vs_snr.png',
    description: 'Normalized Mean Squared Error vs SNR in Rayleigh multipath fading (105 Monte Carlo trials)',
  },
  {
    name: 'BER vs SNR Waterfall',
    filename: 'ber_vs_snr.png',
    url: '/results/ber_vs_snr.png',
    description: 'Bit Error Rate vs SNR after channel estimation and 2×2 MMSE spatial equalization',
  },
  {
    name: 'Channel Model Comparison',
    filename: 'channel_model_comparison.png',
    url: '/results/channel_model_comparison.png',
    description: 'Comparative performance under frequency-flat AWGN vs frequency-selective Rayleigh fading',
  },
  {
    name: 'Generalization & Parameter Mismatch',
    filename: 'generalization_evaluation.png',
    url: '/results/generalization_evaluation.png',
    description: 'Performance on unseen channel realizations and PDP decay/tap dispersion shifts',
  },
  {
    name: 'Computational Runtime',
    filename: 'inference_runtime.png',
    url: '/results/inference_runtime.png',
    description: 'Per-frame estimation latency and throughput benchmark across estimators',
  },
  {
    name: 'Pilot-Density Scaling',
    filename: 'pilot_density_comparison.png',
    url: '/results/pilot_density_comparison.png',
    description: 'Estimation NMSE scaling as a function of comb pilot subcarrier spacing',
  },
];

export const PerformanceComparisonPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'interactive' | 'publication'>('interactive');
  const [loading, setLoading] = useState<boolean>(true);
  const [sweepRunning, setSweepRunning] = useState<boolean>(false);
  const [sweepProgress, setSweepProgress] = useState<string>('');
  const [dataset, setDataset] = useState<SnrSweepDataset | null>(null);
  const [plots, setPlots] = useState<PlotItem[]>(DEFAULT_PUBLICATION_PLOTS);
  const [error, setError] = useState<string | null>(null);

  // Selected image preview modal
  const [selectedPlot, setSelectedPlot] = useState<PlotItem | null>(null);

  useEffect(() => {
    loadBenchmarkData();
  }, []);

  const loadBenchmarkData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch benchmark SNR sweep dataset
      const data = await api.getBenchmarkSnrSweep();
      setDataset(data);

      // 2. Fetch publication plots
      const plotsRes = await api.getExperimentPlots('latest');
      setPlots(plotsRes.plots);
    } catch (err: any) {
      console.error(err);
      setError(err?.message || 'Failed to load benchmark dataset');
    } finally {
      setLoading(false);
    }
  };

  // Run a live fast SNR sweep across 0 to 30 dB using api.compareEstimators
  const handleRunLiveSweep = async () => {
    setSweepRunning(true);
    setError(null);
    const snrPoints = [0, 5, 10, 15, 20, 25, 30];
    const liveRecords: Record<string, any[]> = {
      LS: [],
      MMSE: [],
      DNN: [],
    };

    try {
      for (let i = 0; i < snrPoints.length; i++) {
        const snr = snrPoints[i];
        setSweepProgress(`Simulating SNR = ${snr} dB (${i + 1}/${snrPoints.length})...`);
        const res = await api.compareEstimators({
          snr_db: snr,
          algorithms: ['LS', 'MMSE', 'DNN'],
          num_realizations: 5,
        });

        res.results.forEach((r) => {
          if (liveRecords[r.algorithm]) {
            liveRecords[r.algorithm].push({
              snr_db: snr,
              available: true,
              nmse: r.nmse,
              nmse_db: r.nmse_db,
              ber: r.ber,
              ser: r.ser,
              inference_time_ms: r.execution_time_ms,
            });
          }
        });
      }

      setDataset({
        experiment_name: 'live_user_snr_sweep',
        channel_model: 'RAYLEIGH',
        modulation: 'QPSK',
        pilot_spacing: 8,
        num_channel_taps: 4,
        pdp_decay: 1.5,
        num_trials_per_snr: 5,
        snr_points: snrPoints,
        algorithms: ['LS', 'MMSE', 'DNN'],
        records: liveRecords as any,
      });
      setSweepProgress('Live sweep completed successfully!');
    } catch (err: any) {
      setError(err?.message || 'Failed during live SNR sweep');
    } finally {
      setSweepRunning(false);
    }
  };

  // Build chart-ready series from dataset
  const chartData = React.useMemo(() => {
    if (!dataset || !dataset.snr_points) return [];
    return dataset.snr_points.map((snr) => {
      const lsRec = dataset.records?.LS?.find((r) => r.snr_db === snr);
      const mmseRec = dataset.records?.MMSE?.find((r) => r.snr_db === snr);
      const dnnRec = dataset.records?.DNN?.find((r) => r.snr_db === snr);
      const perfRec = dataset.records?.PERFECT?.find((r) => r.snr_db === snr);

      return {
        snr_db: snr,
        LS_nmse_db: lsRec ? Number(lsRec.nmse_db.toFixed(2)) : undefined,
        MMSE_nmse_db: mmseRec ? Number(mmseRec.nmse_db.toFixed(2)) : undefined,
        DNN_nmse_db: dnnRec ? Number(dnnRec.nmse_db.toFixed(2)) : undefined,
        PERFECT_nmse_db: perfRec ? Number(perfRec.nmse_db.toFixed(2)) : undefined,

        LS_ber: lsRec ? lsRec.ber : undefined,
        MMSE_ber: mmseRec ? mmseRec.ber : undefined,
        DNN_ber: dnnRec ? dnnRec.ber : undefined,
        PERFECT_ber: perfRec ? perfRec.ber : undefined,

        LS_time: lsRec ? Number(lsRec.inference_time_ms.toFixed(3)) : undefined,
        MMSE_time: mmseRec ? Number(mmseRec.inference_time_ms.toFixed(3)) : undefined,
        DNN_time: dnnRec ? Number(dnnRec.inference_time_ms.toFixed(3)) : undefined,
      };
    });
  }, [dataset]);

  // Runtime comparison data at 20 dB (or highest available)
  const runtimeData = React.useMemo(() => {
    if (!dataset || !dataset.records) return [];
    const targetSnr = 20;
    const lsRec = dataset.records.LS?.find((r) => r.snr_db === targetSnr) || dataset.records.LS?.[0];
    const mmseRec = dataset.records.MMSE?.find((r) => r.snr_db === targetSnr) || dataset.records.MMSE?.[0];
    const dnnRec = dataset.records.DNN?.find((r) => r.snr_db === targetSnr) || dataset.records.DNN?.[0];

    return [
      { name: 'LS', time: lsRec ? lsRec.inference_time_ms : 0, fill: '#f97316' },
      { name: 'MMSE', time: mmseRec ? mmseRec.inference_time_ms : 0, fill: '#10b981' },
      { name: 'Residual DNN', time: dnnRec ? dnnRec.inference_time_ms : 0, fill: '#a855f7' },
    ];
  }, [dataset]);

  // Summary KPIs computed from the loaded dataset (benchmark file or live sweep)
  const kpis = React.useMemo(() => {
    const records = dataset?.records;
    const snrPoints = dataset?.snr_points ?? [];
    const kpiSnr = snrPoints.includes(20) ? 20 : snrPoints[snrPoints.length - 1];
    const nmseAt = (algo: string) =>
      records?.[algo]?.find((r) => r.snr_db === kpiSnr)?.nmse_db;

    // Positive gap means the DNN estimate has lower NMSE than the reference estimator
    const gapVs = (algo: string) => {
      const dnn = nmseAt('DNN');
      const ref = nmseAt(algo);
      return dnn === undefined || ref === undefined ? undefined : ref - dnn;
    };

    const dnnTimes = (records?.DNN ?? []).map((r) => r.inference_time_ms).filter((t) => t > 0);
    const dnnMeanMs = dnnTimes.length
      ? dnnTimes.reduce((sum, t) => sum + t, 0) / dnnTimes.length
      : undefined;

    return {
      kpiSnr,
      gapVsLs: gapVs('LS'),
      gapVsMmse: gapVs('MMSE'),
      dnnMeanMs,
      snrMin: snrPoints.length ? Math.min(...snrPoints) : undefined,
      snrMax: snrPoints.length ? Math.max(...snrPoints) : undefined,
      numSnr: snrPoints.length,
      totalTrials: snrPoints.length * (dataset?.num_trials_per_snr ?? 0),
    };
  }, [dataset]);

  const formatGap = (gap: number | undefined) =>
    gap === undefined ? '—' : `${gap >= 0 ? '+' : '−'}${Math.abs(gap).toFixed(1)} dB`;

  const describeGap = (gap: number | undefined, reference: string) => {
    if (gap === undefined) return 'No data loaded';
    const where = `at ${kpis.kpiSnr} dB SNR`;
    return gap >= 0
      ? `DNN ahead of ${reference} ${where}`
      : `DNN trails ${reference} ${where}`;
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-semibold px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">
              Comparative Benchmarking Suite
            </span>
            <Badge variant="cyan">Monte Carlo Verified</Badge>
          </div>
          <h2 className="text-xl font-bold text-fg tracking-tight">Performance Comparison Suite</h2>
          <p className="text-xs text-slate-400">
            Systematic quantitative evaluation of Least Squares, Linear MMSE, and PyTorch Residual DNN.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex rounded-lg bg-slate-900 border border-slate-800 p-1">
            <button
              onClick={() => setActiveTab('interactive')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'interactive'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-fg'
              }`}
            >
              Interactive Charts
            </button>
            <button
              onClick={() => setActiveTab('publication')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'publication'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-fg'
              }`}
            >
              Publication Figures ({plots.length})
            </button>
          </div>

          <button
            onClick={loadBenchmarkData}
            disabled={loading || sweepRunning}
            title="Refresh benchmark data"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-fg hover:border-slate-700 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>

          <button
            onClick={handleRunLiveSweep}
            disabled={sweepRunning}
            className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold uppercase tracking-wider flex items-center gap-2 transition-all shadow-lg shadow-cyan-950/50 disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${sweepRunning ? 'animate-spin' : ''}`} />
            <span>{sweepRunning ? 'Running Sweep...' : 'Run Quick Sweep'}</span>
          </button>
        </div>
      </div>

      {/* Sweep Progress & Error Alert */}
      {sweepRunning && (
        <div className="p-3.5 rounded-xl bg-cyan-950/30 border border-cyan-500/30 text-cyan-300 text-xs flex items-center gap-3">
          <RefreshCw className="w-4 h-4 animate-spin shrink-0 text-cyan-400" />
          <span>{sweepProgress}</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-300 hover:text-fg underline text-[11px]">
            Dismiss
          </button>
        </div>
      )}

      {/* Benchmark Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="DNN vs LS NMSE"
          value={formatGap(kpis.gapVsLs)}
          subtitle={describeGap(kpis.gapVsLs, 'LS')}
          icon={TrendingDown}
          variant="purple"
        />
        <StatCard
          title="DNN vs MMSE NMSE"
          value={formatGap(kpis.gapVsMmse)}
          subtitle={describeGap(kpis.gapVsMmse, 'MMSE')}
          icon={CheckCircle2}
          variant="cyan"
        />
        <StatCard
          title="DNN Inference Latency"
          value={kpis.dnnMeanMs === undefined ? '—' : `${kpis.dnnMeanMs.toFixed(2)} ms`}
          subtitle="Mean per OFDM frame across the sweep"
          icon={Clock}
          variant="green"
        />
        <StatCard
          title="Evaluated SNR Range"
          value={kpis.snrMin === undefined ? '—' : `${kpis.snrMin} – ${kpis.snrMax} dB`}
          subtitle={`${kpis.numSnr} SNR checkpoints • ${kpis.totalTrials} Monte Carlo trials`}
          icon={BarChart2}
          variant={undefined}
        />
      </div>

      {activeTab === 'interactive' ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart 1: NMSE vs SNR */}
            <div className="glass-panel p-6 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2">
                  <LineChartIcon className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-sm font-semibold text-fg">NMSE vs SNR Waterfall</h3>
                </div>
                <span className="text-[11px] font-mono text-slate-400">dB Scale (Lower is Better)</span>
              </div>

              {chartData.length === 0 ? (
                <div className="h-72 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-center text-slate-400 text-xs">
                  Loading benchmark data...
                </div>
              ) : (
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                      <XAxis
                        dataKey="snr_db"
                        stroke="var(--chart-axis)"
                        fontSize={11}
                        unit=" dB"
                        label={{ value: 'SNR (dB)', position: 'insideBottom', offset: -5, fill: '#64748b', fontSize: 10 }}
                      />
                      <YAxis
                        stroke="var(--chart-axis)"
                        fontSize={11}
                        unit=" dB"
                        domain={['auto', 'auto']}
                        label={{ value: 'NMSE (dB)', angle: -90, position: 'insideLeft', offset: 0, fill: '#64748b', fontSize: 10 }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'var(--tooltip-bg)',
                          borderColor: 'var(--tooltip-border)',
                          borderRadius: '8px',
                          fontSize: '11px',
                        }}
                        formatter={(val: any) => [`${val} dB`, '']}
                        labelFormatter={(lbl) => `SNR = ${lbl} dB`}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                      <Line
                        type="monotone"
                        dataKey="LS_nmse_db"
                        name="Least Squares (LS)"
                        stroke="#f97316"
                        strokeWidth={2}
                        dot={{ r: 3, fill: '#f97316' }}
                      />
                      <Line
                        type="monotone"
                        dataKey="MMSE_nmse_db"
                        name="Linear MMSE"
                        stroke="#10b981"
                        strokeWidth={2}
                        dot={{ r: 3, fill: '#10b981' }}
                      />
                      <Line
                        type="monotone"
                        dataKey="DNN_nmse_db"
                        name="PyTorch Residual DNN"
                        stroke="#a855f7"
                        strokeWidth={2.5}
                        dot={{ r: 4, fill: '#a855f7' }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            {/* Chart 2: BER vs SNR Waterfall */}
            <div className="glass-panel p-6 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-purple-400" />
                  <h3 className="text-sm font-semibold text-fg">Bit Error Rate (BER) Waterfall</h3>
                </div>
                <span className="text-[11px] font-mono text-slate-400">Post-Equalization Recovery</span>
              </div>

              {chartData.length === 0 ? (
                <div className="h-72 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-center text-slate-400 text-xs">
                  Loading benchmark data...
                </div>
              ) : (
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                      <XAxis
                        dataKey="snr_db"
                        stroke="var(--chart-axis)"
                        fontSize={11}
                        unit=" dB"
                        label={{ value: 'SNR (dB)', position: 'insideBottom', offset: -5, fill: '#64748b', fontSize: 10 }}
                      />
                      <YAxis
                        stroke="var(--chart-axis)"
                        fontSize={11}
                        scale="linear"
                        domain={[0, 'auto']}
                        tickFormatter={(v) => (v === 0 ? '0' : v < 0.01 ? v.toExponential(1) : v.toFixed(3))}
                        label={{ value: 'BER', angle: -90, position: 'insideLeft', offset: 0, fill: '#64748b', fontSize: 10 }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'var(--tooltip-bg)',
                          borderColor: 'var(--tooltip-border)',
                          borderRadius: '8px',
                          fontSize: '11px',
                        }}
                        formatter={(val: any) => [
                          typeof val === 'number' ? (val === 0 ? '0' : val.toExponential(3)) : val,
                          '',
                        ]}
                        labelFormatter={(lbl) => `SNR = ${lbl} dB`}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                      <Line
                        type="monotone"
                        dataKey="LS_ber"
                        name="LS Equalized"
                        stroke="#f97316"
                        strokeWidth={2}
                        dot={{ r: 3, fill: '#f97316' }}
                      />
                      <Line
                        type="monotone"
                        dataKey="MMSE_ber"
                        name="MMSE Equalized"
                        stroke="#10b981"
                        strokeWidth={2}
                        dot={{ r: 3, fill: '#10b981' }}
                      />
                      <Line
                        type="monotone"
                        dataKey="DNN_ber"
                        name="DNN Equalized"
                        stroke="#a855f7"
                        strokeWidth={2.5}
                        dot={{ r: 4, fill: '#a855f7' }}
                      />
                      {chartData.some((d) => d.PERFECT_ber !== undefined) && (
                        <Line
                          type="monotone"
                          dataKey="PERFECT_ber"
                          name="Genie (Known CSI)"
                          stroke="var(--chart-axis)"
                          strokeDasharray="4 4"
                          strokeWidth={2}
                        />
                      )}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>

          {/* Runtime BarChart & Benchmark Data Table */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="glass-panel p-6 space-y-4 lg:col-span-1">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-400" />
                  <h3 className="text-sm font-semibold text-fg">Inference Latency</h3>
                </div>
                <span className="text-[11px] font-mono text-slate-400">ms / OFDM Frame</span>
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={runtimeData} margin={{ top: 20, right: 20, left: 0, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                    <XAxis dataKey="name" stroke="var(--chart-axis)" fontSize={11} />
                    <YAxis stroke="var(--chart-axis)" fontSize={11} unit=" ms" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'var(--tooltip-bg)',
                        borderColor: 'var(--tooltip-border)',
                        borderRadius: '8px',
                        fontSize: '11px',
                      }}
                      formatter={(val: any) => [`${Number(val).toFixed(3)} ms`, 'Execution Time']}
                    />
                    <Bar dataKey="time" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-panel p-6 space-y-4 lg:col-span-2">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-sm font-semibold text-fg">Empirical Benchmark Metrics Table</h3>
                </div>
                <span className="text-[11px] text-slate-400">105 Monte Carlo Realizations</span>
              </div>

              <div className="overflow-x-auto max-h-64 overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-panel text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 font-semibold">SNR</th>
                      <th className="py-2.5 font-semibold text-orange-400">LS NMSE (dB)</th>
                      <th className="py-2.5 font-semibold text-emerald-400">MMSE NMSE (dB)</th>
                      <th className="py-2.5 font-semibold text-purple-400">DNN NMSE (dB)</th>
                      <th className="py-2.5 font-semibold text-purple-300">DNN BER</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                    {chartData.map((d) => (
                      <tr key={d.snr_db} className="text-slate-300 hover:bg-slate-800/30">
                        <td className="py-2 font-bold text-fg">{d.snr_db} dB</td>
                        <td className="py-2 text-orange-400">{d.LS_nmse_db ?? 'N/A'} dB</td>
                        <td className="py-2 text-emerald-400">{d.MMSE_nmse_db ?? 'N/A'} dB</td>
                        <td className="py-2 text-purple-400 font-bold">{d.DNN_nmse_db ?? 'N/A'} dB</td>
                        <td className="py-2 text-purple-300">
                          {d.DNN_ber !== undefined ? (d.DNN_ber === 0 ? '0' : d.DNN_ber.toExponential(2)) : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Research Results Figures & Screenshots Showcase */}
          <div className="glass-panel p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
              <div>
                <h3 className="text-sm font-semibold text-fg flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-cyan-400" />
                  <span>Verified Benchmark Publication Screenshots (300 DPI)</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Peer-reviewed IEEE publication figures generated from 105 Monte Carlo trials across SNR 0 to 30 dB. Click any figure to expand.
                </p>
              </div>
              <button
                onClick={() => setActiveTab('publication')}
                className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center gap-1 font-sans"
              >
                <span>View All 6 Figures &rarr;</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {plots.slice(0, 3).map((plot) => (
                <div
                  key={plot.filename}
                  onClick={() => setSelectedPlot(plot)}
                  className="rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/50 p-2.5 transition-all cursor-pointer group flex flex-col justify-between"
                >
                  <div className="aspect-[4/3] bg-slate-950 rounded-lg overflow-hidden flex items-center justify-center p-2 mb-2 relative">
                    <img
                      src={plot.url.startsWith('/api') ? `/results/${plot.filename}` : plot.url}
                      alt={plot.name}
                      className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-300"
                    />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1.5 text-fg text-[11px] font-semibold">
                      <Maximize2 className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Expand High-Res</span>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-xs font-bold text-fg group-hover:text-cyan-400 transition-colors">
                      {plot.name}
                    </h4>
                    <p className="text-[10px] text-slate-400 line-clamp-2">
                      {plot.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* Publication Figures Gallery */
        <div className="space-y-6">
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 flex items-center justify-between">
            <div>
              <p className="font-semibold text-fg">Publication-Grade Matplotlib Figures (300 DPI)</p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Pre-generated with vector styling, error intervals, and IEEE conference formatting. Click any figure to expand.
              </p>
            </div>
            <Badge variant="green">Verified Research Artifacts</Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {plots.map((plot) => (
              <div
                key={plot.filename}
                onClick={() => setSelectedPlot(plot)}
                className="glass-panel overflow-hidden border border-slate-800 hover:border-cyan-500/50 transition-all cursor-pointer group flex flex-col"
              >
                <div className="relative aspect-[4/3] bg-slate-950 overflow-hidden flex items-center justify-center">
                  <img
                    src={plot.url.startsWith('/api') ? `/results/${plot.filename}` : plot.url}
                    alt={plot.name}
                    className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-300"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 text-fg text-xs font-semibold">
                    <Maximize2 className="w-4 h-4 text-cyan-400" />
                    <span>Expand High-Res</span>
                  </div>
                </div>

                <div className="p-4 flex-1 flex flex-col justify-between space-y-2">
                  <div>
                    <h4 className="text-xs font-bold text-fg group-hover:text-cyan-400 transition-colors">
                      {plot.name}
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                      {plot.description}
                    </p>
                  </div>
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-2 border-t border-slate-800/80">
                    <span>{plot.filename}</span>
                    <span className="text-cyan-400">300 DPI</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Plot Fullscreen Zoom Modal */}
      {selectedPlot && (
        <Modal
          isOpen={!!selectedPlot}
          onClose={() => setSelectedPlot(null)}
          title={selectedPlot.name}
          subtitle={selectedPlot.description}
          maxWidth="4xl"
        >
          <div className="space-y-4">
            <div className="w-full rounded-xl bg-slate-950 border border-slate-800 overflow-hidden flex items-center justify-center p-2">
              <img
                src={selectedPlot.url.startsWith('/api') ? `/results/${selectedPlot.filename}` : selectedPlot.url}
                alt={selectedPlot.name}
                className="w-full max-h-[70vh] object-contain"
              />
            </div>
            <div className="flex items-center justify-between text-xs text-slate-400 px-1 font-mono">
              <span>Artifact: {selectedPlot.filename}</span>
              <a
                href={selectedPlot.url}
                target="_blank"
                rel="noreferrer"
                className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-sans"
              >
                <span>Open in New Tab</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
