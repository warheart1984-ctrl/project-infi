# CRK-1 Runtime Validator
# Version 1.0

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import yaml

from src.crk1.errors import ConstitutionalError

LineageResolver = Callable[[Any], Sequence[str]]

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_MACHINE_PATH = REPO_ROOT / "docs" / "crk1" / "crk1_state_machine.json"
DEFAULT_INVARIANTS_PATH = REPO_ROOT / "docs" / "crk1" / "crk1_invariants.yaml"

_K0_STATES = frozenset({"OutcomeRecorded", "OutcomeReplayed", "EvidenceAdmitted"})


class CRK1RuntimeValidator:
    def __init__(
        self,
        state_machine_path: str | Path | None = None,
        invariants_path: str | Path | None = None,
        lineage_resolver: LineageResolver | None = None,
    ) -> None:
        sm_path = Path(state_machine_path or DEFAULT_STATE_MACHINE_PATH)
        inv_path = Path(invariants_path or DEFAULT_INVARIANTS_PATH)
        with sm_path.open(encoding="utf-8") as handle:
            self.state_machine: dict[str, Any] = json.load(handle)
        self.invariants = self._load_yaml(inv_path)
        self.lineage_resolver = lineage_resolver or self._default_lineage_resolver

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
        if not isinstance(loaded, dict):
            raise ValueError(f"Invalid invariants file: {path}")
        return loaded

    @staticmethod
    def _default_lineage_resolver(identity: Any) -> list[str]:
        if identity is None:
            return []
        if isinstance(identity, str):
            return [identity]
        identity_id = getattr(identity, "id", None)
        ancestors = getattr(identity, "ancestors", None)
        if isinstance(ancestors, (list, tuple)):
            lineage = [str(item) for item in ancestors]
            if identity_id is not None:
                lineage.append(str(identity_id))
            return lineage or ([str(identity_id)] if identity_id else [])
        if identity_id is not None:
            return [str(identity_id)]
        return []

    # ------------------------------------------------------------
    # State Machine Validation
    # ------------------------------------------------------------

    def validate_transition(self, from_state: str, to_state: str, context: dict[str, Any]) -> None:
        allowed = [
            transition
            for transition in self.state_machine.get("transitions", [])
            if transition.get("from") == from_state and transition.get("to") == to_state
        ]

        if not allowed:
            raise ConstitutionalError(f"Invalid transition: {from_state} → {to_state}")

        transition = allowed[0]
        for cond in transition.get("conditions", []):
            if not context.get(cond, False):
                raise ConstitutionalError(f"Transition condition failed: {cond}")

    def is_forbidden_transition(self, rule: str) -> bool:
        forbidden = self.state_machine.get("forbidden_transitions") or []
        return any(str(item.get("rule")) == rule for item in forbidden)

    # ------------------------------------------------------------
    # Invariant Validation
    # ------------------------------------------------------------

    def validate_k0(self, decision: Any, outcome: Any, evidence: Any) -> None:
        if outcome is None:
            raise ConstitutionalError("K0 violation: Decision must produce Outcome")

        replayable = getattr(outcome, "replayable", None)
        if replayable is not True:
            raise ConstitutionalError("K0 violation: Outcome must be replayable")

        if evidence is None:
            raise ConstitutionalError("K0 violation: Replay must yield Evidence")

        admissible = getattr(evidence, "admissible_for_decision", True)
        if admissible is not True:
            raise ConstitutionalError("K0 violation: Evidence must be admissible")

        if decision is None:
            raise ConstitutionalError("K0 violation: Outcome requires originating Decision")

    def validate_k1(self, attempted_operation: str | None) -> None:
        if not attempted_operation:
            return

        invs = self.invariants.get("invariants") or {}
        k1 = invs.get("K1_ImmutableExposure") or invs.get("K1_ImmutableExposureConstraint") or {}
        forbidden = [
            str(check.get("rule"))
            for check in k1.get("checks", [])
            if check.get("type") == "forbidden_operation" and check.get("rule")
        ]

        if attempted_operation in forbidden:
            raise ConstitutionalError(f"K1 violation: {attempted_operation}")

        if self.is_forbidden_transition(attempted_operation):
            raise ConstitutionalError(f"K1 violation: {attempted_operation}")

    def validate_k2(self, decision: Any, identity: Any, evidence_pool: Sequence[Any]) -> None:
        identity_id = getattr(decision, "identity_id", None)
        if identity_id is None:
            raise ConstitutionalError("K2 violation: Decision requires Identity")

        evidence_ids = getattr(decision, "input_evidence_ids", None)
        if evidence_ids is None:
            evidence_ids = getattr(decision, "evidence_refs", []) or []

        if not evidence_ids:
            raise ConstitutionalError("K2 violation: Decision requires Evidence")

        lineage = set(self.lineage_resolver(identity))
        if not lineage:
            lineage = {str(identity_id)}

        for item in evidence_pool:
            source = getattr(item, "source_identity_id", None)
            if source is not None and str(source) in lineage:
                return

        if not evidence_pool:
            return

        raise ConstitutionalError("K2 violation: Lineage must inherit ancestor Evidence")

    def validate_k3(self, identity: Any, evidence: Any) -> None:
        lineage = set(self.lineage_resolver(identity))
        source = getattr(evidence, "source_identity_id", None)
        if source is None or str(source) not in lineage:
            raise ConstitutionalError("K3 violation: lineage escape detected")

    # ------------------------------------------------------------
    # Unified Validation Entry Point
    # ------------------------------------------------------------

    def validate(self, context: dict[str, Any]) -> bool:
        """
        context = {
            "from_state": ...,
            "to_state": ...,
            "decision": ...,
            "outcome": ...,
            "evidence": ...,
            "identity": ...,
            "evidence_pool": ...,
            "attempted_operation": ...,
            # transition condition flags:
            "identity_present": bool,
            "evidence_present": bool,
            "governance_approval": bool,
            "create_outcome": bool,
            "outcome_replayable": bool,
            "evidence_admissible": bool,
        }
        """

        from_state = str(context["from_state"])
        to_state = str(context["to_state"])

        self.validate_transition(from_state, to_state, context)

        if to_state in _K0_STATES or context.get("outcome") is not None:
            self.validate_k0(
                context.get("decision"),
                context.get("outcome"),
                context.get("evidence"),
            )

        if context.get("attempted_operation"):
            self.validate_k1(str(context["attempted_operation"]))

        if context.get("decision") is not None:
            self.validate_k2(
                context["decision"],
                context.get("identity"),
                context.get("evidence_pool") or [],
            )

        if context.get("evidence") is not None:
            self.validate_k3(context.get("identity"), context["evidence"])

        if context.get("constitutional_change") is not None:
            self.validate_k4(context)
            self.validate_k5(context["constitutional_change"])
            if context.get("ce_before") is not None and context.get("ce_after") is not None:
                self.validate_k6(context["ce_before"], context["ce_after"])

        return True

    def validate_k4(self, context: dict[str, Any]) -> None:
        """K4 — Consequence Preservation Law."""
        changes = context.get("constitutional_change") or {}
        if changes.get("block_consequence_propagation") is True:
            raise ConstitutionalError("K4 violation: blocks consequence propagation")
        if changes.get("insulate_judgment_from_outcomes") is True:
            raise ConstitutionalError("K4 violation: insulates judgment from outcomes")
        outcome = context.get("outcome")
        evidence = context.get("evidence")
        if outcome is not None and evidence is not None:
            self.validate_k0(context.get("decision"), outcome, evidence)

    def validate_k5(self, changes: dict[str, Any]) -> None:
        """K5 — Mutation Admissibility Test."""
        from src.crk1.consequence_lattice import assert_mutation_admissible

        assert_mutation_admissible(changes)

    def validate_k6(self, ce_before: Any, ce_after: Any) -> None:
        """K6 — Constitutional Drift Envelope."""
        from src.crk1.consequence_lattice import validate_drift_envelope

        validate_drift_envelope(ce_before, ce_after)

    def get_invariant_checks(self, invariant_key: str) -> list[dict[str, Any]]:
        """Return machine-readable checks for CI / dashboard consumers."""
        inv = (self.invariants.get("invariants") or {}).get(invariant_key) or {}
        checks = inv.get("checks")
        return list(checks) if isinstance(checks, list) else []

    def list_forbidden_operations(self) -> list[str]:
        """All forbidden_operation rules from K1 and K3 invariants."""
        invs = self.invariants.get("invariants") or {}
        rules: list[str] = []
        for key in ("K1_ImmutableExposure", "K1_ImmutableExposureConstraint", "K3_AntiInsulation"):
            for check in self.get_invariant_checks(key):
                if check.get("type") == "forbidden_operation" and check.get("rule"):
                    rules.append(str(check["rule"]))
        return rules

    @staticmethod
    def replay_hash(outcome_id: str, evidence_id: str) -> str:
        body = f"{outcome_id}:{evidence_id}".encode()
        return hashlib.sha256(body).hexdigest()[:16]
