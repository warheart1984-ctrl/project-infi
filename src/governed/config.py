"""URLs and runtime flags for the governed mission spine."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class GovernedRuntimeConfig:
    nova_base_url: str = field(
        default_factory=lambda: os.environ.get("LAWFUL_NOVA_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
    )
    aais_base_url: str = field(
        default_factory=lambda: os.environ.get("AAIS_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    )
    urg_mission_path: str = "/legacy_api/api/ugr/mission/run"
    aaes_execute_path: str = "/aaes/execute"
    tenant_id: str = "local"
    mission_tenant_id: str = "tenant:acme"
    capability: str = "observe"
    aais_instance_id: str = "aais-local-1"
    use_http_nova: bool = field(
        default_factory=lambda: not _truthy(os.environ.get("GOVERNED_NOVA_IN_PROCESS"))
    )
    use_http_urg: bool = field(
        default_factory=lambda: not _truthy(os.environ.get("GOVERNED_URG_IN_PROCESS"))
    )
    use_http_aaes: bool = field(
        default_factory=lambda: not _truthy(os.environ.get("GOVERNED_AAES_IN_PROCESS"))
    )
    # Spine boundary — Tri-Core routing vs Nexus execution vs NexusOS FOS
    tri_core_routing_authority: str = field(
        default_factory=lambda: os.environ.get("GOVERNED_TRI_CORE_ROUTING_AUTHORITY", "tri_core").strip()
        or "tri_core"
    )
    aaes_execution_module_id: str = field(
        default_factory=lambda: os.environ.get("GOVERNED_AAES_MODULE_ID", "nexus").strip() or "nexus"
    )
    nexus_record_mode: str = field(
        default_factory=lambda: os.environ.get("GOVERNED_NEXUS_RECORD_MODE", "in_process").strip()
        or "in_process"
    )
    nexusos_fos_export: bool = field(
        default_factory=lambda: _truthy(os.environ.get("GOVERNED_NEXUSOS_FOS_EXPORT"))
    )
    mission_runtime: Any | None = None
    orchestrator: Any | None = None

    def urg_url(self) -> str:
        return f"{self.aais_base_url}{self.urg_mission_path}"

    def aaes_url(self) -> str:
        return f"{self.aais_base_url}{self.aaes_execute_path}"

    def nova_chat_url(self) -> str:
        return f"{self.nova_base_url}/v1/chat"


_CONFIG: GovernedRuntimeConfig | None = None


def _apply_ci_stub(cfg: GovernedRuntimeConfig) -> GovernedRuntimeConfig:
    """Use in-process stub URG when CORI_CI_STUB_URG is set (CI docker-compose)."""
    if not _truthy(os.environ.get("CORI_CI_STUB_URG")):
        return cfg
    from src.governed.ci_runtime import stub_mission_runtime

    cfg.use_http_nova = False
    cfg.use_http_urg = False
    cfg.use_http_aaes = False
    cfg.mission_runtime = stub_mission_runtime()
    return cfg


def get_governed_config() -> GovernedRuntimeConfig:
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = _apply_ci_stub(GovernedRuntimeConfig())
    return _CONFIG


def reset_governed_config(config: GovernedRuntimeConfig | None = None) -> None:
    global _CONFIG
    _CONFIG = config
