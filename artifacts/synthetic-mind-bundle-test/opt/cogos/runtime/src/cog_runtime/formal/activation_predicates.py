"""Decidable activation predicates φ : Σ → 𝔹 for conditional lobe composition."""

from __future__ import annotations

from typing import Any, Callable

from src.speaking_runtime import infer_frame_kind

PredicateFn = Callable[[dict[str, Any]], bool]

DECISION_FRAME_KIND = "decision"
EXPLICIT_DELIBERATION_MODES = frozenset({"think", "research"})


def frame_kind(sigma: dict[str, Any]) -> str:
    """σ.frame_kind with deterministic fallback from user_message."""
    explicit = str(sigma.get("frame_kind") or "").strip()
    if explicit:
        return explicit
    return infer_frame_kind(str(sigma.get("user_message") or ""))


def explicit_deliberation(sigma: dict[str, Any]) -> bool:
    """True when response_mode requests deep reasoning on a decision frame."""
    mode = str(sigma.get("response_mode") or "").strip().lower()
    return mode in EXPLICIT_DELIBERATION_MODES and frame_kind(sigma) == DECISION_FRAME_KIND


def phi_delib(sigma: dict[str, Any]) -> bool:
    """φ_delib(σ) ≡ (frame_kind(σ) = decision) ∨ explicit_deliberation(σ)."""
    return frame_kind(sigma) == DECISION_FRAME_KIND or explicit_deliberation(sigma)


def phi_memory(sigma: dict[str, Any]) -> bool:
    """Memory activates on companion turns or when memory_cues are present."""
    if bool(sigma.get("companion_turn")):
        return True
    cues = sigma.get("memory_cues")
    return isinstance(cues, list) and bool(cues)


def phi_speaking(sigma: dict[str, Any]) -> bool:
    """Speaking activates when explicitly enabled or required."""
    if bool(sigma.get("speaking_runtime_enabled")):
        return True
    if bool(sigma.get("require_speaking")):
        return True
    return bool(sigma.get("companion_turn"))


def phi_reflection(sigma: dict[str, Any]) -> bool:
    """Reflection skipped on cortex_fast_path."""
    return not bool(sigma.get("cortex_fast_path"))


ACTIVATION_PREDICATES: dict[str, PredicateFn] = {
    "cognitive.deliberation": phi_delib,
    "cognitive.memory": phi_memory,
    "speaking.runtime": phi_speaking,
    "cognitive.reflection": phi_reflection,
}


def evaluate_activation(lobe_id: str, sigma: dict[str, Any]) -> dict[str, Any]:
    """Evaluate φ for a lobe; default True when no predicate is registered."""
    fn = ACTIVATION_PREDICATES.get(lobe_id)
    if fn is None:
        return {"lobe_id": lobe_id, "active": True, "predicate": None, "decidable": True}
    active = bool(fn(sigma))
    return {
        "lobe_id": lobe_id,
        "active": active,
        "predicate": fn.__name__,
        "frame_kind": frame_kind(sigma),
        "decidable": True,
    }


def activation_predicate_spec() -> dict[str, Any]:
    return {
        "schema_id": "nova.activation_predicates.v1",
        "predicates": {
            "phi_delib": {
                "form": "(frame_kind(σ) = decision) ∨ explicit_deliberation(σ)",
                "implementation": "phi_delib",
                "inputs": ("frame_kind", "user_message", "response_mode"),
                "decidable": True,
            },
            "explicit_deliberation": {
                "form": "response_mode ∈ {think, research} ∧ frame_kind(σ) = decision",
                "implementation": "explicit_deliberation",
                "decidable": True,
            },
            "frame_kind": {
                "form": "σ.frame_kind if set else infer_frame_kind(σ.user_message)",
                "domain": (
                    "question|design|implementation|decision|venting|review|instruction|general"
                ),
                "decidable": True,
            },
        },
        "lobe_map": {lobe: fn.__name__ for lobe, fn in ACTIVATION_PREDICATES.items()},
    }
