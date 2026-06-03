"""Mission causal ledger — tenant-partitioned action IDs for cross-provider steps."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.ugr.invariants.cloud_invariants import CloudCausalityFault
from src.ugr.mission.tenant_manifold import tenant_path_slug
from src.ugr.platform.tenant_registry import normalize_tenant_id


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / ".runtime"


class MissionLedger:
    """Append-only mission action log under runtime dir (partitioned by tenant)."""

    def __init__(self, runtime_dir: str | Path | None = None, *, tenant_id: str | None = None):
        root = Path(runtime_dir or _default_runtime_dir())
        tenant_norm = normalize_tenant_id(tenant_id or "global")
        slug = tenant_path_slug(tenant_norm)
        self.tenant_id = tenant_norm
        self.path = root / "collective-pattern-ledger" / "tenants" / slug / "missions.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append_action(self, record: dict[str, Any]) -> str:
        """Append ledger row; fail-closed on IO error."""
        payload = dict(record)
        payload.setdefault("tenant_id", self.tenant_id)
        line = json.dumps(payload, sort_keys=True, default=str)
        action_id = str(payload.get("action_id") or "")
        try:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise CloudCausalityFault(f"ledger append failed for {action_id}: {exc}") from exc
        return action_id

    def append_governance_mutation(self, record: dict[str, Any]) -> str:
        """Append governance mutation row."""
        payload = dict(record)
        payload.setdefault("type", "governance_mutation")
        return self.append_action(payload)

    def list_for_mission(self, mission_id: str) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get("mission_id") == mission_id:
                    rows.append(row)
        return rows
