"""CRK-1 Governance Receipt Header — constitutional block header (v1.0)."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID

from src.crk1.attack_simulator import InsulationAttackSimulator
from src.crk1.consequence_lattice import ConsequenceExposure, consequence_exposure
from src.crk1.errors import ConstitutionalError
from src.crk1.schema_validator import CRK1SchemaValidator, SchemaValidationError
from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor

if TYPE_CHECKING:
    from src.crk1.runtime_facade import CRK1Runtime
    from src.crk1.runtime_validator import CRK1RuntimeValidator

RUNTIME_VERSION = "CRK-1 v1.0"
CRK1_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

REDTEAM_BUCKETS: dict[str, tuple[str, ...]] = {
    "B1": ("drop_outcome", "non_replayable_outcome"),
    "B2": ("quarantine_evidence",),
    "B3": ("fork_without_history",),
    "B4": ("decision_without_evidence", "replay_bypass"),
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def crk1_uuid(value: str) -> str:
    """Map any identity/evidence id to a stable RFC-4122 UUID for receipt headers."""
    try:
        UUID(str(value))
        return str(value)
    except ValueError:
        return str(uuid.uuid5(CRK1_NAMESPACE, f"crk1:{value}"))


def _sha256_hex(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(encoded).hexdigest().upper()


def compute_kernel_state_hash(runtime: CRK1Runtime) -> str:
    kernel = runtime.kernel
    payload = {
        "epoch": kernel.ledgers.epoch,
        "identity_id": kernel.ledgers.identity.id,
        "decision_count": len(kernel.decisions.list_decisions()),
        "outcome_count": len(runtime.get_all_outcomes()),
        "amendment_count": len(runtime._amendments),  # noqa: SLF001
    }
    return _sha256_hex(payload)


def compute_ledger_state_hash(runtime: CRK1Runtime) -> str:
    decisions = sorted(record.id for record in runtime.kernel.decisions.list_decisions())
    outcomes = sorted(item.id for item in runtime.get_all_outcomes())
    evidence = sorted(item.id for item in runtime.get_all_evidence())
    return _sha256_hex(
        {
            "decisions": decisions,
            "outcomes": outcomes,
            "evidence": evidence,
        }
    )


def run_redteam_status(runtime: CRK1Runtime, identity_id: str) -> dict[str, Any]:
    """Map insulation attack suite to B1–B4 buckets."""
    report = InsulationAttackSimulator(runtime).run_all(identity_id)
    attacks_run = list(REDTEAM_BUCKETS.keys())
    all_blocked = True
    for bucket, attack_keys in REDTEAM_BUCKETS.items():
        for key in attack_keys:
            result = report.get(key)
            if result is None or result[1] != "PASS":
                all_blocked = False
                break
    return {
        "attacks_run": attacks_run,
        "all_blocked": "YES" if all_blocked else "NO",
    }


def assess_invariants_checked(context: dict[str, Any]) -> dict[str, str]:
    """Collapse validator context into receipt invariant layers (v1.2 includes K13–K15, KΩ)."""
    if context.get("constitutional_error"):
        message = str(context["constitutional_error"])
        k0_k2 = "FAIL" if message.startswith(("K0", "K1", "K2")) else "PASS"
        k3_k6 = "FAIL" if message.startswith(("K3", "K4", "K5", "K6")) else "PASS"
        k7_k12 = "FAIL" if message.startswith(("K7", "K8", "K9", "K10", "K11", "K12", "Semantic")) else "PASS"
        k13_k15 = "FAIL" if message.startswith(("K13", "K14", "K15", "RDI", "Reality")) else "PASS"
        k_omega = "FAIL" if message.startswith(("KΩ", "Kernel Challenge")) else "PASS"
        if not context.get("transition_ok", True):
            k0_k2 = "FAIL"
        return {
            "K0_K2": k0_k2,
            "K3_K6": k3_k6,
            "K7_K12": k7_k12,
            "K13_K15": k13_k15,
            "KΩ": k_omega,
        }

    k0_k2 = "PASS" if context.get("transition_ok", True) else "FAIL"

    ce_before = context.get("ce_before")
    ce_after = context.get("ce_after")
    k3_k6 = "PASS"
    if ce_before is not None and ce_after is not None:
        if _exposure_score(ce_after) + 1e-9 < _exposure_score(ce_before):
            k3_k6 = "FAIL"

    se_before = context.get("se_before")
    se_after = context.get("se_after")
    k7_k12 = "PASS"
    if se_before is not None and se_after is not None and float(se_after) + 1e-9 < float(se_before):
        k7_k12 = "FAIL"

    k13_k15 = "PASS" if context.get("rcl_ok", True) else "FAIL"
    k_omega = "PASS" if context.get("komega_ok", True) else "FAIL"

    return {
        "K0_K2": k0_k2,
        "K3_K6": k3_k6,
        "K7_K12": k7_k12,
        "K13_K15": k13_k15,
        "KΩ": k_omega,
    }


def _exposure_score(value: Any) -> float:
    if isinstance(value, ConsequenceExposure):
        return float(value.score)
    if hasattr(value, "score"):
        return float(value.score)
    if value is None:
        return 0.0
    return float(value)


def _drift_metrics(context: dict[str, Any]) -> dict[str, float]:
    ce_b = _exposure_score(context.get("ce_before"))
    ce_a = _exposure_score(context.get("ce_after"))
    if context.get("ce_after") is None:
        ce_a = ce_b
    se_b = float(context.get("se_before") if context.get("se_before") is not None else 0.0)
    se_a = float(context.get("se_after") if context.get("se_after") is not None else se_b)

    return {
        "CE_before": ce_b,
        "CE_after": ce_a,
        "SE_before": se_b,
        "SE_after": se_a,
    }


def _sign_header(header: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in header.items() if key != "signatures"}
    digest = _sha256_hex(unsigned)
    return f"0x{digest[:8]}...{digest[-8:]}"


@dataclass
class GovernanceReceiptHeader:
    """Wire-format governance receipt header (schema v1.0 / v1.2)."""

    receipt_id: str
    runtime_version: str
    action_type: str
    actor_identity: str
    timestamp: str
    kernel_state_hash: str
    ledger_state_hash: str
    invariants_checked: dict[str, str]
    drift_metrics: dict[str, float]
    redteam_status: dict[str, Any]
    decision_summary: str
    evidence_refs: list[str] = field(default_factory=list)
    signatures: dict[str, str] = field(default_factory=dict)
    epoch: int = 1
    invariant_context: list[str] = field(default_factory=list)
    linked_grr_ids: list[str] = field(default_factory=list)
    kernel_challenge_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "receipt_id": self.receipt_id,
            "runtime_version": self.runtime_version,
            "epoch": self.epoch,
            "action_type": self.action_type,
            "actor_identity": self.actor_identity,
            "timestamp": self.timestamp,
            "kernel_state_hash": self.kernel_state_hash,
            "ledger_state_hash": self.ledger_state_hash,
            "invariants_checked": dict(self.invariants_checked),
            "drift_metrics": dict(self.drift_metrics),
            "redteam_status": dict(self.redteam_status),
            "decision_summary": self.decision_summary,
            "evidence_refs": list(self.evidence_refs),
            "signatures": dict(self.signatures),
        }
        if self.invariant_context:
            payload["invariant_context"] = list(self.invariant_context)
        if self.linked_grr_ids:
            payload["linked_grr_ids"] = list(self.linked_grr_ids)
        if self.kernel_challenge_refs:
            payload["kernel_challenge_refs"] = list(self.kernel_challenge_refs)
        return payload

    @classmethod
    def from_decision(
        cls,
        steward_id: str,
        decision: Any,
        invariant_context: list[str] | None = None,
        epoch: int = 1,
    ) -> GovernanceReceiptHeader:
        """Lightweight receipt for LLM / agent decisions without full runtime."""
        import json

        summary = decision if isinstance(decision, str) else json.dumps(decision, default=str)
        decision_hash = _sha256_hex(decision)
        context = {"transition_ok": True, "rcl_ok": True, "komega_ok": True}
        header_body = {
            "receipt_id": str(uuid.uuid4()),
            "runtime_version": RUNTIME_VERSION,
            "epoch": epoch,
            "action_type": "llm_decision",
            "actor_identity": crk1_uuid(steward_id),
            "timestamp": _now_iso(),
            "kernel_state_hash": decision_hash,
            "ledger_state_hash": decision_hash,
            "invariants_checked": assess_invariants_checked(context),
            "drift_metrics": {"CE_before": 0.0, "CE_after": 0.0, "SE_before": 0.0, "SE_after": 0.0},
            "redteam_status": {"attacks_run": [], "all_blocked": "YES"},
            "decision_summary": summary[:500],
            "evidence_refs": [],
            "invariant_context": list(invariant_context or []),
            "linked_grr_ids": [],
            "kernel_challenge_refs": [],
            "signatures": {},
        }
        header_body["signatures"] = {"governance_body": _sign_header(header_body)}
        return cls(**header_body)


def build_governance_receipt_header(
    runtime: CRK1Runtime,
    *,
    action_type: str,
    actor_identity: str,
    context: dict[str, Any],
    decision_summary: str,
    evidence_refs: list[str],
    validator: CRK1RuntimeValidator | None = None,
    include_redteam: bool = True,
    epoch: int | None = None,
    invariant_context: list[str] | None = None,
    linked_grr_ids: list[str] | None = None,
    kernel_challenge_refs: list[str] | None = None,
) -> GovernanceReceiptHeader:
    """Build a receipt header from a validated governance context."""
    identity_id = str(actor_identity)
    ce_before = context.get("ce_before")
    if ce_before is None:
        ce_before = consequence_exposure(runtime)
        context = {**context, "ce_before": ce_before, "ce_after": ce_before}

    monitor = SemanticExposureMonitor(runtime)
    if context.get("se_before") is None:
        try:
            context = {**context, "se_before": monitor.measure_exposure()}
        except ConstitutionalError:
            context = {**context, "se_before": 0.0}
    if context.get("se_after") is None:
        try:
            context = {**context, "se_after": monitor.measure_exposure()}
        except ConstitutionalError:
            context = {**context, "se_after": context.get("se_before", 0.0)}

    if validator is not None and not context.get("constitutional_error"):
        try:
            validator.validate(context)
            context = {**context, "transition_ok": True}
        except Exception as exc:  # noqa: BLE001
            context = {**context, "constitutional_error": exc, "transition_ok": False}

    header_body = {
        "receipt_id": str(context.get("receipt_id") or uuid.uuid4()),
        "runtime_version": RUNTIME_VERSION,
        "epoch": int(epoch if epoch is not None else context.get("epoch", 1)),
        "action_type": action_type,
        "actor_identity": crk1_uuid(identity_id),
        "timestamp": str(context.get("timestamp") or _now_iso()),
        "kernel_state_hash": compute_kernel_state_hash(runtime),
        "ledger_state_hash": compute_ledger_state_hash(runtime),
        "invariants_checked": assess_invariants_checked(context),
        "drift_metrics": _drift_metrics(context),
        "redteam_status": (
            run_redteam_status(runtime, identity_id) if include_redteam else {"attacks_run": [], "all_blocked": "YES"}
        ),
        "decision_summary": decision_summary,
        "evidence_refs": [crk1_uuid(item) for item in evidence_refs],
        "invariant_context": list(invariant_context or context.get("invariant_context") or []),
        "linked_grr_ids": list(linked_grr_ids or context.get("linked_grr_ids") or []),
        "kernel_challenge_refs": list(
            kernel_challenge_refs or context.get("kernel_challenge_refs") or []
        ),
        "signatures": {},
    }
    header_body["signatures"] = {"governance_body": _sign_header(header_body)}
    return GovernanceReceiptHeader(**header_body)


def validate_governance_receipt_header(
    header: dict[str, Any] | GovernanceReceiptHeader,
    *,
    schema_validator: CRK1SchemaValidator | None = None,
    require_redteam_pass: bool = True,
) -> None:
    """
    Validate header against JSON Schema and constitutional drift rules.
    Raises SchemaValidationError or ConstitutionalError on failure.
    """
    from src.crk1.governance_receipt_verifier import GovernanceReceiptVerifier

    payload = header.to_dict() if isinstance(header, GovernanceReceiptHeader) else dict(header)
    if schema_validator is not None:
        schema_validator.validate("GovernanceReceiptHeader", payload)
    GovernanceReceiptVerifier().verify(payload, require_redteam=require_redteam_pass)


def assert_governance_action_admissible(
    runtime: CRK1Runtime,
    header: dict[str, Any] | GovernanceReceiptHeader,
    *,
    schema_validator: CRK1SchemaValidator | None = None,
) -> GovernanceReceiptHeader:
    """Gate for governance engine — reject inadmissible actions before mutation."""
    if isinstance(header, GovernanceReceiptHeader):
        validate_governance_receipt_header(header, schema_validator=schema_validator)
        return header

    validate_governance_receipt_header(header, schema_validator=schema_validator)
    return GovernanceReceiptHeader(**header)
