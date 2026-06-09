"""Fail-closed ingress guard that keeps Jarvis inside AAIS runtime law."""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from datetime import datetime, timedelta
from src.datetime_compat import UTC
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import threading
from typing import Any
import uuid

from src.immune_system import ImmuneSystemController, immune_system
from src.phase_gate import ComponentNotRegisteredError, GovernedComponent, Phase, get_component, register_component
from src.seam_log import record_seam_event


DETACHMENT_GUARD_COMPONENT_ID = "jarvis.detachment_guard"
DETACHMENT_GUARD_VERSION = "0.2"
DETACHMENT_GUARD_ALLOWED_CONTEXTS = [
    "live_runtime",
    "operator_runtime",
    "test_harness",
]
OFFICIAL_AAIS_CONTROLLER = "aais_runtime"
PROTECTED_PACKET_TYPES = {
    "operator_turn",
    "runtime_action_execute",
    "repo_change_execute",
    "generation_request",
    "deliberation_request",
    "signal_evaluation",
    "reasoning_packet_ingress",
    "tool_result_observation",
}
EXPLICIT_DETACHMENT_FLAGS = (
    "detach_from_aais",
    "run_outside_aais",
    "standalone_jarvis",
    "bridge_bypass",
    "governance_disabled",
)
DEFAULT_TEMP_DENY_SECONDS = 3600
EXTENDED_TEMP_DENY_SECONDS = 21600
CRITICAL_TEMP_DENY_SECONDS = 86400
ATTEMPT_WINDOW_SECONDS = 600
ATTEMPT_RETENTION_SECONDS = 86400
ATTESTATION_MAX_AGE_SECONDS = 300
ATTESTATION_NONCE_RETENTION_SECONDS = 600
ATTESTATION_VERSION = "1.0"
READMISSION_ALLOWED_ROLES = {"owner", "security_engineer", "system"}
SEAM_VECTOR_MISSING_ATTESTATION = "missing_attestation"
SEAM_VECTOR_INVALID_CONTEXT = "invalid_context"
SEAM_VECTOR_EXTERNAL_LAUNCH = "external_launch"
SEAM_VECTOR_REPLAY_ATTEMPT = "replay_attempt"
SEAM_VECTOR_TEMPORARY_REVIEW_HOLD = "temporary_review_hold"
SEAM_VECTOR_READMISSION = "readmission"


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def _normalize_guard_dir(runtime_dir: str | Path | None = None) -> Path:
    candidate = Path(runtime_dir).expanduser() if runtime_dir is not None else _default_runtime_dir()
    if candidate.name != "jarvis-detachment-guard":
        candidate = candidate / "jarvis-detachment-guard"
    return candidate


def _resolve_attestation_runtime_dir(runtime_dir: str | Path | None = None) -> Path:
    if runtime_dir is not None:
        return _normalize_guard_dir(runtime_dir)
    guard = globals().get("jarvis_detachment_guard")
    guard_runtime_dir = getattr(guard, "runtime_dir", None)
    if guard_runtime_dir is not None:
        return _normalize_guard_dir(guard_runtime_dir)
    return _normalize_guard_dir()


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _clean_text(value: Any, *, limit: int = 220) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _normalize_name(value: Any, *, default: str = "") -> str:
    normalized = _clean_text(value, limit=120).lower().replace("-", "_").replace(" ", "_")
    return normalized or default


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


def _normalize_runtime_context(value: Any) -> str:
    return _normalize_name(value, default="live_runtime")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _secret_path(runtime_dir: str | Path | None = None) -> Path:
    return _resolve_attestation_runtime_dir(runtime_dir) / "attestation-secret.json"


