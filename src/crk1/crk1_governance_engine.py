"""CRK-1 Governance Engine — commit-refusing constitutional gate."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.crk1.errors import ConstitutionalError
from src.crk1.governance_receipt_index import GovernanceReceiptIndex
from src.crk1.governance_receipt_merkleizer import hash_receipt, merkle_root
from src.crk1.governance_receipt_verifier import GovernanceReceiptVerifier


class CRK1GovernanceEngine:
    """
    Governance engine that refuses to commit any constitutional action unless:

    - a governance receipt is present,
    - the receipt passes schema + invariant + drift + red-team checks,
    - the receipt is anchored into the Merkle root.

    apply_action_fn is invoked only after all checks pass.
    """

    def __init__(
        self,
        apply_action_fn: Callable[[dict[str, Any]], None],
        *,
        verifier: GovernanceReceiptVerifier | None = None,
        index: GovernanceReceiptIndex | None = None,
    ) -> None:
        self.apply_action_fn = apply_action_fn
        self.verifier = verifier or GovernanceReceiptVerifier()
        self.index = index or GovernanceReceiptIndex()
        self._receipts: list[dict[str, Any]] = []
        self._merkle_root: str = merkle_root([])

    @property
    def merkle_root(self) -> str:
        return self._merkle_root

    @property
    def receipts(self) -> list[dict[str, Any]]:
        return list(self._receipts)

    def receipt_leaf_hash(self, receipt: dict[str, Any]) -> str:
        return hash_receipt(receipt)

    def _update_merkle_root(self) -> None:
        self._merkle_root = merkle_root(self._receipts)

    def _anchor_receipt(self, receipt: dict[str, Any]) -> None:
        self._receipts.append(receipt)
        self.index.add_receipt(receipt)
        self._update_merkle_root()

    def commit_action(
        self,
        action: dict[str, Any],
        receipt: dict[str, Any],
        *,
        require_redteam: bool = True,
    ) -> None:
        """
        The only way to perform a constitutional action.

        1. Verify receipt (schema + invariants + drift + red-team).
        2. Anchor receipt into Merkle tree.
        3. Apply action to runtime state.
        """
        if not receipt:
            raise ConstitutionalError("Governance commit refused: receipt required")

        self.verifier.verify(receipt, require_redteam=require_redteam)
        self._anchor_receipt(receipt)
        self.apply_action_fn(action)

    def audit_failures(self) -> list[dict[str, Any]]:
        """Receipts where invariants or drift were violated (empty when healthy)."""
        return self.index.find_failures()
