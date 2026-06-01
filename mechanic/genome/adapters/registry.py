"""Adapter registry."""

from __future__ import annotations

from mechanic.genome.adapters.base import GenomeAdapter
from mechanic.genome.adapters.ci_automation import CiAutomationAdapter
from mechanic.genome.adapters.cursor_rules import CursorRulesAdapter
from mechanic.genome.adapters.filesystem_prompt import FilesystemPromptAdapter
from mechanic.genome.adapters.python_llm import PythonLlmAdapter
from mechanic.genome.adapters.trace_ndjson import TraceNdjsonAdapter
from mechanic.genome.adapters.workflow_json import WorkflowJsonAdapter

_REGISTRY: dict[str, GenomeAdapter] = {
    "filesystem_prompt": FilesystemPromptAdapter(),
    "cursor_rules": CursorRulesAdapter(),
    "workflow_json": WorkflowJsonAdapter(),
    "ci_automation": CiAutomationAdapter(),
    "python_llm_calls": PythonLlmAdapter(),
    "trace_ndjson": TraceNdjsonAdapter(),
}


def get_adapter(adapter_id: str) -> GenomeAdapter:
    adapter = _REGISTRY.get(adapter_id)
    if adapter is None:
        raise KeyError(f"unknown genome adapter: {adapter_id}")
    return adapter


def list_adapter_ids() -> list[str]:
    return list(_REGISTRY.keys())
