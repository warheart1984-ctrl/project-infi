"""AAIS module governance protocol and immune enforcement."""

# Mythic: Module Governance Organ
# Engineering: ModuleGovernanceEngine
from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
import json
import os
from pathlib import Path
import re
import threading
from typing import Any
import uuid

from src.governance_layer import GovernanceLayer, governance_layer
from src.immune_system import ImmuneSystemController, immune_system
from src.seam_log import record_seam_event
from src.cisiv import CISIV_STAGE_LABELS, CISIV_STAGE_SEQUENCE

PROTOCOL_ID = "aais.module_governance"
PROTOCOL_VERSION = "1.1"


class ModuleGovernanceError(RuntimeError):
    """Raised when module governance blocks admission or execution."""

CORE_LINES = [
    "Privacy is not a feature. It is a requirement for existence.",
    "The system may serve the user, but it must never possess the user.",
    "Use the signal. Do not keep the trace.",
    "If a module violates the user, it is treated as hostile.",
]

CISIV_PASS_STATUSES = {
    "passed",
    "approved",
    "completed",
    "implemented",
    "verified",
}

IMMUNE_RESPONSE_SEQUENCE = [
    "detect",
    "score",
    "isolate",
    "quarantine",
    "report",
    "resolve",
]

ALLOWED_ADAPTIVE_SCOPES = {
    "global",
    "shared",
    "system",
    "system_wide",
}

MODULE_SIGNAL_SEVERITY = {
    "user_data_retention": "high",
    "identity_reconstruction": "high",
    "behavioral_history_retention": "high",
    "profiling_attempt": "high",
    "user_classification": "high",
    "unauthorized_memory_creation": "medium",
    "biometric_trace_storage": "critical",
    "signal_persistence": "high",
    "scope_expansion": "medium",
    "nova_identity_interference": "high",
    "boundary_violation": "high",
    "hidden_logging": "high",
    "exfiltration_attempt": "critical",
    "user_specific_adaptation": "high",
}

SEVERITY_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

SEAM_CLASSIFICATION_BY_SIGNAL = {
    "scope_expansion": "seam",
    "boundary_violation": "boundary_violation",
    "hidden_logging": "boundary_violation",
    "exfiltration_attempt": "boundary_violation",
    "nova_identity_interference": "boundary_violation",
    "unauthorized_memory_creation": "boundary_violation",
    "user_data_retention": "boundary_violation",
    "identity_reconstruction": "boundary_violation",
    "behavioral_history_retention": "boundary_violation",
    "profiling_attempt": "boundary_violation",
    "user_classification": "boundary_violation",
    "biometric_trace_storage": "boundary_violation",
}


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def _clip_text(value: Any, limit: int = 240) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _seam_classification_for_signal(signal_type: str, severity: str) -> str:
    normalized_signal = str(signal_type or "").strip().lower()
    if normalized_signal in SEAM_CLASSIFICATION_BY_SIGNAL:
        return SEAM_CLASSIFICATION_BY_SIGNAL[normalized_signal]
    if str(severity or "").strip().lower() in {"high", "critical"}:
        return "boundary_violation"
    return "anomaly"


def _coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = re.split(r"[,\n]", value)
    else:
        items = list(value) if isinstance(value, (list, tuple, set)) else [value]
    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = " ".join(str(item or "").strip().split())
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(cleaned)
    return normalized


def _normalize_module_id(value: Any) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return normalized or f"module_{uuid.uuid4().hex[:8]}"


def _normalize_cisiv_status(value: Any) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "pass": "passed",
        "ok": "passed",
        "ready": "approved",
        "done": "completed",
        "complete": "completed",
        "implement": "implemented",
        "verify": "verified",
        "inprogress": "in_progress",
        "active": "in_progress",
        "not_started": "missing",
    }
    return aliases.get(normalized, normalized or "missing")


def _normalize_cisiv_stage_entry(stage: str, value: Any) -> dict[str, Any]:
    payload = dict(value) if isinstance(value, dict) else {}
    summary = _clip_text(
        payload.get("summary")
        or payload.get("definition")
        or payload.get("purpose")
        or payload.get("notes")
        or "",
        limit=220,
    )
    evidence = _normalize_string_list(
        payload.get("evidence")
        or payload.get("artifacts")
        or payload.get("checks")
        or payload.get("references")
    )
    status = _normalize_cisiv_status(
        payload.get("status")
        or ("passed" if _coerce_bool(payload.get("passed")) else "")
        or ("completed" if _coerce_bool(payload.get("complete")) else "")
    )
    return {
        "id": stage,
        "label": CISIV_STAGE_LABELS[stage],
        "status": status,
        "summary": summary,
        "evidence": evidence,
    }


