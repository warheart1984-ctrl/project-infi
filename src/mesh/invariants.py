"""Distributed invariant propagation for mesh peers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.mesh.paths import mesh_dir

INVARIANTS_FILENAME = "invariants.json"

DEFAULT_INVARIANTS = {
    "version": "1.0",
    "bundle_id": "aais-mesh-default",
    "rules": [
        {"id": "min_confidence", "value": 0.7, "description": "Minimum confidence for ADMIT"},
        {"id": "min_claim_length", "value": 6, "description": "Minimum claim character length"},
        {"id": "reject_known_false", "value": True, "description": "Reject claims in falsity ledger"},
    ],
    "updated_at": None,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _version_key(version) -> tuple[int, ...]:
    if version is None:
        return (0,)
    if isinstance(version, (int, float)):
        return (int(version),)
    parts: list[int] = []
    for piece in str(version).replace("-", ".").split("."):
        piece = piece.strip()
        if not piece:
            continue
        try:
            parts.append(int(piece))
        except ValueError:
            parts.append(0)
    return tuple(parts) if parts else (0,)


def invariants_path(base_dir: str | Path | None = None) -> Path:
    return mesh_dir(base_dir) / INVARIANTS_FILENAME


class InvariantStore:
    def __init__(self, base_dir: str | Path | None = None):
        self.path = invariants_path(base_dir)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            bundle = dict(DEFAULT_INVARIANTS)
            bundle["updated_at"] = _utc_now()
            self.save(bundle)

    def load(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, bundle: dict) -> dict:
        bundle = dict(bundle)
        bundle["updated_at"] = _utc_now()
        self.path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        return bundle

    def digest(self) -> str:
        raw = json.dumps(self.load(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def merge(self, remote_bundle: dict) -> dict:
        local = self.load()
        local_ver = local.get("version", "0")
        remote_ver = remote_bundle.get("version", "0")
        local_ts = local.get("updated_at") or ""
        remote_ts = remote_bundle.get("updated_at") or ""

        if _version_key(remote_ver) > _version_key(local_ver) or (
            _version_key(remote_ver) == _version_key(local_ver) and remote_ts > local_ts
        ):
            merged = dict(remote_bundle)
            merged["propagated_from"] = remote_bundle.get("bundle_id")
            self.save(merged)
            return {"action": "adopted_remote", "digest": self.digest()}

        return {"action": "kept_local", "digest": self.digest()}

    def apply_to_governance(self) -> dict:
        bundle = self.load()
        rules = {r["id"]: r.get("value") for r in bundle.get("rules", [])}
        return {
            "min_confidence": float(rules.get("min_confidence", 0.7)),
            "min_claim_length": int(rules.get("min_claim_length", 6)),
            "reject_known_false": bool(rules.get("reject_known_false", True)),
        }
