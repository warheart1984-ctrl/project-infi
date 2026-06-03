"""HMAC operator + URG receipt signing for Governed Composite Missions."""

from __future__ import annotations

from hashlib import sha256
import hmac
import json
import os
import secrets
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.ugr.mission.ledger_merkle import compute_ledger_merkle_root
from src.ugr.mission.mission_receipt import (
    build_goal_hash,
    build_invariant_digest,
    build_organ_receipt_tuples,
)


RECEIPT_SECRET_VERSION = "1.0"
ALGORITHM_HMAC = "hmac-sha256"
ALGORITHM_CONTENT_ONLY = "sha256-content-only"
URG_OPERATOR_RECEIPT_KEY_ENV = "URG_OPERATOR_RECEIPT_KEY"
URG_RECEIPT_SIGNING_KEY_ENV = "URG_RECEIPT_SIGNING_KEY"
ENV_OPERATOR_KEY_ID = "env:URG_OPERATOR_RECEIPT_KEY"
ENV_URG_KEY_ID = "env:URG_RECEIPT_SIGNING_KEY"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / ".runtime"


def _receipt_secret_path(operator_id: str, runtime_dir: Path) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_:" else "_" for c in operator_id) or "default"
    return runtime_dir / "operators" / safe / "receipt-secret.json"


def _urg_signing_secret_path(runtime_dir: Path) -> Path:
    return runtime_dir / "urg" / "receipt-signing-secret.json"


