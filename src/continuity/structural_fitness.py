"""UGR-SIT-1 — Structure Invariance Theory and structural fitness Sigma(S)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

UGR_SIT_1_CANONICAL_TEXT = """UGR-SIT-1 — Structure Invariance Theory
Class: Constitutional Invariant
Purpose: Preserve operator-independent structural equivalence across representations.

Sigma(S) = w_equiv*S_equiv + w_indep*S_indep + w_recover*S_recover + w_trace*S_trace
Structures below Theta_SIT cannot bind downstream generative or selection laws.
"""

SIT_1_CAPABILITY_ID = "UGR-SIT-1"
DEFAULT_THETA_SIT = 0.72

LAW_STRUCTURE_SUMMARY: dict[str, str] = {
    "SIT-1": "Structural equivalence must survive operator changes and replay.",
    "GIT-1": "Generative law families must share recoverable structure across operators.",
    "PIT-1": "Selection kernel structure must remain traceable to evidence and lineages.",
}

LAW_STRUCTURE_RECOVERY: dict[str, str] = {
    "SIT-1": "Recover structure via lineage continuity trace and invariant preservation.",
    "GIT-1": "Recover generative law G from constraint extraction chi_O(S).",
    "PIT-1": "Recover fitness surface F(G) from law ledger evaluations and evidence bindings.",
}


@dataclass
class StructuralComponents:
    S_equiv: float
    S_indep: float
    S_recover: float
    S_trace: float

    def to_dict(self) -> dict[str, float]:
        return {
            "S_equiv": round(self.S_equiv, 6),
            "S_indep": round(self.S_indep, 6),
            "S_recover": round(self.S_recover, 6),
            "S_trace": round(self.S_trace, 6),
        }


@dataclass
class StructuralConfig:
    w_equiv: float = 0.25
    w_indep: float = 0.25
    w_recover: float = 0.25
    w_trace: float = 0.25
    theta_sit: float = DEFAULT_THETA_SIT


@dataclass
class SITStrip:
    object_type: str
    object_id: str
    sigma: float
    structure_summary: str
    recovery_hint: str
    operator_independence: str
    components: StructuralComponents
    ready: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_type": self.object_type,
            "object_id": self.object_id,
            "sigma": round(self.sigma, 6),
            "structure_summary": self.structure_summary,
            "recovery_hint": self.recovery_hint,
            "operator_independence": self.operator_independence,
            "components": self.components.to_dict(),
            "ready": self.ready,
        }


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def compute_sigma(
    components: StructuralComponents,
    cfg: StructuralConfig | None = None,
) -> float:
    config = cfg or StructuralConfig()
    sigma = (
        config.w_equiv * components.S_equiv
        + config.w_indep * components.S_indep
        + config.w_recover * components.S_recover
        + config.w_trace * components.S_trace
    )
    return clamp01(sigma)


def components_from_law_context(
    law_record: dict[str, Any],
    *,
    lineage_count: int = 0,
    graph: dict[str, Any] | None = None,
    evidence_present: bool = False,
) -> StructuralComponents:
    status = str(law_record.get("status") or "")
    fitness = float(
        (law_record.get("fitness") or {}).get("current")
        or law_record.get("current_fitness")
        or 0.0
    )

    s_equiv = clamp01(0.55 + 0.08 * min(lineage_count, 5))
    s_indep = 1.0 if status == "sovereign" else clamp01(0.72 + 0.04 * min(lineage_count, 4))
    node_count = len((graph or {}).get("nodes") or [])
    edge_count = len((graph or {}).get("edges") or [])
    if evidence_present:
        s_recover = clamp01(0.42 + 0.1 * min(node_count, 5) + 0.05 * min(fitness, 1.0))
        s_trace = clamp01(0.4 + 0.08 * min(edge_count, 6) + 0.06 * min(lineage_count, 3))
    else:
        s_recover = clamp01(0.5 + 0.06 * min(lineage_count, 4))
        s_trace = clamp01(0.45 + 0.05 * min(lineage_count, 4))

    return StructuralComponents(
        S_equiv=s_equiv,
        S_indep=s_indep,
        S_recover=s_recover,
        S_trace=s_trace,
    )


def build_law_structural_strip(
    law_record: dict[str, Any],
    *,
    lineage_count: int = 0,
    graph: dict[str, Any] | None = None,
    evidence_present: bool = False,
    cfg: StructuralConfig | None = None,
) -> SITStrip:
    config = cfg or StructuralConfig()
    law_id = str(law_record.get("law_id") or "")
    components = components_from_law_context(
        law_record,
        lineage_count=lineage_count,
        graph=graph,
        evidence_present=evidence_present,
    )
    sigma = compute_sigma(components, config)
    return SITStrip(
        object_type="law",
        object_id=law_id,
        sigma=sigma,
        structure_summary=LAW_STRUCTURE_SUMMARY.get(
            law_id,
            f"{law_id}: {lineage_count} lineages, "
            f"{len((graph or {}).get('nodes') or [])} graph nodes.",
        ),
        recovery_hint=LAW_STRUCTURE_RECOVERY.get(
            law_id,
            "Replay lineage trace and verify structural recovery under operator change.",
        ),
        operator_independence=(
            "Sovereign structure — operator-independent equivalence verified."
            if str(law_record.get("status")) == "sovereign"
            else "Experimental structure — operator convergence under observation."
        ),
        components=components,
        ready=sigma >= config.theta_sit,
    )
