"""Daniel execution module — pluggable bounded action interface."""

# Mythic: Daniel execution module
# Engineering: DanielExecutionModule
from __future__ import annotations

from typing import Any, Protocol

from src.aaes_os.pipeline_types import AAESAction


from src.aaes_os.modules.nexus import NexusExecutionModule
from src.aaes_os.tsr_routing import is_daniel_runtime_enabled


class ExecutionModule(Protocol):
    module_id: str

    def execute(self, action: AAESAction) -> dict[str, Any]:
        ...


class DanielExecutionModule:
    """Stub Daniel module; returns structured placeholder outcomes."""

    module_id = "daniel"

    def execute(self, action: AAESAction) -> dict[str, Any]:
        if not isinstance(action, AAESAction):
            raise TypeError("action must be AAESAction")
        action.validate()
        return {
            "module_id": self.module_id,
            "operation": action.operation,
            "status": "stub_ok",
            "args": dict(action.args),
            "message": f"Daniel stub executed {action.operation}",
        }


# Back-compat alias for older imports and docs.
DanielModule = DanielExecutionModule


class ModuleRegistry:
    """Resolve execution modules by engineering id."""

    def __init__(self, *, include_daniel: bool | None = None) -> None:
        daniel_enabled = is_daniel_runtime_enabled() if include_daniel is None else include_daniel
        self._modules: dict[str, ExecutionModule] = {
            NexusExecutionModule.module_id: NexusExecutionModule(),
        }
        if daniel_enabled:
            self._modules[DanielExecutionModule.module_id] = DanielExecutionModule()

    def register(self, module: ExecutionModule) -> None:
        module_id = str(getattr(module, "module_id", "") or "").strip()
        if not module_id:
            raise ValueError("module_id is required")
        self._modules[module_id] = module

    def get(self, module_id: str) -> ExecutionModule:
        key = str(module_id or "").strip()
        if not key:
            raise ValueError("module_id is required")
        module = self._modules.get(key)
        if module is None:
            raise KeyError(f"unknown module: {key}")
        return module

    def execute(self, action: AAESAction) -> dict[str, Any]:
        module = self.get(action.module_id)
        return module.execute(action)
