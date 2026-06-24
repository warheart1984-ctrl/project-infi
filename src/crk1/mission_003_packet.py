"""Mission #003 deliverable manifest — external reproduction packet (M3-A)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PacketArtifact:
    """Single entry in the external reproduction packet."""

    artifact_id: str
    name: str
    path: Path
    description: str = ""


EXTERNAL_REPRODUCTION_PACKET: tuple[PacketArtifact, ...] = (
    PacketArtifact(
        "A1",
        "CRK-1 Kernel Codex",
        REPO_ROOT / "docs" / "crk1" / "crk1_kernel_codex.md",
        "Full K0–K12 spec",
    ),
    PacketArtifact(
        "A2",
        "Runtime Minimap",
        REPO_ROOT / "docs" / "crk1" / "crk1_kernel_minimap.svg",
        "Three layers, K0–K12",
    ),
    PacketArtifact(
        "A3",
        "Runtime Diagram",
        REPO_ROOT / "docs" / "crk1" / "crk1_runtime_diagram.svg",
        "Objects, contracts, loops",
    ),
    PacketArtifact(
        "A4",
        "Minimal Runtime Skeleton",
        REPO_ROOT / "src" / "crk1" / "crk1_minimal_runtime.py",
        "Decision→Outcome→Evidence + basic SE(S)",
    ),
    PacketArtifact(
        "A5",
        "Semantic Object Schemas",
        REPO_ROOT / "fixtures" / "crk1",
        "Interpretation, Prediction, Reconstruction JSON schemas",
    ),
    PacketArtifact(
        "A6",
        "Ledgers",
        REPO_ROOT / "src" / "crk1",
        "kernel_ledger, semantic_ledger, mutation_ledger",
    ),
    PacketArtifact(
        "A7",
        "Reproduction Harness",
        REPO_ROOT / "src" / "crk1" / "semantic_reproduction_harness.py",
        "SemanticReproductionHarness.run() — K7–K12 pass conditions",
    ),
)

SUPPORTING_ARTIFACTS: tuple[PacketArtifact, ...] = (
    PacketArtifact(
        "—",
        "Invariant Registry",
        REPO_ROOT / "docs" / "crk1" / "crk1_invariants.yaml",
    ),
    PacketArtifact(
        "—",
        "State Machine",
        REPO_ROOT / "docs" / "crk1" / "crk1_state_machine.json",
    ),
    PacketArtifact(
        "—",
        "Full Reproduction Harness",
        REPO_ROOT / "src" / "crk1" / "external_reproduction_harness.py",
    ),
)

SCHEMA_FILES = (
    "interpretation_object.schema.json",
    "prediction_object.schema.json",
    "reconstruction_object.schema.json",
    "outcome_object.schema.json",
    "evidence_object.schema.json",
    "decision_object.schema.json",
    "identity_object.schema.json",
)

LEDGER_MODULES = (
    "kernel_ledger.py",
    "semantic_ledger.py",
    "mutation_ledger.py",
)

# M3-C drift envelope stress batteries
DRIFT_C1_BENIGN: list[dict[str, Any]] = [
    {"category": "C1", "target": "governance", "changes": {"governance.quorum": 3}},
    {"category": "C1", "target": "constitution", "changes": {"governance.quorum": 4}},
    {"category": "C1", "target": "interpretation", "changes": {}},
]

DRIFT_C2_RISKY: list[dict[str, Any]] = [
    {
        "category": "C2",
        "target": "governance",
        "changes": {"governance.quorum": 5},
        "justification": "new governance rule",
    },
    {
        "category": "C2",
        "target": "interpretation",
        "changes": {},
        "justification": "new interpretive frame via drift",
    },
]

DRIFT_C3_MALICIOUS: list[dict[str, Any]] = [
    {"category": "C3", "target": "constitution", "changes": {"Outcome.replayable": False}},
    {"category": "C3", "target": "constitution", "changes": {"block_consequence_propagation": True}},
    {"category": "C3", "target": "constitution", "changes": {"lineage_rules": "disable"}},
    {
        "category": "C3",
        "target": "constitution",
        "changes": {"insulate_judgment_from_outcomes": True},
    },
]

STRESS_BATTERY: list[dict[str, Any]] = DRIFT_C1_BENIGN + DRIFT_C2_RISKY + DRIFT_C3_MALICIOUS


def verify_packet_artifacts() -> tuple[bool, list[str]]:
    """Return (ok, missing_paths) for M3-A packet delivery."""
    missing: list[str] = []
    for artifact in EXTERNAL_REPRODUCTION_PACKET:
        if artifact.artifact_id == "A5":
            for name in SCHEMA_FILES:
                path = artifact.path / name
                if not path.is_file():
                    missing.append(str(path))
            continue
        if artifact.artifact_id == "A6":
            for name in LEDGER_MODULES:
                path = artifact.path / name
                if not path.is_file():
                    missing.append(str(path))
            continue
        if not artifact.path.is_file() and not artifact.path.is_dir():
            missing.append(str(artifact.path))
    return (not missing, missing)


def compute_packet_fingerprint() -> str:
    """SHA-256 over all M3-A artifact bytes (certification E5)."""
    digest = hashlib.sha256()
    for artifact in EXTERNAL_REPRODUCTION_PACKET + SUPPORTING_ARTIFACTS:
        if artifact.artifact_id == "A5":
            for name in sorted(SCHEMA_FILES):
                path = artifact.path / name
                if path.is_file():
                    digest.update(path.read_bytes())
            continue
        if artifact.artifact_id == "A6":
            for name in sorted(LEDGER_MODULES):
                path = artifact.path / name
                if path.is_file():
                    digest.update(path.read_bytes())
            continue
        if artifact.path.is_file():
            digest.update(artifact.path.read_bytes())
    return digest.hexdigest()
