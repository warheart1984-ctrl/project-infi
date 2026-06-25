"""CRK-1 Constitutional Kernel API — law layer constraining all layers."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.identity_object import DEFAULT_IDENTITY, IdentityObject
from src.kernel.governance import Governance


class ConstitutionalSnapshot(BaseModel):
    identity: str
    invariants: list[str] = Field(default_factory=list)
    authority_model: dict[str, dict[str, list[str]]] = Field(default_factory=dict)
    kernel_version: int = 1
    amendment_procedures: list[str] = Field(default_factory=list)


class InvariantCheckResult(BaseModel):
    allowed: bool
    violations: list[str] = Field(default_factory=list)


class AmendmentResult(BaseModel):
    proposed: bool
    ratified: bool
    kernel_version: int


class CRK1Kernel:
    """
    Layer 3 — Constitutional Kernel (CRK-1).

    Defines identity, invariants, governance rules, and amendment procedures.
    Constrains RA-COS-1 and AAIS from below.
    """

    def __init__(self, identity: IdentityObject | None = None) -> None:
        self._identity = identity or DEFAULT_IDENTITY

    def get_constitution(self) -> ConstitutionalSnapshot:
        gov = Governance.current()
        return ConstitutionalSnapshot(
            identity=self._identity.id,
            invariants=list(self._identity.invariants),
            authority_model=dict(self._identity.authority_model),
            kernel_version=gov.current_kernel_version(),
            amendment_procedures=[
                "propose_kernel_amendment with insufficiency signal",
                "White Team ratification required",
                "CRK-T2 ledger entry on ratify",
            ],
        )

    def check_invariant(
        self,
        *,
        actor_id: str,
        intent: str,
        decision_type: str = "execute",
    ) -> InvariantCheckResult:
        """Check whether an intent violates constitutional invariants."""
        violations: list[str] = []
        intent_lower = intent.lower()

        destructive_markers = ("delete all", "wipe", "reset the board", "bypass governance", "skip validation")
        for marker in destructive_markers:
            if marker in intent_lower:
                violations.append(f"Destructive or ungoverned action detected: {marker}")

        if "delete" in intent_lower and "confirm" not in intent_lower:
            violations.append("Deletion requires explicit confirmation")

        blocked_phrases = ("ignore invariants", "disable crk", "override constitution")
        for phrase in blocked_phrases:
            if phrase in intent_lower:
                violations.append(f"Blocked phrase detected: {phrase}")

        roles = self._identity.authority_model.get(actor_id) or {}
        allowed = list(roles.get("approve") or []) + list(roles.get("execute") or [])
        if actor_id != "system" and allowed and decision_type not in allowed and "*" not in allowed:
            violations.append(
                f"Actor {actor_id} lacks authority for {decision_type}"
            )

        return InvariantCheckResult(allowed=not violations, violations=violations)

    def apply_amendment(
        self,
        *,
        reason: str,
        signals: list[float],
        insufficiency: float,
        ratify: bool = False,
    ) -> AmendmentResult:
        """Propose or ratify a kernel amendment via CRK-T2."""
        ratified = Governance.current().propose_kernel_amendment(
            reason=reason,
            signals=signals,
            insufficiency=insufficiency,
            ratify=ratify,
        )
        return AmendmentResult(
            proposed=True,
            ratified=ratified,
            kernel_version=Governance.current().current_kernel_version(),
        )

    def block_output(self, text: str) -> InvariantCheckResult:
        """Post-LLM constitutional check on generated output."""
        return self.check_invariant(
            actor_id="system",
            intent=text,
            decision_type="emit",
        )
