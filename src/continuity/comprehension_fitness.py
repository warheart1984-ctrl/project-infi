"""UGR-CIT-1 / CIT-2 — Comprehension Invariance Theory and drift bounds."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

UGR_CIT_1_CANONICAL_TEXT = """UGR-CIT-1 — Comprehension Invariance Theory
Class: Constitutional Invariant
Status: Proposed → Experimental → Admitted (pending PIT + EIT)

CIT-1.1 — Purpose
To ensure that every constitutional object remains understandable by human operators
through a bounded explanation procedure, preventing governance from outgrowing human comprehension.

CIT-1.3 — Statement
For every constitutional object X, there exists a bounded explanation procedure B(X) such
that any admissible operator O can reconstruct purpose, dependencies, evidence, consequences,
and constitutional role without traversing the entire substrate.

CIT-1.5 — Violations
Any object lacking a valid bounded explanation is constitutionally incomplete and cannot be sovereign.
"""

UGR_CIT_2_CANONICAL_TEXT = """UGR-CIT-2 — Comprehension Drift Bounds
Class: Constitutional Invariant (CIT extension)

CIT-2.3 — Bounds
Floor: Chi_t(X) >= Theta_CIT,min
Drift bound: |Delta_t(X)| <= Delta_max
Multi-epoch window W: |Chi_{t+W}(X) - Chi_t(X)| <= W * Delta_max

