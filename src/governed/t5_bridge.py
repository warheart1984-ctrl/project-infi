"""T5 reference binding for governed missions."""

from __future__ import annotations

from typing import Any

from nova.bridges import reference_bridge


def attach_t5_references(law_eval: dict[str, Any]) -> dict[str, Any]:
    """Attach live T5 reference binding to a LAW_EVAL artifact."""
    binding = reference_bridge.current_reference_binding()
    evaluation = dict(law_eval.get("evaluation") or law_eval)
    context_t5 = str(
        (evaluation.get("context") or {}).get("t5_ref_signal_hash")
        or evaluation.get("t5_ref_signal_hash")
        or ""
    )
    return {
        "ref_hash": binding.ref_hash,
        "bound": binding.bound,
        "metrics": dict(binding.metrics),
        "law_eval_t5": context_t5 or binding.ref_hash,
    }
