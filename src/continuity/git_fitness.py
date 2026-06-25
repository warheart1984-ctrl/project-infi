"""UGR-GIT-1 — Generative fitness Lambda(G) for law recovery invariance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.continuity.generative_law import (
    GIT_1_CAPABILITY_ID,
    UGR_GIT_1_CANONICAL_TEXT,
    extract_structure,
    recover_generative_law,
    structures_share_generative_law,
)

DEFAULT_THETA_GIT = 0.70


@dataclass
class GenerativeComponents:
    G_recover: float
    G_cross: float
    G_intra: float
    G_trace: float

    def to_dict(self) -> dict[str, float]:
        return {
            "G_recover": round(self.G_recover, 6),
            "G_cross": round(self.G_cross, 6),
            "G_intra": round(self.G_intra, 6),
            "G_trace": round(self.G_trace, 6),
        }


@dataclass
class GenerativeConfig:
    w_recover: float = 0.25
    w_cross: float = 0.25
    w_intra: float = 0.25
    w_trace: float = 0.25
    theta_git: float = DEFAULT_THETA_GIT


@dataclass
class GITStrip:
    object_type: str
    object_id: str
    lambda_value: float
    generative_law: str
    cross_operator_note: str
    recovery_summary: str
    components: GenerativeComponents
    ready: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_type": self.object_type,
            "object_id": self.object_id,
            "lambda": round(self.lambda_value, 6),
            "generative_law": self.generative_law,
            "cross_operator_note": self.cross_operator_note,
            "recovery_summary": self.recovery_summary,
            "components": self.components.to_dict(),
            "ready": self.ready,
        }


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def compute_lambda(
    components: GenerativeComponents,
    cfg: GenerativeConfig | None = None,
) -> float:
    config = cfg or GenerativeConfig()
    value = (
        config.w_recover * components.G_recover
        + config.w_cross * components.G_cross
        + config.w_intra * components.G_intra
        + config.w_trace * components.G_trace
    )
    return clamp01(value)


def components_from_lineages(lineages: list[Any]) -> tuple[GenerativeComponents, str, bool]:
    if not lineages:
        return (
            GenerativeComponents(G_recover=0.0, G_cross=0.0, G_intra=0.0, G_trace=0.0),
            "",
            False,
        )

    operator_ids = (
        "symbolic_mathematician",
        "numerical_analyst",
        "geometric_physicist",
        "lineage_auditor",
    )
    primary = lineages[0]
    views = [extract_structure(primary, operator_id=op) for op in operator_ids]
    share = structures_share_generative_law(views)
    generative_law = str(share.get("generative_law") or "")
    passed = bool(share.get("passed"))

    recovered = [recover_generative_law(view) for view in views]
    unique_laws = len(set(recovered))
    g_recover = 1.0 if passed else clamp01(1.0 - 0.2 * max(unique_laws - 1, 0))
    g_cross = g_recover
    g_intra = clamp01(0.65 + 0.08 * min(len(lineages), 4))
    trace_len = len(getattr(primary, "event_ids", ()) or ())
    g_trace = clamp01(0.5 + 0.06 * min(trace_len, 8))

    return (
        GenerativeComponents(
            G_recover=g_recover,
            G_cross=g_cross,
            G_intra=g_intra,
            G_trace=g_trace,
        ),
        generative_law,
        passed,
    )


def build_law_generative_strip(
    law_record: dict[str, Any],
    *,
    lineages: list[Any] | None = None,
    cfg: GenerativeConfig | None = None,
) -> GITStrip:
    config = cfg or GenerativeConfig()
    law_id = str(law_record.get("law_id") or "")
    components, generative_law, passed = components_from_lineages(list(lineages or []))
    lambda_value = compute_lambda(components, config)
    return GITStrip(
        object_type="law",
        object_id=law_id,
        lambda_value=lambda_value,
        generative_law=generative_law or "C-Chain Evolution Law",
        cross_operator_note=(
            "Cross-operator generative law recovery converged."
            if passed
            else "Cross-operator recovery diverged — steward review required."
        ),
        recovery_summary=(
            f"Recovered generative law: {generative_law or 'pending'} "
            f"from {len(lineages or [])} lineage(s)."
        ),
        components=components,
        ready=lambda_value >= config.theta_git and passed,
    )


__all__ = [
    "DEFAULT_THETA_GIT",
    "GIT_1_CAPABILITY_ID",
    "GITStrip",
    "GenerativeComponents",
    "GenerativeConfig",
    "UGR_GIT_1_CANONICAL_TEXT",
    "build_law_generative_strip",
    "clamp01",
    "compute_lambda",
    "components_from_lineages",
]
