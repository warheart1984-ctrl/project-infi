# CRK-1 Governance Engine
# Version 1.0

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.crk1.consequence_lattice import (
    apply_amendment_with_drift_check,
    consequence_exposure,
    mutation_admissible,
    validate_consequence_preservation,
)
from src.crk1.crk1_governance_engine import CRK1GovernanceEngine
from src.crk1.errors import ConstitutionalError
from src.crk1.governance_receipt_header import (
    GovernanceReceiptHeader,
    build_governance_receipt_header,
)
from src.crk1.governance_receipt_index import GovernanceReceiptIndex
from src.crk1.governance_receipt_verifier import GovernanceReceiptVerifier
from src.crk1.runtime_facade import CRK1Evidence, CRK1Outcome, CRK1Runtime
from src.crk1.runtime_validator import CRK1RuntimeValidator
from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor


class GovernanceEngine:
    """Steward proposal → deliberation → ratification → amendment with Consequence Preservation."""

    def __init__(
        self,
        runtime: CRK1Runtime,
        validator: CRK1RuntimeValidator,
        *,
        receipt_index: GovernanceReceiptIndex | None = None,
        receipt_verifier: GovernanceReceiptVerifier | None = None,
        commit_gate: CRK1GovernanceEngine | None = None,
    ) -> None:
        self.runtime = runtime
        self.validator = validator
        self.receipt_index = receipt_index or GovernanceReceiptIndex()
        self.receipt_verifier = receipt_verifier or GovernanceReceiptVerifier()
        self._pending_apply: Callable[[dict[str, Any]], None] | None = None
        self.commit_gate = commit_gate or CRK1GovernanceEngine(
            self._dispatch_pending_apply,
            verifier=self.receipt_verifier,
            index=self.receipt_index,
        )
        self.last_receipt_header: GovernanceReceiptHeader | None = None

    @property
    def merkle_root(self) -> str:
        return self.commit_gate.merkle_root

    def audit_failures(self) -> list[dict[str, Any]]:
        return self.commit_gate.audit_failures()

    def _dispatch_pending_apply(self, action: dict[str, Any]) -> None:
        if self._pending_apply is None:
            raise ConstitutionalError("Governance commit refused: no apply handler registered")
        self._pending_apply(action)

    def _se_snapshot(self) -> float:
        monitor = SemanticExposureMonitor(self.runtime)
        try:
            return monitor.measure_exposure()
        except ConstitutionalError:
            return 0.0

    def _commit_constitutional(
        self,
        action: dict[str, Any],
        header: GovernanceReceiptHeader,
        apply_fn: Callable[[dict[str, Any]], None],
        *,
        require_redteam: bool = True,
    ) -> GovernanceReceiptHeader:
        self._pending_apply = apply_fn
        try:
            self.commit_gate.commit_action(
                action,
                header.to_dict(),
                require_redteam=require_redteam,
            )
        finally:
            self._pending_apply = None
        self.last_receipt_header = header
        return header

    def _build_receipt(
        self,
        *,
        action_type: str,
        identity: str,
        context: dict[str, Any],
        decision_summary: str,
        evidence_refs: list[str],
        include_redteam: bool = True,
    ) -> GovernanceReceiptHeader:
        return build_governance_receipt_header(
            self.runtime,
            action_type=action_type,
            actor_identity=identity,
            context=context,
            decision_summary=decision_summary,
            evidence_refs=evidence_refs,
            validator=self.validator,
            include_redteam=include_redteam,
        )

    # ------------------------------------------------------------
    # Proposal Phase
    # ------------------------------------------------------------

    def propose(self, identity: str, proposal: dict[str, Any]) -> Any:
        """
        proposal = {
            "type": "policy" | "amendment" | "parameter_change",
            "content": {...},
            "justification": "...",
            "evidence_ids": [...]
        }
        """
        evidence_ids = list(proposal.get("evidence_ids") or [])
        if not evidence_ids:
            raise ConstitutionalError("Governance proposal requires evidence_ids")
        decision = self.runtime.create_decision(
            identity=identity,
            evidence=evidence_ids,
            payload=proposal,
        )
        self.runtime.save_decision(decision)
        return decision

    # ------------------------------------------------------------
    # Deliberation Phase
    # ------------------------------------------------------------

    def deliberate(self, decision_id: str, reviewers: list[dict[str, Any]]) -> bool:
        """Reviewers attach evidence, arguments, or counterarguments."""
        for reviewer in reviewers:
            self.runtime.attach_review(decision_id, reviewer)
        return True

    # ------------------------------------------------------------
    # Ratification Phase
    # ------------------------------------------------------------

    def ratify(self, decision_id: str) -> tuple[CRK1Outcome, CRK1Evidence]:
        decision = self.runtime.load_decision(decision_id)
        ce_before = consequence_exposure(self.runtime)
        se_before = self._se_snapshot()

        pre_context: dict[str, Any] = {
            "from_state": "ApprovedDecision",
            "to_state": "ExecutedDecision",
            "decision": decision,
            "identity": decision.identity_id,
            "evidence_pool": self.runtime.get_all_evidence(),
            "attempted_operation": None,
            "identity_present": True,
            "evidence_present": bool(decision.evidence_refs),
            "governance_approval": True,
            "create_outcome": True,
            "ce_before": ce_before,
            "ce_after": ce_before,
            "se_before": se_before,
            "se_after": se_before,
        }
        self.validator.validate(pre_context)

        header = self._build_receipt(
            action_type="governance_decision",
            identity=decision.identity_id,
            context=pre_context,
            decision_summary=f"Ratified decision {decision_id}",
            evidence_refs=list(decision.evidence_refs),
        )

        outcome_holder: dict[str, CRK1Outcome | CRK1Evidence] = {}

        def apply_ratify(_action: dict[str, Any]) -> None:
            outcome = self.runtime.execute_decision(decision_id)
            evidence = self.runtime.replay_outcome(outcome.id)
            post_context = {
                **pre_context,
                "outcome": outcome,
                "evidence": evidence,
            }
            self.validator.validate(post_context)
            outcome_holder["outcome"] = outcome
            outcome_holder["evidence"] = evidence

        self._commit_constitutional(
            {"kind": "governance_decision", "decision_id": decision_id},
            header,
            apply_ratify,
        )
        return outcome_holder["outcome"], outcome_holder["evidence"]  # type: ignore[return-value]

    # ------------------------------------------------------------
    # Amendment Phase (Consequence Preservation Gate)
    # ------------------------------------------------------------

    def amend(self, identity: str, amendment: dict[str, Any]) -> tuple[CRK1Outcome, CRK1Evidence]:
        """
        amendment = {
            "type": "amendment",
            "changes": {...},
            "evidence_ids": [...],
            "justification": "..."
        }
        """
        changes = amendment.get("changes") or {}
        proposal = {
            "type": "amendment",
            "content": changes,
            "justification": amendment.get("justification", "constitutional amendment"),
            "evidence_ids": list(amendment.get("evidence_ids") or []),
        }

        if not mutation_admissible(changes):
            raise ConstitutionalError(
                "K5 violation: amendment inadmissible — reduces consequence exposure",
            )
        validate_consequence_preservation(self.runtime, changes=changes)

        decision = self.propose(identity, proposal)
        outcome = self.runtime.execute_decision(decision.id)
        evidence = self.runtime.replay_outcome(outcome.id)

        ce_before = consequence_exposure(self.runtime)
        se_before = self._se_snapshot()

        pre_context: dict[str, Any] = {
            "from_state": "OutcomeReplayed",
            "to_state": "EvidenceAdmitted",
            "decision": decision,
            "outcome": outcome,
            "evidence": evidence,
            "identity": identity,
            "evidence_pool": self.runtime.get_all_evidence(),
            "attempted_operation": None,
            "constitutional_change": changes,
            "ce_before": ce_before,
            "ce_after": ce_before,
            "identity_present": True,
            "evidence_present": True,
            "governance_approval": True,
            "create_outcome": True,
            "outcome_replayable": True,
            "evidence_admissible": True,
            "se_before": se_before,
            "se_after": se_before,
        }
        self.validator.validate(pre_context)

        header = self._build_receipt(
            action_type="mutation",
            identity=identity,
            context=pre_context,
            decision_summary=str(amendment.get("justification") or "constitutional amendment"),
            evidence_refs=list(amendment.get("evidence_ids") or []),
        )

        def apply_amendment(_action: dict[str, Any]) -> None:
            apply_amendment_with_drift_check(self.runtime, _action["changes"])

        self._commit_constitutional(
            {"kind": "mutation", "changes": changes},
            header,
            apply_amendment,
        )
        return outcome, evidence

    def _preserves_consequence_flow(self, amendment: dict[str, Any]) -> bool:
        """K4/K5 compatibility — delegates to mutation_admissible."""
        return mutation_admissible(amendment.get("changes") or {})
