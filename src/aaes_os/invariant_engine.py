"""InvariantEngine — maps architecture invariants to RFC INV-1..7 checks."""

# Mythic: Governance & Invariants layer
# Engineering: InvariantEngine
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.aaes_os.errors import AaesOsValidationError
from src.aaes_os.models import AuthEnvelope, RuntimeContext, TraceEvent
from src.aaes_os.pipeline_types import AAESRequest, AAESStep

# Back-compat alias for span-level RFC engine naming
AaesInvariantEngine = None  # set after class definition


@dataclass(frozen=True, slots=True)
class InvariantCheckResult:
    ok: bool
    code: str | None = None
    message: str | None = None


ARCHITECTURE_TO_RFC: dict[str, tuple[str, ...]] = {
    "traceability": ("INV-1", "INV-2"),
    "integrity_of_state": ("INV-3", "INV-5"),
    "identity_and_auth": ("INV-1",),
    "scope_and_boundaries": ("INV-7",),
    "explainability_hook": ("INV-6",),
    "reversibility_failsafe": ("INV-6",),
    "governance_first": ("INV-7",),
}

RFC_TO_ARCHITECTURE: dict[str, str] = {
    "INV-1": "identity_and_auth",
    "INV-2": "traceability",
    "INV-3": "integrity_of_state",
    "INV-4": "integrity_of_state",
    "INV-5": "integrity_of_state",
    "INV-6": "reversibility_failsafe",
    "INV-7": "governance_first",
}


class InvariantEngine:
    """Pre-flight invariant checks before orchestrator stages run."""

    def check(
        self,
        *,
        request: AAESRequest,
        runtime_context: RuntimeContext,
        steps: list[AAESStep] | None = None,
        pending_event: TraceEvent | None = None,
    ) -> InvariantCheckResult:
        if not isinstance(request, AAESRequest):
            raise TypeError("request must be AAESRequest")
        if not isinstance(runtime_context, RuntimeContext):
            raise TypeError("runtime_context must be RuntimeContext")

        try:
            request.validate()
            runtime_context.validate()
        except ValueError as exc:
            return InvariantCheckResult(False, "AAES_INVARIANT_VIOLATION", str(exc))

        if request.metadata.get("force_invariant_block"):
            return InvariantCheckResult(
                False,
                "AAES_INVARIANT_VIOLATION",
                "request metadata force_invariant_block set",
            )

        if steps is not None:
            explain_steps = [row for row in steps if row.step_type.value == "explain"]
            if steps and not explain_steps and any(
                row.step_type.value == "action" for row in steps
            ):
                return InvariantCheckResult(
                    False,
                    "AAES_INVARIANT_VIOLATION",
                    "explainability hook missing after action stage",
                )

        if pending_event is not None:
            auth_result = self._check_auth(pending_event.auth)
            if not auth_result.ok:
                return auth_result
            if pending_event.event_type.value == "RESULT":
                rollback = pending_event.payload.get("rollback_possible")
                if rollback is None:
                    return InvariantCheckResult(
                        False,
                        "AAES_INVARIANT_VIOLATION",
                        "RESULT payload missing rollback_possible (INV-6)",
                    )

        return InvariantCheckResult(True)

    def check_or_raise(self, **kwargs: Any) -> InvariantCheckResult:
        result = self.check(**kwargs)
        if not result.ok:
            raise AaesOsValidationError(
                result.code or "AAES_INVARIANT_VIOLATION",
                result.message or "invariant check failed",
            )
        return result

    @staticmethod
    def _check_auth(auth: AuthEnvelope) -> InvariantCheckResult:
        try:
            auth.validate()
        except ValueError as exc:
            return InvariantCheckResult(False, "AAES_AUTH_MISSING", str(exc))
        return InvariantCheckResult(True)

    @staticmethod
    def architecture_mapping() -> dict[str, tuple[str, ...]]:
        return dict(ARCHITECTURE_TO_RFC)


AaesInvariantEngine = InvariantEngine