def load_operator_receipt_key(
    operator_id: str,
    *,
    runtime_dir: str | Path | None = None,
    create_if_missing: bool = True,
) -> tuple[str | None, str | None]:
    """Resolve operator HMAC key: env override, then per-operator secret file."""
    env_key = os.getenv(URG_OPERATOR_RECEIPT_KEY_ENV, "").strip()
    if env_key:
        return env_key, ENV_OPERATOR_KEY_ID

    op = str(operator_id or "").strip() or "default"
    root = Path(runtime_dir) if runtime_dir else _default_runtime_dir()
    path = _receipt_secret_path(op, root)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            secret = str(payload.get("secret") or "").strip()
            key_id = str(payload.get("key_id") or "").strip() or None
            if secret:
                return secret, key_id
        except json.JSONDecodeError:
            pass

    if not create_if_missing:
        return None, None

    path.parent.mkdir(parents=True, exist_ok=True)
    secret = secrets.token_hex(32)
    key_id = str(uuid4())
    path.write_text(
        json.dumps(
            {
                "version": RECEIPT_SECRET_VERSION,
                "operator_id": op,
                "key_id": key_id,
                "secret": secret,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return secret, key_id


def load_urg_receipt_signing_key(
    *,
    runtime_dir: str | Path | None = None,
    create_if_missing: bool = True,
) -> tuple[str | None, str | None]:
    """Resolve URG authority HMAC key."""
    env_key = os.getenv(URG_RECEIPT_SIGNING_KEY_ENV, "").strip()
    if env_key:
        return env_key, ENV_URG_KEY_ID

    root = Path(runtime_dir) if runtime_dir else _default_runtime_dir()
    path = _urg_signing_secret_path(root)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            secret = str(payload.get("secret") or "").strip()
            key_id = str(payload.get("key_id") or "").strip() or None
            if secret:
                return secret, key_id
        except json.JSONDecodeError:
            pass

    if not create_if_missing:
        return None, None

    path.parent.mkdir(parents=True, exist_ok=True)
    secret = secrets.token_hex(32)
    key_id = str(uuid4())
    path.write_text(
        json.dumps(
            {
                "version": RECEIPT_SECRET_VERSION,
                "role": "urg_receipt_authority",
                "key_id": key_id,
                "secret": secret,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return secret, key_id


def build_receipt_canonical_payload(
    gcm: dict[str, Any],
    *,
    ingress: dict[str, Any],
    aais_step_summaries: list[str] | None = None,
) -> dict[str, Any]:
    """Canonical body for legacy v1.2 digest and HMAC."""
    summaries = list(aais_step_summaries or [])
    summaries_digest = sha256(_stable_json(summaries).encode("utf-8")).hexdigest() if summaries else ""
    return {
        "gcm_version": gcm.get("gcm_version"),
        "mission_id": gcm.get("mission_id"),
        "status": gcm.get("status"),
        "goal": gcm.get("goal"),
        "constraints": gcm.get("constraints"),
        "participating_organs": gcm.get("participating_organs"),
        "invariant_all_passed": (gcm.get("invariant_set") or {}).get("all_passed"),
        "ledger_action_ids": (gcm.get("ledger_trail") or {}).get("action_ids"),
        "ingress_stamp_hash": ingress.get("stamp_hash"),
        "aais_step_summaries_digest": summaries_digest,
    }


def build_operator_sig_canonical(receipt: dict[str, Any]) -> dict[str, Any]:
    """Operator-bound fields for operator_mac."""
    operator_sig = dict(receipt.get("operator_sig") or {})
    return {
        "operator_id": operator_sig.get("operator_id"),
        "tenant_id": operator_sig.get("tenant_id"),
        "aais_instance_id": operator_sig.get("aais_instance_id"),
        "stamped_at": operator_sig.get("stamped_at"),
        "goal_hash": receipt.get("goal_hash"),
        "operator_key_id": operator_sig.get("operator_key_id"),
    }


def build_urg_receipt_canonical(receipt: dict[str, Any]) -> dict[str, Any]:
    """Full MissionReceipt body for URG receipt_sig (excludes signature fields)."""
    body = dict(receipt)
    body.pop("receipt_sig", None)
    body.pop("receipt_algorithm", None)
    return body


def sign_operator_fields(
    receipt: dict[str, Any],
    *,
    operator_id: str,
    runtime_dir: str | Path | None = None,
    create_key_if_missing: bool = False,
) -> dict[str, Any]:
    """Sign operator_sig block; returns updated operator_sig dict."""
    operator_sig = dict(receipt.get("operator_sig") or {})
    key, key_id = load_operator_receipt_key(
        operator_id,
        runtime_dir=runtime_dir,
        create_if_missing=create_key_if_missing,
    )
    if key_id:
        operator_sig["operator_key_id"] = key_id
    canonical = _stable_json(build_operator_sig_canonical({**receipt, "operator_sig": operator_sig}))
    if key:
        operator_sig["operator_mac"] = hmac.new(key.encode("utf-8"), canonical.encode("utf-8"), sha256).hexdigest()
    else:
        operator_sig["operator_mac"] = sha256(canonical.encode("utf-8")).hexdigest()
    return operator_sig


def sign_urg_receipt(
    receipt: dict[str, Any],
    *,
    runtime_dir: str | Path | None = None,
    create_key_if_missing: bool = False,
) -> tuple[str, str, str | None]:
    """Return (receipt_sig, receipt_algorithm, urg_key_id)."""
    _, urg_key_id = load_urg_receipt_signing_key(
        runtime_dir=runtime_dir,
        create_if_missing=create_key_if_missing,
    )
    canonical = _stable_json(build_urg_receipt_canonical(receipt))
    key, _ = load_urg_receipt_signing_key(
        runtime_dir=runtime_dir,
        create_if_missing=create_key_if_missing,
    )
    if key:
        mac = hmac.new(key.encode("utf-8"), canonical.encode("utf-8"), sha256).hexdigest()
        return mac, ALGORITHM_HMAC, urg_key_id
    digest = sha256(canonical.encode("utf-8")).hexdigest()
    return digest, ALGORITHM_CONTENT_ONLY, urg_key_id


def sign_mission_receipt_v2(
    receipt: dict[str, Any],
    *,
    operator_id: str,
    runtime_dir: str | Path | None = None,
    create_keys_if_missing: bool = True,
) -> dict[str, Any]:
    """Apply dual signatures to MissionReceipt v1.1."""
    signed = dict(receipt)
    signed["operator_sig"] = sign_operator_fields(
        signed,
        operator_id=operator_id,
        runtime_dir=runtime_dir,
        create_key_if_missing=create_keys_if_missing,
    )
    _, urg_key_id = load_urg_receipt_signing_key(
        runtime_dir=runtime_dir,
        create_if_missing=create_keys_if_missing,
    )
    if urg_key_id:
        signed["urg_key_id"] = urg_key_id
    receipt_sig, algorithm, _ = sign_urg_receipt(
        signed,
        runtime_dir=runtime_dir,
        create_key_if_missing=create_keys_if_missing,
    )
    signed["receipt_sig"] = receipt_sig
    signed["receipt_algorithm"] = algorithm
    return signed


def sign_receipt_payload(
    canonical_payload: dict[str, Any],
    *,
    operator_id: str,
    runtime_dir: str | Path | None = None,
    create_key_if_missing: bool = False,
) -> dict[str, Any]:
    """Produce content_digest and optional receipt_mac (legacy v1.2)."""
    canonical = _stable_json(canonical_payload)
    content_digest = sha256(canonical.encode("utf-8")).hexdigest()
    key, _ = load_operator_receipt_key(
        operator_id,
        runtime_dir=runtime_dir,
        create_if_missing=create_key_if_missing,
    )

    if key:
        mac = hmac.new(key.encode("utf-8"), canonical.encode("utf-8"), sha256).hexdigest()
        return {
            "content_digest": content_digest,
            "receipt_mac": mac,
            "receipt_algorithm": ALGORITHM_HMAC,
            "receipt_signature": mac,
            "operator_id": operator_id,
        }

    return {
        "content_digest": content_digest,
        "receipt_mac": None,
        "receipt_algorithm": ALGORITHM_CONTENT_ONLY,
        "receipt_signature": content_digest,
        "operator_id": operator_id,
    }


def verify_mission_receipt(
    receipt: dict[str, Any],
    gcm: dict[str, Any],
    *,
    ingress: dict[str, Any],
    operator_id: str | None = None,
    key: str | None = None,
    aais_step_summaries: list[str] | None = None,
) -> tuple[bool, str]:
    """Fail-closed verification for legacy v1.2 flat receipt."""
    op = str(operator_id or receipt.get("operator_id") or (gcm.get("goal") or {}).get("operator_id") or "")
    canonical = build_receipt_canonical_payload(
        gcm, ingress=ingress, aais_step_summaries=aais_step_summaries
    )
    canonical_str = _stable_json(canonical)
    expected_digest = sha256(canonical_str.encode("utf-8")).hexdigest()
    if str(receipt.get("content_digest") or "") != expected_digest:
        return False, "content_digest_mismatch"

    algorithm = str(receipt.get("receipt_algorithm") or "")
    if algorithm == ALGORITHM_CONTENT_ONLY:
        if str(receipt.get("receipt_signature") or "") != expected_digest:
            return False, "content_signature_mismatch"
        return True, "ok"

    if algorithm != ALGORITHM_HMAC:
        return False, f"unknown_algorithm:{algorithm}"

    secret = key
    if not secret:
        secret, _ = load_operator_receipt_key(op, create_if_missing=False)
    if not secret:
        return False, "missing_operator_receipt_key"

    expected_mac = hmac.new(secret.encode("utf-8"), canonical_str.encode("utf-8"), sha256).hexdigest()
    mac = str(receipt.get("receipt_mac") or receipt.get("receipt_signature") or "")
    if not hmac.compare_digest(mac, expected_mac):
        return False, "receipt_mac_mismatch"
    return True, "ok"


def verify_mission_receipt_v2(
    receipt: dict[str, Any],
    *,
    gcm: dict[str, Any] | None = None,
    ingress: dict[str, Any] | None = None,
    ledger_rows: list[dict[str, Any]] | None = None,
    operator_key: str | None = None,
    urg_key: str | None = None,
    runtime_dir: str | Path | None = None,
) -> tuple[bool, str]:
    """Fail-closed verification for MissionReceipt schema v1.2."""
    gcm = dict(gcm or {})
    ingress = dict(ingress or {})
    goal = dict(gcm.get("goal") or {})
    constraints = dict(gcm.get("constraints") or {})
    invariant_set = dict(gcm.get("invariant_set") or {})

    if receipt.get("cloud_identity_hash"):
        expected_identity = str(ingress.get("cloud_identity_hash") or "")
        if expected_identity and str(receipt.get("cloud_identity_hash") or "") != expected_identity:
            return False, "cloud_identity_hash_mismatch"

    if receipt.get("boundary_digest"):
        expected_boundary = str(ingress.get("boundary_digest") or "")
        if expected_boundary and str(receipt.get("boundary_digest") or "") != expected_boundary:
            return False, "boundary_digest_mismatch"

    expected_goal_hash = build_goal_hash(goal, constraints)
    if str(receipt.get("goal_hash") or "") != expected_goal_hash:
        return False, "goal_hash_mismatch"

    expected_invariant = build_invariant_digest(invariant_set)
    if str(receipt.get("invariant_digest") or "") != expected_invariant:
        return False, "invariant_digest_mismatch"

    expected_root = compute_ledger_merkle_root(list(ledger_rows or []))
    if str(receipt.get("ledger_root") or "") != expected_root:
        return False, "ledger_root_mismatch"

    op_id = str((receipt.get("operator_sig") or {}).get("operator_id") or goal.get("operator_id") or "")
    op_canonical = _stable_json(build_operator_sig_canonical(receipt))
    op_secret = operator_key
    if not op_secret:
        op_secret, _ = load_operator_receipt_key(
            op_id, runtime_dir=runtime_dir, create_if_missing=False
        )
    expected_op_mac = str((receipt.get("operator_sig") or {}).get("operator_mac") or "")
    if op_secret:
        computed_op = hmac.new(op_secret.encode("utf-8"), op_canonical.encode("utf-8"), sha256).hexdigest()
        if not hmac.compare_digest(expected_op_mac, computed_op):
            return False, "operator_mac_mismatch"
    else:
        if expected_op_mac != sha256(op_canonical.encode("utf-8")).hexdigest():
            return False, "operator_mac_mismatch"

    urg_canonical = _stable_json(build_urg_receipt_canonical(receipt))
    algorithm = str(receipt.get("receipt_algorithm") or ALGORITHM_HMAC)
    expected_sig = str(receipt.get("receipt_sig") or "")
    if algorithm == ALGORITHM_CONTENT_ONLY:
        if expected_sig != sha256(urg_canonical.encode("utf-8")).hexdigest():
            return False, "receipt_sig_mismatch"
        return True, "ok"

    urg_secret = urg_key
    if not urg_secret:
        urg_secret, _ = load_urg_receipt_signing_key(runtime_dir=runtime_dir, create_if_missing=False)
    if not urg_secret:
        return False, "missing_urg_receipt_signing_key"
    computed_urg = hmac.new(urg_secret.encode("utf-8"), urg_canonical.encode("utf-8"), sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, computed_urg):
        return False, "receipt_sig_mismatch"
    return True, "ok"