CIT-2.4 — Violations
Chi_t(X) < Theta_CIT,min: comprehension-unsafe.
|Delta_t(X)| > Delta_max: comprehension shock; epoch commit quarantined or steward override.
"""

UGR_META_CIT_1_CANONICAL_TEXT = """UGR-META-CIT-1 — Meta-Comprehension Governance
Theta_CIT,min, Delta_max, and weights v_i in Chi(X) are governed objects, not magic constants.
Changes must pass Law Ledger (GIT + PIT), be backed by evidence (EIT), and preserve bootstrapped CIT.
"""

CIT_1_CAPABILITY_ID = "UGR-CIT-1"
CIT_2_CAPABILITY_ID = "UGR-CIT-2"

DEFAULT_THETA_CIT_MIN = 0.75
DEFAULT_DELTA_MAX = 0.10
DEFAULT_DRIFT_WINDOW = 3

LAW_PURPOSE_TEXT: dict[str, str] = {
    "SIT-1": "Structure Invariance Theory — operator-independent structural equivalence.",
    "GIT-1": "Generative Invariance Theory — recoverable generative law structure.",
    "PIT-1": "Proof Invariance Theory — sovereign law selection via fitness F(G).",
}

LAW_BREAKS_TEXT: dict[str, str] = {
    "SIT-1": "Structural equivalence collapses; operator divergence becomes unbounded.",
    "GIT-1": "Law recovery fails; generative structure cannot be replayed.",
    "PIT-1": "Sovereign selection kernel loses fitness basis; law admission becomes arbitrary.",
}

LAW_ROLES: dict[str, list[str]] = {
    "SIT-1": ["SIT", "CIT"],
    "GIT-1": ["GIT", "SIT", "CIT"],
    "PIT-1": ["PIT", "EIT", "CIT"],
}


@dataclass
class ComprehensionComponents:
    C_loc: float
    C_clr: float
    C_cons: float
    C_link: float

    def to_dict(self) -> dict[str, float]:
        return {
            "C_loc": round(self.C_loc, 6),
            "C_clr": round(self.C_clr, 6),
            "C_cons": round(self.C_cons, 6),
            "C_link": round(self.C_link, 6),
        }


@dataclass
class ComprehensionConfig:
    v_loc: float = 0.25
    v_clr: float = 0.25
    v_cons: float = 0.25
    v_link: float = 0.25
    theta_min: float = DEFAULT_THETA_CIT_MIN
    delta_max: float = DEFAULT_DELTA_MAX
    drift_window: int = DEFAULT_DRIFT_WINDOW


@dataclass
class CITStrip:
    """UI contract — bounded explanation panel for any constitutional object."""

    object_type: str
    object_id: str
    explain: str
    summarize: str
    why_exists: str
    what_breaks_if_removed: str
    constitutional_role: list[str]
    chi: float
    components: ComprehensionComponents
    trace_links: list[dict[str, str]] = field(default_factory=list)
    replay_hint: str = ""
    ready: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_type": self.object_type,
            "object_id": self.object_id,
            "explain": self.explain,
            "summarize": self.summarize,
            "why_exists": self.why_exists,
            "what_breaks_if_removed": self.what_breaks_if_removed,
            "constitutional_role": list(self.constitutional_role),
            "chi": round(self.chi, 6),
            "components": self.components.to_dict(),
            "trace_links": list(self.trace_links),
            "replay_hint": self.replay_hint,
            "ready": self.ready,
        }


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def compute_chi(components: ComprehensionComponents, cfg: ComprehensionConfig | None = None) -> float:
    config = cfg or ComprehensionConfig()
    chi = (
        config.v_loc * components.C_loc
        + config.v_clr * components.C_clr
        + config.v_cons * components.C_cons
        + config.v_link * components.C_link
    )
    return clamp01(chi)


def graph_metrics_from_counts(
    *,
    avg_hops: float,
    ambiguity_score: float,
    consequence_coverage: float,
    link_density: float,
) -> dict[str, float]:
    return {
        "avg_hops": avg_hops,
        "ambiguity_score": ambiguity_score,
        "consequence_coverage": consequence_coverage,
        "link_density": link_density,
    }


def components_from_graph_metrics(graph_metrics: dict[str, float]) -> ComprehensionComponents:
    avg_hops = float(graph_metrics.get("avg_hops") or 1.0)
    ambiguity = float(graph_metrics.get("ambiguity_score") or 0.0)
    consequence = float(graph_metrics.get("consequence_coverage") or 0.0)
    link_density = float(graph_metrics.get("link_density") or 0.0)

    return ComprehensionComponents(
        C_loc=clamp01(1.0 / (1.0 + avg_hops)),
        C_clr=clamp01(1.0 - ambiguity),
        C_cons=clamp01(consequence),
        C_link=clamp01(link_density),
    )


def compute_law_comprehension(
    law_record: dict[str, Any],
    graph_metrics: dict[str, float],
    cfg: ComprehensionConfig | None = None,
) -> tuple[float, ComprehensionComponents]:
    components = components_from_graph_metrics(graph_metrics)
    return compute_chi(components, cfg), components


def compute_evidence_comprehension(
    evidence: dict[str, Any],
    graph_metrics: dict[str, float],
    cfg: ComprehensionConfig | None = None,
) -> tuple[float, ComprehensionComponents]:
    trace_count = len(evidence.get("trace_links") or [])
    dependency_count = len(evidence.get("dependencies") or [])
    merged = {
        **graph_metrics,
        "avg_hops": graph_metrics.get("avg_hops", 1.0 + trace_count * 0.05),
        "link_density": graph_metrics.get(
            "link_density",
            clamp01(0.5 + 0.1 * min(trace_count + dependency_count, 5)),
        ),
    }
    components = components_from_graph_metrics(merged)
    return compute_chi(components, cfg), components


def law_graph_metrics(law_record: dict[str, Any], *, evidence_linked: bool) -> dict[str, float]:
    law_id = str(law_record.get("law_id") or "")
    dependencies = law_record.get("dependencies") or []
    domains = law_record.get("domains") or []
    fitness = law_record.get("fitness") or {}
    history_len = len(fitness.get("history") or [])

    avg_hops = 1.0 + len(dependencies) * 0.15 + (0.35 if not evidence_linked else 0.0)
    ambiguity = clamp01(0.1 * len(law_record.get("conflicts") or []))
    consequence = clamp01(0.65 + 0.08 * min(len(dependencies), 4))
    link_density = clamp01(0.5 + 0.06 * history_len + (0.22 if evidence_linked else 0.0) + 0.04 * len(domains))

    if law_id in LAW_PURPOSE_TEXT:
        avg_hops = min(avg_hops, 1.0)
        consequence = max(consequence, 0.90)
        link_density = max(link_density, 0.82 if evidence_linked else 0.76)
        ambiguity = min(ambiguity, 0.02)

    return graph_metrics_from_counts(
        avg_hops=avg_hops,
        ambiguity_score=ambiguity,
        consequence_coverage=consequence,
        link_density=link_density,
    )


def evaluate_drift(
    chi: float,
    prev_chi: float | None,
    *,
    cfg: ComprehensionConfig | None = None,
    history: list[float] | None = None,
) -> dict[str, Any]:
    """CIT-2 drift evaluation for a single epoch step."""

    config = cfg or ComprehensionConfig()
    delta = None if prev_chi is None else round(chi - prev_chi, 6)
    status = "ok"
    warnings: list[str] = []

    if chi < config.theta_min:
        status = "breach"
        warnings.append("CIT-LOW")

    if delta is not None and abs(delta) > config.delta_max:
        status = "warning" if status == "ok" else status
        warnings.append("CIT-DRIFT")

    if history and len(history) >= config.drift_window:
        window_delta = chi - history[-config.drift_window]
        if abs(window_delta) > config.drift_window * config.delta_max:
            status = "warning" if status == "ok" else status
            if "CIT-DRIFT" not in warnings:
                warnings.append("CIT-DRIFT")

    if status == "breach":
        warnings.append("CIT-BLOCK")

    return {
        "chi": round(chi, 6),
        "prev_chi": None if prev_chi is None else round(prev_chi, 6),
        "delta": delta,
        "status": status,
        "warnings": warnings,
        "thresholds": {
            "theta_min": config.theta_min,
            "delta_max": config.delta_max,
            "drift_window": config.drift_window,
        },
    }


def build_law_cit_strip(
    law_record: dict[str, Any],
    *,
    evidence_id: str | None = None,
    epoch: int = 0,
    cfg: ComprehensionConfig | None = None,
) -> CITStrip:
    law_id = str(law_record.get("law_id") or "")
    metrics = law_graph_metrics(law_record, evidence_linked=bool(evidence_id))
    chi, components = compute_law_comprehension(law_record, metrics, cfg)

    purpose = LAW_PURPOSE_TEXT.get(law_id, f"Sovereign law {law_id} governing substrate behavior.")
    breaks = LAW_BREAKS_TEXT.get(
        law_id,
        "Downstream laws and evidence may become orphaned; operator stewardship degrades.",
    )
    fitness = law_record.get("fitness") or {}
    current_f = fitness.get("current", 0.0)
    status = law_record.get("status", "unknown")

    trace_links: list[dict[str, str]] = []
    for dep in law_record.get("dependencies") or []:
        trace_links.append({"kind": "law", "target": dep, "label": f"depends on {dep}"})
    if evidence_id:
        trace_links.append({"kind": "evidence", "target": evidence_id, "label": f"evidence {evidence_id}"})
    trace_links.append({"kind": "epoch", "target": str(epoch), "label": f"epoch {epoch}"})

    return CITStrip(
        object_type="law",
        object_id=law_id,
        explain=(
            f"{law_id} ({status}) is a sovereign law with fitness F={current_f:.3f}. "
            f"{purpose}"
        ),
        summarize=f"{law_id}: {status}, F={current_f:.3f}, domains={', '.join(law_record.get('domains') or []) or 'none'}.",
        why_exists=purpose,
        what_breaks_if_removed=breaks,
        constitutional_role=LAW_ROLES.get(law_id, ["CIT"]),
        chi=chi,
        components=components,
        trace_links=trace_links,
        replay_hint=f"Replay fitness derivation D = f(E) via evidence {evidence_id or 'pending'}.",
        ready=bool(law_id) and chi >= (cfg or ComprehensionConfig()).theta_min,
    )


def build_evidence_cit_strip(
    evidence: dict[str, Any],
    *,
    graph: dict[str, Any] | None = None,
    cfg: ComprehensionConfig | None = None,
) -> CITStrip:
    evidence_id = str(evidence.get("evidence_id") or "")
    law_id = str(evidence.get("_law_id") or evidence.get("law_id") or "")
    node_count = len((graph or {}).get("nodes") or [])
    edge_count = len((graph or {}).get("edges") or [])

    metrics = graph_metrics_from_counts(
        avg_hops=1.0 + node_count * 0.08,
        ambiguity_score=clamp01(0.05 * max(node_count - 8, 0)),
        consequence_coverage=clamp01(0.55 + 0.05 * min(edge_count, 6)),
        link_density=clamp01(0.45 + 0.04 * min(edge_count, 8)),
    )
    chi, components = compute_evidence_comprehension(evidence, metrics, cfg)

    trace_links = [
        {"kind": "evidence", "target": evidence_id, "label": evidence_id},
    ]
    if law_id:
        trace_links.append({"kind": "law", "target": law_id, "label": f"binds {law_id}"})

    return CITStrip(
        object_type="evidence",
        object_id=evidence_id,
        explain=(
            f"Evidence {evidence_id} backs lawful decisions for {law_id or 'substrate'} "
            f"with confidence {float(evidence.get('confidence') or 0):.3f}."
        ),
        summarize=f"{evidence_id}: {evidence.get('evidence_type', 'derivation')}, epoch {evidence.get('source_epoch', 0)}.",
        why_exists="EIT-1 requires every lawful decision to bind recoverable evidence.",
        what_breaks_if_removed=(
            f"Law evaluations referencing {evidence_id} become constitutionally void."
        ),
        constitutional_role=["EIT", "PIT", "CIT"],
        chi=chi,
        components=components,
        trace_links=trace_links,
        replay_hint="Replay canonical_hash against lineage trace_links.",
        ready=chi >= (cfg or ComprehensionConfig()).theta_min,
    )
