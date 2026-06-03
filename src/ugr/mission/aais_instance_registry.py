"""Resolve AAIS instance IDs to runtime dirs and bridge pairs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.cognitive_bridge import CognitiveBridgeService
from src.ugr.mission.aais_step_bridge import bootstrap_mission_aais
from src.ugr.unified_runtime import UnifiedGovernedRuntime


def _default_config_path() -> Path:
    env_path = os.getenv("URG_AAIS_INSTANCES_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "aais-instances.json"


def _default_runtime_root() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / ".runtime"


class AaisInstanceRegistry:
    """Load AAIS instance routing table and cache bridge/runtime pairs."""

    def __init__(self, config_path: str | Path | None = None):
        path = Path(config_path or _default_config_path())
        self._instances: dict[str, dict[str, Any]] = {}
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            self._instances = dict(payload.get("instances") or {})
        self._cache: dict[str, tuple[CognitiveBridgeService, UnifiedGovernedRuntime]] = {}

    def resolve_runtime_dir(self, instance_id: str) -> Path:
        """Resolve instance runtime directory (absolute path)."""
        iid = str(instance_id or "").strip() or "aais-primary"
        spec = dict(self._instances.get(iid) or {})
        rel = str(spec.get("runtime_dir") or ".runtime").strip()
        if rel in {".runtime", ".", ""}:
            return _default_runtime_root()
        path = Path(rel)
        if path.is_absolute():
            return path.expanduser()
        base = _default_runtime_root()
        if rel.startswith(".runtime"):
            return (base.parent / rel).resolve()
        return (base / rel).resolve()

    def get_bridge_pair(
        self,
        instance_id: str,
    ) -> tuple[CognitiveBridgeService, UnifiedGovernedRuntime]:
        """Return cached or bootstrapped bridge + UGR runtime for instance."""
        iid = str(instance_id or "").strip() or "aais-primary"
        if iid in self._cache:
            return self._cache[iid]
        runtime_dir = self.resolve_runtime_dir(iid)
        pair = bootstrap_mission_aais(runtime_dir)
        self._cache[iid] = pair
        return pair

    def list_instance_ids(self) -> list[str]:
        return sorted(self._instances.keys())
