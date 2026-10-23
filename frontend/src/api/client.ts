import type {
  HealthResponse,
  ConfigResponse,
  ModelStatus,
  SimulationConfig,
  SimulationResult,
  EstimationAlgorithm,
  AlgorithmComparisonResult,
  ModelTrainResult,
  TrainingJobStatus,
  ModelPredictResult,
  ExperimentRecord,
  ExperimentPlotsResponse,
  SnrSweepDataset,
} from '../types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let errorMessage = `API Error [${response.status}]`;
    // A response body can only be read once, so read it as text and parse it here.
    const errorText = await response.text();
    try {
      const errorJson = JSON.parse(errorText);
      const detail = errorJson.detail;
      if (typeof detail === 'string') {
        errorMessage = detail;
      } else if (detail) {
        errorMessage = JSON.stringify(detail);
      }
    } catch {
      errorMessage = errorText || response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    return fetchJson<HealthResponse>(`${API_BASE}/health`);
  },

  async getConfig(): Promise<ConfigResponse> {
    return fetchJson<ConfigResponse>(`${API_BASE}/config`);
  },

  async getModelStatus(): Promise<ModelStatus> {
    return fetchJson<ModelStatus>(`${API_BASE}/model/status`);
  },

  async getTrainingStatus(): Promise<TrainingJobStatus> {
    return fetchJson<TrainingJobStatus>(`${API_BASE}/model/train/status`);
  },

  async getExperiments(): Promise<ExperimentRecord[]> {
    return fetchJson<ExperimentRecord[]>(`${API_BASE}/experiments`);
  },

  async getExperimentById(id: string): Promise<ExperimentRecord> {
    return fetchJson<ExperimentRecord>(`${API_BASE}/experiments/${id}`);
  },

  async getExperimentPlots(id: string = 'latest'): Promise<ExperimentPlotsResponse> {
    return fetchJson<ExperimentPlotsResponse>(`${API_BASE}/experiments/${id}/plots`);
  },

  getPlotImageUrl(id: string, filename: string): string {
    return `${API_BASE}/experiments/${id}/plots/${filename}`;
  },

  async runSimulation(config: SimulationConfig): Promise<SimulationResult> {
    return fetchJson<SimulationResult>(`${API_BASE}/simulation/run`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  },

  async compareEstimators(params: {
    snr_db: number;
    algorithms: EstimationAlgorithm[];
    num_realizations?: number;
    fft_size?: number;
    cp_length?: number;
    modulation?: string;
  }): Promise<{ snr_db: number; results: AlgorithmComparisonResult[] }> {
    return fetchJson(`${API_BASE}/estimation/compare`, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  async trainModel(params: {
    epochs: number;
    batch_size: number;
    learning_rate: number;
    num_samples: number;
    snr_range: [number, number];
    background?: boolean;
    random_seed?: number;
  }): Promise<ModelTrainResult> {
    return fetchJson<ModelTrainResult>(`${API_BASE}/model/train`, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  async predictChannel(params: {
    features?: number[];
    snr_db?: number;
    channel_model?: string;
    modulation?: string;
  }): Promise<ModelPredictResult> {
    return fetchJson<ModelPredictResult>(`${API_BASE}/model/predict`, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  async getBenchmarkSnrSweep(): Promise<SnrSweepDataset> {
    return fetchJson<SnrSweepDataset>(`${API_BASE}/experiments/benchmark/snr-sweep`);
  },
};
