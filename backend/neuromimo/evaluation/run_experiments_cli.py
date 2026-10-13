"""CLI interface for running reproducible NeuroMIMO evaluation experiments.

Executes all 6 required experimental benchmarks:
1. NMSE versus SNR.
2. BER versus SNR after channel estimation and equalization.
3. Performance under AWGN and multipath Rayleigh fading.
4. Generalization to channel realizations excluded from training and parameter mismatch.
5. High-resolution inference-time comparison.
6. Pilot-density comparison.

Generates structured JSON/CSV files and publication-grade 300 DPI research figures.
"""

import argparse
import sys
import os

# Add backend directory to path if running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from neuromimo.evaluation.experiments import ExperimentRunner


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run reproducible NeuroMIMO channel estimation evaluation experiments."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory where JSON, CSV, and PNG plot artifacts will be written.",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=20,
        help="Number of Monte Carlo trials per SNR point (default: 20).",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Path to trained PyTorch DNN checkpoint (.pt file).",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run in quick smoke-test mode with fewer trials and SNR points for rapid verification.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic reproducibility (default: 42).",
    )

    args = parser.parse_args()

    print("================================================================================")
    print("                    NeuroMIMO Experimental Evaluation Suite                     ")
    print("================================================================================")
    print(f"Output Directory : {args.output_dir}")
    print(f"Monte Carlo Runs : {5 if args.quick else args.trials} trials per test point")
    print(f"Deterministic RNG: Seed {args.seed}")
    print(f"Execution Mode   : {'QUICK SMOKE TEST' if args.quick else 'FULL RESEARCH SUITE'}")
    print("--------------------------------------------------------------------------------")

    runner = ExperimentRunner(
        checkpoint_path=args.checkpoint,
        output_dir=args.output_dir,
        random_seed=args.seed,
    )

    results = runner.run_all_experiments(
        num_trials=args.trials,
        quick_mode=args.quick,
    )

    print("--------------------------------------------------------------------------------")
    print("[Success] All evaluation benchmarks executed successfully!")
    print(f"Generated artifacts saved to: {os.path.abspath(args.output_dir)}")
    for category, files in results.get("artifacts", {}).items():
        print(f"  [{category.upper()}]")
        for k, v in files.items():
            print(f"    - {k}: {v}")
    print("================================================================================")


if __name__ == "__main__":
    main()
