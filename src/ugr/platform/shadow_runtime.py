"""Shadow runtime comparison for cognition CI/CD."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.ugr.unified_runtime import UnifiedGovernedRuntime


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _belief_signature(belief: dict[str, Any]) -> str:
    payload = {
        "subject": belief.get("subject"),
        "predicate": belief.get("predicate"),
        "object": belief.get("object"),
        "status": belief.get("status"),
    }
    return sha256(_stable_json(payload).encode("utf-8")).hexdigest()[:16]


def extract_beliefs(result: dict[str, Any]) -> list[dict[str, Any]]:
    convergence = dict(result.get("convergence") or {})
    return list(convergence.get("final_beliefs") or [])


def compare_deliberation_results(
    prod_result: dict[str, Any],
    shadow_result: dict[str, Any],
) -> dict[str, Any]:
    prod_beliefs = extract_beliefs(prod_result)
    shadow_beliefs = extract_beliefs(shadow_result)
    prod_sigs = {_belief_signature(item): item for item in prod_beliefs}
    shadow_sigs = {_belief_signature(item): item for item in shadow_beliefs}
    shared = sorted(set(prod_sigs.keys()) & set(shadow_sigs.keys()))
    prod_only = sorted(set(prod_sigs.keys()) - set(shadow_sigs.keys()))
    shadow_only = sorted(set(shadow_sigs.keys()) - set(prod_sigs.keys()))
    union_size = len(set(prod_sigs.keys()) | set(shadow_sigs.keys()))
    match_rate = len(shared) / union_size if union_size else 1.0
    return {
        "prod_status": prod_result.get("status"),
        "shadow_status": shadow_result.get("status"),
        "prod_belief_count": len(prod_beliefs),
        "shadow_belief_count": len(shadow_beliefs),
        "shared_signatures": shared,
        "prod_only_signatures": prod_only,
        "shadow_only_signatures": shadow_only,
        "belief_match_rate": round(match_rate, 4),
        "status_match": prod_result.get("status") == shadow_result.get("status"),
    }


class ShadowRuntimeEvaluator:
    """Run prod vs shadow deliberation and compare belief outputs."""

    def __init__(
        self,
        *,
        prod_runtime: UnifiedGovernedRuntime | None = None,
        shadow_runtime: UnifiedGovernedRuntime | None = None,
        runtime_root: str | Path | None = None,
        shadow_suffix: str = "shadow",
    ):
        from src.ugr.unified_runtime import UnifiedGovernedRuntime as Runtime

        root = Path(runtime_root or os.getenv("AAIS_RUNTIME_DIR") or Path(__file__).resolve().parents[3] / ".runtime")
        self.prod = prod_runtime or Runtime(runtime_dir=root)
        shadow_root = root.parent / f"{root.name}-{shadow_suffix}" if root.name != shadow_suffix else root / shadow_suffix
        self.shadow = shadow_runtime or Runtime(runtime_dir=shadow_root)

    def evaluate(self, request: dict[str, Any]) -> dict[str, Any]:
        payload = dict(request or {})
        prod_result = self.prod.handle_request(payload)
        shadow_result = self.shadow.handle_request(payload)
        comparison = compare_deliberation_results(prod_result, shadow_result)
        return {
            "comparison": comparison,
            "prod": {
                "trace_id": prod_result.get("trace_id"),
                "status": prod_result.get("status"),
                "summary": prod_result.get("summary"),
            },
            "shadow": {
                "trace_id": shadow_result.get("trace_id"),
                "status": shadow_result.get("status"),
                "summary": shadow_result.get("summary"),
            },
        }
