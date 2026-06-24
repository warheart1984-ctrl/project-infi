"""CRK-1 Governance Receipt Index — query surface for continuity audits."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.crk1.governance_receipt_merkleizer import audit_spine, merkle_root

_DRIFT_EPSILON = 1e-9


class GovernanceReceiptIndex:
    """In-memory index of verified governance receipt headers."""

    def __init__(self) -> None:
        self.by_id: dict[str, dict[str, Any]] = {}
        self.by_actor: dict[str, list[str]] = defaultdict(list)
        self.by_action_type: dict[str, list[str]] = defaultdict(list)

    def add_receipt(self, receipt: dict[str, Any]) -> None:
        receipt_id = receipt["receipt_id"]
        self.by_id[receipt_id] = receipt
        self.by_actor[receipt["actor_identity"]].append(receipt_id)
        self.by_action_type[receipt["action_type"]].append(receipt_id)

    def get_by_id(self, receipt_id: str) -> dict[str, Any] | None:
        return self.by_id.get(receipt_id)

    def get_by_actor(self, actor_id: str) -> list[dict[str, Any]]:
        return [self.by_id[receipt_id] for receipt_id in self.by_actor.get(actor_id, [])]

    def get_by_action_type(self, action_type: str) -> list[dict[str, Any]]:
        return [
            self.by_id[receipt_id]
            for receipt_id in self.by_action_type.get(action_type, [])
        ]

    def all_receipts(self) -> list[dict[str, Any]]:
        return list(self.by_id.values())

    def merkle_root(self) -> str:
        return merkle_root(self.all_receipts())

    def audit_spine(self) -> dict[str, Any]:
        return audit_spine(self.all_receipts())

    def find_failures(self) -> list[dict[str, Any]]:
        """Receipts where any invariant layer or drift envelope failed."""
        failures: list[dict[str, Any]] = []
        for receipt in self.by_id.values():
            invariants = receipt["invariants_checked"]
            metrics = receipt["drift_metrics"]
            redteam = receipt.get("redteam_status", {})
            if (
                invariants["K0_K2"] == "FAIL"
                or invariants["K3_K6"] == "FAIL"
                or invariants["K7_K12"] == "FAIL"
                or metrics["CE_after"] + _DRIFT_EPSILON < metrics["CE_before"]
                or metrics["SE_after"] + _DRIFT_EPSILON < metrics["SE_before"]
                or redteam.get("all_blocked") == "NO"
            ):
                failures.append(receipt)
        return failures
