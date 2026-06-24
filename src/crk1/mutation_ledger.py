"""CRK-1 Mutation Ledger — constitutional change history (K4–K6, K11)."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.crk1.consequence_lattice import (
    ConsequenceExposure,
    mutation_admissible,
    validate_consequence_preservation,
    validate_drift_envelope,
)
from src.crk1.errors import ConstitutionalError

MUTATION_LEDGER_VERSION = "1.0"
MUTATION_LEDGER_TYPE = "Constitutional Mutation Record"

MutationType = Literal["constitution", "governance", "interpretation"]


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ExposureSnapshot(BaseModel):
    ce: float
    se: float


class ConstitutionalTestResults(BaseModel):
    k4_consequence_preservation: Literal["PASS", "FAIL"] = "FAIL"
    k5_mutation_admissibility: Literal["PASS", "FAIL"] = "FAIL"
    k6_drift_envelope_ce: Literal["PASS", "FAIL"] = "FAIL"
    k11_drift_envelope_se: Literal["PASS", "FAIL"] = "FAIL"


class MutationEntry(BaseModel):
    """Single constitutional mutation record."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=_now_iso)
    proposer_identity: str
    mutation_type: MutationType
    changes: dict[str, str] = Field(default_factory=dict)
    justification: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    exposure_before: ExposureSnapshot
    exposure_after: ExposureSnapshot
    constitutional_tests: ConstitutionalTestResults = Field(default_factory=ConstitutionalTestResults)
    constitutional: bool = False
    signature: str = ""

    def entry_hash(self) -> str:
        payload = self.model_dump(mode="json", exclude={"signature"})
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def finalize_signature(self) -> str:
        self.signature = self.entry_hash()
        return self.signature

    def to_canonical_text_lines(self) -> list[str]:
        lines = [
            "MutationEntry:",
            f"  id: {self.id}",
            f"  timestamp: {self.timestamp}",
            f"  proposer_identity: {self.proposer_identity}",
            f'  mutation_type: "{self.mutation_type}"',
            "  changes:",
        ]
        for key, value in self.changes.items():
            lines.append(f"    {key}: {value}")
        lines.append(f"  justification: {self.justification}")
        ids = ", ".join(self.evidence_ids)
        lines.append(f"  evidence_ids: [{ids}]")
        lines.append("")
        lines.append("Exposure Before:")
        lines.append(f"  CE_before: {self.exposure_before.ce}")
        lines.append(f"  SE_before: {self.exposure_before.se}")
        lines.append("")
        lines.append("Exposure After:")
        lines.append(f"  CE_after: {self.exposure_after.ce}")
        lines.append(f"  SE_after: {self.exposure_after.se}")
        lines.append("")
        lines.append("Constitutional Tests:")
        tests = self.constitutional_tests
        lines.append(f"  - K4: Consequence Preservation → {tests.k4_consequence_preservation}")
        lines.append(f"  - K5: Mutation Admissibility → {tests.k5_mutation_admissibility}")
        lines.append(f"  - K6: Drift Envelope (CE) → {tests.k6_drift_envelope_ce}")
        lines.append(f"  - K11: Interpretive Drift Envelope (SE) → {tests.k11_drift_envelope_se}")
        lines.append("")
        lines.append("Final Verdict:")
        lines.append(f"  constitutional: {str(self.constitutional).lower()}")
        lines.append("")
        lines.append("Signature:")
        lines.append(f"  {self.signature or self.finalize_signature()}")
        return lines