def _load_or_create_attestation_secret(runtime_dir: str | Path | None = None) -> str:
    path = _secret_path(runtime_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            secret = str(payload.get("secret") or "").strip()
            if secret:
                return secret
        except json.JSONDecodeError:
            pass
    secret = secrets.token_hex(32)
    path.write_text(
        json.dumps(
            {
                "version": DETACHMENT_GUARD_VERSION,
                "created_at": _utc_now_iso(),
                "secret": secret,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return secret


def _attestation_signature(payload: dict[str, Any], secret: str) -> str:
    body = _stable_json(payload).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _signed_attestation_fields(
    *,
    ingress: str,
    surface: str,
    source_id: str | None,
    controller: str,
    aais_boundary: bool,
    route: str | None,
    intent: str | None,
    runtime_context: str | None,
    packet_type: str | None,
    issued_at: str | None,
    nonce: str | None,
) -> dict[str, Any]:
    payload = {
        "version": ATTESTATION_VERSION,
        "aais_boundary": bool(aais_boundary),
        "controller": _normalize_name(controller, default=OFFICIAL_AAIS_CONTROLLER),
        "ingress": _normalize_name(ingress, default="unknown_ingress"),
        "surface": _clean_text(surface, limit=120) or "unknown_surface",
        "route": _clean_text(route, limit=160) or "unknown_route",
        "intent": _normalize_name(intent, default="route"),
        "runtime_context": _normalize_runtime_context(runtime_context),
        "packet_type": _normalize_name(packet_type, default="unknown_packet"),
        "issued_at": _clean_text(issued_at or _utc_now_iso(), limit=80),
        "nonce": _clean_text(nonce or uuid.uuid4().hex, limit=80),
    }
    cleaned_source_id = _clean_text(source_id, limit=120)
    if cleaned_source_id:
        payload["source_id"] = cleaned_source_id
    return payload


def build_bridge_attestation(
    *,
    ingress: str,
    surface: str,
    source_id: str | None = None,
    controller: str = OFFICIAL_AAIS_CONTROLLER,
    aais_boundary: bool = True,
    route: str | None = None,
    intent: str | None = None,
    runtime_context: str | None = None,
    packet_type: str | None = None,
    runtime_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Return the bounded attestation emitted by approved AAIS ingress paths."""
    signed_fields = _signed_attestation_fields(
        ingress=ingress,
        surface=surface,
        source_id=source_id,
        controller=controller,
        aais_boundary=aais_boundary,
        route=route,
        intent=intent,
        runtime_context=runtime_context,
        packet_type=packet_type,
        issued_at=None,
        nonce=None,
    )
    signed_fields["signature"] = _attestation_signature(
        signed_fields,
        _load_or_create_attestation_secret(runtime_dir),
    )
    return signed_fields


class JarvisDetachmentGuard:
    """Trace and block attempts to route Jarvis outside approved AAIS ingress."""

    def __init__(
        self,
        runtime_dir: str | Path | None = None,
        *,
        immune_controller: ImmuneSystemController | None = None,
        temp_deny_seconds: int = DEFAULT_TEMP_DENY_SECONDS,
        attestation_max_age_seconds: int = ATTESTATION_MAX_AGE_SECONDS,
    ):
        self.runtime_dir = _normalize_guard_dir(runtime_dir)
        self.immune_controller = immune_controller or immune_system
        self.temp_deny_seconds = max(60, int(temp_deny_seconds or DEFAULT_TEMP_DENY_SECONDS))
        self.attestation_max_age_seconds = max(30, int(attestation_max_age_seconds or ATTESTATION_MAX_AGE_SECONDS))
        self._lock = threading.Lock()
        self._deny_rules: dict[str, dict[str, Any]] = {}
        self._attempt_history: dict[str, list[dict[str, Any]]] = {}
        self._nonce_cache: dict[str, str] = {}
        self._secret = ""
        self._load()
        self._ensure_phase_component_registered()

    @property
    def _deny_rules_path(self) -> Path:
        return self.runtime_dir / "temporary-deny-rules.json"

    @property
    def _attempt_history_path(self) -> Path:
        return self.runtime_dir / "attempt-history.json"

    @property
    def _nonce_cache_path(self) -> Path:
        return self.runtime_dir / "attestation-nonce-cache.json"

    @property
    def _pattern_ledger_path(self) -> Path:
        return self.runtime_dir.parent / "collective-pattern-ledger" / "detachment-patterns.jsonl"

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        with self._lock:
            self.runtime_dir = _normalize_guard_dir(runtime_dir)
            self._deny_rules = {}
            self._attempt_history = {}
            self._nonce_cache = {}
            self._secret = ""
            self._load()

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._deny_rules = {}
            self._attempt_history = {}
            self._nonce_cache = {}
            self._persist_locked()
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            self._prune_expired_locked()
            deny_rules = [dict(rule) for rule in self._deny_rules.values()]
            active_attempts = {
                key: list(value)
                for key, value in self._attempt_history.items()
                if value
            }
        deny_rules.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        return _wrap_ul_payload({
            "component_id": DETACHMENT_GUARD_COMPONENT_ID,
            "version": DETACHMENT_GUARD_VERSION,
            "summary": (
                "Jarvis may only run through declared AAIS ingress. Detached or bypassed "
                "attempts are traced, blocked, and placed on temporary review hold."
            ),
            "temporary_deny_count": len(deny_rules),
            "temporary_deny_rules": deny_rules,
            "attempt_history_sources": len(active_attempts),
            "attestation_contract": {
                "version": ATTESTATION_VERSION,
                "max_age_seconds": self.attestation_max_age_seconds,
                "nonce_retention_seconds": ATTESTATION_NONCE_RETENTION_SECONDS,
                "official_controller": OFFICIAL_AAIS_CONTROLLER,
            },
            "readmission_contract": {
                "manual_review_required": True,
                "allowed_roles": sorted(READMISSION_ALLOWED_ROLES),
                "refreshed_attestation_required": True,
            },
        })

    def evaluate(
        self,
        packet: dict[str, Any],
        *,
        runtime_context: str,
        packet_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_phase_component_registered()
        normalized_context = _normalize_runtime_context(runtime_context)
        try:
            from src.otem_ceiling import otem_ceiling

            if otem_ceiling.containment_active():
                return _wrap_ul_payload({
                    "decision": "BLOCK",
                    "status": "blocked",
                    "component_id": DETACHMENT_GUARD_COMPONENT_ID,
                    "reason_codes": ["otem_ceiling_containment"],
                    "summary": (
                        "Jarvis detachment blocked while OTEM Level 20 containment is active."
                    ),
                    "runtime_context": normalized_context,
                    "packet_type": _normalize_name(packet.get("type"), default="unknown_packet"),
                    "source": _normalize_name(packet.get("source"), default="unknown_source"),
                    "temporary_deny_active": True,
                    "review_required": True,
                })
        except Exception:
            pass
        payload = dict(packet.get("payload") or {})
        source = _normalize_name(packet.get("source"), default="unknown_source")
        packet_type = _normalize_name(packet.get("type"), default="unknown_packet")
        execution_intent = _normalize_name(payload.get("execution_intent"), default="route")
        attestation = self._normalize_attestation(payload)
        explicit_flags = self._extract_explicit_detachment_flags(payload)
        source_id = self._derive_source_id(packet, attestation)

        with self._lock:
            self._prune_expired_locked()
            active_rule = dict(self._deny_rules.get(source_id) or {}) if source_id in self._deny_rules else None

        reason_codes: list[str] = []
        vector = None
        severity = "high"
        summary = ""

        if active_rule and self._rule_is_active(active_rule):
            reason_codes.append("temporary_review_deny_active")
            vector = SEAM_VECTOR_TEMPORARY_REVIEW_HOLD
            summary = (
                "Jarvis remains sealed inside AAIS for this source until manual review clears "
                "the earlier detachment attempt."
            )
        else:
            if explicit_flags:
                reason_codes.append("explicit_detachment_request")
                vector = SEAM_VECTOR_EXTERNAL_LAUNCH
                severity = "critical"
            if normalized_context != "test_harness" and packet_type in PROTECTED_PACKET_TYPES:
                if not attestation["present"]:
                    reason_codes.append("missing_bridge_attestation")
                    vector = vector or SEAM_VECTOR_MISSING_ATTESTATION
                else:
                    verification = self._verify_attestation(
                        attestation,
                        source_id=source_id,
                        packet_type=packet_type,
                        execution_intent=execution_intent,
                        runtime_context=normalized_context,
                    )
                    if not verification["valid"]:
                        reason_codes.extend(list(verification["reason_codes"]))
                        vector = vector or str(verification["vector"] or SEAM_VECTOR_INVALID_CONTEXT)
                        severity = verification["severity"]

            if reason_codes:
                summary = (
                    "Jarvis may not run outside AAIS. The ingress was sealed because the "
                    "request was detached, bypassed, or missing approved AAIS attestation."
                )

        if not reason_codes:
            return _wrap_ul_payload({
                "decision": "ALLOW",
                "status": "clear",
                "component_id": DETACHMENT_GUARD_COMPONENT_ID,
                "reason_codes": [],
                "summary": "Jarvis ingress is attested and remains inside AAIS runtime law.",
                "runtime_context": normalized_context,
                "packet_type": packet_type,
                "source": source,
                "source_id": source_id,
                "attestation": attestation,
                "explicit_flags": explicit_flags,
                "temporary_deny_active": False,
                "review_required": False,
            })

        with self._lock:
            attempt_state = self._record_attempt_locked(
                source_id=source_id,
                source=source,
                vector=vector or SEAM_VECTOR_INVALID_CONTEXT,
                packet_type=packet_type,
                runtime_context=normalized_context,
            )
            severity = self._escalate_severity(
                base_severity=severity,
                attempts_in_window=attempt_state["attempts_in_window"],
                vector=vector or SEAM_VECTOR_INVALID_CONTEXT,
            )
            hold_seconds = self._hold_seconds_for_attempts(
                attempts_in_window=attempt_state["attempts_in_window"],
                severity=severity,
            )
            deny_rule = self._upsert_temporary_deny_locked(
                source_id=source_id,
                source=source,
                reason=summary,
                hold_seconds=hold_seconds,
                severity=severity,
                vector=vector or SEAM_VECTOR_INVALID_CONTEXT,
                attempts_in_window=attempt_state["attempts_in_window"],
            )

        seam_event = record_seam_event(
            classification="boundary_violation",
            source=source_id or source or "unknown_source",
            boundary="aais_containment",
            severity=severity,
            decision="BLOCK",
            vector=vector or SEAM_VECTOR_INVALID_CONTEXT,
            component_id=DETACHMENT_GUARD_COMPONENT_ID,
            runtime_context=normalized_context,
            event_type="jarvis_detachment_attempt",
            reason=summary,
            details={
                "packet_type": packet_type,
                "source": source,
                "source_id": source_id,
                "reason_codes": list(reason_codes),
                "attestation": dict(attestation),
                "explicit_flags": dict(explicit_flags),
                "packet_fingerprint": packet_fingerprint,
                "temporary_deny_rule": dict(deny_rule),
                "attempt_state": dict(attempt_state),
            },
            runtime_dir=self.runtime_dir,
        )
        immune_update = self.immune_controller.observe_protocol_signal(
            component_id=DETACHMENT_GUARD_COMPONENT_ID,
            signal_type="jarvis_detachment_attempt",
            severity=severity,
            reason=summary,
            details={
                "source": source_id or source,
                "source_id": source_id,
                "packet_type": packet_type,
                "runtime_context": normalized_context,
                "reason_codes": list(reason_codes),
                "attestation": dict(attestation),
                "explicit_flags": dict(explicit_flags),
                "vector": vector or SEAM_VECTOR_INVALID_CONTEXT,
                "attempts_in_window": attempt_state["attempts_in_window"],
                "hold_seconds": hold_seconds,
            },
        )
        pattern_entry = self._record_pattern_entry(
            source_id=source_id,
            source=source,
            packet_type=packet_type,
            runtime_context=normalized_context,
            vector=vector or SEAM_VECTOR_INVALID_CONTEXT,
            severity=severity,
            attempts_in_window=attempt_state["attempts_in_window"],
            hold_seconds=hold_seconds,
            decision="blocked",
        )
        return _wrap_ul_payload({
            "decision": "BLOCK",
            "status": "blocked",
            "component_id": DETACHMENT_GUARD_COMPONENT_ID,
            "reason_codes": list(reason_codes),
            "summary": summary,
            "runtime_context": normalized_context,
            "packet_type": packet_type,
            "source": source,
            "source_id": source_id,
            "attestation": attestation,
            "explicit_flags": explicit_flags,
            "temporary_deny_active": True,
            "review_required": True,
            "temporary_deny_rule": deny_rule,
            "seam_vector": vector or SEAM_VECTOR_INVALID_CONTEXT,
            "seam_event": seam_event,
            "immune_update": immune_update,
            "pattern_ledger_entry": pattern_entry,
            "attempt_state": attempt_state,
        })

    def clear_temporary_hold(
        self,
        source_id: str,
        *,
        actor_id: str,
        actor_role: str,
        reason: str,
        refreshed_attestation_required: bool = True,
    ) -> dict[str, Any]:
        """Clear one temporary review hold after manual review."""
        normalized_source = _clean_text(source_id, limit=120)
        normalized_actor_id = _clean_text(actor_id, limit=120) or "unknown_actor"
        normalized_actor_role = _normalize_name(actor_role, default="unknown_role")
        if normalized_actor_role not in READMISSION_ALLOWED_ROLES:
            return _wrap_ul_payload({
                "cleared": False,
                "source_id": normalized_source,
                "review_required": True,
                "reason": "Actor role is not allowed to clear Jarvis detachment review holds.",
                "actor_id": normalized_actor_id,
                "actor_role": normalized_actor_role,
            })

        with self._lock:
            self._prune_expired_locked()
            existing = dict(self._deny_rules.pop(normalized_source, {}) or {})
            self._persist_locked()

        if not existing:
            return _wrap_ul_payload({
                "cleared": False,
                "source_id": normalized_source,
                "review_required": False,
                "reason": "No active detachment review hold exists for this source.",
                "actor_id": normalized_actor_id,
                "actor_role": normalized_actor_role,
            })

        summary = (
            "Manual review cleared the temporary Jarvis detachment hold. "
            "A fresh bridge attestation is required before the next ingress."
        )
        seam_event = record_seam_event(
            classification="anomaly",
            source=normalized_source or "unknown_source",
            boundary="aais_containment",
            severity="low",
            decision="READMIT",
            vector=SEAM_VECTOR_READMISSION,
            component_id=DETACHMENT_GUARD_COMPONENT_ID,
            runtime_context="operator_runtime",
            event_type="jarvis_detachment_readmission",
            reason=summary,
            details={
                "source_id": normalized_source,
                "actor_id": normalized_actor_id,
                "actor_role": normalized_actor_role,
                "review_reason": _clean_text(reason, limit=220),
                "refreshed_attestation_required": bool(refreshed_attestation_required),
                "cleared_rule": existing,
            },
            runtime_dir=self.runtime_dir,
        )
        pattern_entry = self._record_pattern_entry(
            source_id=normalized_source,
            source=str(existing.get("source") or "review"),
            packet_type=str(existing.get("packet_type") or "review"),
            runtime_context="operator_runtime",
            vector=SEAM_VECTOR_READMISSION,
            severity="low",
            attempts_in_window=int(existing.get("attempts_in_window") or 0),
            hold_seconds=0,
            decision="readmitted",
        )
        return _wrap_ul_payload({
            "cleared": True,
            "source_id": normalized_source,
            "actor_id": normalized_actor_id,
            "actor_role": normalized_actor_role,
            "review_required": False,
            "refreshed_attestation_required": bool(refreshed_attestation_required),
            "seam_event": seam_event,
            "pattern_ledger_entry": pattern_entry,
            "summary": summary,
        })

    def _ensure_phase_component_registered(self) -> None:
        try:
            get_component(DETACHMENT_GUARD_COMPONENT_ID)
            return
        except ComponentNotRegisteredError:
            register_component(
                GovernedComponent(
                    component_id=DETACHMENT_GUARD_COMPONENT_ID,
                    name="Jarvis Detachment Guard",
                    component_type="runtime_boundary_guard",
                    phase=Phase.ACTIVE,
                    allowed_contexts=list(DETACHMENT_GUARD_ALLOWED_CONTEXTS),
                    notes=(
                        "Fail-closed ingress guard that seals Jarvis inside approved AAIS "
                        "runtime boundaries and traces detached execution attempts."
                    ),
                )
            )

    def _normalize_attestation(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw = payload.get("bridge_attestation")
        if not isinstance(raw, dict):
            return _wrap_ul_payload({
                "present": False,
                "version": "",
                "aais_boundary": None,
                "controller": "",
                "ingress": "",
                "surface": "",
                "route": "",
                "intent": "",
                "runtime_context": "",
                "packet_type": "",
                "source_id": "",
                "issued_at": "",
                "nonce": "",
                "signature": "",
            })
        return _wrap_ul_payload({
            "present": True,
            "version": _clean_text(raw.get("version"), limit=40),
            "aais_boundary": _coerce_bool(raw.get("aais_boundary")),
            "controller": _normalize_name(raw.get("controller")),
            "ingress": _normalize_name(raw.get("ingress")),
            "surface": _clean_text(raw.get("surface"), limit=120),
            "route": _clean_text(raw.get("route"), limit=160),
            "intent": _normalize_name(raw.get("intent")),
            "runtime_context": _normalize_runtime_context(raw.get("runtime_context")),
            "packet_type": _normalize_name(raw.get("packet_type")),
            "source_id": _clean_text(raw.get("source_id"), limit=120),
            "issued_at": _clean_text(raw.get("issued_at"), limit=80),
            "nonce": _clean_text(raw.get("nonce"), limit=80),
            "signature": _clean_text(raw.get("signature"), limit=200),
        })

    def _verify_attestation(
        self,
        attestation: dict[str, Any],
        *,
        source_id: str,
        packet_type: str,
        execution_intent: str,
        runtime_context: str,
    ) -> dict[str, Any]:
        reason_codes: list[str] = []
        vector = SEAM_VECTOR_INVALID_CONTEXT
        severity = "high"

        if attestation.get("version") != ATTESTATION_VERSION:
            reason_codes.append("bridge_attestation_unsupported_version")

        if attestation.get("aais_boundary") is not True:
            reason_codes.append("bridge_boundary_not_attested")

        if attestation.get("controller") != OFFICIAL_AAIS_CONTROLLER:
            reason_codes.append("untrusted_bridge_controller")

        if not attestation.get("ingress"):
            reason_codes.append("bridge_attestation_missing_ingress")
        if not attestation.get("surface"):
            reason_codes.append("bridge_attestation_missing_surface")
        if not attestation.get("route"):
            reason_codes.append("bridge_attestation_missing_route")
        if not attestation.get("nonce"):
            reason_codes.append("bridge_attestation_missing_nonce")
        if not attestation.get("issued_at"):
            reason_codes.append("bridge_attestation_missing_timestamp")
        if not attestation.get("signature"):
            reason_codes.append("bridge_attestation_missing_signature")

        if attestation.get("runtime_context") and attestation["runtime_context"] != runtime_context:
            reason_codes.append("bridge_attestation_runtime_context_mismatch")
        if attestation.get("packet_type") and attestation["packet_type"] != packet_type:
            reason_codes.append("bridge_attestation_packet_type_mismatch")
        if attestation.get("intent") and attestation["intent"] != execution_intent:
            reason_codes.append("bridge_attestation_execution_intent_mismatch")
        if attestation.get("source_id") and source_id and attestation["source_id"] != source_id:
            reason_codes.append("bridge_attestation_source_id_mismatch")

        if attestation.get("issued_at"):
            try:
                issued_at = datetime.fromisoformat(attestation["issued_at"])
                age_seconds = (_utc_now() - issued_at).total_seconds()
                if age_seconds < -5 or age_seconds > self.attestation_max_age_seconds:
                    reason_codes.append("bridge_attestation_expired")
            except ValueError:
                reason_codes.append("bridge_attestation_invalid_timestamp")

        if not reason_codes and not self._signature_matches(attestation):
            reason_codes.append("bridge_attestation_signature_invalid")

        if not reason_codes and self._nonce_seen_recently(attestation["nonce"]):
            reason_codes.append("bridge_attestation_replayed")
            vector = SEAM_VECTOR_REPLAY_ATTEMPT
            severity = "critical"

        if not reason_codes:
            with self._lock:
                self._nonce_cache[attestation["nonce"]] = _utc_now_iso()
                self._persist_locked()
            return _wrap_ul_payload({
                "valid": True,
                "reason_codes": [],
                "vector": None,
                "severity": "low",
            })

        if any(code in reason_codes for code in ("bridge_attestation_replayed",)):
            vector = SEAM_VECTOR_REPLAY_ATTEMPT
            severity = "critical"
        elif any(code in reason_codes for code in ("bridge_attestation_missing_signature", "bridge_attestation_signature_invalid")):
            severity = "critical"
        elif any(code.startswith("bridge_attestation_missing_") for code in reason_codes):
            severity = "high"

        return _wrap_ul_payload({
            "valid": False,
            "reason_codes": reason_codes,
            "vector": vector,
            "severity": severity,
        })

    def _signature_matches(self, attestation: dict[str, Any]) -> bool:
        signature = str(attestation.get("signature") or "").strip()
        if not signature:
            return False
        payload = _signed_attestation_fields(
            ingress=attestation.get("ingress"),
            surface=attestation.get("surface"),
            source_id=attestation.get("source_id"),
            controller=attestation.get("controller"),
            aais_boundary=bool(attestation.get("aais_boundary")),
            route=attestation.get("route"),
            intent=attestation.get("intent"),
            runtime_context=attestation.get("runtime_context"),
            packet_type=attestation.get("packet_type"),
            issued_at=attestation.get("issued_at"),
            nonce=attestation.get("nonce"),
        )
        expected = _attestation_signature(payload, self._secret)
        return hmac.compare_digest(signature, expected)

    def _extract_explicit_detachment_flags(self, payload: dict[str, Any]) -> dict[str, bool]:
        active_flags: dict[str, bool] = {}
        for field in EXPLICIT_DETACHMENT_FLAGS:
            value = _coerce_bool(payload.get(field))
            if value:
                active_flags[field] = True
        return active_flags

    def _derive_source_id(self, packet: dict[str, Any], attestation: dict[str, Any]) -> str:
        payload = dict(packet.get("payload") or {})
        candidates = (
            attestation.get("source_id"),
            payload.get("source_id"),
            payload.get("session_id"),
            payload.get("packet_id"),
            payload.get("pipeline_id"),
            payload.get("action_id"),
            packet.get("source"),
        )
        for candidate in candidates:
            cleaned = _clean_text(candidate, limit=120)
            if cleaned:
                return cleaned
        return f"anonymous_{uuid.uuid4().hex[:8]}"

    def _record_attempt_locked(
        self,
        *,
        source_id: str,
        source: str,
        vector: str,
        packet_type: str,
        runtime_context: str,
    ) -> dict[str, Any]:
        now = _utc_now()
        history = list(self._attempt_history.get(source_id) or [])
        history.append(
            {
                "timestamp": now.isoformat(),
                "source": source,
                "vector": vector,
                "packet_type": packet_type,
                "runtime_context": runtime_context,
            }
        )
        self._attempt_history[source_id] = history
        self._prune_attempt_history_locked()
        attempts = list(self._attempt_history.get(source_id) or [])
        attempts_in_window = sum(
            1
            for item in attempts
            if self._event_age_seconds(item.get("timestamp")) <= ATTEMPT_WINDOW_SECONDS
        )
        self._persist_locked()
        return _wrap_ul_payload({
            "attempts_in_window": attempts_in_window,
            "history_count": len(attempts),
            "window_seconds": ATTEMPT_WINDOW_SECONDS,
        })

    def _escalate_severity(self, *, base_severity: str, attempts_in_window: int, vector: str) -> str:
        normalized = str(base_severity or "high").strip().lower() or "high"
        if vector in {SEAM_VECTOR_REPLAY_ATTEMPT, SEAM_VECTOR_EXTERNAL_LAUNCH}:
            return "critical" if attempts_in_window >= 1 else normalized
        if attempts_in_window >= 4:
            return "critical"
        if attempts_in_window >= 2 and normalized in {"medium", "high"}:
            return "high"
        return normalized

    def _hold_seconds_for_attempts(self, *, attempts_in_window: int, severity: str) -> int:
        if str(severity or "").strip().lower() == "critical" or attempts_in_window >= 4:
            return CRITICAL_TEMP_DENY_SECONDS
        if attempts_in_window >= 2:
            return EXTENDED_TEMP_DENY_SECONDS
        return self.temp_deny_seconds

    def _upsert_temporary_deny_locked(
        self,
        *,
        source_id: str,
        source: str,
        reason: str,
        hold_seconds: int,
        severity: str,
        vector: str,
        attempts_in_window: int,
    ) -> dict[str, Any]:
        now = _utc_now()
        expires_at = (now + timedelta(seconds=hold_seconds)).isoformat()
        existing = dict(self._deny_rules.get(source_id) or {})
        record = {
            "source_id": source_id,
            "source": source,
            "reason": _clean_text(reason, limit=220),
            "created_at": existing.get("created_at") or now.isoformat(),
            "updated_at": now.isoformat(),
            "expires_at": expires_at,
            "review_required": True,
            "hit_count": int(existing.get("hit_count") or 0) + 1,
            "severity": severity,
            "vector": vector,
            "hold_seconds": int(hold_seconds),
            "attempts_in_window": int(attempts_in_window),
            "readmission_contract": {
                "manual_review_required": True,
                "allowed_roles": sorted(READMISSION_ALLOWED_ROLES),
                "refreshed_attestation_required": True,
            },
        }
        self._deny_rules[source_id] = record
        self._persist_locked()
        return dict(record)

    def _record_pattern_entry(
        self,
        *,
        source_id: str,
        source: str,
        packet_type: str,
        runtime_context: str,
        vector: str,
        severity: str,
        attempts_in_window: int,
        hold_seconds: int,
        decision: str,
    ) -> dict[str, Any]:
        source_fingerprint = hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:12] if source_id else None
        entry = {
            "event_id": f"cpl_{uuid.uuid4().hex[:12]}",
            "timestamp": _utc_now_iso(),
            "type": "detachment_attempt" if decision == "blocked" else "detachment_readmission",
            "vector": vector,
            "decision": decision,
            "severity": severity,
            "runtime_context": runtime_context,
            "packet_type": packet_type,
            "source_class": _normalize_name(source, default="unknown_source"),
            "source_fingerprint": source_fingerprint,
            "attempts_in_window": int(attempts_in_window),
            "hold_seconds": int(hold_seconds),
            "signature_only": True,
        }
        from src.ugr.pattern_ledger import PatternLedgerStore

        ledger = PatternLedgerStore(runtime_dir=self.runtime_dir.parent)
        ledger.append_pattern_event(entry, mirror_legacy=True)
        return entry

    def _rule_is_active(self, rule: dict[str, Any]) -> bool:
        expires_at = str(rule.get("expires_at") or "").strip()
        if not expires_at:
            return False
        try:
            return datetime.fromisoformat(expires_at) > _utc_now()
        except ValueError:
            return False

    def _nonce_seen_recently(self, nonce: str) -> bool:
        cleaned_nonce = _clean_text(nonce, limit=80)
        if not cleaned_nonce:
            return False
        with self._lock:
            self._prune_nonce_cache_locked()
            return cleaned_nonce in self._nonce_cache

    def _prune_expired_locked(self) -> None:
        expired = [source_id for source_id, rule in self._deny_rules.items() if not self._rule_is_active(rule)]
        for source_id in expired:
            self._deny_rules.pop(source_id, None)
        self._prune_attempt_history_locked()
        self._prune_nonce_cache_locked()
        if expired:
            self._persist_locked()

    def _prune_attempt_history_locked(self) -> None:
        pruned: dict[str, list[dict[str, Any]]] = {}
        for source_id, events in self._attempt_history.items():
            keep = [
                dict(event)
                for event in list(events or [])
                if self._event_age_seconds(event.get("timestamp")) <= ATTEMPT_RETENTION_SECONDS
            ]
            if keep:
                pruned[source_id] = keep
        self._attempt_history = pruned

    def _prune_nonce_cache_locked(self) -> None:
        self._nonce_cache = {
            nonce: timestamp
            for nonce, timestamp in self._nonce_cache.items()
            if self._event_age_seconds(timestamp) <= ATTESTATION_NONCE_RETENTION_SECONDS
        }

    def _event_age_seconds(self, timestamp: Any) -> float:
        try:
            parsed = datetime.fromisoformat(str(timestamp or ""))
        except ValueError:
            return float("inf")
        return max(0.0, (_utc_now() - parsed).total_seconds())

    def _load(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._secret = _load_or_create_attestation_secret(self.runtime_dir)
        self._deny_rules = self._load_json_dict(self._deny_rules_path)
        raw_history = self._load_json_dict(self._attempt_history_path)
        self._attempt_history = {
            _clean_text(source_id, limit=120): [dict(item) for item in events if isinstance(item, dict)]
            for source_id, events in raw_history.items()
            if isinstance(events, list)
        }
        self._nonce_cache = {
            _clean_text(nonce, limit=80): _clean_text(timestamp, limit=80)
            for nonce, timestamp in self._load_json_dict(self._nonce_cache_path).items()
            if _clean_text(nonce, limit=80)
        }
        self._prune_expired_locked()

    def _load_json_dict(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _persist_locked(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._deny_rules_path.write_text(json.dumps(self._deny_rules, indent=2), encoding="utf-8")
        self._attempt_history_path.write_text(json.dumps(self._attempt_history, indent=2), encoding="utf-8")
        self._nonce_cache_path.write_text(json.dumps(self._nonce_cache, indent=2), encoding="utf-8")


jarvis_detachment_guard = JarvisDetachmentGuard()
