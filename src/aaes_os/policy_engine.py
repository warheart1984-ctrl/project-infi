"""PolicyEngine — allow / block / warn before governed execution."""

# Mythic: Governance & Invariants layer
# Engineering: PolicyEngine
from __future__ import annotations

from src.aaes_os.pipeline_types import AAESContext, AAESDecision, AAESRequest, PolicyVerdict


class PolicyEngine:
    """Minimal policy surface; production may load hashes from RuntimeContext."""

    def __init__(self, *, deny_operations: frozenset[str] | None = None) -> None:
        self._deny_operations = deny_operations or frozenset(
            {"destructive_reset", "force_push"}
        )

    def evaluate(
        self,
        request: AAESRequest,
        context: AAESContext | None = None,
    ) -> AAESDecision:
        if not isinstance(request, AAESRequest):
            raise TypeError("request must be AAESRequest")

        request.validate()
        metadata = dict(request.metadata or {})
        operation = str(metadata.get("operation") or "execute").strip()

        if metadata.get("policy_block") is True:
            return AAESDecision(
                verdict=PolicyVerdict.BLOCK,
                reason="explicit policy_block in request metadata",
                policy_id="metadata_block",
                payload={"operation": operation},
            )

        if operation in self._deny_operations:
            return AAESDecision(
                verdict=PolicyVerdict.BLOCK,
                reason=f"operation denied by policy: {operation}",
                policy_id="deny_list",
                payload={"operation": operation},
            )

        if metadata.get("policy_warn") is True:
            return AAESDecision(
                verdict=PolicyVerdict.WARN,
                reason="policy_warn flag set; proceeding with caution",
                policy_id="warn_flag",
                payload={"operation": operation},
            )

        scope = str(metadata.get("scope") or "default")
        if context is not None and scope == "out_of_bounds":
            return AAESDecision(
                verdict=PolicyVerdict.BLOCK,
                reason="scope out_of_bounds",
                policy_id="scope_boundary",
                payload={"scope": scope},
            )

        return AAESDecision(
            verdict=PolicyVerdict.ALLOW,
            reason="default allow",
            policy_id="default",
            payload={"operation": operation},
        )
