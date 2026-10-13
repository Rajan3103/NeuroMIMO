"""Command-line training script for NeuroMIMO PyTorch Channel Estimator."""

import os
import sys
import argparse
import torch
from torch.utils.data import TensorDataset, DataLoader

# Ensure neuromimo is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from neuromimo.estimation.trainer import (
    generate_channel_dataset,
    split_dataset,
    ChannelEstimationTrainer,
)
from neuromimo.estimation.dnn import DEFAULT_CHECKPOINT_PATH


def run_training(
    num_samples: int = 500,
    epochs: int = 15,
    batch_size: int = 32,
    learning_rate: float = 0.003,
    checkpoint_path: str = DEFAULT_CHECKPOINT_PATH,
    random_seed: int = 42,
):
    print("=" * 60)
    print("NeuroMIMO PyTorch DNN Channel Estimator Training Pipeline")
    print("=" * 60)
    print(f"Dataset Size: {num_samples} channel realizations")
    print(f"Epochs: {epochs} | Batch Size: {batch_size} | Learning Rate: {learning_rate}")
    print(f"Random Seed: {random_seed} | Checkpoint Destination: {checkpoint_path}")
    print("-" * 60)

    print("Step 1/4: Generating synthetic MIMO-OFDM dataset...")
    X, Y, snrs = generate_channel_dataset(
        num_samples=num_samples,
        snr_range=(0.0, 30.0),
        random_seed=random_seed,
    )
    print(f"Generated feature matrix X: {X.shape}, target matrix Y: {Y.shape}")

    print("Step 2/4: Splitting dataset (70% Train, 15% Val, 15% Test)...")
    (X_tr, Y_tr), (X_val, Y_val), (X_te, Y_te) = split_dataset(
        X, Y, train_ratio=0.70, val_ratio=0.15, random_seed=random_seed
    )
    print(f"Train samples: {len(X_tr)} | Val samples: {len(X_val)} | Test samples: {len(X_te)}")

    tr_ds = TensorDataset(torch.from_numpy(X_tr), torch.from_numpy(Y_tr))
    val_ds = TensorDataset(torch.from_numpy(X_val), torch.from_numpy(Y_val))
    te_ds = TensorDataset(torch.from_numpy(X_te), torch.from_numpy(Y_te))

    tr_loader = DataLoader(tr_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    te_loader = DataLoader(te_ds, batch_size=batch_size)

    print("Step 3/4: Training Residual MLP network...")
    trainer = ChannelEstimationTrainer(learning_rate=learning_rate)
    res = trainer.fit(
        tr_loader,
        val_loader,
        epochs=epochs,
        checkpoint_path=checkpoint_path,
    )

    print("Epoch-by-Epoch Loss Progress:")
    for pt in res["history"]:
        print(f"  Epoch {pt['epoch']:2d}/{epochs} | Train Loss: {pt['train_loss']:.6f} | Val Loss: {pt['val_loss']:.6f}")

    print("-" * 60)
    print(f"Training Complete! Final Train Loss: {res['final_train_loss']:.6f} | Best Val Loss: {res['final_val_loss']:.6f}")

    print("Step 4/4: Evaluating on strictly held-out test set...")
    test_eval = trainer.evaluate_test_set(te_loader)
    print(f"Held-out Test MSE:     {test_eval['test_mse']:.6f}")
    print(f"Held-out Test NMSE:    {test_eval['test_nmse']:.6f}")
    print(f"Held-out Test NMSE_dB: {test_eval['test_nmse_db']:.2f} dB")
    print(f"Checkpoint successfully saved to: {checkpoint_path}")
    print("=" * 60)
    return res, test_eval


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train NeuroMIMO Channel Estimator")
    parser.add_argument("--samples", type=int, default=500)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=0.003)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=DEFAULT_CHECKPOINT_PATH)
    args = parser.parse_args()

    run_training(
        num_samples=args.samples,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        checkpoint_path=args.output,
        random_seed=args.seed,
    )
