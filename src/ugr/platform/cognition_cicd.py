"""Cognition CI/CD promotion pipeline for shadow runtime evaluation."""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
import json
import os
from pathlib import Path
from typing import Any

from src.ugr.platform.shadow_runtime import ShadowRuntimeEvaluator, compare_deliberation_results


def _default_promotion_path() -> Path:
    env_path = os.getenv("UGR_COGNITION_PROMOTION_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "cognition-promotion.json"


class CognitionCICDPipeline:
    """Evaluate prod vs shadow deliberation and emit promotion decisions."""

    def __init__(
        self,
        *,
        promotion_path: str | Path | None = None,
        evaluator: ShadowRuntimeEvaluator | None = None,
    ):
        self.path = Path(promotion_path) if promotion_path else _default_promotion_path()
        self.evaluator = evaluator or ShadowRuntimeEvaluator()
        self._rules = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    @property
    def rules(self) -> dict[str, Any]:
        return dict(self._rules.get("promotion") or {})

    def decide(self, comparison: dict[str, Any]) -> dict[str, Any]:
        min_match = float(self.rules.get("min_belief_match_rate") or 0.95)
        require_status_match = bool(self.rules.get("require_status_match", True))
        allowed_statuses = tuple(self.rules.get("allowed_prod_statuses") or ("ok",))
        allow_contested = bool(self.rules.get("allow_contested_beliefs", False))

        reasons: list[str] = []
        prod_status = str(comparison.get("prod_status") or "")
        if prod_status not in allowed_statuses:
            reasons.append(f"prod_status_not_allowed:{prod_status}")
        if require_status_match and not comparison.get("status_match"):
            reasons.append("status_divergence")
        match_rate = float(comparison.get("belief_match_rate") or 0.0)
        if match_rate < min_match:
            reasons.append(f"belief_match_below_threshold:{match_rate}<{min_match}")
        if comparison.get("prod_only_signatures") or comparison.get("shadow_only_signatures"):
            if match_rate < 1.0:
                reasons.append("belief_signature_divergence")
        if not allow_contested and prod_status == "ok":
            # contested beliefs still ok at runtime level; gate on signature match only
            pass

        if not reasons:
            decision = "promote"
        elif any(
            token in reasons
            for token in (
                "status_divergence",
                "belief_match_below_threshold",
                "belief_signature_divergence",
                "prod_status_not_allowed",
            )
        ):
            decision = "human_review" if match_rate >= min_match * 0.8 else "reject"
        else:
            decision = "human_review"

        return _wrap_ul_payload({
            "decision": decision,
            "reasons": reasons,
            "rules": dict(self.rules),
            "belief_match_rate": match_rate,
        })

    def evaluate(self, request: dict[str, Any]) -> dict[str, Any]:
        shadow_eval = self.evaluator.evaluate(request)
        comparison = dict(shadow_eval.get("comparison") or {})
        promotion = self.decide(comparison)
        return _wrap_ul_payload({
            "status": "ok",
            "promotion": promotion,
            "comparison": comparison,
            "prod": shadow_eval.get("prod"),
            "shadow": shadow_eval.get("shadow"),
        })

    def evaluate_comparison(self, comparison: dict[str, Any]) -> dict[str, Any]:
        return _wrap_ul_payload({
            "status": "ok",
            "promotion": self.decide(comparison),
            "comparison": comparison,
        })
