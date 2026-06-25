"""GovernanceEnforcementEngine — invariant checks across strata (TS mirror)."""

from __future__ import annotations

from governed_memory.authority_ledger import AuthorityLedger
from governed_memory.intent_ledger import IntentLedger
from governed_memory.types import ExecutionTrace

DRIFT_THRESHOLD = 0.35


class GovernanceEnforcementEngine:
    def __init__(
        self,
        intent_ledger: IntentLedger,
        authority_ledger: AuthorityLedger,
    ) -> None:
        self._intent = intent_ledger
        self._authority = authority_ledger

    def check_intent_alignment(self, intent_version: int, step_goal_hint: str | None = None) -> None:
        intent = self._intent.get_version(intent_version)
        if not intent:
            raise ValueError("INTENT_DRIFT: unknown intent version")
        if not self._intent.verify_chain():
            raise ValueError("INTENT_DRIFT: intent ledger chain invalid")
        # Soft semantic placeholder — mirrors TS (embedding/symbolic diff deferred).
        if step_goal_hint and intent.semantic_goal:
            prefix = intent.semantic_goal[:8]
            if prefix and prefix not in step_goal_hint:
                pass

    def validate_authority(self, token_id: str, capability: str) -> None:
        ok, reason = self._authority.validate(token_id, capability)
        if not ok:
            if reason == "revoked":
                raise ValueError("AUTHORITY_FAULT: revoked")
            raise ValueError(f"AUTHORITY_INVALID: {reason or 'denied'}")

    def validate_authority_binding(self, token_id: str, intent_version: int) -> None:
        """Ensure token exists, is not revoked, and is bound to the intent version."""
        token = self._authority.get(token_id)
        if not token:
            raise ValueError("AUTHORITY_INVALID: missing_token")
        if token.revoked:
            raise ValueError("AUTHORITY_FAULT: revoked")
        if token.scope.intent_version != intent_version:
            raise ValueError("AUTHORITY_INVALID: intent_version_mismatch")

    def validate_trace_step(self, step: ExecutionTrace) -> None:
        if not step.justification.strip():
            raise ValueError("EXECUTION_UNGOVERNED: missing justification")
        self.check_intent_alignment(step.references.intent_version, step.content)
        self.validate_authority_binding(
            step.references.authority_token_id,
            step.references.intent_version,
        )
