"""Adapter that calls the LawfulLLM and normalizes tool_calls."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from operator_kernel.config import load_config
from operator_kernel.contracts import LawfulAskRequest, LawfulAskResponse, ToolCall
from operator_kernel.lawful_brain.errors import PlannerError
from operator_kernel.lawful_brain.planner_fallback import enrich_parsed_plan
from operator_kernel.tools.openai_tools import openai_tools_for_constraints

_WRITE_TOOLS = frozenset({"write_patch", "run_command", "run_tests", "git_commit"})


class LawfulBrainAdapter:
    """Bridge between Operator Kernel and the LawfulLLM runtime."""

    def __init__(self) -> None:
        self._llm = None
        self._llm_error: str | None = None
        self._init_llm()

    def _init_llm(self) -> None:
        try:
            from nova.runtime_factory import build_lawful_llm

            secret = os.environ.get("AAIS_SIGNING_SECRET", "operator-kernel-dev-secret")
            self._llm = build_lawful_llm(
                operator_session_id="operator-kernel",
                signing_secret=secret,
            )
        except Exception as exc:  # pragma: no cover - optional dependency
            self._llm_error = str(exc)

    def ask(self, request: LawfulAskRequest) -> LawfulAskResponse:
        read_only = bool((request.constraints or {}).get("read_only"))

        if self._llm is None:
            return self._response_from_parsed(
                self._fallback_parsed(request, read_only=read_only),
                read_only=read_only,
                prefix_explanation=f"LawfulLLM unavailable: {self._llm_error or 'not installed'}",
            )

        if _frontier_planner_enabled():
            try:
                return self._ask_frontier(request, read_only=read_only)
            except Exception as exc:
                if not _planner_fallback_enabled():
                    raise PlannerError(f"Frontier planner failed: {exc}") from exc
                parsed = self._fallback_parsed(
                    request,
                    read_only=read_only,
                    error_note=f"Frontier planner failed, using JSON fallback: {exc}",
                )
                return self._response_from_parsed(parsed, read_only=read_only)

        return self._ask_json_fallback(request, read_only=read_only)

    def _ask_frontier(self, request: LawfulAskRequest, *, read_only: bool) -> LawfulAskResponse:
        messages = _build_planner_messages(request)
        openai_tools = openai_tools_for_constraints(request.constraints)
        tenant_id = os.environ.get("OPERATOR_LAWFUL_TENANT_ID", "local")
        capability = os.environ.get("OPERATOR_LAWFUL_CAPABILITY", "reason")

        turn = self._llm.complete_openai(
            messages,
            tenant_id=tenant_id,
            capability=capability,
            tools=openai_tools or None,
        )
        nova_cortex = turn.nova_cortex if isinstance(turn.nova_cortex, dict) else {}
        raw_tool_calls = nova_cortex.get("tool_calls") or []
        tool_calls = _filter_read_only(_tool_results_to_calls(raw_tool_calls), read_only=read_only)

        explanations: list[str] = []
        text = str(turn.text or "").strip()
        if text:
            explanations.append(text)

        receipts: list[dict[str, Any]] = []
        if turn.receipt:
            receipts.append(
                {
                    "receipt": turn.receipt,
                    "verified": self._llm.verify_receipt(turn.receipt),
                    "decision": (turn.voss_runtime or {}).get("decision"),
                }
            )

        return LawfulAskResponse(
            tool_calls=tool_calls,
            steps=[],
            explanations=explanations,
            receipts=receipts,
        )

    def _ask_json_fallback(self, request: LawfulAskRequest, *, read_only: bool) -> LawfulAskResponse:
        prompt = self._build_json_prompt(request)
        try:
            turn = self._llm.ask(
                prompt,
                tenant_id=os.environ.get("OPERATOR_LAWFUL_TENANT_ID", "local"),
                capability=os.environ.get("OPERATOR_LAWFUL_CAPABILITY", "reason"),
            )
            parsed = _extract_json_object(turn.text)
        except Exception as exc:
            parsed = {
                "tool_calls": [],
                "steps": [],
                "explanations": [f"LawfulLLM error: {exc}"],
            }
            if _planner_fallback_enabled():
                parsed = enrich_parsed_plan(
                    parsed,
                    request.intent,
                    read_only=read_only,
                    workspace_root=load_config().resolved_workspace_root(),
                )
            tool_calls = _filter_read_only(_parse_tool_calls(parsed.get("tool_calls", [])), read_only=read_only)
            if not tool_calls and not parsed.get("explanations"):
                raise PlannerError(f"JSON fallback planner failed: {exc}") from exc
            return LawfulAskResponse(
                tool_calls=tool_calls,
                steps=[str(step) for step in parsed.get("steps", []) if str(step).strip()],
                explanations=[str(item) for item in parsed.get("explanations", []) if str(item).strip()],
                receipts=[],
            )

        if _planner_fallback_enabled():
            parsed = enrich_parsed_plan(
                parsed,
                request.intent,
                read_only=read_only,
                workspace_root=load_config().resolved_workspace_root(),
            )

        return self._response_from_parsed(parsed, read_only=read_only)

    def _fallback_parsed(
        self,
        request: LawfulAskRequest,
        *,
        read_only: bool,
        error_note: str | None = None,
    ) -> dict[str, Any]:
        parsed: dict[str, Any] = {"tool_calls": [], "steps": [], "explanations": []}
        if error_note:
            parsed["explanations"].append(error_note)
        if _planner_fallback_enabled():
            parsed = enrich_parsed_plan(
                parsed,
                request.intent,
                read_only=read_only,
                workspace_root=load_config().resolved_workspace_root(),
            )
        return parsed

    def _response_from_parsed(
        self,
        parsed: dict[str, Any],
        *,
        read_only: bool,
        prefix_explanation: str | None = None,
    ) -> LawfulAskResponse:
        tool_calls = _filter_read_only(_parse_tool_calls(parsed.get("tool_calls", [])), read_only=read_only)
        explanations = [str(item) for item in parsed.get("explanations", []) if str(item).strip()]
        if prefix_explanation:
            explanations.insert(0, prefix_explanation)
        return LawfulAskResponse(
            tool_calls=tool_calls,
            steps=[str(step) for step in parsed.get("steps", []) if str(step).strip()],
            explanations=explanations,
            receipts=[],
        )

    def _build_json_prompt(self, request: LawfulAskRequest) -> str:
        tools = request.tools or []
        tool_lines = "\n".join(f"- {tool['name']}: {tool.get('description', '')}" for tool in tools)
        constraints = json.dumps(request.constraints or {}, indent=2)
        context = json.dumps(request.context or {}, indent=2)
        return (
            "You are the Lawful Brain planner for an operator kernel.\n"
            "Return ONLY valid JSON with keys: tool_calls, steps, explanations.\n"
            "Each tool_calls item must include id, name, args.\n"
            "Prefer concrete tool_calls over prose when the user asks to create or modify files.\n\n"
            f"Intent:\n{request.intent}\n\n"
            f"Constraints:\n{constraints}\n\n"
            f"Context:\n{context}\n\n"
            f"Available tools:\n{tool_lines}\n"
        )


def _frontier_planner_enabled() -> bool:
    if os.environ.get("OPERATOR_FRONTIER_PLANNER", "").strip().lower() in {"0", "false", "no"}:
        return False
    try:
        from nova.provider_factory import resolve_frontier_provider

        return resolve_frontier_provider() is not None
    except ImportError:
        return False


def _planner_fallback_enabled() -> bool:
    if os.environ.get("OPERATOR_LAWFUL_PLANNER_FALLBACK", "").strip().lower() in {"0", "false", "no"}:
        return False
    return load_config().planner_fallback_enabled


def _build_planner_messages(request: LawfulAskRequest) -> list[dict[str, Any]]:
    task_id = str((request.context or {}).get("task_id") or "").strip()
    if task_id:
        try:
            from operator_kernel.events import TaskEventStore
            from operator_kernel.memory.context_builder import build_planner_messages as build_with_memory

            store = TaskEventStore(load_config().tasks_dir())
            return build_with_memory(request, store=store)
        except Exception:
            pass
    tools = request.tools or []
    tool_lines = "\n".join(f"- {tool['name']}: {tool.get('description', '')}" for tool in tools)
    system = (
        "You are the Lawful Brain planner for an operator kernel.\n"
        "Use the provided tools to accomplish the user's intent.\n"
        "Prefer calling tools over prose when files, patches, or commands are needed.\n\n"
        f"Available tools:\n{tool_lines}\n"
    )
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    context_messages = (request.context or {}).get("messages") or []
    for item in context_messages:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "user")
        content = item.get("content")
        if content is not None and str(content).strip():
            messages.append({"role": role, "content": str(content)})
    messages.append({"role": "user", "content": request.intent})
    return messages


def _filter_read_only(tool_calls: list[ToolCall], *, read_only: bool) -> list[ToolCall]:
    if not read_only:
        return tool_calls
    return [tc for tc in tool_calls if tc.name not in _WRITE_TOOLS]


def _tool_results_to_calls(raw_calls: list[Any]) -> list[ToolCall]:
    parsed: list[ToolCall] = []
    for index, item in enumerate(raw_calls):
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("tool") or "").strip()
            if not name:
                continue
            args = item.get("args") if isinstance(item.get("args"), dict) else item.get("arguments")
            if not isinstance(args, dict):
                raw_args = item.get("arguments")
                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        args = {"raw": raw_args}
                else:
                    args = {}
            parsed.append(ToolCall(id=str(item.get("id") or f"tc-{index + 1}"), name=name, args=args))
            continue
        name = str(getattr(item, "name", None) or "").strip()
        if not name:
            continue
        args = getattr(item, "arguments", None)
        if not isinstance(args, dict):
            args = getattr(item, "args", None)
        if not isinstance(args, dict):
            args = {}
        parsed.append(
            ToolCall(
                id=str(getattr(item, "id", None) or f"tc-{index + 1}"),
                name=name,
                args=args,
            )
        )
    return parsed


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        return {}
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        stripped = fence.group(1).strip()
    try:
        loaded = json.loads(stripped)
        if isinstance(loaded, dict):
            return loaded
    except json.JSONDecodeError:
        pass
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        try:
            loaded = json.loads(stripped[start : end + 1])
            if isinstance(loaded, dict):
                return loaded
        except json.JSONDecodeError:
            pass
    return {}


def _parse_tool_calls(raw_calls: list[Any]) -> list[ToolCall]:
    parsed: list[ToolCall] = []
    for index, item in enumerate(raw_calls):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        args = item.get("args")
        if not isinstance(args, dict):
            args = {}
        parsed.append(
            ToolCall(
                id=str(item.get("id") or f"tc-{index + 1}"),
                name=name,
                args=args,
            )
        )
    return parsed
