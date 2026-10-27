"""Benchmark LS, LMMSE, DNN and perfect CSI on DeepMIMO ray-traced channels.

Every estimator sees identical channels and noise at each SNR point. LMMSE uses
the delay profile measured from the loaded channels, and BER points carry 95%
Wilson confidence intervals.

Usage (from backend/):
    python -m neuromimo.evaluation.deepmimo_cli path/to/channels.npy
    python -m neuromimo.evaluation.deepmimo_cli channels.npz --key channel --trials 20
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from neuromimo.config import SimulationConfig, EstimationAlgorithm  # noqa: E402
from neuromimo.estimation.dnn import DNNEstimator, DEFAULT_CHECKPOINT_PATH  # noqa: E402
from neuromimo.evaluation.metrics import compute_confidence_interval_ber  # noqa: E402
from neuromimo.wireless.deepmimo import DeepMIMOChannelSet  # noqa: E402
from neuromimo.wireless.simulation import MIMOSimulationPipeline  # noqa: E402

DEFAULT_SNR_POINTS = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
DEFAULT_OUTPUT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "results", "deepmimo_snr_sweep.json")
)


def run_deepmimo_sweep(
    channel_set: DeepMIMOChannelSet,
    snr_points: Sequence[float] = DEFAULT_SNR_POINTS,
    num_trials: int = 15,
    algorithms: Sequence[str] = ("LS", "MMSE", "DNN", "PERFECT"),
    checkpoint_path: Optional[str] = None,
    random_seed: int = 42,
) -> Dict[str, List[Dict[str, Any]]]:
    """Runs an SNR sweep for each estimator on the given channels.

    Returns:
        Mapping of algorithm name to one record per SNR point with NMSE, BER,
        bit errors and the 95% confidence interval.
    """
    checkpoint = checkpoint_path or DEFAULT_CHECKPOINT_PATH
    records: Dict[str, List[Dict[str, Any]]] = {}

    for algo in algorithms:
        if algo == "DNN" and not os.path.exists(checkpoint):
            print(f"Skipping DNN: checkpoint not found at {checkpoint}")
            continue

        config = SimulationConfig(
            num_rx=channel_set.num_rx,
            num_tx=channel_set.num_tx,
            fft_size=channel_set.fft_size,
            algorithm=EstimationAlgorithm(algo),
            random_seed=random_seed,
        )
        pipeline = MIMOSimulationPipeline(config, channel_set=channel_set)
        if algo == "DNN":
            pipeline.estimator = DNNEstimator(
                model_path=checkpoint,
                fft_size=config.fft_size,
                num_rx=config.num_rx,
                num_tx=config.num_tx,
            )

        records[algo] = []
        for snr in snr_points:
            config.snr_db = float(snr)
            # Same seed per SNR point, so every estimator sees the same channels and noise
            pipeline.channel.rng = np.random.RandomState(random_seed)
            nmse_values, bit_errors, total_bits = [], 0, 0
            for _ in range(num_trials):
                result = pipeline.run_single_shot()
                nmse_values.append(result["nmse"])
                bit_errors += result["bit_errors"]
                total_bits += result["total_bits"]

            mean_nmse = float(np.mean(nmse_values))
            ci = compute_confidence_interval_ber(bit_errors, total_bits)
            records[algo].append(
                {
                    "snr_db": float(snr),
                    "nmse": mean_nmse,
                    "nmse_db": float(10.0 * np.log10(max(mean_nmse, 1e-12))),
                    "ber": ci["ber"],
                    "ci_lower": ci["ci_lower"],
                    "ci_upper": ci["ci_upper"],
                    "bit_errors": int(bit_errors),
                    "total_bits": int(total_bits),
                }
            )
    return records


def _print_table(records: Dict[str, List[Dict[str, Any]]]) -> None:
    algos = list(records)
    header = "SNR (dB) | " + " | ".join(f"{a:>8} NMSE  {a:>8} BER " for a in algos)
    print(header)
    print("-" * len(header))
    for i, rec in enumerate(records[algos[0]]):
        cells = []
        for a in algos:
            r = records[a][i]
            nmse = "  exact  " if r["nmse_db"] <= -100 else f"{r['nmse_db']:8.2f} dB"
            cells.append(f"{nmse}  {r['ber']:.2e}  ")
        print(f"{rec['snr_db']:8.0f} | " + " | ".join(cells))


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark channel estimators on DeepMIMO channels.")
    parser.add_argument("channels", help="DeepMIMO channel file (.npy, .npz or .mat).")
    parser.add_argument("--key", default=None, help="Array name inside a .npz or .mat file.")
    parser.add_argument("--trials", type=int, default=15, help="Monte Carlo trials per SNR point.")
    parser.add_argument("--snr", type=float, nargs="+", default=DEFAULT_SNR_POINTS, help="SNR points in dB.")
    parser.add_argument("--checkpoint", default=None, help="DNN checkpoint (default: the trained model).")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Where to save the JSON results.")
    args = parser.parse_args()

    channel_set = DeepMIMOChannelSet.from_file(args.channels, key=args.key)
    print(f"Loaded {channel_set.num_channels} DeepMIMO channels "
          f"({channel_set.num_dropped_users} users without paths dropped).")

    records = run_deepmimo_sweep(
        channel_set,
        snr_points=args.snr,
        num_trials=args.trials,
        checkpoint_path=args.checkpoint,
        random_seed=args.seed,
    )
    _print_table(records)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(
            {
                "experiment_name": "deepmimo_snr_sweep",
                "source_file": os.path.basename(args.channels),
                "num_channels": channel_set.num_channels,
                "num_trials_per_snr": args.trials,
                "snr_points": list(args.snr),
                "records": records,
            },
            f,
            indent=2,
        )
    print(f"Saved results to {args.output}")


if __name__ == "__main__":
    main()
