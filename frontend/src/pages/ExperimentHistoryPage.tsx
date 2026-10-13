import React, { useEffect, useState } from 'react';
import {
  History,
  RefreshCw,
  Database,
  Search,
  Filter,
  Download,
  Eye,
  Activity,
  Radio,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { StatCard } from '../components/common/StatCard';
import { Modal } from '../components/common/Modal';
import { api } from '../api/client';
import type { ExperimentRecord } from '../types';

export const ExperimentHistoryPage: React.FC = () => {
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [algoFilter, setAlgoFilter] = useState<string>('ALL');
  const [selectedExp, setSelectedExp] = useState<ExperimentRecord | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getExperiments();
      setExperiments(data);
    } catch (err: any) {
      console.error(err);
      setError(err?.message || 'Failed to fetch experiment history from backend database.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  // Filtered experiments
  const filteredExperiments = experiments.filter((exp) => {
    const matchesSearch =
      exp.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      exp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      exp.algorithm.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesAlgo = algoFilter === 'ALL' || exp.algorithm.toUpperCase() === algoFilter;

    return matchesSearch && matchesAlgo;
  });

  // Export to CSV
  const handleExportCsv = () => {
    if (experiments.length === 0) return;

    const headers = [
      'id',
      'created_at',
      'name',
      'algorithm',
      'snr_db',
      'nmse',
      'ber',
      'ser',
      'execution_time_ms',
    ];

    const rows = experiments.map((exp) => [
      exp.id,
      exp.created_at,
      `"${exp.name.replace(/"/g, '""')}"`,
      exp.algorithm,
      exp.snr_db,
      exp.nmse,
      exp.ber,
      exp.ser,
      exp.execution_time_ms,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `neuromimo_experiments_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-semibold px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">
              Audit & Provenance Log
            </span>
            <Badge variant="cyan">
              <Database className="w-3 h-3 inline mr-1" />
              SQLite Database
            </Badge>
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">Experiment History</h2>
          <p className="text-xs text-slate-400">
            Persistent log of simulation runs, estimation benchmarks, and channel realizations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportCsv}
            disabled={experiments.length === 0}
            className="px-3.5 py-2 rounded-lg bg-slate-900 border border-slate-700 hover:border-slate-600 text-slate-200 text-xs font-semibold flex items-center gap-2 transition-all disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={fetchHistory}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Recorded Experiments"
          value={experiments.length.toString()}
          subtitle="Indexed in SQLite storage"
          icon={Database}
          variant="cyan"
        />
        <StatCard
          title="Best Recorded NMSE"
          value={
            experiments.length > 0
              ? `${Math.min(...experiments.map((e) => (10 * Math.log10(Math.max(1e-12, e.nmse))))).toFixed(2)} dB`
              : 'N/A'
          }
          subtitle="Across all historical trials"
          icon={Activity}
          variant="purple"
        />
        <StatCard
          title="Average Latency"
          value={
            experiments.length > 0
              ? `${(experiments.reduce((a, b) => a + b.execution_time_ms, 0) / experiments.length).toFixed(2)} ms`
              : '0.00 ms'
          }
          subtitle="Mean computational runtime"
          icon={Radio}
          variant="green"
        />
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-72">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search experiments by name, ID or algo..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-400 font-medium">Algorithm:</span>
          <select
            value={algoFilter}
            onChange={(e) => setAlgoFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
          >
            <option value="ALL">All Algorithms</option>
            <option value="DNN">DNN</option>
            <option value="MMSE">MMSE</option>
            <option value="LS">LS</option>
            <option value="PERFECT">PERFECT</option>
          </select>
        </div>
      </div>

      {/* Experiments Table */}
      <div className="glass-panel p-6">
        {filteredExperiments.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-xs space-y-2">
            <History className="w-8 h-8 mx-auto text-slate-600 mb-2" />
            <p className="font-semibold text-slate-300">No matching experiment records found.</p>
            <p className="text-slate-500 text-[11px]">
              Execute simulations from the MIMO-OFDM Simulator or Channel Estimation Lab to populate records.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="pb-3 font-semibold">Timestamp</th>
                  <th className="pb-3 font-semibold">Experiment Name</th>
                  <th className="pb-3 font-semibold">Algorithm</th>
                  <th className="pb-3 font-semibold">SNR</th>
                  <th className="pb-3 font-semibold">NMSE</th>
                  <th className="pb-3 font-semibold">BER</th>
                  <th className="pb-3 font-semibold">Runtime</th>
                  <th className="pb-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {filteredExperiments.map((exp) => (
                  <tr key={exp.id} className="text-slate-200 hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 text-slate-400 text-[11px]">
                      {new Date(exp.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 font-sans font-medium text-white max-w-[180px] truncate">
                      {exp.name}
                    </td>
                    <td className="py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          exp.algorithm === 'DNN'
                            ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                            : exp.algorithm === 'MMSE'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'bg-orange-500/20 text-orange-300 border border-orange-500/30'
                        }`}
                      >
                        {exp.algorithm}
                      </span>
                    </td>
                    <td className="py-3 text-cyan-400">{exp.snr_db} dB</td>
                    <td className="py-3 text-slate-300">{exp.nmse.toExponential(2)}</td>
                    <td className="py-3 text-emerald-400">{exp.ber.toExponential(2)}</td>
                    <td className="py-3 text-slate-400">{exp.execution_time_ms.toFixed(1)} ms</td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => setSelectedExp(exp)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 hover:text-cyan-300 text-[11px] font-sans font-semibold inline-flex items-center gap-1 transition-colors"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Inspect Experiment Modal */}
      {selectedExp && (
        <Modal
          isOpen={!!selectedExp}
          onClose={() => setSelectedExp(null)}
          title={`Experiment Inspection: ${selectedExp.name}`}
          subtitle={`ID: ${selectedExp.id} • Recorded: ${new Date(selectedExp.created_at).toLocaleString()}`}
          maxWidth="4xl"
        >
          <div className="space-y-5">
            {/* Quick Metrics Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-slate-900 border border-slate-800 font-mono text-xs">
              <div>
                <span className="text-slate-500 text-[10px] block">Algorithm:</span>
                <span className="text-white font-bold">{selectedExp.algorithm}</span>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] block">SNR:</span>
                <span className="text-cyan-400 font-bold">{selectedExp.snr_db} dB</span>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] block">NMSE:</span>
                <span className="text-purple-400 font-bold">{selectedExp.nmse.toExponential(4)}</span>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] block">BER / SER:</span>
                <span className="text-emerald-400 font-bold">
                  {selectedExp.ber.toExponential(2)} / {selectedExp.ser.toExponential(2)}
                </span>
              </div>
            </div>

            {/* Config JSON & Raw Results */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-cyan-400" />
                <span>Simulation Configuration & Parameters</span>
              </h4>
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 max-h-48 overflow-y-auto">
                <pre className="text-[11px] font-mono text-cyan-300/90 whitespace-pre-wrap">
                  {JSON.stringify(selectedExp.config, null, 2)}
                </pre>
              </div>
            </div>

            {selectedExp.results && (
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-purple-400" />
                  <span>Detailed Execution Output</span>
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs font-mono p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                  <div>
                    <span className="text-slate-500 text-[10px] block">Bit Errors:</span>
                    <span className="text-white">
                      {selectedExp.results.bit_errors} / {selectedExp.results.total_bits}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] block">Symbol Errors:</span>
                    <span className="text-white">
                      {selectedExp.results.symbol_errors} / {selectedExp.results.total_symbols}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[10px] block">Pipeline Latency:</span>
                    <span className="text-white">{selectedExp.execution_time_ms.toFixed(2)} ms</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
