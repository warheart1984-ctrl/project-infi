"""Automatic Discovery Pod admission — decide if an operator merits pod registration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.ugr.discovery.proven_contribution import is_proven_contribution

UGR_POD_AUTO_ADMIT_ENV = "UGR_POD_AUTO_ADMIT"
UGR_POD_MIN_INVARIANT_PASS_COUNT_ENV = "UGR_POD_MIN_INVARIANT_PASS_COUNT"
UGR_POD_EXPLICIT_REQUIRES_RECEIPT_ENV = "UGR_POD_EXPLICIT_REQUIRES_RECEIPT"
ADMISSION_POLICY_PATH_ENV = "UGR_DISCOVERY_POD_ADMISSION_POLICY_PATH"

_DEFAULT_POLICY: dict[str, Any] = {
    "version": "1.0",
    "auto_admit_enabled": True,
    "explicit_pod_fields_always_admit": True,
    "explicit_pod_requires_receipt": False,
    "admit_on_proven": True,
    "admit_deferred_types_when_proven": True,
    "admit_contribution_types": ["proof", "subsystem", "organ", "invariant", "workflow"],
    "defer_types_until_proven": ["capability", "substrate"],
    "deny_operator_slugs": ["anonymous", "default", "local", "system", "unknown"],
    "require_verifiable_receipt": True,
    "min_invariant_pass_count": 1,
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_admission_policy_path() -> Path:
    override = os.environ.get(ADMISSION_POLICY_PATH_ENV, "").strip()
    if override:
        return Path(override)
    return _repo_root() / "deploy" / "ugr" / "discovery-pod-admission.json"


def pod_auto_admit_enabled() -> bool:
    raw = os.getenv(UGR_POD_AUTO_ADMIT_ENV, "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def explicit_pod_requires_receipt_from_policy(pol: dict[str, Any]) -> bool:
    """Policy default, overridable via UGR_POD_EXPLICIT_REQUIRES_RECEIPT."""
    raw = os.getenv(UGR_POD_EXPLICIT_REQUIRES_RECEIPT_ENV, "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return bool(pol.get("explicit_pod_requires_receipt", False))


def min_invariant_pass_count_from_policy(pol: dict[str, Any]) -> int:
    """Policy file default, overridable via UGR_POD_MIN_INVARIANT_PASS_COUNT."""
    raw = os.getenv(UGR_POD_MIN_INVARIANT_PASS_COUNT_ENV, "").strip()
    if raw.lstrip("-").isdigit():
        return int(raw)
    return int(pol.get("min_invariant_pass_count") or 0)


def load_pod_admission_policy(path: str | Path | None = None) -> dict[str, Any]:
    policy_path = Path(path) if path else default_admission_policy_path()
    if not policy_path.exists():
        return dict(_DEFAULT_POLICY)
    try:
        loaded = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(_DEFAULT_POLICY)
    merged = dict(_DEFAULT_POLICY)
    merged.update({k: v for k, v in loaded.items() if v is not None})
    return merged


def _slug_list(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {str(v).strip().lower() for v in values if str(v).strip()}


def _explicit_pod_intent(spec_payload: dict[str, Any] | None) -> bool:
    payload = dict(spec_payload or {})
    for key in ("discovery_pod_id", "pod_id", "pod_display_name", "display_name"):
        if str(payload.get(key) or "").strip():
            return True
    return False


def _invariant_pass_count(receipt: dict[str, Any] | None) -> int:
    if not receipt:
        return 0
    count = 0
    for inv in receipt.get("invariants_passed") or []:
        if str(inv.get("status") or "").strip().lower() == "pass":
            count += 1
    return count


@dataclass
class PodAdmissionVerdict:
    eligible: bool
    reason: str = ""
    signals: list[str] = field(default_factory=list)
    policy_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "reason": self.reason,
            "signals": list(self.signals),
            "policy_version": self.policy_version,
        }


def evaluate_pod_admission(
    *,
    operator_id: str,
    contribution_type: str,
    spec_payload: dict[str, Any] | None = None,
    receipt: dict[str, Any] | None = None,
    receipt_verified: bool | None = None,
    operator_slug: str = "",
    policy: dict[str, Any] | None = None,
) -> PodAdmissionVerdict:
    """Return whether this discovery warrants registering a new Discovery Pod."""
    pol = policy or load_pod_admission_policy()
    version = str(pol.get("version") or "1.0")
    signals: list[str] = []

    if not pod_auto_admit_enabled():
        return PodAdmissionVerdict(
            eligible=False,
            reason="pod_auto_admit_disabled",
            policy_version=version,
        )

    if not pol.get("auto_admit_enabled", True):
        return PodAdmissionVerdict(
            eligible=False,
            reason="admission_policy_disabled",
            policy_version=version,
        )

    slug = str(operator_slug or "").strip().lower()
    if not slug and operator_id:
        from src.ugr.discovery.discovery_pod_ledger import id_slug_from_prefixed_id, slugify_pod_name

        raw = str(operator_id).strip()
        if raw.startswith("operator:"):
            slug = id_slug_from_prefixed_id(raw, prefix="operator")
        else:
            slug = slugify_pod_name(raw)

    deny = _slug_list(pol.get("deny_operator_slugs"))
    if slug in deny:
        return PodAdmissionVerdict(
            eligible=False,
            reason=f"operator_slug_denied:{slug}",
            policy_version=version,
        )

    payload = dict(spec_payload or {})
    ctype = str(contribution_type or "").strip().lower()
    receipt_obj = dict(receipt or {})
    proven = bool(receipt_obj) and is_proven_contribution(receipt_obj)
    explicit = _explicit_pod_intent(payload)

    explicit_requires_receipt = explicit_pod_requires_receipt_from_policy(pol)
    if (
        explicit
        and pol.get("explicit_pod_fields_always_admit", True)
        and not explicit_requires_receipt
    ):
        signals.append("explicit_pod_intent")
        return PodAdmissionVerdict(
            eligible=True,
            reason="explicit_pod_fields",
            signals=signals,
            policy_version=version,
        )

    if proven and pol.get("admit_on_proven", True):
        signals.append("proven_contribution")
        return PodAdmissionVerdict(
            eligible=True,
            reason="proven_contribution",
            signals=signals,
            policy_version=version,
        )

    if pol.get("require_verifiable_receipt", True):
        if receipt_verified is False:
            reason = (
                "explicit_pod_requires_receipt"
                if explicit and explicit_requires_receipt
                else "receipt_not_verified"
            )
            return PodAdmissionVerdict(
                eligible=False,
                reason=reason,
                signals=signals,
                policy_version=version,
            )
        if receipt_obj and not str(receipt_obj.get("receipt_sig") or "").strip():
            reason = (
                "explicit_pod_requires_receipt"
                if explicit and explicit_requires_receipt
                else "receipt_unsigned"
            )
            return PodAdmissionVerdict(
                eligible=False,
                reason=reason,
                signals=signals,
                policy_version=version,
            )
        if explicit and explicit_requires_receipt and not receipt_obj:
            return PodAdmissionVerdict(
                eligible=False,
                reason="explicit_pod_requires_receipt",
                signals=signals,
                policy_version=version,
            )

    min_pass = min_invariant_pass_count_from_policy(pol)
    pass_count = _invariant_pass_count(receipt_obj)
    if min_pass > 0 and pass_count < min_pass:
        return PodAdmissionVerdict(
            eligible=False,
            reason="insufficient_invariant_passes",
            signals=signals,
            policy_version=version,
        )

    defer = _slug_list(pol.get("defer_types_until_proven"))
    if ctype in defer:
        if proven and pol.get("admit_deferred_types_when_proven", True):
            signals.append("deferred_type_proven")
            return PodAdmissionVerdict(
                eligible=True,
                reason=f"deferred_type_proven:{ctype}",
                signals=signals,
                policy_version=version,
            )
        return PodAdmissionVerdict(
            eligible=False,
            reason=f"deferred_until_proven:{ctype}",
            signals=signals,
            policy_version=version,
        )

    if explicit and explicit_requires_receipt:
        signals.append("explicit_pod_intent")
        return PodAdmissionVerdict(
            eligible=True,
            reason="explicit_pod_verified",
            signals=signals,
            policy_version=version,
        )

    admit_types = _slug_list(pol.get("admit_contribution_types"))
    if ctype in admit_types:
        signals.append(f"contribution_type:{ctype}")
        return PodAdmissionVerdict(
            eligible=True,
            reason=f"admitted_type:{ctype}",
            signals=signals,
            policy_version=version,
        )

    return PodAdmissionVerdict(
        eligible=False,
        reason=f"contribution_type_not_admitted:{ctype or 'unknown'}",
        signals=signals,
        policy_version=version,
    )
