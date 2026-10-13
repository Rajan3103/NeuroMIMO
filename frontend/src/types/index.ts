export type ModulationType = 'QPSK' | '16QAM';
export type ChannelModelType = 'RAYLEIGH' | 'AWGN';
export type EstimationAlgorithm = 'PERFECT' | 'LS' | 'MMSE' | 'DNN';
export type EqualizerType = 'ZF' | 'MMSE';

export interface HealthResponse {
  status: string;
  version: string;
  device: string;
  cuda_available: boolean;
  torch_version: string;
  numpy_version: string;
}

export interface ConfigResponse {
  default_snr_db: number;
  min_snr_db: number;
  max_snr_db: number;
  fft_sizes: number[];
  default_fft_size: number;
  cp_lengths: number[];
  pilot_spacings: number[];
  supported_modulations: string[];
  supported_channel_models: string[];
  supported_algorithms: string[];
  supported_antennas: { tx: number; rx: number }[];
}

export interface ConstellationPoint {
  i: number;
  q: number;
}

export interface SimulationConfig {
  num_tx: number;
  num_rx: number;
  fft_size: number;
  cp_length: number;
  pilot_spacing: number;
  modulation: ModulationType;
  channel_model: ChannelModelType;
  snr_db: number;
  algorithm: EstimationAlgorithm;
  num_ofdm_symbols: number;
  random_seed?: number;
}

export interface SimulationResult {
  id?: string;
  mse: number;
  nmse: number;
  nmse_db: number;
  ber: number;
  ser: number;
  total_bits: number;
  bit_errors: number;
  total_symbols: number;
  symbol_errors: number;
  snr_db: number;
  algorithm: string;
  execution_time_ms: number;
  tx_constellation_sample: ConstellationPoint[];
  rx_constellation_sample: ConstellationPoint[];
  channel_magnitude_profile: number[];
}

export interface AlgorithmComparisonResult {
  algorithm: string;
  nmse: number;
  nmse_db: number;
  ber: number;
  ser: number;
  execution_time_ms: number;
}

export interface ModelStatus {
  trained: boolean;
  checkpoint_exists: boolean;
  checkpoint_path: string;
  parameters_count: number;
  device: string;
  active_job_id?: string;
  training_status?: string;
}

export interface TrainingProgressPoint {
  epoch: number;
  train_loss: number;
  val_loss: number;
}

export interface ModelTrainResult {
  status: string;
  job_id?: string;
  epochs_completed: number;
  final_train_loss: number;
  final_val_loss: number;
  history: TrainingProgressPoint[];
  checkpoint_saved: boolean;
  checkpoint_path: string;
}

export interface TrainingJobStatus {
  job_id: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  epochs_completed: number;
  total_epochs: number;
  current_train_loss?: number;
  current_val_loss?: number;
  history: TrainingProgressPoint[];
  error?: string;
}

export interface ModelPredictResult {
  status: string;
  h_pred_real: number[];
  h_pred_imag: number[];
  h_true_real?: number[];
  h_true_imag?: number[];
  nmse?: number;
  nmse_db?: number;
  inference_time_ms: number;
  shape: number[];
}

export interface PlotItem {
  name: string;
  filename: string;
  url: string;
  description: string;
}

export interface ExperimentPlotsResponse {
  experiment_id: string;
  plots: PlotItem[];
}

export interface ExperimentRecord {
  id: string;
  created_at: string;
  name: string;
  config: any;
  algorithm: string;
  snr_db: number;
  nmse: number;
  ber: number;
  ser: number;
  execution_time_ms: number;
  results?: SimulationResult;
  notes?: string;
}

export interface SnrSweepRecord {
  snr_db: number;
  available: boolean;
  mse: number;
  nmse: number;
  nmse_db: number;
  ber: number;
  ci_lower: number;
  ci_upper: number;
  ser: number;
  bit_errors: number;
  total_bits: number;
  symbol_errors: number;
  total_symbols: number;
  inference_time_ms: number;
  statistically_conclusive: boolean;
  confidence_note: string;
}

export interface SnrSweepDataset {
  experiment_name: string;
  channel_model: string;
  modulation: string;
  pilot_spacing: number;
  num_channel_taps: number;
  pdp_decay: number;
  num_trials_per_snr: number;
  snr_points: number[];
  algorithms: string[];
  records: Record<string, SnrSweepRecord[]>;
}
