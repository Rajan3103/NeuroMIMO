"""Supervised training and dataset generation pipeline for PyTorch DNN channel estimation.

Provides reproducible dataset generation from the MIMO-OFDM simulation pipeline,
data leakage prevention via strictly separated train/val/test splits,
training loop with validation tracking, checkpoint persistence, and benchmark comparisons.
"""

import os
import time
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from ..config import SimulationConfig, ChannelModelType, ModulationType
from .dnn import ChannelEstimationNet, DNNEstimator, DEFAULT_CHECKPOINT_PATH
from .ls import LSEstimator
from .mmse import MMSEEstimator
from ..wireless.ofdm import OFDMPipeline
from ..wireless.channel import WirelessChannel
from ..wireless.modulation import get_modulator, generate_random_bits
from ..evaluation.metrics import calculate_mse, calculate_nmse


def generate_channel_dataset(
    num_samples: int = 1000,
    config: Optional[SimulationConfig] = None,
    snr_range: Tuple[float, float] = (0.0, 30.0),
    random_seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generates synthetic MIMO-OFDM channel training dataset without ground-truth leakage.

    For each sample:
        1. A new independent Rayleigh multipath fading channel realization H is drawn.
        2. A random SNR is uniformly sampled from snr_range.
        3. Known pilot symbols are transmitted through the channel with calibrated AWGN.
        4. The receiver extracts pilot observations and computes the initial LS estimate H_LS.
        5. Features X: [Re(H_LS), Im(H_LS)].
        6. Targets Y: [Re(H_true), Im(H_true)].

    Args:
        num_samples: Number of channel realizations to generate.
        config: Simulation configuration (default 2x2 MIMO, 64-FFT, 4 taps).
        snr_range: Min and max SNR (dB) for uniformly sampled training noise.
        random_seed: Seed for reproducible generation.

    Returns:
        Tuple:
            - X: Shape (num_samples, 512) float32 initial LS features
            - Y: Shape (num_samples, 512) float32 ground-truth channel targets
            - snrs: Shape (num_samples,) float32 SNR values in dB
    """
    if config is None:
        config = SimulationConfig(
            num_tx=2,
            num_rx=2,
            fft_size=64,
            cp_length=16,
            pilot_spacing=8,
            num_channel_taps=4,
            random_seed=random_seed,
        )

    rng = np.random.RandomState(random_seed)
    ofdm = OFDMPipeline(
        num_tx=config.num_tx,
        fft_size=config.fft_size,
        cp_length=config.cp_length,
        pilot_spacing=config.pilot_spacing,
    )
    channel = WirelessChannel(
        num_tx=config.num_tx,
        num_rx=config.num_rx,
        num_taps=config.num_channel_taps,
        fft_size=config.fft_size,
        channel_type=ChannelModelType.RAYLEIGH,
        random_seed=random_seed,
    )
    modulator = get_modulator(ModulationType.QPSK)
    ls_estimator = LSEstimator()

    feature_dim = config.fft_size * config.num_rx * config.num_tx * 2
    X = np.zeros((num_samples, feature_dim), dtype=np.float32)
    Y = np.zeros((num_samples, feature_dim), dtype=np.float32)
    snrs = np.zeros(num_samples, dtype=np.float32)

    # Pre-generate random payload bits for transmission slot
    num_symbols = 4
    total_data_symbols_per_tx = num_symbols * ofdm.num_data
    bits_per_sym = modulator.bits_per_symbol
    total_bits_per_tx = total_data_symbols_per_tx * bits_per_sym

    for i in range(num_samples):
        # Sample random SNR uniformly from snr_range
        snr_db = float(rng.uniform(snr_range[0], snr_range[1]))
        snrs[i] = snr_db

        # Transmit payload
        tx_bits = np.zeros((config.num_tx, total_bits_per_tx), dtype=np.int32)
        tx_data_symbols = np.zeros((config.num_tx, num_symbols, ofdm.num_data), dtype=np.complex128)
        for t in range(config.num_tx):
            tx_bits[t] = generate_random_bits(total_bits_per_tx, rng=rng)
            tx_data_symbols[t] = modulator.modulate(tx_bits[t]).reshape(num_symbols, ofdm.num_data)

        tx_freq = ofdm.assemble_mimo_frame(tx_data_symbols)

        # Independent channel realization
        _, H_freq_true = channel.generate_channel_response()

        # Channel propagation with calibrated noise
        rx_freq, noise_var = channel.apply_channel(tx_freq, H_freq_true, snr_db=snr_db)

        # Receiver pilot extraction (only information known to receiver)
        rx_pilots_dict, _ = ofdm.extract_pilots_and_data(rx_freq)

        # Receiver initial LS channel estimate
        H_ls = ls_estimator.estimate(
            rx_pilots=rx_pilots_dict,
            tx_pilots=ofdm.known_pilots_per_tx,
            pilot_indices=ofdm.pilot_indices_per_tx,
            fft_size=config.fft_size,
            num_rx=config.num_rx,
            num_tx=config.num_tx,
        )

        # Feature vector: [Re(H_ls), Im(H_ls)]
        re_ls = np.real(H_ls).flatten()
        im_ls = np.imag(H_ls).flatten()
        X[i] = np.concatenate([re_ls, im_ls]).astype(np.float32)

        # Target vector: [Re(H_true), Im(H_true)]
        re_true = np.real(H_freq_true).flatten()
        im_true = np.imag(H_freq_true).flatten()
        Y[i] = np.concatenate([re_true, im_true]).astype(np.float32)

    return X, Y, snrs


def split_dataset(
    X: np.ndarray,
    Y: np.ndarray,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    random_seed: int = 42,
) -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]]:
    """Splits dataset into Train, Validation, and Held-out Test sets without data leakage."""
    num_samples = len(X)
    rng = np.random.RandomState(random_seed)
    indices = rng.permutation(num_samples)

    n_train = int(num_samples * train_ratio)
    n_val = int(num_samples * val_ratio)

    train_idx = indices[:n_train]
    val_idx = indices[n_train : n_train + n_val]
    test_idx = indices[n_train + n_val :]

    train_set = (X[train_idx], Y[train_idx])
    val_set = (X[val_idx], Y[val_idx])
    test_set = (X[test_idx], Y[test_idx])

    return train_set, val_set, test_set


class ChannelEstimationTrainer:
    """Manages PyTorch DNN training, validation curves, checkpoints, and evaluation."""

    def __init__(
        self,
        model: Optional[ChannelEstimationNet] = None,
        learning_rate: float = 0.001,
        weight_decay: float = 1e-5,
        device: str = "cpu",
    ) -> None:
        self.device = torch.device(device)
        self.model = model or ChannelEstimationNet()
        self.model.to(self.device)
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="min", factor=0.5, patience=3
        )
        self.history: List[Dict[str, Any]] = []

    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 20,
        checkpoint_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Trains the network across epochs while evaluating validation loss."""
        self.history = []
        best_val_loss = float("inf")
        best_state = None

        for epoch in range(1, epochs + 1):
            # Training phase
            self.model.train()
            train_loss_acc = 0.0
            num_train_batches = 0

            for bx, by in train_loader:
                bx = bx.to(self.device)
                by = by.to(self.device)

                self.optimizer.zero_grad()
                pred = self.model(bx)
                loss = self.criterion(pred, by)
                loss.backward()
                self.optimizer.step()

                train_loss_acc += float(loss.item())
                num_train_batches += 1

            epoch_train_loss = train_loss_acc / max(1, num_train_batches)

            # Validation phase
            self.model.eval()
            val_loss_acc = 0.0
            num_val_batches = 0
            with torch.no_grad():
                for vx, vy in val_loader:
                    vx = vx.to(self.device)
                    vy = vy.to(self.device)
                    v_pred = self.model(vx)
                    v_loss = self.criterion(v_pred, vy)
                    val_loss_acc += float(v_loss.item())
                    num_val_batches += 1

            epoch_val_loss = val_loss_acc / max(1, num_val_batches)
            self.scheduler.step(epoch_val_loss)

            self.history.append(
                {
                    "epoch": epoch,
                    "train_loss": float(epoch_train_loss),
                    "val_loss": float(epoch_val_loss),
                }
            )

            # Checkpoint best weights
            if epoch_val_loss < best_val_loss:
                best_val_loss = epoch_val_loss
                best_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}

        # Load best weights
        if best_state is not None:
            self.model.load_state_dict(best_state)

        # Save checkpoint to disk if path specified
        save_path = checkpoint_path or DEFAULT_CHECKPOINT_PATH
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "history": self.history,
                "final_train_loss": self.history[-1]["train_loss"] if self.history else 0.0,
                "final_val_loss": float(best_val_loss),
                "epochs": epochs,
            },
            save_path,
        )

        return {
            "status": "completed",
            "epochs_completed": epochs,
            "final_train_loss": self.history[-1]["train_loss"] if self.history else 0.0,
            "final_val_loss": float(best_val_loss),
            "history": self.history,
            "checkpoint_saved": True,
            "checkpoint_path": save_path,
        }

    def evaluate_test_set(self, test_loader: DataLoader) -> Dict[str, float]:
        """Evaluates model performance metrics on held-out test dataset."""
        self.model.eval()
        mse_acc = 0.0
        nmse_acc = 0.0
        num_batches = 0

        with torch.no_grad():
            for tx, ty in test_loader:
                tx = tx.to(self.device)
                ty = ty.to(self.device)
                preds = self.model(tx)

                batch_mse = nn.functional.mse_loss(preds, ty).item()
                mse_acc += batch_mse

                # NMSE: ||y - pred||^2 / ||y||^2
                err_norm = torch.sum((ty - preds) ** 2, dim=-1)
                true_norm = torch.sum(ty ** 2, dim=-1)
                batch_nmse = torch.mean(err_norm / torch.clamp(true_norm, min=1e-8)).item()
                nmse_acc += batch_nmse
                num_batches += 1

        avg_mse = mse_acc / max(1, num_batches)
        avg_nmse = nmse_acc / max(1, num_batches)
        avg_nmse_db = float(10.0 * np.log10(max(avg_nmse, 1e-12)))

        return {
            "test_mse": float(avg_mse),
            "test_nmse": float(avg_nmse),
            "test_nmse_db": float(avg_nmse_db),
        }
