from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from story_forge.identity import PACKAGE_VERSION


ADMISSION_SCHEMA = "story_forge_packaged_admission/v1"
ADMISSION_STATUS_ADMITTED = "admitted"
ADMISSION_STATUS_PENDING_SMOKE = "pending_smoke"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def packaged_admission_path(exe_path: str | Path) -> Path:
    return Path(exe_path).with_suffix(".admission.json")


def packaged_smoke_token_path(exe_path: str | Path) -> Path:
    return Path(exe_path).with_suffix(".smoke-token.json")


def compute_file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_payload(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _read_payload(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def write_packaged_smoke_token(
    exe_path: str | Path,
    *,
    scope: str,
) -> Path:
    exe = Path(exe_path)
    payload = {
        "schema": ADMISSION_SCHEMA,
        "status": ADMISSION_STATUS_PENDING_SMOKE,
        "generated_at": _now_iso(),
        "scope": scope,
        "exe_name": exe.name,
        "entrypoint": exe.name,
        "package_version": PACKAGE_VERSION,
        "exe_sha256": compute_file_sha256(exe),
    }
    return _write_payload(packaged_smoke_token_path(exe), payload)


def write_packaged_admission(
    exe_path: str | Path,
    *,
    scope: str,
    audit_mode: str,
    audit_artifact_path: str | Path | None = None,
) -> Path:
    exe = Path(exe_path)
    payload = {
        "schema": ADMISSION_SCHEMA,
        "status": ADMISSION_STATUS_ADMITTED,
        "generated_at": _now_iso(),
        "scope": scope,
        "audit_mode": audit_mode,
        "audit_artifact_path": str(audit_artifact_path or ""),
        "exe_name": exe.name,
        "entrypoint": exe.name,
        "package_version": PACKAGE_VERSION,
        "exe_sha256": compute_file_sha256(exe),
    }
    return _write_payload(packaged_admission_path(exe), payload)


def clear_packaged_admission(exe_path: str | Path) -> None:
    packaged_admission_path(exe_path).unlink(missing_ok=True)
    packaged_smoke_token_path(exe_path).unlink(missing_ok=True)


def verify_packaged_admission(exe_path: str | Path) -> tuple[bool, str]:
    exe = Path(exe_path)
    payload = _read_payload(packaged_admission_path(exe))
    if payload is None:
        return False, (
            "This packaged build is not admitted yet. Run the completion-audited "
            "build flow before launching Story Forge."
        )

    if payload.get("schema") != ADMISSION_SCHEMA:
        return False, "This packaged build has an unreadable admission record."
    if payload.get("status") != ADMISSION_STATUS_ADMITTED:
        return False, "This packaged build has not passed packaged admission."
    if str(payload.get("exe_name", "")).strip() != exe.name:
        return False, "This packaged build's admission record targets a different executable."
    if str(payload.get("entrypoint", "")).strip() != exe.name:
        return False, "This packaged build's admission record has the wrong entrypoint."
    if str(payload.get("package_version", "")).strip() != PACKAGE_VERSION:
        return False, "This packaged build's admission record targets a different Story Forge version."

    expected_hash = str(payload.get("exe_sha256", "")).strip()
    if not expected_hash:
        return False, "This packaged build's admission record is missing its executable hash."
    if compute_file_sha256(exe) != expected_hash:
        return False, "This packaged build has changed since its packaged audit was recorded."
    return True, ""


def verify_packaged_smoke_token(
    exe_path: str | Path,
    token_path: str | Path,
) -> tuple[bool, str]:
    exe = Path(exe_path)
    token = _read_payload(Path(token_path))
    if token is None:
        return False, "Packaged audit smoke token is missing or unreadable."
    if token.get("schema") != ADMISSION_SCHEMA:
        return False, "Packaged audit smoke token has the wrong schema."
    if token.get("status") != ADMISSION_STATUS_PENDING_SMOKE:
        return False, "Packaged audit smoke token is not pending smoke admission."
    if str(token.get("exe_name", "")).strip() != exe.name:
        return False, "Packaged audit smoke token targets a different executable."
    if str(token.get("entrypoint", "")).strip() != exe.name:
        return False, "Packaged audit smoke token has the wrong entrypoint."
    if str(token.get("package_version", "")).strip() != PACKAGE_VERSION:
        return False, "Packaged audit smoke token targets a different Story Forge version."

    expected_hash = str(token.get("exe_sha256", "")).strip()
    if not expected_hash:
        return False, "Packaged audit smoke token is missing its executable hash."
    if compute_file_sha256(exe) != expected_hash:
        return False, "This packaged build changed after the smoke token was issued."
    return True, ""
