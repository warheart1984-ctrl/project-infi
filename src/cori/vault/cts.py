"""CTS-1.0 — Continuity OS Trust Boundary Specification."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.cori.vault.models import CTS_VERSION, BoneKingProofPackage

FORBIDDEN_BOUNDARIES = [
    "founder_interpretation",
    "institutional_memory",
    "narrative_explanation",
    "external_data_source",
    "non_deterministic_computation",
    "hidden_state",
]


class TrustBoundary(str, Enum):
    """Constitutionally permitted trust boundaries (CTS-1.0)."""

    IDENTITY = "TB-1"
    EVIDENCE = "TB-2"
    REPRODUCTION = "TB-3"


@dataclass
class BoundaryCheckResult:
    passed: bool
    boundaries_crossed: list[TrustBoundary] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


class BoundaryViolationError(RuntimeError):
    """Raised when a continuity package crosses a forbidden trust boundary."""

    def __init__(self, violations: list[str], *, details: dict[str, Any] | None = None) -> None:
        self.violations = violations
        self.details = details or {}
        message = f"CTS-{CTS_VERSION} boundary violation: {', '.join(violations)}"
        super().__init__(message)


@dataclass
class SafeguardState:
    active: bool
    quarantined_chains: list[str] = field(default_factory=list)
    violation_log: list[dict[str, Any]] = field(default_factory=list)


def validate_package_boundaries(package: BoneKingProofPackage) -> BoundaryCheckResult:
    """
  Verify package only crosses TB-1 (identity via actor_id), TB-2 (evidence hash),
  and TB-3 (replay verification). Reject hidden or non-deterministic artifacts.
    """
    artifacts = package.artifacts
    violations: list[str] = []

    if not artifacts.event.actor_id:
        violations.append("TB-1: missing actor identity")
    if not artifacts.memory.event_hash:
        violations.append("TB-2: missing canonical event hash")
    if artifacts.verification.method.startswith("verify_world_claim"):
        pass
    else:
        violations.append("TB-3: verification must use deterministic replay")

    if artifacts.verification.status != "verified":
        violations.append("TB-3: reproduction boundary failed — claim not verified")

    for forbidden in FORBIDDEN_BOUNDARIES:
        raw = artifacts.memory.raw
        if forbidden.replace("_", " ") in str(raw).lower():
            violations.append(f"forbidden boundary signal: {forbidden}")

    boundaries = [TrustBoundary.IDENTITY, TrustBoundary.EVIDENCE, TrustBoundary.REPRODUCTION]
    return BoundaryCheckResult(
        passed=len(violations) == 0,
        boundaries_crossed=boundaries if not violations else [],
        violations=violations,
        details={"spec": CTS_VERSION, "package_id": package.id},
    )


def enforce_package_boundaries(package: BoneKingProofPackage) -> BoundaryCheckResult:
    result = validate_package_boundaries(package)
    if not result.passed:
        raise BoundaryViolationError(result.violations, details=result.details)
    return result


def handle_boundary_violation(
    chain_id: str,
    violations: list[str],
    *,
    safeguard: SafeguardState | None = None,
) -> SafeguardState:
    """CTS violation protocol: log, quarantine chain, enter safeguard mode."""
    state = safeguard or SafeguardState(active=False)
    entry = {
        "chain_id": chain_id,
        "violations": violations,
        "action": "quarantine",
    }
    state.violation_log.append(entry)
    if chain_id not in state.quarantined_chains:
        state.quarantined_chains.append(chain_id)
    state.active = True
    return state