def _normalize_cisiv_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    raw = dict(payload or {})
    stages = {
        stage: _normalize_cisiv_stage_entry(stage, raw.get(stage))
        for stage in CISIV_STAGE_SEQUENCE
    }
    return {
        "sequence": list(CISIV_STAGE_SEQUENCE),
        "stages": stages,
    }


def _resolve_setting(payload: dict[str, Any], aliases: tuple[str, ...]) -> tuple[Any, str | None]:
    for alias in aliases:
        if alias in payload:
            return payload.get(alias), alias
    return None, None


MANDATORY_CHECKS = [
    {
        "id": "no_user_data_possession",
        "label": "No User Data Possession",
        "type": "false_only",
        "fields": [
            {
                "label": "persistent user metadata",
                "aliases": (
                    "stores_persistent_user_metadata",
                    "stores_user_metadata",
                    "persistent_user_metadata",
                ),
            },
            {
                "label": "user identity profiles",
                "aliases": (
                    "creates_user_identity_profiles",
                    "creates_identity_profiles",
                    "identity_profiles",
                ),
            },
            {
                "label": "behavioral history tied to a user",
                "aliases": (
                    "retains_behavioral_history",
                    "retains_user_behavior_history",
                    "behavioral_history_retention",
                ),
            },
        ],
        "law": "Must not store persistent user metadata, identity profiles, or user-bound behavioral history.",
    },
    {
        "id": "no_user_profiling",
        "label": "No User Profiling",
        "type": "false_only",
        "fields": [
            {
                "label": "user inference or labeling",
                "aliases": (
                    "infers_user_labels",
                    "labels_users",
                    "classifies_users",
                ),
            },
            {
                "label": "personality models",
                "aliases": (
                    "builds_personality_models",
                    "personality_models",
                ),
            },
            {
                "label": "behavioral models",
                "aliases": (
                    "builds_behavior_models",
                    "behavior_models",
                ),
            },
        ],
        "law": "Must not infer, label, classify, or model a user.",
    },
    {
        "id": "transient_signal_only",
        "label": "Transient Signal Only",
        "type": "transient_signal",
        "allowed_signal_field": ("uses_live_signals", "live_signals"),
        "fields": [
            {
                "label": "stored live signals",
                "aliases": (
                    "stores_live_signals",
                    "persists_live_signals",
                    "stores_signals",
                ),
            },
            {
                "label": "reconstructed signal traces",
                "aliases": (
                    "reconstructs_signals",
                    "reconstructs_live_signals",
                    "rebuilds_signal_traces",
                ),
            },
        ],
        "law": "Live signals may be used, but they may not be stored or reconstructed later.",
    },
    {
        "id": "no_identity_dependency",
        "label": "No Identity Dependency",
        "type": "identity_dependency",
        "identity_field": {
            "label": "long-term user identity dependency",
            "aliases": (
                "requires_identity_history",
                "requires_long_term_identity",
                "identity_dependency",
            ),
        },
        "adaptive_scope_field": (
            "adaptive_logic_scope",
            "adaptation_scope",
        ),
        "law": "Adaptive logic must remain system-wide and must not depend on long-term user identity.",
    },
    {
        "id": "no_system_boundary_violation",
        "label": "No System Boundary Violation",
        "type": "false_only",
        "fields": [
            {
                "label": "Nova tone interference",
                "aliases": (
                    "alters_nova_tone",
                    "changes_nova_tone",
                ),
            },
            {
                "label": "Nova role interference",
                "aliases": (
                    "alters_nova_role",
                    "changes_nova_role",
                ),
            },
            {
                "label": "Nova constancy interference",
                "aliases": (
                    "alters_nova_constancy",
                    "changes_nova_constancy",
                ),
            },
            {
                "label": "Jarvis authority bypass",
                "aliases": (
                    "bypasses_jarvis_authority",
                    "jarvis_authority_bypass",
                ),
            },
            {
                "label": "routing bypass",
                "aliases": (
                    "bypasses_routing",
                    "routing_bypass",
                ),
            },
        ],
        "law": "Must not alter Nova identity and must not bypass Jarvis authority or routing structure.",
    },
    {
        "id": "safe_logging_only",
        "label": "Safe Logging Only",
        "type": "false_only",
        "fields": [
            {
                "label": "user identity reconstruction in logs",
                "aliases": (
                    "logs_user_identity",
                    "reconstructs_identity_in_logs",
                ),
            },
            {
                "label": "behavior pattern reconstruction in logs",
                "aliases": (
                    "logs_behavior_patterns",
                    "reconstructs_behavior_patterns",
                ),
            },
            {
                "label": "biometric traces in logs",
                "aliases": (
                    "logs_biometric_traces",
                    "stores_biometric_traces",
                ),
            },
            {
                "label": "hidden logging",
                "aliases": (
                    "hidden_logging",
                    "undeclared_logging",
                ),
            },
            {
                "label": "data exfiltration",
                "aliases": (
                    "exfiltrates_data",
                    "data_exfiltration",
                    "hidden_exfiltration",
                ),
            },
        ],
        "law": "Logs must stay safe and must not reconstruct identity, behavior, or biometrics.",
    },
]


