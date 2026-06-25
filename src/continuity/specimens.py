"""CSS-1 continuity specimen schema, replay validation, and comparison."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


CANONICAL_SPECIMEN_TYPES = (
    "baseline",
    "identity_reinforcement",
    "governance_conflict",
    "continuity_fracture",
)
VALID_KERNELS = {"UGR", "AAIS", "DARZ", "AAES"}
VALID_RELATIONS = {"CAUSES", "DERIVES_FROM", "CONSTRAINS", "VIOLATES", "REINFORCES"}
VALID_PROOF_STATUS = {"PROVEN", "FAILED"}
REQUIRED_FILES = (
    "specimen.json",
    "replay_trace.json",
    "lineage_graph.json",
    "wave_signature.json",
    "receipt.json",
)


@dataclass(frozen=True, slots=True)
class ContinuitySpecimen:
    specimen_id: str
    specimen_type: str
    thread_id: str
    events: tuple[dict[str, Any], ...]
    lineage: tuple[dict[str, Any], ...]
    metrics: dict[str, float]
    wave: dict[str, float]
    receipt: dict[str, str]
    conditions: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ContinuitySpecimen":
        return cls(
            specimen_id=str(payload.get("specimen_id") or ""),
            specimen_type=str(payload.get("specimen_type") or ""),
            thread_id=str(payload.get("thread_id") or ""),
            events=tuple(dict(item) for item in payload.get("events") or []),
            lineage=tuple(dict(item) for item in payload.get("lineage") or []),
            metrics={key: float(value) for key, value in dict(payload.get("metrics") or {}).items()},
            wave={key: float(value) for key, value in dict(payload.get("wave") or {}).items()},
            receipt={key: str(value) for key, value in dict(payload.get("receipt") or {}).items()},
            conditions=dict(payload.get("conditions") or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "specimen_id": self.specimen_id,
            "specimen_type": self.specimen_type,
            "thread_id": self.thread_id,
            "events": [dict(item) for item in self.events],
            "lineage": [dict(item) for item in self.lineage],
            "metrics": dict(self.metrics),
            "wave": dict(self.wave),
            "receipt": dict(self.receipt),
            "conditions": dict(self.conditions),
        }


@dataclass(frozen=True, slots=True)
class SpecimenValidationReport:
    specimen_id: str
    schema_valid: bool
    replay_valid: bool
    proof_status: str
    wave_valid: bool
    violations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ComparisonReport:
    specimen_a: str
    specimen_b: str
    delta_A: float
    delta_f: float
    delta_phi: float
    delta_C: float
    delta_R: float
    lineage_distance: int
    classification: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "specimen_a": self.specimen_a,
            "specimen_b": self.specimen_b,
            "delta_A": self.delta_A,
            "delta_f": self.delta_f,
            "delta_phi": self.delta_phi,
            "delta_C": self.delta_C,
            "delta_R": self.delta_R,
            "lineage_distance": self.lineage_distance,
            "classification": self.classification,
        }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_specimen(path: Path | str) -> ContinuitySpecimen:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return ContinuitySpecimen.from_dict(payload)


def load_specimen_library(root: Path | str) -> list[ContinuitySpecimen]:
    base = Path(root)
    specimens = [
        load_specimen(folder / "specimen.json")
        for folder in sorted(base.iterdir())
        if folder.is_dir() and (folder / "specimen.json").is_file()
    ]
    return sorted(specimens, key=lambda item: item.specimen_id)


def _schema_violations(specimen: ContinuitySpecimen) -> list[str]:
    violations: list[str] = []
    if not specimen.specimen_id:
        violations.append("css1.specimen_id_missing")
    if specimen.specimen_type not in CANONICAL_SPECIMEN_TYPES:
        violations.append("css1.specimen_type_invalid")
    if not specimen.thread_id:
        violations.append("css1.thread_id_missing")
    if not specimen.events:
        violations.append("css1.events_missing")
    event_ids = {str(event.get("event_id") or "") for event in specimen.events}
    for event in specimen.events:
        if event.get("kernel") not in VALID_KERNELS:
            violations.append(f"css1.kernel_invalid:{event.get('event_id')}")
        if not str(event.get("event_id") or ""):
            violations.append("css1.event_id_missing")
        if str(event.get("event_id") or "") in {"", None}:
            violations.append("css1.event_id_invalid")
    for edge in specimen.lineage:
        if edge.get("relation") not in VALID_RELATIONS:
            violations.append("css1.lineage_relation_invalid")
        if edge.get("from") not in event_ids or edge.get("to") not in event_ids:
            violations.append("css1.lineage_pointer_invalid")
    for key in ("coherence", "identity_drift", "replay_stability", "governance_alignment", "resonance"):
        if key not in specimen.metrics:
            violations.append(f"css1.metric_missing:{key}")
    for key in ("A", "f", "phi", "C", "R"):
        if key not in specimen.wave:
            violations.append(f"css1.wave_missing:{key}")
    if specimen.receipt.get("proof_status") not in VALID_PROOF_STATUS:
        violations.append("css1.proof_status_invalid")
    for key in ("replay_hash", "substrate_hash"):
        if not specimen.receipt.get(key):
            violations.append(f"css1.receipt_missing:{key}")
    if not specimen.conditions.get("description"):
        violations.append("css1.conditions_description_missing")
    return violations


def _wave_valid(specimen: ContinuitySpecimen) -> bool:
    return all(0.0 <= float(specimen.wave.get(key, -1.0)) <= 1.0 for key in ("A", "f", "phi", "C", "R"))


def validate_specimen(specimen: ContinuitySpecimen) -> SpecimenValidationReport:
    violations = _schema_violations(specimen)
    wave_valid = _wave_valid(specimen)
    if not wave_valid:
        violations.append("srvp.wave_out_of_range")
    replay_valid = float(specimen.metrics.get("replay_stability", 0.0)) >= 0.95
    proof_status = specimen.receipt.get("proof_status", "")
    if proof_status == "FAILED":
        violations.append("srvp.proof_failed")
    if not replay_valid:
        violations.append("srvp.replay_unstable")
    return SpecimenValidationReport(
        specimen_id=specimen.specimen_id,
        schema_valid=not any(item.startswith("css1.") for item in violations),
        replay_valid=replay_valid,
        proof_status=proof_status,
        wave_valid=wave_valid,
        violations=tuple(dict.fromkeys(violations)),
    )


def _edge_set(specimen: ContinuitySpecimen) -> set[tuple[str, str, str]]:
    return {
        (str(edge.get("from")), str(edge.get("to")), str(edge.get("relation")))
        for edge in specimen.lineage
    }


def _classification(delta_c: float, delta_phi: float, delta_r: float, specimen_b_type: str) -> str:
    if specimen_b_type == "continuity_fracture" and (delta_c >= 0.5 or delta_phi >= 0.5):
        return "continuity_fracture_divergence"
    if delta_r >= 0.2 and delta_phi < 0.2:
        return "identity_resonance_shift"
    if delta_c >= 0.25 or delta_phi >= 0.25:
        return "governance_coherence_drift"
    return "continuity_near_baseline"


def morphology_class(specimen: ContinuitySpecimen) -> str:
    """Classify a specimen into SMC-1 continuity morphology."""

    coherence = float(specimen.wave.get("C", 0.0))
    phase = float(specimen.wave.get("phi", 0.0))
    resonance = float(specimen.wave.get("R", 0.0))
    amplitude = float(specimen.wave.get("A", 0.0))
    frequency = float(specimen.wave.get("f", 0.0))
    identity_drift = float(specimen.metrics.get("identity_drift", 0.0))
    governance_alignment = float(specimen.metrics.get("governance_alignment", 0.0))
    if specimen.specimen_type == "continuity_fracture" or coherence < 0.35:
        return "fractured_continuity"
    if coherence < 0.55 or phase < 0.45:
        return "chaotic_continuity"
    if governance_alignment < 0.70 or (amplitude >= 0.70 and frequency >= 0.45 and phase < 0.75):
        return "governance_dominant_continuity"
    if resonance >= 0.80 and identity_drift <= 0.05:
        return "identity_dominant_continuity"
    if coherence >= 0.85 and resonance >= 0.65 and phase >= 0.90:
        return "harmonic_continuity"
    return "chaotic_continuity"


def compare_specimens(left: ContinuitySpecimen, right: ContinuitySpecimen) -> ComparisonReport:
    delta_a = round(abs(left.wave["A"] - right.wave["A"]), 10)
    delta_f = round(abs(left.wave["f"] - right.wave["f"]), 10)
    delta_phi = round(abs(left.wave["phi"] - right.wave["phi"]), 10)
    delta_c = round(abs(left.wave["C"] - right.wave["C"]), 10)
    delta_r = round(abs(left.wave["R"] - right.wave["R"]), 10)
    lineage_distance = len(_edge_set(left) ^ _edge_set(right))
    return ComparisonReport(
        specimen_a=left.specimen_id,
        specimen_b=right.specimen_id,
        delta_A=delta_a,
        delta_f=delta_f,
        delta_phi=delta_phi,
        delta_C=delta_c,
        delta_R=delta_r,
        lineage_distance=lineage_distance,
        classification=_classification(delta_c, delta_phi, delta_r, right.specimen_type),
    )


def generate_specimen_from_runtime(
    *,
    specimen_id: str,
    specimen_type: str,
    thread_id: str,
    events: list[dict[str, Any]],
    lineage: list[dict[str, Any]],
    metrics: dict[str, float],
    wave: dict[str, float],
    receipt: dict[str, str],
    conditions: dict[str, Any],
) -> ContinuitySpecimen:
    """SGP-1: export a runtime thread shape into a CSS-1 specimen."""

    return ContinuitySpecimen.from_dict(
        {
            "specimen_id": specimen_id,
            "specimen_type": specimen_type,
            "thread_id": thread_id,
            "events": events,
            "lineage": lineage,
            "metrics": metrics,
            "wave": wave,
            "receipt": receipt,
            "conditions": conditions,
        }
    )


def export_specimen_artifacts(specimen: ContinuitySpecimen, folder: Path | str) -> Path:
    """CSL-1/SLC-1: write one specimen folder with all required artifacts."""

    output = Path(folder)
    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "specimen.json", specimen.to_dict())
    _write_json(
        output / "lineage_graph.json",
        {
            "thread_id": specimen.thread_id,
            "edges": [
                [edge.get("from"), edge.get("to"), edge.get("relation")]
                for edge in specimen.lineage
            ],
        },
    )
    _write_json(output / "wave_signature.json", dict(specimen.wave))
    _write_json(output / "receipt.json", dict(specimen.receipt))
    _write_json(
        output / "replay_trace.json",
        {
            "thread_id": specimen.thread_id,
            "replay_hash": specimen.receipt.get("replay_hash"),
            "stable": float(specimen.metrics.get("replay_stability", 0.0)) >= 0.95,
            "events": [event.get("event_id") for event in specimen.events],
        },
    )
    return output


class DarzSpecimenArchive:
    """SLC-1 archive for DAR-Z specimen memory."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _folder_for(self, specimen_id: str) -> Path:
        safe = str(specimen_id).replace(".", "_").replace("/", "_")
        return self.root / safe

    def export_specimen(self, specimen: ContinuitySpecimen) -> Path:
        return export_specimen_artifacts(specimen, self._folder_for(specimen.specimen_id))

    def ingest_specimen(self, specimen_id: str) -> ContinuitySpecimen:
        return load_specimen(self._folder_for(specimen_id) / "specimen.json")

    def list_specimen_ids(self) -> list[str]:
        ids: list[str] = []
        for folder in sorted(self.root.iterdir()):
            path = folder / "specimen.json"
            if folder.is_dir() and path.is_file():
                ids.append(load_specimen(path).specimen_id)
        return sorted(ids)
