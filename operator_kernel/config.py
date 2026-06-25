"""OperatorKernel configuration (YAML + environment overrides)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class KernelCapabilities(BaseModel):
    allow_shell: bool = False
    allow_git_commit: bool = False
    allow_network: bool = False


class OperatorKernelConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8790
    lawful_brain_url: str = "http://127.0.0.1:8791"
    workspace_root: str = ""
    runtime_dir: str = ""
    capabilities: KernelCapabilities = Field(default_factory=KernelCapabilities)
    command_allowlist_id: str = "default_dev"
    tenant_id: str = "operator-kernel"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173", "null"]
    )
    planner_fallback_enabled: bool = True
    inter_step_sleep_sec: float = 0.0
    patch_require_approval: bool = True

    def resolved_workspace_root(self) -> Path:
        if self.workspace_root.strip():
            return Path(self.workspace_root).expanduser().resolve()
        env_root = os.getenv("AAIS_WORKSPACE_ROOT", "").strip()
        if env_root:
            return Path(env_root).expanduser().resolve()
        env_config = os.getenv("OPERATOR_KERNEL_CONFIG", "").strip()
        if env_config:
            packaged_ws = Path(env_config).expanduser().parent / "workspace"
            if packaged_ws.is_dir():
                return packaged_ws.resolve()
        for candidate in _default_config_paths():
            packaged_ws = candidate.parent / "workspace"
            if packaged_ws.is_dir():
                return packaged_ws.resolve()
        return Path(__file__).resolve().parents[1]

    def resolved_runtime_dir(self) -> Path:
        if self.runtime_dir.strip():
            return Path(self.runtime_dir).expanduser().resolve()
        return self.resolved_workspace_root() / ".runtime" / "operator_kernel"

    def tasks_dir(self) -> Path:
        return self.resolved_runtime_dir() / "tasks"


def _default_config_paths() -> list[Path]:
    root = Path(__file__).resolve().parents[1]
    return [
        root / "operator_kernel.config.yaml",
        root / "config" / "operator_kernel.config.yaml",
    ]


def load_config(path: str | Path | None = None) -> OperatorKernelConfig:
    if path is not None:
        return _load_yaml(Path(path))

    env_path = os.getenv("OPERATOR_KERNEL_CONFIG", "").strip()
    if env_path:
        candidate = Path(env_path).expanduser()
        if candidate.is_file():
            return _load_yaml(candidate)

    for candidate in _default_config_paths():
        if candidate.is_file():
            return _load_yaml(candidate)

    return OperatorKernelConfig(workspace_root=str(Path(__file__).resolve().parents[1]))


def _load_yaml(path: Path) -> OperatorKernelConfig:
    raw: dict[str, Any] = {}
    if path.is_file():
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
            if isinstance(loaded, dict):
                raw = loaded

    if os.getenv("OPERATOR_KERNEL_PORT"):
        raw["port"] = int(os.environ["OPERATOR_KERNEL_PORT"])
    if os.getenv("LAWFUL_BRAIN_URL"):
        raw["lawful_brain_url"] = os.environ["LAWFUL_BRAIN_URL"]
    if os.getenv("AAIS_WORKSPACE_ROOT"):
        raw["workspace_root"] = os.environ["AAIS_WORKSPACE_ROOT"]
    if os.getenv("OPERATOR_LAWFUL_PLANNER_FALLBACK", "").lower() in {"0", "false", "no"}:
        raw["planner_fallback_enabled"] = False
    if os.getenv("OPERATOR_AGENT_INTER_STEP_SLEEP_SEC"):
        raw["inter_step_sleep_sec"] = float(os.environ["OPERATOR_AGENT_INTER_STEP_SLEEP_SEC"])
    if os.getenv("OPERATOR_PATCH_REQUIRE_APPROVAL", "").lower() in {"0", "false", "no", "off"}:
        raw["patch_require_approval"] = False

    return OperatorKernelConfig.model_validate(raw)


def patch_require_approval_enabled() -> bool:
    """When true, write_patch stops at preview until operator approves via API."""
    raw = os.environ.get("OPERATOR_PATCH_REQUIRE_APPROVAL", "1").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if raw in {"1", "true", "yes", "on"}:
        return True
    try:
        cfg = load_config()
        return bool(cfg.patch_require_approval)
    except Exception:
        return True
