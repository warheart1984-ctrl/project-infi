"""OTEM Level 20 constitutional recovery ceiling — triggers, containment, ODL pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
import threading
from pathlib import Path
from typing import Any

from src.otem_capability import (
    OTEM_SOVEREIGN_LEVEL,
    authority_band,
    get_otem_capability_level,
    is_containment_band,
    is_ceiling_level,
)

CEILING_RULES_VERSION = "aais.otem_ceiling.v1"
STATE_FILENAME = "otem_ceiling_state.json"

CONSTITUTIONAL_LAW_IDS = (
    "human_principal_root",
    "fail_closed",
    "no_self_delegation_of_ceiling_authority",
    "auditability_odl_binding",
    "defensive_only",
    "monotonic_authority_constraints",
)

MUTABLE_POLICY_REFS = (
    "authority_mask_spec",
    "hardening_thresholds",
    "escalation_rules",
    "admission_rules",
)

PIPELINE_STATES = frozenset(
    {"idle", "diagnostic", "preview", "awaiting_decision", "closing_ledger"}
)

CEILING_DECISIONS = frozenset(
    {
        "rollback_to_checkpoint",
        "quarantine_archive",
        "safe_mode_reanchor",
        "accept_containment",
        "constitutional_amendment",
    }
)

RECOVERY_VERBS = frozenset(
    {"rollback", "quarantine", "safe_mode", "reanchor", "accept_containment"}
)


class OtemCeilingError(RuntimeError):
    """Raised when ceiling pipeline cannot proceed safely."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _fingerprint(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()[:16]


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def default_rules_snapshot(
    *,
    numeric_level: int | None = None,
    ceiling_active: bool = False,
    containment_mode: bool = False,
    activation_triggers: list[str] | None = None,
    pipeline_state: str = "idle",
) -> dict[str, Any]:
    """Default otem_ceiling_rules block for Governance IR."""
    level = get_otem_capability_level() if numeric_level is None else int(numeric_level)
    band = authority_band(level)
    if ceiling_active:
        band = "sovereign"
        level = OTEM_SOVEREIGN_LEVEL
    elif containment_mode and band not in {"containment", "sovereign"}:
        band = "containment"
    return {
        "ceiling_version": CEILING_RULES_VERSION,
        "authority_band": band,
        "numeric_level": level,
        "ceiling_active": bool(ceiling_active),
        "containment_mode": bool(containment_mode),
        "activation_triggers": list(activation_triggers or [])[:16],
        "constitutional_law": list(CONSTITUTIONAL_LAW_IDS),
        "mutable_policy_refs": list(MUTABLE_POLICY_REFS),
        "operator_unavailable_policy": {
            "timeout_minutes": 30,
            "fallback": "quarantine_archive",
        },
        "pipeline_state": pipeline_state if pipeline_state in PIPELINE_STATES else "idle",
        "diagnostic_bundle_id": None,
        "preview_fingerprint": None,
        "pending_decision": None,
        "odl_root_id": None,
        "invocation_count": 0,
        "last_trigger_at": None,
    }


def default_law_registry() -> dict[str, Any]:
    """Constitutional vs mutable law registry for compiler gates."""
    return {
        "constitutional": [
            {"law_id": law_id, "law_class": "constitutional", "amendment_required": True}
            for law_id in CONSTITUTIONAL_LAW_IDS
        ],
        "mutable": [
            {"law_id": ref, "law_class": "mutable", "amendment_required": False}
            for ref in MUTABLE_POLICY_REFS
        ],
    }


