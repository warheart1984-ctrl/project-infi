"""Corridor law envelope — admission, adjudication, delegation (L2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from runtime_law_spine.runtime_law_spine.gate import RuntimeLawSpineGate
from runtime_law_spine.runtime_law_spine.immune import is_law_evolution_corridor
from src.ucr import ucr_attestation
from src.ucr.corridor_loader import CorridorLoader, CorridorLoaderError


@dataclass(frozen=True)
class DelegateAttestation:
    """Child agent capabilities must be subset of parent."""

    parent_id: str
    child_id: str
    parent_capabilities: frozenset[str]
    child_capabilities: frozenset[str]

    def validate(self) -> tuple[bool, str]:
        if not self.child_capabilities <= self.parent_capabilities:
            extra = self.child_capabilities - self.parent_capabilities
            return False, f"delegation_violation: {sorted(extra)}"
        return True, "ok"


@dataclass
class CorridorExecutor:
    """Admission → execute → adjudicate → receipt."""

    registry_dir: Path
    receipts: list[dict[str, Any]] = field(default_factory=list)

    def admit(
        self,
        corridor_id: str,
        *,
        capabilities: set[str] | None = None,
        required_capability: str | None = None,
        delegate: DelegateAttestation | None = None,
    ) -> tuple[bool, str]:
        gate = RuntimeLawSpineGate.instance()
        if not gate.substrate_ok:
            return False, "unsealed_runtime"
        try:
            CorridorLoader(self.registry_dir)
        except CorridorLoaderError as exc:
            return False, str(exc)
        if required_capability and capabilities is not None:
            if required_capability not in capabilities:
                return False, f"missing_capability:{required_capability}"
        if delegate is not None:
            ok, reason = delegate.validate()
            if not ok:
                return False, reason
        return True, "admitted"

    def propose_mutation(
        self,
        corridor_id: str,
        patch: dict[str, Any],
        *,
        target: str = "state",
    ) -> dict[str, Any]:
        return {
            "corridor_id": corridor_id,
            "target": target,
            "patch": patch,
            "status": "proposed",
        }

    def adjudicate_mutation(
        self,
        proposal: dict[str, Any],
        *,
        capabilities: set[str] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        cid = proposal.get("corridor_id", "")
        if proposal.get("target") == "law_spine" and not is_law_evolution_corridor(cid):
            receipt = {**proposal, "status": "rejected", "reason": "law_evolution_corridor_required"}
            self.receipts.append(receipt)
            return False, receipt
        if capabilities is not None and "mutate" not in capabilities:
            receipt = {**proposal, "status": "rejected", "reason": "missing_mutate_capability"}
            self.receipts.append(receipt)
            return False, receipt
        receipt = {**proposal, "status": "committed"}
        self.receipts.append(receipt)
        return True, receipt

    def execute_task(
        self,
        corridor_id: str,
        attestation: dict[str, Any] | None = None,
        *,
        capabilities: set[str] | None = None,
    ) -> dict[str, Any]:
        caps = capabilities or set(attestation.get("capabilities", []) if attestation else [])
        ok, reason = self.admit(corridor_id, capabilities=caps)
        record = {
            "corridor_id": corridor_id,
            "admitted": ok,
            "reason": reason,
            "attestation": attestation,
        }
        if ok and attestation:
            try:
                ucr_attestation.verify_attestation(attestation, registry_dir=self.registry_dir)
                record["attestation_verified"] = True
            except ucr_attestation.AttestationError as exc:
                record["admitted"] = False
                record["reason"] = str(exc)
                record["attestation_verified"] = False
        self.receipts.append(record)
        return record