class CRK1MutationLedger(BaseModel):
    """Append-only evolutionary history of CRK-1."""

    version: str = MUTATION_LEDGER_VERSION
    ledger_type: str = MUTATION_LEDGER_TYPE
    entries: list[MutationEntry] = Field(default_factory=list)
    signature: str = ""

    def append(self, entry: MutationEntry) -> MutationEntry:
        entry.finalize_signature()
        self.entries.append(entry)
        return entry

    def finalize_signature(self) -> str:
        body = json.dumps(
            [entry.model_dump(mode="json") for entry in self.entries],
            sort_keys=True,
            separators=(",", ":"),
        )
        self.signature = hashlib.sha256(body.encode("utf-8")).hexdigest()
        return self.signature

    def to_canonical_text(self) -> str:
        sig = self.signature or self.finalize_signature()
        lines = [
            "CRK‑1 Mutation Ledger",
            f"Version: {self.version}",
            f"Ledger Type: {self.ledger_type}",
            "",
        ]
        for entry in self.entries:
            lines.extend(entry.to_canonical_text_lines())
            lines.append("")
        lines.append("Signature:")
        lines.append(f"  {sig}")
        return "\n".join(lines)


def build_mutation_entry(
    *,
    runtime: Any,
    mutation: dict[str, Any],
    drift_result: dict[str, Any],
    proposer_identity: str,
    justification: str = "",
    evidence_ids: list[str] | None = None,
) -> MutationEntry:
    """Construct a MutationEntry from a DriftSimulator result."""
    changes_raw: dict[str, Any] = dict(mutation.get("changes") or {})
    changes = {key: f"<prior> → {value}" for key, value in changes_raw.items()}

    mutation_type: MutationType = mutation.get("target", "constitution")
    before = drift_result.get("before") or {}
    after = drift_result.get("after") or {}
    ce_before = float(before.get("CE", 0.0))
    se_before = float(before.get("SE", 0.0))
    ce_after = float(after.get("CE", ce_before))
    se_after = float(after.get("SE", se_before))

    tests = ConstitutionalTestResults()
    tests.k5_mutation_admissibility = "PASS" if mutation_admissible(changes_raw) else "FAIL"

    try:
        validate_consequence_preservation(runtime, changes=changes_raw)
        tests.k4_consequence_preservation = "PASS"
    except ConstitutionalError:
        tests.k4_consequence_preservation = "FAIL"

    ce_detail_before = drift_result.get("ce_detail_before")
    ce_detail_after = drift_result.get("ce_detail_after")
    if ce_detail_before and ce_detail_after:
        ce_before_obj = ConsequenceExposure(**ce_detail_before)
        ce_after_obj = ConsequenceExposure(**ce_detail_after)
        try:
            validate_drift_envelope(ce_before_obj, ce_after_obj)
            tests.k6_drift_envelope_ce = "PASS"
        except ConstitutionalError:
            tests.k6_drift_envelope_ce = "FAIL"
    else:
        tests.k6_drift_envelope_ce = "PASS" if drift_result.get("CE_preserved") else "FAIL"

    tests.k11_drift_envelope_se = "PASS" if drift_result.get("SE_preserved") else "FAIL"
    constitutional = bool(drift_result.get("constitutional"))

    return MutationEntry(
        proposer_identity=proposer_identity,
        mutation_type=mutation_type,
        changes=changes,
        justification=justification,
        evidence_ids=list(evidence_ids or []),
        exposure_before=ExposureSnapshot(ce=ce_before, se=se_before),
        exposure_after=ExposureSnapshot(ce=ce_after, se=se_after),
        constitutional_tests=tests,
        constitutional=constitutional,
    )


def record_drift_test(
    ledger: CRK1MutationLedger,
    *,
    runtime: Any,
    mutation: dict[str, Any],
    drift_result: dict[str, Any],
    proposer_identity: str,
    justification: str = "",
    evidence_ids: list[str] | None = None,
) -> MutationEntry:
    """Append a mutation ledger entry from a drift simulation."""
    _ = runtime  # reserved for future lineage hooks
    entry = build_mutation_entry(
        runtime=runtime,
        mutation=mutation,
        drift_result=drift_result,
        proposer_identity=proposer_identity,
        justification=justification,
        evidence_ids=evidence_ids,
    )
    return ledger.append(entry)
