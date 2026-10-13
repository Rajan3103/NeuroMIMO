"""Evaluation metrics and benchmark runner for NeuroMIMO."""

from .metrics import (
    calculate_mse,
    calculate_nmse,
    calculate_nmse_db,
    calculate_ber,
    calculate_ser,
    compute_confidence_interval_ber,
    SimulationMetrics,
)
from .benchmarks import benchmark_channel_estimators
from .experiments import ExperimentRunner

__all__ = [
    "calculate_mse",
    "calculate_nmse",
    "calculate_nmse_db",
    "calculate_ber",
    "calculate_ser",
    "compute_confidence_interval_ber",
    "SimulationMetrics",
    "benchmark_channel_estimators",
    "ExperimentRunner",
]

