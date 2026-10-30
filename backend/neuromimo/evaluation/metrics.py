"""Performance evaluation metrics for MIMO-OFDM communication systems."""

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class SimulationMetrics:
    """Aggregated simulation metrics across runs."""
    mse: float
    nmse: float
    nmse_db: float
    ber: float
    ser: float
    total_bits: int
    bit_errors: int
    total_symbols: int
    symbol_errors: int
    snr_db: float
    execution_time_ms: float
    inference_time_ms: Optional[float] = None


def calculate_mse(h_true: np.ndarray, h_est: np.ndarray) -> float:
    """Calculates Mean Squared Error (MSE) between true and estimated CFR."""
    error = h_true - h_est
    return float(np.mean(np.abs(error) ** 2))


def calculate_nmse(h_true: np.ndarray, h_est: np.ndarray) -> float:
    """Calculates Normalized Mean Squared Error (NMSE).

    Formula:
        NMSE = ||H_true - H_est||_F^2 / ||H_true||_F^2
    """
    error = h_true - h_est
    err_energy = np.sum(np.abs(error) ** 2)
    true_energy = np.sum(np.abs(h_true) ** 2)
    if true_energy == 0:
        return 0.0
    return float(err_energy / true_energy)


def calculate_nmse_db(h_true: np.ndarray, h_est: np.ndarray, min_val: float = 1e-12) -> float:
    """Calculates Normalized Mean Squared Error (NMSE) in decibels (dB)."""
    nmse = calculate_nmse(h_true, h_est)
    return float(10.0 * np.log10(max(nmse, min_val)))


def calculate_ber(bits_true: np.ndarray, bits_est: np.ndarray) -> float:
    """Calculates Bit Error Rate (BER)."""
    b_t = np.asarray(bits_true).flatten()
    b_e = np.asarray(bits_est).flatten()
    if len(b_t) == 0:
        return 0.0
    errors = np.count_nonzero(b_t != b_e)
    return float(errors / len(b_t))


def compute_confidence_interval_ber(
    bit_errors: int,
    total_bits: int,
    confidence_level: float = 0.95,
) -> dict:
    """Computes statistical confidence intervals for Monte Carlo BER estimates.

    Utilizes the Wilson score interval for binomial proportions and the
    Poisson 'Rule of Three' when zero errors are observed.
    Flag is_conclusive is True when at least 10 bit error events have occurred
    or when zero errors are observed over at least 10,000 transmitted bits.
    """
    if total_bits <= 0:
        return {
            "ber": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "is_conclusive": False,
            "explanation": "No bits transmitted.",
        }

    ber = float(bit_errors / total_bits)

    if bit_errors == 0:
        # Rule of Three for zero observed events at ~95% confidence
        upper_bound = float(3.0 / total_bits)
        is_conclusive = bool(total_bits >= 10000)
        expl = (
            "Zero errors observed over sufficient sample (>=10k bits)."
            if is_conclusive
            else f"Zero errors observed, but sample size ({total_bits} bits) is small; 95% CI upper bound is {upper_bound:.2e}."
        )
        return {
            "ber": 0.0,
            "ci_lower": 0.0,
            "ci_upper": upper_bound,
            "is_conclusive": is_conclusive,
            "explanation": expl,
        }

    # Standard Wilson score interval (z = 1.96 for 95% CI)
    z = 1.95996 if abs(confidence_level - 0.95) < 0.01 else 2.57583
    denominator = 1.0 + (z**2) / total_bits
    center = (ber + (z**2) / (2.0 * total_bits)) / denominator
    half_width = (
        z * np.sqrt((ber * (1.0 - ber) / total_bits) + (z**2) / (4.0 * total_bits**2))
    ) / denominator

    ci_lower = max(0.0, float(center - half_width))
    ci_upper = min(1.0, float(center + half_width))
    is_conclusive = bool(bit_errors >= 10)

    expl = (
        f"Statistically conclusive (>=10 errors observed: {bit_errors})."
        if is_conclusive
        else f"Inconclusive (<10 errors observed: {bit_errors} errors in {total_bits} bits). Variance is high."
    )

    return {
        "ber": ber,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "is_conclusive": is_conclusive,
        "explanation": expl,
    }


def count_symbol_errors(bits_true: np.ndarray, bits_est: np.ndarray, bits_per_symbol: int) -> int:
    """Counts detected symbols with at least one wrong bit (hard-decision symbol errors).

    Args:
        bits_true: Transmitted bits, shape (num_tx, num_bits) or flat.
        bits_est: Recovered bits with the same shape.
        bits_per_symbol: Bits carried by one modulation symbol (2 for QPSK, 4 for 16-QAM).
    """
    wrong = np.asarray(bits_true).reshape(-1, bits_per_symbol) != np.asarray(bits_est).reshape(-1, bits_per_symbol)
    return int(np.count_nonzero(np.any(wrong, axis=1)))


def calculate_ser(symbols_true: np.ndarray, symbols_est: np.ndarray, threshold: float = 1e-3) -> float:
    """Calculates Symbol Error Rate (SER)."""
    s_t = np.asarray(symbols_true).flatten()
    s_e = np.asarray(symbols_est).flatten()
    if len(s_t) == 0:
        return 0.0
    errors = np.count_nonzero(np.abs(s_t - s_e) > threshold)
    return float(errors / len(s_t))

