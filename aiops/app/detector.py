from __future__ import annotations

from dataclasses import dataclass

from .config import MetricConfig


@dataclass(frozen=True)
class Evaluation:
    status: str
    reasons: tuple[str, ...]


def _format_value(value: float, unit: str) -> str:
    suffix = f" {unit}" if unit else ""
    return f"{value:.4g}{suffix}"


def _crosses_threshold(value: float, threshold: float, direction: str) -> bool:
    if direction == "below":
        return value <= threshold
    if direction == "both":
        return abs(value) >= abs(threshold)
    return value >= threshold


def _crosses_z(value: float, threshold: float, direction: str) -> bool:
    if direction == "below":
        return value <= -threshold
    if direction == "both":
        return abs(value) >= threshold
    return value >= threshold


def evaluate(
    metric: MetricConfig,
    value: float,
    features: dict[str, float | int],
    min_samples: int,
) -> Evaluation:
    samples = int(features.get("samples", 0))
    if samples < min_samples:
        return Evaluation(
            status="warming_up",
            reasons=(f"need {min_samples} baseline samples, have {samples}",),
        )

    status = "ok"
    reasons: list[str] = []

    if metric.critical_threshold is not None and _crosses_threshold(
        value, metric.critical_threshold, metric.direction
    ):
        status = "critical"
        reasons.append(
            f"value {_format_value(value, metric.unit)} crossed critical threshold "
            f"{_format_value(metric.critical_threshold, metric.unit)}"
        )
    elif metric.warning_threshold is not None and _crosses_threshold(
        value, metric.warning_threshold, metric.direction
    ):
        status = "warning"
        reasons.append(
            f"value {_format_value(value, metric.unit)} crossed warning threshold "
            f"{_format_value(metric.warning_threshold, metric.unit)}"
        )

    z_score = float(features.get("z_score", 0.0))
    robust_z_score = float(features.get("robust_z_score", 0.0))
    critical_z = (
        metric.critical_z_threshold
        if metric.critical_z_threshold is not None
        else metric.z_threshold * 1.5
    )

    z_critical = _crosses_z(z_score, critical_z, metric.direction)
    robust_critical = _crosses_z(robust_z_score, critical_z, metric.direction)
    z_warning = _crosses_z(z_score, metric.z_threshold, metric.direction)
    robust_warning = _crosses_z(robust_z_score, metric.z_threshold, metric.direction)

    if z_critical or robust_critical:
        status = "critical"
        if z_critical:
            reasons.append(f"z-score {z_score:.2f} crossed critical threshold {critical_z:.2f}")
        if robust_critical:
            reasons.append(
                f"robust z-score {robust_z_score:.2f} crossed critical threshold "
                f"{critical_z:.2f}"
            )
    elif z_warning or robust_warning:
        if status != "critical":
            status = "warning"
        if z_warning:
            reasons.append(f"z-score {z_score:.2f} crossed warning threshold {metric.z_threshold:.2f}")
        if robust_warning:
            reasons.append(
                f"robust z-score {robust_z_score:.2f} crossed warning threshold "
                f"{metric.z_threshold:.2f}"
            )

    return Evaluation(status=status, reasons=tuple(reasons))
