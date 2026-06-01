from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ULPayload:
    source: str
    kind: str
    section: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "kind": self.kind,
            "section": self.section,
            "data": self.data,
            "metadata": self.metadata,
        }


class ULAdapter(ABC):
    name = "ul_adapter"

    @abstractmethod
    def supports(self, raw: Any) -> bool:
        raise NotImplementedError

    @abstractmethod
    def adapt(self, raw: Any) -> ULPayload:
        raise NotImplementedError


class ULRegistry:
    def __init__(self) -> None:
        self.adapters: List[ULAdapter] = []

    def register(self, adapter: ULAdapter) -> None:
        self.adapters.append(adapter)

    def adapt(self, raw: Any) -> ULPayload:
        for adapter in self.adapters:
            if adapter.supports(raw):
                return adapter.adapt(raw)
        raise ValueError("No UL adapter found for payload.")

    def try_adapt(self, raw: Any) -> Optional[ULPayload]:
        for adapter in self.adapters:
            if adapter.supports(raw):
                return adapter.adapt(raw)
        return None


class RuntimeContextAdapter(ULAdapter):
    name = "runtime_context_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("type") == "runtime_context"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="context",
            section="runtime_context",
            data={
                "environment": raw.get("environment"),
                "provider": raw.get("provider"),
                "mode": raw.get("mode"),
            },
            metadata={"raw_type": raw.get("type")},
        )


class WorkspaceRunnerAdapter(ULAdapter):
    name = "workspace_runner_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("type") == "workspace_runner"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="workspace",
            section="workspace_context",
            data={
                "status": raw.get("status"),
                "active_task": raw.get("active_task"),
                "artifacts": raw.get("artifacts", []),
                "steps": raw.get("steps", []),
            },
            metadata={"raw_type": raw.get("type")},
        )


class ToolResultAdapter(ULAdapter):
    name = "tool_result_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("type") == "tool_result"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="tool_result",
            section="tool_results",
            data={
                "tool": raw.get("tool"),
                "status": raw.get("status"),
                "result": raw.get("result"),
            },
            metadata={"raw_type": raw.get("type")},
        )


class AttachmentAdapter(ULAdapter):
    name = "attachment_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("type") == "attachment"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="attachment",
            section="attachments",
            data={
                "name": raw.get("name"),
                "mime_type": raw.get("mime_type"),
                "size": raw.get("size"),
            },
            metadata={"raw_type": raw.get("type")},
        )


def build_default_registry() -> ULRegistry:
    registry = ULRegistry()
    registry.register(RuntimeContextAdapter())
    registry.register(WorkspaceRunnerAdapter())
    registry.register(ToolResultAdapter())
    registry.register(AttachmentAdapter())
    return registry


DEFAULT_REGISTRY = build_default_registry()


if __name__ == "__main__":
    registry = build_default_registry()
    demo_payloads = [
        {"type": "runtime_context", "environment": "dev", "provider": "openai", "mode": "mystic"},
        {"type": "workspace_runner", "status": "idle", "active_task": {"name": "sync"}, "artifacts": [], "steps": []},
        {"type": "tool_result", "tool": "search", "status": "ok", "result": {"count": 3}},
        {"type": "attachment", "name": "notes.md", "mime_type": "text/markdown", "size": 2048},
    ]

    for raw in demo_payloads:
        payload = registry.adapt(raw)
        print(payload.to_dict())
