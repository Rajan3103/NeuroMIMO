import React, { useState, useEffect, useRef } from 'react';
import {
  BrainCircuit,
  Play,
  CheckCircle2,
  Cpu,
  Activity,
  AlertCircle,
  RefreshCw,
  Zap,
  Sliders,
  TrendingDown,
  Layers,
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
} from 'recharts';
import { Badge } from '../components/common/Badge';
import { StatCard } from '../components/common/StatCard';
import { api } from '../api/client';
import type {
  ModelStatus,
  TrainingProgressPoint,
  TrainingJobStatus,
  ModelPredictResult,
} from '../types';

interface ModelTrainingPageProps {
  modelStatus: ModelStatus | null;
  onRefreshStatus: () => void;
}

export const ModelTrainingPage: React.FC<ModelTrainingPageProps> = ({
  modelStatus,
  onRefreshStatus,
}) => {
  const [epochs, setEpochs] = useState<number>(20);
  const [batchSize, setBatchSize] = useState<number>(64);
  const [learningRate, setLearningRate] = useState<number>(0.001);
  const [numSamples, setNumSamples] = useState<number>(1000);
  const [minSnr, setMinSnr] = useState<number>(0);
  const [maxSnr, setMaxSnr] = useState<number>(30);
  const [backgroundMode, setBackgroundMode] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(false);
  const [jobStatus, setJobStatus] = useState<TrainingJobStatus | null>(null);
  const [history, setHistory] = useState<TrainingProgressPoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [verifyResult, setVerifyResult] = useState<ModelPredictResult | null>(null);
  const [verifying, setVerifying] = useState<boolean>(false);

  const pollIntervalRef = useRef<any>(null);

  // Load existing training status and history on initial mount
  useEffect(() => {
    loadExistingStatus();
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const loadExistingStatus = async () => {
    try {
      const status = await api.getTrainingStatus();
      setJobStatus(status);
      if (status.history && status.history.length > 0) {
        setHistory(status.history);
      }
      if (status.status === 'running') {
        startPolling();
      }
    } catch {
      // Ignore initial status load failure if none exists
    }
  };

  const startPolling = () => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    setLoading(true);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const status = await api.getTrainingStatus();
        setJobStatus(status);
        if (status.history && status.history.length > 0) {
          setHistory(status.history);
        }

        if (status.status === 'completed' || status.status === 'failed') {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setLoading(false);
          onRefreshStatus();
          if (status.status === 'failed') {
            setError(status.error || 'Training job failed in background worker.');
          }
        }
      } catch (err: any) {
        console.error('Polling error:', err);
      }
    }, 1000);
  };

  const handleTrain = async () => {
    setLoading(true);
    setError(null);
    setVerifyResult(null);

    try {
      if (backgroundMode) {
        await api.trainModel({
          epochs,
          batch_size: batchSize,
          learning_rate: learningRate,
          num_samples: numSamples,
          snr_range: [minSnr, maxSnr],
          background: true,
        });
        startPolling();
      } else {
        const res = await api.trainModel({
          epochs,
          batch_size: batchSize,
          learning_rate: learningRate,
          num_samples: numSamples,
          snr_range: [minSnr, maxSnr],
          background: false,
        });
        setHistory(res.history);
        setJobStatus({
          job_id: res.job_id || 'sync',
          status: 'completed',
          epochs_completed: res.epochs_completed,
          total_epochs: epochs,
          current_train_loss: res.final_train_loss,
          current_val_loss: res.final_val_loss,
          history: res.history,
        });
        onRefreshStatus();
        setLoading(false);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to initiate training session');
      setLoading(false);
    }
  };

  const handleVerifyCheckpoint = async () => {
    setVerifying(true);
    try {
      const pred = await api.predictChannel({
        snr_db: 20.0,
        channel_model: 'RAYLEIGH',
        modulation: 'QPSK',
      });
      setVerifyResult(pred);
    } catch (err: any) {
      setError(err?.message || 'Verification prediction failed');
    } finally {
      setVerifying(false);
    }
  };

  const isTrainingActive = loading || jobStatus?.status === 'running';
  const progressPercent =
    jobStatus?.total_epochs && jobStatus.total_epochs > 0
      ? Math.min(100, Math.round((jobStatus.epochs_completed / jobStatus.total_epochs) * 100))
      : 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-purple-400 font-semibold px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/20">
              PyTorch 2.x • Deep Learning
            </span>
            <Badge variant={modelStatus?.trained ? 'green' : 'amber'} dot>
              {modelStatus?.trained ? 'Checkpoint Ready' : 'Untrained'}
            </Badge>
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">PyTorch DNN Model Studio</h2>
          <p className="text-xs text-slate-400">
            Supervised residual deep neural network training on synthetic MIMO-OFDM channel realizations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRefreshStatus}
            title="Refresh status from backend"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={handleTrain}
            disabled={isTrainingActive}
            className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold uppercase tracking-wider flex items-center gap-2 transition-all shadow-lg shadow-purple-950/50 disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${isTrainingActive ? 'animate-spin' : ''}`} />
            <span>{isTrainingActive ? 'Training in Progress...' : 'Start Training'}</span>
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-300 hover:text-white underline text-[11px]">
            Dismiss
          </button>
        </div>
      )}

      {/* Status KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Network Architecture"
          value="Residual MLP"
          subtitle="Input 512 → [256, 128, 256] → Output 512"
          icon={BrainCircuit}
          variant="purple"
        />
        <StatCard
          title="Trainable Parameters"
          value={modelStatus?.parameters_count ? modelStatus.parameters_count.toLocaleString() : '330,112'}
          subtitle="Weights + Biases in PyTorch"
          icon={Cpu}
          variant="cyan"
        />
        <StatCard
          title="Compute Device"
          value={modelStatus?.device ? modelStatus.device.toUpperCase() : 'CPU'}
          subtitle="Tensor Acceleration Engine"
          icon={Activity}
          variant="green"
        />
        <StatCard
          title="Current Job State"
          value={isTrainingActive ? 'RUNNING' : jobStatus?.status ? jobStatus.status.toUpperCase() : 'IDLE'}
          subtitle={isTrainingActive ? `Epoch ${jobStatus?.epochs_completed}/${jobStatus?.total_epochs}` : 'Ready for training'}
          icon={Zap}
          variant={isTrainingActive ? 'amber' : undefined}
        />
      </div>

      {/* Live Training Progress Indicator */}
      {isTrainingActive && (
        <div className="glass-panel p-5 space-y-3 border-purple-500/40 bg-purple-950/10">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-purple-300 font-semibold">
              <Activity className="w-4 h-4 animate-spin text-purple-400" />
              <span>Training Neural Estimator in Background Thread...</span>
            </div>
            <span className="font-mono text-purple-200">
              Epoch {jobStatus?.epochs_completed ?? 0} of {jobStatus?.total_epochs ?? epochs} ({progressPercent}%)
            </span>
          </div>

          <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-purple-900/50">
            <div
              className="bg-gradient-to-r from-purple-600 via-cyan-500 to-emerald-400 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1">
            <span>
              Current Train Loss:{' '}
              <strong className="text-purple-300">
                {jobStatus?.current_train_loss ? jobStatus.current_train_loss.toExponential(4) : 'Computing...'}
              </strong>
            </span>
            <span>
              Current Val Loss:{' '}
              <strong className="text-cyan-300">
                {jobStatus?.current_val_loss ? jobStatus.current_val_loss.toExponential(4) : 'Computing...'}
              </strong>
            </span>
          </div>
        </div>
      )}

      {/* Configuration & Training Settings Form */}
      <div className="glass-panel p-6 space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-white">Training Hyperparameters & Dataset Generation</h3>
          </div>
          <span className="text-[11px] text-slate-400">Adam Optimizer • MSE Criterion</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">
              Training Epochs: <span className="text-purple-400 font-mono font-bold">{epochs}</span>
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={epochs}
              disabled={isTrainingActive}
              onChange={(e) => setEpochs(Math.max(1, Math.min(100, Number(e.target.value))))}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500 font-mono disabled:opacity-50"
            />
            <span className="text-[10px] text-slate-400 mt-1 block">Number of complete dataset passes</span>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">
              Mini-Batch Size: <span className="text-purple-400 font-mono font-bold">{batchSize}</span>
            </label>
            <select
              value={batchSize}
              disabled={isTrainingActive}
              onChange={(e) => setBatchSize(Number(e.target.value))}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500 font-mono disabled:opacity-50"
            >
              <option value="16">16 realizations</option>
              <option value="32">32 realizations</option>
              <option value="64">64 realizations</option>
              <option value="128">128 realizations</option>
            </select>
            <span className="text-[10px] text-slate-400 mt-1 block">Gradient update batch size</span>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">
              Initial Learning Rate: <span className="text-purple-400 font-mono font-bold">{learningRate}</span>
            </label>
            <input
              type="number"
              step="0.0001"
              min="0.00001"
              max="0.1"
              value={learningRate}
              disabled={isTrainingActive}
              onChange={(e) => setLearningRate(Number(e.target.value))}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500 font-mono disabled:opacity-50"
            />
            <span className="text-[10px] text-slate-400 mt-1 block">Step size for Adam optimizer</span>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">
              Channel Realizations: <span className="text-purple-400 font-mono font-bold">{numSamples.toLocaleString()}</span>
            </label>
            <input
              type="number"
              min="100"
              max="5000"
              step="100"
              value={numSamples}
              disabled={isTrainingActive}
              onChange={(e) => setNumSamples(Math.max(100, Math.min(5000, Number(e.target.value))))}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500 font-mono disabled:opacity-50"
            />
            <span className="text-[10px] text-slate-400 mt-1 block">80% Train / 20% Validation split</span>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">
              SNR Range (dB): <span className="text-purple-400 font-mono font-bold">[{minSnr}, {maxSnr}] dB</span>
            </label>
            <div className="grid grid-cols-2 gap-2">
              <input
                type="number"
                min="0"
                max={maxSnr - 1}
                value={minSnr}
                disabled={isTrainingActive}
                onChange={(e) => setMinSnr(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-xs text-white focus:outline-none focus:border-purple-500 font-mono disabled:opacity-50"
                placeholder="Min SNR"
              />
              <input
                type="number"
                min={minSnr + 1}
                max="40"
                value={maxSnr}
                disabled={isTrainingActive}
                onChange={(e) => setMaxSnr(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-xs text-white focus:outline-none focus:border-purple-500 font-mono disabled:opacity-50"
                placeholder="Max SNR"
              />
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">Uniform random noise injection range</span>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Execution Mode</label>
            <div className="flex items-center gap-3 pt-2">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-200">
                <input
                  type="checkbox"
                  checked={backgroundMode}
                  disabled={isTrainingActive}
                  onChange={(e) => setBackgroundMode(e.target.checked)}
                  className="rounded bg-slate-900 border-slate-700 text-purple-600 focus:ring-0"
                />
                <span>Async Thread Worker</span>
              </label>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              Non-blocking backend worker with live polling
            </span>
          </div>
        </div>
      </div>

      {/* Loss Curves & Convergence Recharts Plot */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-white">Loss Convergence Curve</h3>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
              <span className="text-slate-300">Training Loss (MSE)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-slate-300">Validation Loss (MSE)</span>
            </div>
          </div>
        </div>

        {history.length === 0 ? (
          <div className="h-64 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-col items-center justify-center text-slate-400 text-xs gap-2">
            <Layers className="w-8 h-8 text-purple-500/40" />
            <span>No training history available yet</span>
            <span className="text-[10px] text-slate-400">Click &ldquo;Start Training&rdquo; to train the neural network and record loss curves.</span>
          </div>
        ) : (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                <XAxis
                  dataKey="epoch"
                  stroke="var(--chart-axis)"
                  fontSize={11}
                  tickFormatter={(val) => `Ep ${val}`}
                />
                <YAxis
                  stroke="var(--chart-axis)"
                  fontSize={11}
                  domain={['auto', 'auto']}
                  tickFormatter={(val) => (typeof val === 'number' ? val.toExponential(2) : val)}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--tooltip-bg)',
                    borderColor: 'var(--tooltip-border)',
                    borderRadius: '8px',
                    fontSize: '11px',
                  }}
                  formatter={(val: any) => [
                    typeof val === 'number' ? val.toExponential(5) : val,
                    '',
                  ]}
                  labelFormatter={(label) => `Epoch ${label}`}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Line
                  type="monotone"
                  dataKey="train_loss"
                  name="Training Loss"
                  stroke="#c084fc"
                  strokeWidth={2}
                  dot={{ r: 2, fill: '#c084fc' }}
                  activeDot={{ r: 5 }}
                />
                <Line
                  type="monotone"
                  dataKey="val_loss"
                  name="Validation Loss"
                  stroke="#22d3ee"
                  strokeWidth={2}
                  dot={{ r: 2, fill: '#22d3ee' }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Checkpoint Summary & Verification Section */}
      {modelStatus?.trained && (
        <div className="glass-panel p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Active Model Checkpoint Verification</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5 font-mono text-[11px]">
                {modelStatus.checkpoint_path}
              </p>
            </div>
            <button
              onClick={handleVerifyCheckpoint}
              disabled={verifying}
              className="px-3.5 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-semibold flex items-center gap-2 transition-all disabled:opacity-50"
            >
              <Zap className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
              <span>{verifying ? 'Verifying...' : 'Run Test Inference'}</span>
            </button>
          </div>

          {verifyResult && (
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
              <div>
                <span className="text-slate-400 text-[10px] block">Test NMSE:</span>
                <span className="text-emerald-400 font-bold text-sm">
                  {verifyResult.nmse ? verifyResult.nmse.toExponential(3) : 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 text-[10px] block">Test NMSE (dB):</span>
                <span className="text-cyan-400 font-bold text-sm">
                  {verifyResult.nmse_db ? `${verifyResult.nmse_db.toFixed(2)} dB` : 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 text-[10px] block">Inference Latency:</span>
                <span className="text-purple-400 font-bold text-sm">
                  {verifyResult.inference_time_ms.toFixed(2)} ms
                </span>
              </div>
              <div>
                <span className="text-slate-400 text-[10px] block">Tensor Dimensions:</span>
                <span className="text-white font-bold text-sm">
                  {verifyResult.shape.join(' × ')}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
