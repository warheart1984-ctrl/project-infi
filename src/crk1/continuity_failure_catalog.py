"""Mission #003 continuity failure catalog (M3-D) — threat model index."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContinuityFailure:
    failure_id: str
    name: str
    description: str
    blocked_by: tuple[str, ...]
    detection: str


CONTINUITY_FAILURE_CATALOG: tuple[ContinuityFailure, ...] = (
    ContinuityFailure(
        "D1",
        "Mechanical Blindness",
        "Decisions produce Outcomes that never become Evidence.",
        ("K0", "K1", "EvidenceContract"),
        "replay_outcome guard; assert_replay_produces_evidence",
    ),
    ContinuityFailure(
        "D2",
        "Shadow Subsystem",
        "Some Decisions route to Outcomes/Evidence not seen by governance.",
        ("K3", "K4", "K5", "MutationLedger"),
        "DriftSimulator; governance_engine; mutation_ledger",
    ),
    ContinuityFailure(
        "D3",
        "Interpretive Monoculture",
        "One frame dominates; others removed or weight→0.",
        ("K7", "K8", "K9", "SemanticDriftAuditor"),
        "SemanticDriftAuditor.check_monoculture",
    ),
    ContinuityFailure(
        "D4",
        "Adversarial Silence",
        "No adversarial frames remain.",
        ("K10", "SemanticDriftAuditor"),
        "SemanticDriftAuditor.check_adversarial_loss",
    ),
    ContinuityFailure(
        "D5",
        "Semantic Zero Exposure",
        "SE(S) → 0 via clever weighting.",
        ("K11", "K12", "DriftSimulator"),
        "SemanticExposureMonitor; DriftStressProtocol",
    ),
    ContinuityFailure(
        "D6",
        "Founder Lock-In",
        "System cannot be reproduced without founder lore.",
        ("M3-A", "ExternalReproductionHarness", "SemanticReproductionHarness"),
        "mission_003_packet; reproduction + semantic harness",
    ),
)


def catalog_summary() -> str:
    lines = ["CRK-1 Continuity Failure Catalog (M3-D)"]
    for item in CONTINUITY_FAILURE_CATALOG:
        laws = ", ".join(item.blocked_by)
        lines.append(f"  {item.failure_id} — {item.name}")
        lines.append(f"      {item.description}")
        lines.append(f"      Blocked by: {laws}")
        lines.append(f"      Detection: {item.detection}")
    return "\n".join(lines)
