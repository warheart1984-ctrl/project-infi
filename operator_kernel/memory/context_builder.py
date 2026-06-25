"""Unified planner message construction with memory layers."""

from __future__ import annotations

import os
import re
from typing import Any

from operator_kernel.contracts import LawfulAskRequest
from operator_kernel.events import TaskEventStore
from operator_kernel.memory.project_memory import ProjectMemory, _project_id
from operator_kernel.memory.semantic_store import SemanticStore
from operator_kernel.memory.task_context import build_messages_from_task, task_summary_block


def _extract_paths_from_intent(intent: str) -> list[str]:
    return re.findall(r"[\w./\\-]+\.(?:py|ts|tsx|js|jsx|md|json|yaml|yml|svelte|rs|go)", intent)


def build_planner_messages(
    request: LawfulAskRequest,
    *,
    store: TaskEventStore | None = None,
) -> list[dict[str, Any]]:
    context = request.context or {}
    workspace_root = str(context.get("workspace_root") or os.environ.get("AAIS_WORKSPACE_ROOT") or "")
    project_id = _project_id(workspace_root or None)
    task_id = str(context.get("task_id") or "").strip()

    memory_blocks: list[str] = []
    if store and task_id:
        block = task_summary_block(store, task_id)
        if block:
            memory_blocks.append(block)

    project = ProjectMemory()
    files = _extract_paths_from_intent(request.intent)
    project_block = project.summarize_for_prompt(project_id, files)
    if project_block:
        memory_blocks.append(project_block)

    semantic = SemanticStore()
    semantic_block = semantic.summarize_for_prompt(project_id, request.intent)
    if semantic_block:
        memory_blocks.append(semantic_block)

    tools = request.tools or []
    tool_lines = "\n".join(f"- {tool['name']}: {tool.get('description', '')}" for tool in tools)
    system_parts = [
        "You are the Lawful Brain planner for an operator kernel.",
        "Use the provided tools to accomplish the user's intent.",
        "Prefer calling tools over prose when files, patches, or commands are needed.",
        "You must not modify files without approval when governance requires it.",
        *memory_blocks,
        f"\nAvailable tools:\n{tool_lines}\n",
    ]
    messages: list[dict[str, Any]] = [{"role": "system", "content": "\n".join(system_parts)}]

    if store and task_id:
        for msg in build_messages_from_task(store, task_id, limit=20):
            messages.append(msg)
    else:
        for item in context.get("messages") or []:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "user")
            content = item.get("content")
            if content is not None and str(content).strip():
                messages.append({"role": role, "content": str(content)})

    messages.append({"role": "user", "content": request.intent})
    return messages