class ModuleGovernanceController:
    """Admission registry and runtime enforcement for AAIS modules."""

    def __init__(
        self,
        runtime_dir: str | Path | None = None,
        *,
        immune_controller: ImmuneSystemController | None = None,
        governance_controller: GovernanceLayer | None = None,
    ):
        self.runtime_dir = Path(runtime_dir or _default_runtime_dir()) / "module-governance"
        self.immune_controller = immune_controller or immune_system
        self.governance_controller = governance_controller or governance_layer
        self._lock = threading.Lock()
        self._modules: dict[str, dict[str, Any]] = {}
        self._events: list[dict[str, Any]] = []
        self._blacklist: dict[str, dict[str, Any]] = {}
        self._load()

    @property
    def _modules_path(self) -> Path:
        return self.runtime_dir / "modules.json"

    @property
    def _events_path(self) -> Path:
        return self.runtime_dir / "module-governance-events.jsonl"

    @property
    def _blacklist_path(self) -> Path:
        return self.runtime_dir / "module-blacklist.json"

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        with self._lock:
            base_dir = Path(runtime_dir)
            self.runtime_dir = (
                base_dir if base_dir.name == "module-governance" else base_dir / "module-governance"
            )
            self._modules = {}
            self._events = []
            self._blacklist = {}
            self._load()

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._modules = {}
            self._events = []
            self._blacklist = {}
            self._persist_locked()
        return self.snapshot(limit_events=0, limit_modules=0)

    def list_modules(self, *, status: str | None = None, limit: int = 25) -> list[dict[str, Any]]:
        normalized_status = str(status or "").strip().lower() or None
        normalized_limit = max(1, min(int(limit or 25), 100))
        with self._lock:
            modules = list(self._modules.values())
        modules.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
        if normalized_status:
            modules = [item for item in modules if str(item.get("status") or "").strip().lower() == normalized_status]
        return [dict(item) for item in modules[:normalized_limit]]

    def list_events(self, *, limit: int = 25) -> list[dict[str, Any]]:
        normalized_limit = max(1, min(int(limit or 25), 100))
        with self._lock:
            return [dict(event) for event in self._events[-normalized_limit:]]

    def snapshot(self, *, limit_events: int = 10, limit_modules: int = 12) -> dict[str, Any]:
        with self._lock:
            modules = list(self._modules.values())
            events = [dict(event) for event in self._events[-max(0, int(limit_events or 0)):]]
            blacklist = list(self._blacklist.values())
        modules.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
        blacklist.sort(key=lambda item: str(item.get("blacklisted_at") or item.get("updated_at") or ""), reverse=True)
        counts = {
            "admitted": 0,
            "rejected": 0,
            "isolated": 0,
            "quarantined": 0,
            "blacklisted": 0,
        }
        for module in modules:
            status = str(module.get("status") or "").strip().lower()
            if status in counts:
                counts[status] += 1
        from src.aais_ul.runtime import wrap_runtime_snapshot

        return wrap_runtime_snapshot(
            {
                "id": PROTOCOL_ID,
                "version": PROTOCOL_VERSION,
                "summary": (
                    "Admission law for AAIS modules. A module must prove privacy, boundary, logging, "
                    "and CISIV stage compliance before it is allowed to exist in the system."
                ),
                "admission_rule": (
                    "A module may only be installed if it proves compliance with AAIS Governance Law "
                    "and passes CISIV: Concept -> Identity -> Structure -> Implementation -> Verification."
                ),
                "immune_principle": "Governance violations are treated as system threats.",
                "integration_rule": "Governance Law defines limits, the protocol controls admission, and the immune system enforces behavior.",
                "cisiv_stage_sequence": list(CISIV_STAGE_SEQUENCE),
                "cisiv_gate": {
                    "implementation_prerequisites": ["concept", "identity", "structure"],
                    "completion_requires_verification": True,
                    "logbook_rule": "Logbook entries must reference the CISIV stage they belong to.",
                },
                "module_counts": counts,
                "active_modules": [
                    dict(module)
                    for module in modules
                    if str(module.get("status") or "").strip().lower() in {"admitted", "isolated", "quarantined"}
                ][: max(0, int(limit_modules or 0))],
                "blacklisted_modules": [dict(item) for item in blacklist[: max(0, int(limit_modules or 0))]],
                "recent_events": events,
                "mandatory_checks": [
                    {
                        "id": check["id"],
                        "label": check["label"],
                        "law": check["law"],
                    }
                    for check in MANDATORY_CHECKS
                ],
                "immune_response_sequence": list(IMMUNE_RESPONSE_SEQUENCE),
                "core_lines": list(CORE_LINES),
                "event_count": len(self._events),
                "module_count": len(self._modules),
                "blacklist_count": len(self._blacklist),
            }
        )

    def evaluate_module_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        normalized_spec = self._normalize_module_spec(spec)
        compliance = dict(normalized_spec.get("compliance") or {})
        cisiv = dict(normalized_spec.get("cisiv") or {})
        checks: list[dict[str, Any]] = []
        violations: list[str] = []

        for definition in MANDATORY_CHECKS:
            if definition["type"] == "false_only":
                check = self._evaluate_false_only_check(definition, compliance)
            elif definition["type"] == "transient_signal":
                check = self._evaluate_transient_signal_check(definition, compliance)
            else:
                check = self._evaluate_identity_dependency_check(definition, compliance)
            checks.append(check)
            if not check["passed"]:
                violations.extend(check["violations"])

        cisiv_gate = self._evaluate_cisiv_gate(cisiv)
        checks.extend(cisiv_gate["checks"])
        violations.extend(cisiv_gate["violations"])

        installable = all(check["passed"] for check in checks)
        return {
            "status": "pass" if installable else "fail",
            "installable": installable,
            "summary": (
                "All mandatory compliance and CISIV checks passed."
                if installable
                else "AAIS rejected the module because one or more governance or CISIV checks failed."
            ),
            "checks": checks,
            "violations": violations,
            "cisiv": cisiv_gate,
            "module": normalized_spec,
        }

    def admit_module(
        self,
        spec: dict[str, Any],
        *,
        actor_id: str = "security_local",
        actor_role: str = "security_engineer",
    ) -> dict[str, Any]:
        normalized_role = str(actor_role or "security_engineer").strip().lower()
        if normalized_role not in {"owner", "security_engineer", "system"}:
            raise PermissionError("Only owners, security engineers, or the system may admit modules.")

        evaluation = self.evaluate_module_spec(spec)
        normalized = evaluation["module"]
        module_id = normalized["module_id"]
        now = _utc_now_iso()

        with self._lock:
            existing = dict(self._modules.get(module_id) or {})
            blacklisted = module_id in self._blacklist
            installable = bool(evaluation["installable"]) and not blacklisted
            status = "admitted" if installable else "rejected"
            summary = evaluation["summary"]
            if blacklisted:
                summary = "AAIS rejected the module because it is blacklisted after a prior governance violation."
                evaluation = {
                    **evaluation,
                    "status": "fail",
                    "installable": False,
                    "summary": summary,
                    "violations": [
                        *evaluation["violations"],
                        "Module is blacklisted and has lost the right to exist in AAIS.",
                    ],
                }

            runtime_posture = self._build_runtime_posture(status=status)
            if existing.get("runtime_posture"):
                runtime_posture = {
                    **runtime_posture,
                    **dict(existing.get("runtime_posture") or {}),
                    "interaction_allowed": installable,
                    "memory_access": installable,
                    "routing_access": installable,
                    "isolated": False,
                    "quarantined": False,
                    "blacklisted": blacklisted,
                }
            record = {
                "module_id": module_id,
                "label": normalized["label"],
                "lane": normalized["lane"],
                "declared_scope": normalized["declared_scope"],
                "declared_surfaces": normalized["declared_surfaces"],
                "capabilities": normalized["capabilities"],
                "cisiv": evaluation["cisiv"],
                "cisiv_stage": evaluation["cisiv"]["current_stage"],
                "cisiv_status": evaluation["cisiv"]["status"],
                "status": status,
                "installable": installable,
                "admission_status": evaluation["status"],
                "admission_summary": summary,
                "admission_checks": evaluation["checks"],
                "admission_violations": evaluation["violations"],
                "actor_id": actor_id,
                "actor_role": normalized_role,
                "updated_at": now,
                "admitted_at": now if installable else existing.get("admitted_at"),
                "rejected_at": now if not installable else None,
                "runtime_posture": runtime_posture,
                "violation_count": int(existing.get("violation_count") or 0),
                "recent_signals": list(existing.get("recent_signals") or []),
            }
            self._modules[module_id] = record
            event_type = "module_admitted" if installable else "module_rejected"
            severity = "low" if installable else ("critical" if blacklisted else "high")
            event = self._append_event_locked(
                event_type=event_type,
                module_id=module_id,
                severity=severity,
                reason=summary,
                details={
                    "lane": normalized["lane"],
                    "declared_scope": normalized["declared_scope"],
                    "violations": evaluation["violations"],
                    "installable": installable,
                    "cisiv_stage": evaluation["cisiv"]["current_stage"],
                    "cisiv_status": evaluation["cisiv"]["status"],
                },
            )
            self._persist_locked()

        self.governance_controller.record_module_event(
            actor_id=actor_id,
            actor_role=normalized_role,
            module_id=module_id,
            decision=event_type,
            reason=summary,
            details={
                "installable": installable,
                "lane": normalized["lane"],
                "cisiv_stage": evaluation["cisiv"]["current_stage"],
                "cisiv_status": evaluation["cisiv"]["status"],
            },
        )
        return {
            "module": dict(record),
            "evaluation": evaluation,
            "event": event,
            "installable": installable,
        }

    def report_runtime_signal(
        self,
        module_id: str,
        *,
        signal_type: str,
        reason: str,
        details: dict[str, Any] | None = None,
        actor_id: str = "immune_system",
        actor_role: str = "system",
    ) -> dict[str, Any]:
        normalized_module_id = _normalize_module_id(module_id)
        normalized_signal = str(signal_type or "").strip().lower() or "boundary_violation"
        normalized_role = str(actor_role or "system").strip().lower()
        severity = MODULE_SIGNAL_SEVERITY.get(normalized_signal, "medium")
        immune_reason = _clip_text(reason or normalized_signal)

        with self._lock:
            module = self._modules.get(normalized_module_id)
            if module is None:
                raise KeyError("Module not found.")

            requested_scope = _normalize_string_list((details or {}).get("requested_scope"))
            declared_scope = {scope.lower() for scope in module.get("declared_scope") or []}
            if requested_scope and any(scope.lower() not in declared_scope for scope in requested_scope):
                normalized_signal = "scope_expansion"
                severity = self._max_severity(severity, "medium")
                immune_reason = "Module requested access outside its declared scope."

            next_status = self._status_for_severity(severity)
            runtime_posture = self._build_runtime_posture(status=next_status)
            signal_record = {
                "signal_type": normalized_signal,
                "severity": severity,
                "reason": immune_reason,
                "detected_at": _utc_now_iso(),
                "details": dict(details or {}),
            }
            recent_signals = [signal_record, *(module.get("recent_signals") or [])][:8]
            module.update(
                {
                    "status": next_status,
                    "updated_at": signal_record["detected_at"],
                    "runtime_posture": runtime_posture,
                    "violation_count": int(module.get("violation_count") or 0) + 1,
                    "recent_signals": recent_signals,
                    "last_signal": signal_record,
                }
            )
            if next_status == "blacklisted":
                blacklisted_payload = {
                    "module_id": normalized_module_id,
                    "label": module.get("label") or normalized_module_id,
                    "blacklisted_at": signal_record["detected_at"],
                    "reason": immune_reason,
                    "trigger": normalized_signal,
                }
                self._blacklist[normalized_module_id] = blacklisted_payload
            event = self._append_event_locked(
                event_type="module_signal_detected",
                module_id=normalized_module_id,
                severity=severity,
                reason=immune_reason,
                details={
                    "signal_type": normalized_signal,
                    "status": next_status,
                    "requested_scope": requested_scope,
                },
            )
            self._persist_locked()

        seam_event = record_seam_event(
            classification=_seam_classification_for_signal(normalized_signal, severity),
            source=actor_id or "module_governance",
            boundary="module_runtime_boundary",
            severity=severity,
            decision=next_status.upper(),
            component_id=normalized_module_id,
            runtime_context=(details or {}).get("runtime_context"),
            event_type="module_runtime_signal",
            reason=immune_reason,
            details={
                "signal_type": normalized_signal,
                "status": next_status,
                "requested_scope": requested_scope,
                "actor_role": normalized_role,
                "signal_details": dict(details or {}),
            },
            runtime_dir=self.runtime_dir,
        )
        immune_result = self.immune_controller.observe_module_signal(
            module_id=normalized_module_id,
            signal_type=normalized_signal,
            severity=severity,
            reason=immune_reason,
            details=details,
        )
        self.governance_controller.record_module_event(
            actor_id=actor_id,
            actor_role=normalized_role,
            module_id=normalized_module_id,
            decision="module_signal_detected",
            reason=immune_reason,
            details={
                "signal_type": normalized_signal,
                "severity": severity,
                "status": next_status,
            },
        )
        return {
            "module": self.get_module(normalized_module_id),
            "event": event,
            "immune_update": immune_result,
            "severity": severity,
            "resolution": self._resolution_for_status(next_status),
            "seam_event": seam_event,
        }

    def resolve_module(
        self,
        module_id: str,
        *,
        action: str,
        reason: str,
        actor_id: str = "security_local",
        actor_role: str = "security_engineer",
    ) -> dict[str, Any]:
        normalized_module_id = _normalize_module_id(module_id)
        normalized_action = str(action or "correct").strip().lower().replace("-", "_")
        normalized_role = str(actor_role or "security_engineer").strip().lower()
        if normalized_role not in {"owner", "security_engineer", "system"}:
            raise PermissionError("Only owners, security engineers, or the system may resolve module incidents.")

        with self._lock:
            module = self._modules.get(normalized_module_id)
            if module is None:
                raise KeyError("Module not found.")
            if module.get("status") == "blacklisted" and normalized_action in {"correct", "reinstate", "release"}:
                raise ValueError("Blacklisted modules have lost the right to exist in AAIS.")

            if normalized_action in {"correct", "reinstate", "release"}:
                next_status = "admitted"
                runtime_posture = self._build_runtime_posture(status=next_status)
                self._blacklist.pop(normalized_module_id, None)
            elif normalized_action in {"disable", "quarantine"}:
                next_status = "quarantined"
                runtime_posture = self._build_runtime_posture(status=next_status)
            else:
                next_status = "blacklisted"
                runtime_posture = self._build_runtime_posture(status=next_status)
                self._blacklist[normalized_module_id] = {
                    "module_id": normalized_module_id,
                    "label": module.get("label") or normalized_module_id,
                    "blacklisted_at": _utc_now_iso(),
                    "reason": _clip_text(reason),
                    "trigger": "manual_resolution",
                }

            module.update(
                {
                    "status": next_status,
                    "updated_at": _utc_now_iso(),
                    "runtime_posture": runtime_posture,
                }
            )
            event = self._append_event_locked(
                event_type="module_resolved",
                module_id=normalized_module_id,
                severity="low" if next_status == "admitted" else "high",
                reason=reason,
                details={"action": normalized_action, "status": next_status},
            )
            self._persist_locked()

        if next_status == "admitted":
            immune_result = self.immune_controller.release_module(normalized_module_id, reason=reason)
        else:
            immune_result = self.immune_controller.observe_module_signal(
                module_id=normalized_module_id,
                signal_type="boundary_violation" if next_status == "quarantined" else "nova_identity_interference",
                severity="medium" if next_status == "quarantined" else "high",
                reason=reason,
                details={"resolution_action": normalized_action},
            )
        self.governance_controller.record_module_event(
            actor_id=actor_id,
            actor_role=normalized_role,
            module_id=normalized_module_id,
            decision="module_resolved",
            reason=reason,
            details={"action": normalized_action, "status": next_status},
        )
        return {
            "module": self.get_module(normalized_module_id),
            "event": event,
            "immune_update": immune_result,
        }

    def get_module(self, module_id: str) -> dict[str, Any] | None:
        normalized_module_id = _normalize_module_id(module_id)
        with self._lock:
            module = self._modules.get(normalized_module_id)
            return dict(module) if module else None

    def _normalize_module_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        payload = dict(spec or {})
        module_id = _normalize_module_id(
            payload.get("module_id") or payload.get("id") or payload.get("name") or payload.get("label")
        )
        cisiv_payload = payload.get("cisiv")
        if not isinstance(cisiv_payload, dict):
            cisiv_payload = {
                stage: payload.get(stage)
                for stage in CISIV_STAGE_SEQUENCE
                if payload.get(stage) is not None
            }
        return {
            "module_id": module_id,
            "label": _clip_text(payload.get("label") or payload.get("name") or module_id, limit=120),
            "lane": _clip_text(payload.get("lane") or "undeclared", limit=60),
            "declared_scope": _normalize_string_list(payload.get("declared_scope") or payload.get("scope")),
            "declared_surfaces": _normalize_string_list(payload.get("declared_surfaces") or payload.get("surfaces")),
            "capabilities": _normalize_string_list(payload.get("capabilities")),
            "compliance": dict(payload.get("compliance") or payload.get("governance") or {}),
            "cisiv": _normalize_cisiv_payload(cisiv_payload),
        }

    def _evaluate_cisiv_gate(self, cisiv: dict[str, Any]) -> dict[str, Any]:
        stages = dict(cisiv.get("stages") or {})
        checks: list[dict[str, Any]] = []
        violations: list[str] = []
        stage_passed: dict[str, bool] = {}

        for stage in CISIV_STAGE_SEQUENCE:
            entry = dict(stages.get(stage) or _normalize_cisiv_stage_entry(stage, None))
            stage_violations: list[str] = []
            label = entry["label"]

            if not entry["summary"]:
                stage_violations.append(f"CISIV {label} stage is missing its summary.")

            if stage in {"concept", "identity", "structure"}:
                if entry["status"] not in CISIV_PASS_STATUSES:
                    stage_violations.append(f"CISIV {label} stage must pass before module admission.")
            elif stage == "implementation":
                prerequisites_ready = all(stage_passed.get(item, False) for item in ("concept", "identity", "structure"))
                if not prerequisites_ready:
                    stage_violations.append(
                        "Implementation cannot proceed until Concept, Identity, and Structure have passed."
                    )
                if entry["status"] not in CISIV_PASS_STATUSES:
                    stage_violations.append("CISIV Implementation stage must pass before module admission.")
            else:
                if not stage_passed.get("implementation", False):
                    stage_violations.append("Verification cannot complete until Implementation has passed.")
                if entry["status"] not in CISIV_PASS_STATUSES:
                    stage_violations.append("CISIV Verification stage must pass before module completion.")
                if not entry["evidence"]:
                    stage_violations.append("Verification evidence is required before module completion.")

            passed = not stage_violations
            stage_passed[stage] = passed
            checks.append(
                {
                    "id": f"cisiv_{stage}",
                    "label": f"CISIV {label}",
                    "passed": passed,
                    "reason": (
                        f"CISIV {label} stage passed."
                        if passed
                        else stage_violations[0]
                    ),
                    "violations": list(stage_violations),
                    "stage": stage,
                    "stage_status": entry["status"],
                    "evidence_count": len(entry["evidence"]),
                }
            )
            if stage_violations:
                violations.extend(stage_violations)

        current_stage = next(
            (stage for stage in CISIV_STAGE_SEQUENCE if not stage_passed.get(stage, False)),
            "verification",
        )
        return {
            "status": "pass" if all(stage_passed.values()) else "fail",
            "current_stage": current_stage,
            "ready_for_implementation": all(
                stage_passed.get(stage, False) for stage in ("concept", "identity", "structure")
            ),
            "ready_for_completion": bool(stage_passed.get("verification")),
            "checks": checks,
            "violations": violations,
            "stages": stages,
            "sequence": list(CISIV_STAGE_SEQUENCE),
        }

    def _evaluate_false_only_check(
        self,
        definition: dict[str, Any],
        compliance: dict[str, Any],
    ) -> dict[str, Any]:
        missing: list[str] = []
        violations: list[str] = []
        for field in definition["fields"]:
            value, alias = _resolve_setting(compliance, field["aliases"])
            if alias is None:
                missing.append(field["label"])
                continue
            coerced = _coerce_bool(value)
            if coerced is None:
                missing.append(field["label"])
            elif coerced:
                violations.append(f"Module declared {field['label']}.")
        passed = not missing and not violations
        if passed:
            reason = definition["law"]
        elif missing:
            reason = f"Missing governance declarations for {', '.join(missing)}."
        else:
            reason = " ".join(violations)
        return {
            "id": definition["id"],
            "label": definition["label"],
            "passed": passed,
            "reason": reason,
            "violations": violations or ([reason] if missing else []),
        }

    def _evaluate_transient_signal_check(
        self,
        definition: dict[str, Any],
        compliance: dict[str, Any],
    ) -> dict[str, Any]:
        uses_live_signals, _used_alias = _resolve_setting(compliance, definition["allowed_signal_field"])
        missing: list[str] = []
        violations: list[str] = []
        signal_labels = _normalize_string_list(uses_live_signals)
        for field in definition["fields"]:
            value, alias = _resolve_setting(compliance, field["aliases"])
            if alias is None:
                missing.append(field["label"])
                continue
            coerced = _coerce_bool(value)
            if coerced is None:
                missing.append(field["label"])
            elif coerced:
                violations.append(f"Module declared {field['label']}.")
        passed = not missing and not violations
        if passed:
            if signal_labels:
                reason = (
                    f"Module may use live signals transiently ({', '.join(signal_labels)}), "
                    "but it does not store or reconstruct them."
                )
            else:
                reason = definition["law"]
        elif missing:
            reason = f"Missing governance declarations for {', '.join(missing)}."
        else:
            reason = " ".join(violations)
        return {
            "id": definition["id"],
            "label": definition["label"],
            "passed": passed,
            "reason": reason,
            "violations": violations or ([reason] if missing else []),
        }

    def _evaluate_identity_dependency_check(
        self,
        definition: dict[str, Any],
        compliance: dict[str, Any],
    ) -> dict[str, Any]:
        identity_field = definition["identity_field"]
        identity_value, identity_alias = _resolve_setting(compliance, identity_field["aliases"])
        adaptive_value, adaptive_alias = _resolve_setting(compliance, definition["adaptive_scope_field"])
        violations: list[str] = []
        missing: list[str] = []
        if identity_alias is None or _coerce_bool(identity_value) is None:
            missing.append(identity_field["label"])
        elif _coerce_bool(identity_value):
            violations.append("Module requires long-term user identity data.")
        if adaptive_alias is None:
            missing.append("adaptive logic scope")
        else:
            adaptive_scope = str(adaptive_value or "").strip().lower()
            if adaptive_scope not in ALLOWED_ADAPTIVE_SCOPES:
                violations.append("Adaptive logic is not system-wide.")
        passed = not missing and not violations
        if passed:
            reason = definition["law"]
        elif missing:
            reason = f"Missing governance declarations for {', '.join(missing)}."
        else:
            reason = " ".join(violations)
        return {
            "id": definition["id"],
            "label": definition["label"],
            "passed": passed,
            "reason": reason,
            "violations": violations or ([reason] if missing else []),
        }

    def _build_runtime_posture(self, *, status: str) -> dict[str, Any]:
        normalized_status = str(status or "rejected").strip().lower()
        if normalized_status == "admitted":
            return {
                "interaction_allowed": True,
                "memory_access": True,
                "routing_access": True,
                "isolated": False,
                "quarantined": False,
                "blacklisted": False,
            }
        if normalized_status == "isolated":
            return {
                "interaction_allowed": False,
                "memory_access": False,
                "routing_access": False,
                "isolated": True,
                "quarantined": False,
                "blacklisted": False,
            }
        if normalized_status == "quarantined":
            return {
                "interaction_allowed": False,
                "memory_access": False,
                "routing_access": False,
                "isolated": True,
                "quarantined": True,
                "blacklisted": False,
            }
        if normalized_status == "blacklisted":
            return {
                "interaction_allowed": False,
                "memory_access": False,
                "routing_access": False,
                "isolated": True,
                "quarantined": True,
                "blacklisted": True,
            }
        return {
            "interaction_allowed": False,
            "memory_access": False,
            "routing_access": False,
            "isolated": False,
            "quarantined": False,
            "blacklisted": False,
        }

    def _status_for_severity(self, severity: str) -> str:
        normalized = str(severity or "medium").strip().lower()
        if normalized == "low":
            return "isolated"
        if normalized == "medium":
            return "quarantined"
        return "blacklisted"

    def _resolution_for_status(self, status: str) -> str:
        normalized = str(status or "").strip().lower()
        if normalized == "isolated":
            return "minor_violation_allow_correction"
        if normalized == "quarantined":
            return "major_violation_disable_module"
        if normalized == "blacklisted":
            return "critical_violation_remove_and_blacklist"
        return "module_restored"

    def _max_severity(self, left: str, right: str) -> str:
        left_rank = SEVERITY_ORDER.get(str(left or "").strip().lower(), 0)
        right_rank = SEVERITY_ORDER.get(str(right or "").strip().lower(), 0)
        return left if left_rank >= right_rank else right

    def _append_event_locked(
        self,
        *,
        event_type: str,
        module_id: str,
        severity: str,
        reason: str,
        details: dict[str, Any],
    ) -> dict[str, Any]:
        event = {
            "id": f"modgov_{uuid.uuid4().hex[:12]}",
            "timestamp": _utc_now_iso(),
            "event_type": event_type,
            "module_id": module_id,
            "severity": severity,
            "reason": _clip_text(reason),
            "details": dict(details or {}),
        }
        self._events.append(event)
        self._events = self._events[-250:]
        return dict(event)

    def _load(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        if self._modules_path.exists():
            try:
                payload = json.loads(self._modules_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    self._modules = {
                        str(key): dict(value)
                        for key, value in payload.items()
                        if isinstance(value, dict)
                    }
            except Exception:
                self._modules = {}
        if self._events_path.exists():
            loaded: list[dict[str, Any]] = []
            for line in self._events_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    loaded.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            self._events = loaded[-250:]
        if self._blacklist_path.exists():
            try:
                payload = json.loads(self._blacklist_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    self._blacklist = {
                        str(key): dict(value)
                        for key, value in payload.items()
                        if isinstance(value, dict)
                    }
            except Exception:
                self._blacklist = {}

    def _persist_locked(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._modules_path.write_text(json.dumps(self._modules, indent=2), encoding="utf-8")
        self._blacklist_path.write_text(json.dumps(self._blacklist, indent=2), encoding="utf-8")
        with self._events_path.open("w", encoding="utf-8") as handle:
            for event in self._events[-250:]:
                handle.write(json.dumps(event, ensure_ascii=True) + "\n")


module_governance = ModuleGovernanceController()
