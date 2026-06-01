"""Sovereign export pack (v50)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

from platform.ledger.writer import export_ledger_jsonl
from platform.sovereign.exports import export_attestations_csv, export_audit_csv
from platform.sovereign.exports import export_usage_csv_range
from platform.store import PlatformStore


def _manifest_secret() -> str:
    return os.environ.get("PLATFORM_EXPORT_PACK_SECRET", "platform-export-pack-secret")


def build_export_pack(*, store: PlatformStore, org_id: str) -> tuple[bytes, dict[str, Any]]:
    audit = export_audit_csv(store=store, org_id=org_id)
    attestations = export_attestations_csv(store=store, org_id=org_id)
    usage = export_usage_csv_range(store=store, org_id=org_id)
    ledger = export_ledger_jsonl(store=store, org_id=org_id)
    manifest = {
        "pack_version": "platform.sovereign_export_pack.v1",
        "org_id": org_id,
        "files": ["audit.csv", "attestations.csv", "usage.csv", "ledger.jsonl"],
        "claim_label": "asserted",
    }
    body = json.dumps(manifest, sort_keys=True)
    manifest["signature"] = hmac.new(_manifest_secret().encode(), body.encode(), hashlib.sha256).hexdigest()
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        zf.writestr("audit.csv", audit)
        zf.writestr("attestations.csv", attestations)
        zf.writestr("usage.csv", usage)
        zf.writestr("ledger.jsonl", ledger)
    return buffer.getvalue(), manifest


def write_export_pack(*, store: PlatformStore, org_id: str, output: Path) -> Path:
    data, manifest = build_export_pack(store=store, org_id=org_id)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    sidecar = output.with_suffix(".manifest.json")
    sidecar.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return output
