"""Judgment-quality metrics for assimilation (Q_pre, Q_post, ΔA)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class JudgmentMetrics:
    prediction_error: float
    calibration_aligned: bool

    def quality(self) -> float:
        error_penalty = max(0.0, min(1.0, self.prediction_error))
        alignment_bonus = 0.25 if self.calibration_aligned else 0.0
        return max(0.0, min(1.0, 1.0 - error_penalty + alignment_bonus))


def assimilation_delta(pre: JudgmentMetrics, post: JudgmentMetrics) -> float:
    return post.quality() - pre.quality()
