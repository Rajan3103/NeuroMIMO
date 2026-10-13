"""Deep Neural Network (DNN) Channel Estimator implemented in PyTorch.

Accepts noisy pilot observations or LS initial estimates, learns non-linear channel
refinement and residual denoising, and outputs refined full Channel Frequency Response (CFR).
"""

import os
from typing import Optional, List, Tuple, Union, Dict
import numpy as np
import torch
import torch.nn as nn
from .base import BaseChannelEstimator
from .ls import LSEstimator

DEFAULT_CHECKPOINT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "neuromimo_dnn.pt"
)


class ChannelEstimationNet(nn.Module):
    """Deep residual neural network for MIMO-OFDM channel denoising and estimation.

    Architecture:
        x_in (512) -> Linear(512, 256) -> LayerNorm -> GELU -> Dropout
                   -> Linear(256, 128) -> LayerNorm -> GELU -> Dropout
                   -> Linear(128, 256) -> LayerNorm -> GELU -> Dropout
                   -> Linear(256, 512) -> + x_in (Residual skip connection)
    """

    def __init__(
        self,
        input_dim: int = 64 * 2 * 2 * 2,  # (fft_size * num_rx * num_tx * 2_real_imag = 512)
        hidden_dims: Optional[List[int]] = None,
        output_dim: int = 64 * 2 * 2 * 2,
        dropout_rate: float = 0.05,
    ) -> None:
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [256, 128, 256]

        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, h_dim))
            layers.append(nn.LayerNorm(h_dim))
            layers.append(nn.GELU())
            if dropout_rate > 0.0:
                layers.append(nn.Dropout(dropout_rate))
            prev_dim = h_dim

        layers.append(nn.Linear(prev_dim, output_dim))
        self.residual_branch = nn.Sequential(*layers)
        self.input_dim = input_dim
        self.output_dim = output_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass with residual skip connection: output = x + delta(x)."""
        delta = self.residual_branch(x)
        if x.shape[-1] == delta.shape[-1]:
            return x + delta
        return delta


class DNNEstimator(BaseChannelEstimator):
    """Wraps PyTorch ChannelEstimationNet for inference and evaluation."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        fft_size: int = 64,
        num_rx: int = 2,
        num_tx: int = 2,
        device: str = "cpu",
    ) -> None:
        self.fft_size = fft_size
        self.num_rx = num_rx
        self.num_tx = num_tx
        self.device = torch.device(device)
        self.ls_preprocessor = LSEstimator()

        self.input_dim = fft_size * num_rx * num_tx * 2
        self.output_dim = fft_size * num_rx * num_tx * 2
        self.model = ChannelEstimationNet(
            input_dim=self.input_dim,
            output_dim=self.output_dim,
        ).to(self.device)

        self.model_loaded = False
        target_path = model_path or DEFAULT_CHECKPOINT_PATH
        if target_path and os.path.exists(target_path):
            self.load_checkpoint(target_path)

    def load_checkpoint(self, path: str) -> None:
        """Loads trained weights and architecture configurations from checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        if "model_state_dict" in checkpoint:
            self.model.load_state_dict(checkpoint["model_state_dict"])
        else:
            self.model.load_state_dict(checkpoint)
        self.model.eval()
        self.model_loaded = True

    def save_checkpoint(
        self,
        path: str,
        training_metadata: Optional[Dict] = None,
    ) -> None:
        """Saves model weights along with metadata."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        payload = {
            "model_state_dict": self.model.state_dict(),
            "fft_size": self.fft_size,
            "num_rx": self.num_rx,
            "num_tx": self.num_tx,
            "input_dim": self.input_dim,
            "output_dim": self.output_dim,
        }
        if training_metadata:
            payload.update(training_metadata)
        torch.save(payload, path)

    def estimate(
        self,
        rx_pilots: Union[np.ndarray, Dict[int, np.ndarray]],
        tx_pilots: Union[np.ndarray, Dict[int, np.ndarray]],
        pilot_indices: Union[np.ndarray, Dict[int, np.ndarray]],
        fft_size: int,
        noise_var: Optional[float] = None,
        num_rx: Optional[int] = None,
        num_tx: Optional[int] = None,
        **kwargs,
    ) -> np.ndarray:
        """Runs DNN-based channel estimation.

        If a trained checkpoint is not loaded, falls back to LS initial estimate
        so the simulation pipeline functions prior to model training.
        """
        n_rx = num_rx or self.num_rx
        n_tx = num_tx or self.num_tx

        # Step 1: Initial Least Squares estimation from received pilots only
        h_ls = self.ls_preprocessor.estimate(
            rx_pilots=rx_pilots,
            tx_pilots=tx_pilots,
            pilot_indices=pilot_indices,
            fft_size=fft_size,
            noise_var=noise_var,
            num_rx=n_rx,
            num_tx=n_tx,
        )

        if not self.model_loaded:
            # Fallback to LS baseline if no trained checkpoint exists yet
            return h_ls

        # Step 2: Extract real and imaginary components
        # Shape of h_ls: (n_rx, n_tx, fft_size)
        real_part = np.real(h_ls).flatten()
        imag_part = np.imag(h_ls).flatten()
        features = np.concatenate([real_part, imag_part]).astype(np.float32)

        tensor_in = torch.from_numpy(features).unsqueeze(0).to(self.device)

        # Step 3: PyTorch Model Inference
        self.model.eval()
        with torch.no_grad():
            preds = self.model(tensor_in).cpu().squeeze(0).numpy()

        # Step 4: Reconstruct complex matrix from predicted real & imag components
        half_len = len(preds) // 2
        pred_real = preds[:half_len].reshape(n_rx, n_tx, fft_size)
        pred_imag = preds[half_len:].reshape(n_rx, n_tx, fft_size)

        return (pred_real + 1j * pred_imag).astype(np.complex128)
