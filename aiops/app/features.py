from __future__ import annotations

from math import isfinite
from statistics import fmean, median, pstdev
from typing import Sequence


def _slope(values: Sequence[float]) -> float:
    count = len(values)
    if count < 2:
        return 0.0

    mean_x = (count - 1) / 2
    mean_y = fmean(values)
    numerator = sum((index - mean_x) * (value - mean_y) for index, value in enumerate(values))
    denominator = sum((index - mean_x) ** 2 for index in range(count))
    return numerator / denominator if denominator else 0.0


def compute_features(
    history: Sequence[float],
    current: float,
    window: int,
) -> dict[str, float | int]:
    values = [float(value) for value in history[-max(window, 1) :] if isfinite(value)]
    if not values:
        return {
            "samples": 0,
            "mean": 0.0,
            "std": 0.0,
            "median": 0.0,
            "mad": 0.0,
            "z_score": 0.0,
            "robust_z_score": 0.0,
            "delta": 0.0,
            "min": 0.0,
            "max": 0.0,
            "slope": 0.0,
        }

    mean = fmean(values)
    std = pstdev(values)
    med = median(values)
    mad = median([abs(value - med) for value in values])
    z_score = (current - mean) / std if std > 1e-12 else 0.0
    robust_z_score = 0.6745 * (current - med) / mad if mad > 1e-12 else 0.0

    return {
        "samples": len(values),
        "mean": mean,
        "std": std,
        "median": med,
        "mad": mad,
        "z_score": z_score,
        "robust_z_score": robust_z_score,
        "delta": current - values[-1],
        "min": min(values),
        "max": max(values),
        "slope": _slope(values),
    }