def operator_invoke_requested() -> bool:
    raw = str(os.environ.get("AAIS_OTEM_CEILING_INVOKE", "")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


@dataclass
class CeilingTriggerEvent:
    trigger_id: str
    trigger_type: str
    severity: str
    summary: str
    recorded_at: str
    details: dict[str, Any]


class OtemCeilingController:
    """Stateful ceiling pipeline controller (runtime_dir/otem_ceiling_state.json)."""

    def __init__(self, *, runtime_dir: Path | str | None = None) -> None:
        self._runtime_dir = Path(runtime_dir).expanduser() if runtime_dir else _default_runtime_dir()
        self._lock = threading.Lock()
        self._state = self._load_state()

    @property
    def state_path(self) -> Path:
        return self._runtime_dir / STATE_FILENAME

    def _load_state(self) -> dict[str, Any]:
        path = self._runtime_dir / STATE_FILENAME
        if not path.exists():
            return default_rules_snapshot()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                base = default_rules_snapshot()
                base.update(payload)
                return base
        except (json.JSONDecodeError, OSError):
            pass
        return default_rules_snapshot()

    def _persist(self) -> None:
        path = self.state_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_stable_json(self._state) + "\n", encoding="utf-8")

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def rules_for_ir(self) -> dict[str, Any]:
        with self._lock:
            return default_rules_snapshot(
                numeric_level=int(self._state.get("numeric_level") or get_otem_capability_level()),
                ceiling_active=bool(self._state.get("ceiling_active")),
                containment_mode=bool(self._state.get("containment_mode")),
                activation_triggers=list(self._state.get("activation_triggers") or []),
                pipeline_state=str(self._state.get("pipeline_state") or "idle"),
            )

    def containment_active(self) -> bool:
        with self._lock:
            return bool(self._state.get("containment_mode") or self._state.get("ceiling_active"))

    def evaluate_trigger(
        self,
        *,
        trigger_type: str,
        severity: str = "high",
        summary: str = "",
        details: dict[str, Any] | None = None,
        scope_id: str | None = None,
    ) -> CeilingTriggerEvent | None:
        """Evaluate whether a trigger should enter containment (band 16+)."""
        normalized_type = str(trigger_type or "").strip().lower()
        if not normalized_type:
            return None
        auto_triggers = {
            "immune_critical",
            "governance_drift",
            "ir_core_violation",
            "checkpoint_block",
            "repeated_escalation",
            "substrate_drift",
            "irreversible_mutation_attempt",
            "operator_invoke",
        }
        if normalized_type not in auto_triggers and not operator_invoke_requested():
            return None
        if normalized_type == "operator_invoke" and not operator_invoke_requested():
            return None

        event = CeilingTriggerEvent(
            trigger_id=_fingerprint({"type": normalized_type, "at": _utc_now()}),
            trigger_type=normalized_type,
            severity=str(severity or "high"),
            summary=str(summary or normalized_type)[:500],
            recorded_at=_utc_now(),
            details=dict(details or {}),
        )
        with self._lock:
            already = bool(self._state.get("containment_mode"))
            triggers = list(self._state.get("activation_triggers") or [])
            if normalized_type not in triggers:
                triggers.append(normalized_type)
            self._state["activation_triggers"] = triggers[-16:]
            self._state["last_trigger_at"] = event.recorded_at
            if not already:
                self._state["invocation_count"] = int(self._state.get("invocation_count") or 0) + 1
        self._persist()
        if already:
            return event

        row = self._append_odl_invocation(event, scope_id=scope_id)
        if row:
            with self._lock:
                self._state["odl_root_id"] = str(row.get("decision_id") or self._state.get("odl_root_id"))
            self._persist()
        self.enter_containment(reason=event.summary, trigger=event, scope_id=scope_id)
        return event

    def enter_containment(
        self,
        *,
        reason: str,
        trigger: CeilingTriggerEvent | None = None,
        scope_id: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            self._state["containment_mode"] = True
            self._state["authority_band"] = "containment"
            level = int(self._state.get("numeric_level") or get_otem_capability_level())
            if level < 16:
                self._state["numeric_level"] = 16
            self._state["pipeline_state"] = "diagnostic"
        self._persist()
        bundle = self.build_diagnostic_bundle(reason=reason, trigger=trigger, scope_id=scope_id)
        return {"status": "containment", "reason": reason, "bundle": bundle}

    def build_diagnostic_bundle(
        self,
        *,
        reason: str = "",
        trigger: CeilingTriggerEvent | None = None,
        ir_snapshot: dict[str, Any] | None = None,
        scope_id: str | None = None,
    ) -> dict[str, Any]:
        bundle_id = _fingerprint(
            {
                "reason": reason,
                "trigger": asdict(trigger) if trigger else None,
                "at": _utc_now(),
            }
        )
        ir_body = dict(ir_snapshot or {})
        ir_fingerprint = ir_body.get("ir_fingerprint") or _fingerprint(ir_body) if ir_body else None
        violation_trace: list[dict[str, Any]] = []
        if trigger:
            violation_trace.append(
                {
                    "trigger_id": trigger.trigger_id,
                    "trigger_type": trigger.trigger_type,
                    "severity": trigger.severity,
                    "summary": trigger.summary,
                }
            )
        odl_subgraph: dict[str, Any] = {}
        try:
            from src.operator_decision_ledger import operator_decision_ledger

            if scope_id:
                root = str(self._state.get("odl_root_id") or "")
                if root:
                    odl_subgraph = operator_decision_ledger.build_action_graph(scope_id, root)
        except Exception:
            odl_subgraph = {}

        heal_projection: dict[str, Any] = {}
        try:
            from src.immune_hardening import project_hardening_recommendations

            heal_projection = project_hardening_recommendations(
                {"reason": reason, "trigger_type": trigger.trigger_type if trigger else None}
            )
        except Exception:
            heal_projection = {"status": "unavailable"}

        bundle = {
            "bundle_id": bundle_id,
            "built_at": _utc_now(),
            "reason": reason[:500],
            "ir_fingerprint": ir_fingerprint,
            "ir_snapshot": ir_body if ir_body else None,
            "violation_trace": violation_trace,
            "odl_subgraph": odl_subgraph,
            "heal_harden_projection": heal_projection,
            "authority_delta": {
                "prior_band": authority_band(get_otem_capability_level()),
                "current_band": "containment",
                "containment_mode": True,
            },
            "constitutional_law": list(CONSTITUTIONAL_LAW_IDS),
            "mutable_policy_refs": list(MUTABLE_POLICY_REFS),
        }
        with self._lock:
            self._state["diagnostic_bundle_id"] = bundle_id
            self._state["pipeline_state"] = "diagnostic"
        self._persist()
        return bundle

    def preview_decision(
        self,
        decision: str,
        *,
        scope_id: str | None = None,
        ir_snapshot: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = str(decision or "").strip().lower()
        if normalized not in CEILING_DECISIONS:
            raise OtemCeilingError(f"unsupported ceiling decision: {decision}")
        if normalized == "constitutional_amendment":
            requires_amendment = True
        else:
            requires_amendment = False
        preview_payload = {
            "decision": normalized,
            "preview_only": True,
            "requires_constitutional_amendment": requires_amendment,
            "recovery_verbs": sorted(RECOVERY_VERBS),
            "ir_snapshot": ir_snapshot,
        }
        preview_fp = _fingerprint(preview_payload)
        dry_run: dict[str, Any] = {"status": "preview", "allows": False}
        try:
            from src.decode_governance_executor import execute_with_decode_governance

            envelope = {
                "session_id": scope_id,
                "preview_only": True,
                "ceiling_decision": normalized,
            }
            bridge_result = {
                "normalized_input": {"type": "ceiling_preview", "payload": preview_payload},
                "governance_packet": {
                    "packet_type": "ceiling_preview",
                    "effectful": False,
                    "invariants": list(CONSTITUTIONAL_LAW_IDS),
                },
            }
            dry_run = execute_with_decode_governance(
                envelope,
                bridge_result=bridge_result,
                force_execute=False,
                preview_only=True,
            )
        except TypeError:
            dry_run = {"status": "preview", "allows": not requires_amendment, "note": "preview_stub"}
        except Exception as exc:
            dry_run = {"status": "preview_failed", "error": str(exc), "allows": False}

        with self._lock:
            self._state["preview_fingerprint"] = preview_fp
            self._state["pending_decision"] = normalized
            self._state["pipeline_state"] = "preview"
        self._persist()
        self._append_odl_preview(normalized, preview_fp, scope_id=scope_id)
        return {
            "preview_fingerprint": preview_fp,
            "decision": normalized,
            "dry_run": dry_run,
            "requires_constitutional_amendment": requires_amendment,
        }

    def apply_decision(
        self,
        decision: str,
        *,
        scope_id: str | None = None,
        operator_id: str | None = None,
        ir_before: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = str(decision or "").strip().lower()
        if normalized not in CEILING_DECISIONS:
            raise OtemCeilingError(f"unsupported ceiling decision: {decision}")
        with self._lock:
            if not self._state.get("containment_mode") and normalized != "constitutional_amendment":
                raise OtemCeilingError("ceiling decision requires active containment")
            pending = str(self._state.get("pending_decision") or "").strip().lower()
            if pending and pending != normalized:
                raise OtemCeilingError("decision does not match pending preview decision")

        if normalized == "constitutional_amendment":
            result = self._apply_constitutional_amendment(scope_id=scope_id, operator_id=operator_id)
        elif normalized == "rollback_to_checkpoint":
            result = self._apply_rollback(scope_id=scope_id)
        elif normalized == "quarantine_archive":
            result = self._apply_quarantine_archive(scope_id=scope_id)
        elif normalized == "safe_mode_reanchor":
            result = self._apply_safe_mode_reanchor(scope_id=scope_id)
        elif normalized == "accept_containment":
            result = self._apply_accept_containment()
        else:
            raise OtemCeilingError("unhandled decision path")

        ir_after_fp = _fingerprint(result.get("ir_after") or {})
        with self._lock:
            self._state["pipeline_state"] = "closing_ledger"
            if normalized in {"safe_mode_reanchor", "constitutional_amendment"}:
                self._state["ceiling_active"] = True
                self._state["authority_band"] = "sovereign"
                self._state["numeric_level"] = OTEM_SOVEREIGN_LEVEL
            elif normalized == "accept_containment":
                pass
            else:
                self._state["containment_mode"] = False
                self._state["pipeline_state"] = "idle"
                self._state["pending_decision"] = None
                self._state["preview_fingerprint"] = None
        self._persist()
        odl_row = self._append_odl_decision(
            normalized,
            scope_id=scope_id,
            operator_id=operator_id,
            ir_before=ir_before,
            ir_after_fingerprint=ir_after_fp,
        )
        self._post_decision_hardening(normalized, scope_id=scope_id)
        with self._lock:
            self._state["pipeline_state"] = "idle"
            if odl_row:
                self._state["odl_root_id"] = str(odl_row.get("decision_id") or self._state.get("odl_root_id"))
        self._persist()
        return {
            "status": "applied",
            "decision": normalized,
            "result": result,
            "odl_decision_id": (odl_row or {}).get("decision_id"),
        }

    def _apply_rollback(self, *, scope_id: str | None) -> dict[str, Any]:
        return {
            "action": "rollback_to_checkpoint",
            "scope_id": scope_id,
            "ir_after": {"genesis": "rollback_checkpoint"},
        }

    def _apply_quarantine_archive(self, *, scope_id: str | None) -> dict[str, Any]:
        try:
            from src.immune_system import immune_system

            immune_system.observe_protocol_signal(
                component_id="otem_ceiling",
                signal_type="quarantine_archive",
                severity="critical",
                reason="otem_ceiling_quarantine_archive",
            )
        except Exception:
            pass
        return {
            "action": "quarantine_archive",
            "scope_id": scope_id,
            "ir_after": {"mode": "quarantine_archive"},
        }

    def _apply_safe_mode_reanchor(self, *, scope_id: str | None) -> dict[str, Any]:
        safe_mode: dict[str, Any] = {"status": "unavailable"}
        try:
            from src.cogos_runtime_bridge import build_ceiling_safe_mode_status

            safe_mode = build_ceiling_safe_mode_status(scope_id=scope_id)
        except Exception:
            pass
        return {
            "action": "safe_mode_reanchor",
            "scope_id": scope_id,
            "safe_mode": safe_mode,
            "ir_after": {"genesis": "safe_mode_reanchor", "odl_bound": True},
        }

    def _apply_accept_containment(self) -> dict[str, Any]:
        with self._lock:
            self._state["containment_mode"] = True
            self._state["authority_band"] = "containment"
        return {"action": "accept_containment", "ir_after": {"containment_mode": True}}

    def _apply_constitutional_amendment(
        self,
        *,
        scope_id: str | None,
        operator_id: str | None,
    ) -> dict[str, Any]:
        with self._lock:
            self._state["ceiling_active"] = True
            self._state["authority_band"] = "sovereign"
            self._state["numeric_level"] = OTEM_SOVEREIGN_LEVEL
        return {
            "action": "constitutional_amendment",
            "scope_id": scope_id,
            "operator_id": operator_id,
            "ir_after": {"genesis": "constitutional_amendment", "law_class": "constitutional"},
        }

    def _post_decision_hardening(self, decision: str, *, scope_id: str | None) -> None:
        try:
            from src.immune_hardening import enroll_post_ceiling_hardening

            enroll_post_ceiling_hardening(decision, scope_id=scope_id)
        except Exception:
            pass
        try:
            from src.invariant_compiler import compile_from_ir
            from src.governance_ir import build_governance_ir

            ir = self.rules_for_ir()
            compile_from_ir(
                {
                    "ir_version": "aais.governance_ir.v1",
                    "ir_fingerprint": _fingerprint(ir),
                    "authority_envelope": {"capabilities": [], "delegation_depth": 0, "max_subagent_depth": 3},
                    "invariant_set": {"hard": list(CONSTITUTIONAL_LAW_IDS), "conditional": [], "stage_linked": {}},
                    "execution_context": {
                        "otem_level": "blocked" if self.containment_active() else "detected",
                        "cisiv_stage": "verification",
                    },
                    "otem_ceiling_rules": ir,
                }
            )
        except Exception:
            pass

    def _append_odl_invocation(
        self,
        event: CeilingTriggerEvent,
        *,
        scope_id: str | None,
    ) -> dict[str, Any] | None:
        try:
            from src.operator_decision_ledger import operator_decision_ledger

            return operator_decision_ledger.append_otem_ceiling_invocation(
                scope_id or "global",
                trigger_type=event.trigger_type,
                summary=event.summary,
                details=event.details,
            )
        except Exception:
            return None

    def _append_odl_preview(
        self,
        decision: str,
        preview_fp: str,
        *,
        scope_id: str | None,
    ) -> dict[str, Any] | None:
        try:
            from src.operator_decision_ledger import operator_decision_ledger

            return operator_decision_ledger.append_otem_ceiling_preview(
                scope_id or "global",
                decision=decision,
                preview_fingerprint=preview_fp,
            )
        except Exception:
            return None

    def _append_odl_decision(
        self,
        decision: str,
        *,
        scope_id: str | None,
        operator_id: str | None,
        ir_before: dict[str, Any] | None,
        ir_after_fingerprint: str,
    ) -> dict[str, Any] | None:
        try:
            from src.operator_decision_ledger import operator_decision_ledger

            return operator_decision_ledger.append_otem_ceiling_decision(
                scope_id or "global",
                decision=decision,
                operator_id=operator_id,
                ir_fingerprint_before=(ir_before or {}).get("ir_fingerprint"),
                ir_fingerprint_after=ir_after_fingerprint,
            )
        except Exception:
            return None

    def status_for_console(self) -> dict[str, Any]:
        snap = self.snapshot()
        return {
            "ceiling_version": snap.get("ceiling_version"),
            "authority_band": snap.get("authority_band"),
            "numeric_level": snap.get("numeric_level"),
            "ceiling_active": snap.get("ceiling_active"),
            "containment_mode": snap.get("containment_mode"),
            "pipeline_state": snap.get("pipeline_state"),
            "activation_triggers": list(snap.get("activation_triggers") or []),
            "invocation_count": snap.get("invocation_count"),
            "last_trigger_at": snap.get("last_trigger_at"),
            "diagnostic_bundle_id": snap.get("diagnostic_bundle_id"),
            "pending_decision": snap.get("pending_decision"),
        }


otem_ceiling = OtemCeilingController()


def max_action_class_for_band(band: str, *, ceiling_active: bool = False) -> str:
    """Band-aware max action class for mask lowering."""
    normalized = str(band or "autonomous").strip().lower()
    if ceiling_active or normalized == "sovereign":
        return "observe"
    if normalized == "containment":
        return "observe"
    if normalized == "governed":
        return "propose"
    return "execute"


def touches_constitutional_law(target: str) -> bool:
    return str(target or "").strip().lower() in CONSTITUTIONAL_LAW_IDS
