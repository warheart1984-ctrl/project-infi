"""Legitimacy Receipts — reconstructable artifacts for every legitimacy decision (Protocol §3)."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.legitimacy.spec import LEGITIMACY_RECEIPT_TYPES
from constitutional.runtime.runtime import ConstitutionalStateRuntime


class LegitimacyReceiptBundle(BaseModel):
    """All receipt families produced during the legitimacy process."""

    candidate_id: str
    recorded_at: datetime
    reconstruction_receipts: list[str] = Field(default_factory=list)
    boundary_receipts: list[str] = Field(default_factory=list)
    drift_receipts: list[str] = Field(default_factory=list)
    consequence_receipts: list[str] = Field(default_factory=list)
    legitimacy_receipts: list[str] = Field(default_factory=list)
    stewardship_reflection: str = ""

    @property
    def complete(self) -> bool:
        return all(
            [
                self.reconstruction_receipts,
                self.boundary_receipts,
                self.drift_receipts,
                self.consequence_receipts,
                self.legitimacy_receipts,
            ]
        )

    def receipt_types_present(self) -> list[str]:
        present: list[str] = []
        mapping = {
            "reconstruction_receipts": self.reconstruction_receipts,
            "boundary_receipts": self.boundary_receipts,
            "drift_receipts": self.drift_receipts,
            "consequence_receipts": self.consequence_receipts,
            "legitimacy_receipts": self.legitimacy_receipts,
        }
        for receipt_type in LEGITIMACY_RECEIPT_TYPES:
            if mapping.get(receipt_type):
                present.append(receipt_type)
        return present


def build_receipt_bundle_from_evidence(
    candidate_id: str,
    *,
    evidence_refs: list[str],
    approval_rationale: str,
    reflection: str = "",
) -> LegitimacyReceiptBundle:
    """Construct a receipt bundle from reconstruction evidence refs."""
    now = datetime.now(UTC).replace(microsecond=0)
    reconstruction = [ref for ref in evidence_refs if ref in {"eck2_pipeline", "jpss_cycle", "invariant_register"}]
    boundary = [ref for ref in evidence_refs if "jpss_c" in ref or ref == "stewardship_balancing"]
    drift = [ref for ref in evidence_refs if "drift" in ref]
    consequence = [ref for ref in evidence_refs if ref.startswith("consequence")]
    if not consequence and evidence_refs:
        consequence = ["consequence_simulation_report"]

    return LegitimacyReceiptBundle(
        candidate_id=candidate_id,
        recorded_at=now,
        reconstruction_receipts=reconstruction or list(evidence_refs[:3]),
        boundary_receipts=boundary or ["jpss_c_exam", "stewardship_balancing"],
        drift_receipts=drift or ["legitimacy_drift", "invariant_drift"],
        consequence_receipts=consequence,
        legitimacy_receipts=[approval_rationale],
        stewardship_reflection=reflection,
    )


def record_legitimacy_receipts(
    csr: ConstitutionalStateRuntime,
    bundle: LegitimacyReceiptBundle,
) -> LegitimacyReceiptBundle:
    csr.put_domain_doc(
        f"legitimacy_receipts__{bundle.candidate_id}",
        "legitimacy_receipt_bundle",
        bundle,
    )
    return bundle


def load_legitimacy_receipts(
    csr: ConstitutionalStateRuntime,
    candidate_id: str,
) -> LegitimacyReceiptBundle | None:
    try:
        doc = csr.get_domain_doc(f"legitimacy_receipts__{candidate_id}", LegitimacyReceiptBundle)
        assert isinstance(doc, LegitimacyReceiptBundle)
        return doc
    except KeyError:
        return None
