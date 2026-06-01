from __future__ import annotations
import json
import hashlib
from app.llm import chat, make_system_prompt
from app.tools import TOOLS
from app.memory import retrieve_memory, store_memory
from app.db import log_event, get_cached_response, set_cached_response
from app.router import fast_route, is_cacheable

def _safe_json_parse(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        return {"action": "final", "response": text}

def cache_key(session_id: str, user_message: str) -> str:
    return hashlib.sha256(f"{session_id}::{user_message.strip()}".encode("utf-8")).hexdigest()

def build_messages(user_message: str, recent_history: list[dict[str, str]], session_id: str) -> list[dict[str, str]]:
    memories = retrieve_memory(user_message, session_id=session_id, n_results=3)
    memory_context = "Relevant past memory:\n" + ("\n".join(f"- {m}" for m in memories) if memories else "- none")
    trimmed = recent_history[-8:]
    return [
        {"role": "system", "content": make_system_prompt()},
        {"role": "system", "content": memory_context},
        *trimmed,
        {"role": "user", "content": user_message},
    ]

def run_fast_path(user_message: str, session_id: str):
    tool_name, tool_input = fast_route(user_message)
    if tool_name and tool_name in TOOLS:
        result = TOOLS[tool_name](tool_input)
        response = result
        store_memory(f"Tool used: {tool_name}\nInput: {tool_input}\nResult: {result}", session_id=session_id)
        return response, tool_name, result, "fast_path"
    return None

def run_tool_loop(user_message: str, recent_history: list[dict[str, str]], session_id: str = "default") -> tuple[str, str | None, str | None, bool, str]:
    key = cache_key(session_id, user_message)
    if is_cacheable(user_message):
        cached = get_cached_response(key)
        if cached:
            return cached["response"], cached["used_tool"], cached["tool_result"], True, cached["route"] or "cache"

    fast = run_fast_path(user_message, session_id)
    if fast:
        response, used_tool, tool_result, route = fast
        if is_cacheable(user_message):
            set_cached_response(key, response, used_tool, tool_result, route)
        return response, used_tool, tool_result, False, route

    messages = build_messages(user_message, recent_history, session_id)
    used_tool = None
    tool_result = None
    last_tool_input = ""

    log_event("chat_request", {"session_id": session_id, "message": user_message})

    for _ in range(4):
        raw = chat(messages, fast=True if len(user_message) < 80 else False)
        data = _safe_json_parse(raw)

        if data.get("action") == "tool":
            tool_name = data.get("tool")
            tool_input = str(data.get("input", ""))
            last_tool_input = tool_input

            if tool_name not in TOOLS:
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content": f"Tool '{tool_name}' does not exist. Give a final answer."})
                continue

            used_tool = tool_name
            tool_result = TOOLS[tool_name](tool_input)
            log_event("tool_used", {"session_id": session_id, "tool": tool_name, "input": tool_input, "result": tool_result[:500]})
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"Tool result for {tool_name}: {tool_result}"})
            continue

        response = data.get("response", raw)
        store_memory(f"User: {user_message}\nAssistant: {response}", session_id=session_id)
        if used_tool:
            store_memory(f"Tool used: {used_tool}\nInput: {last_tool_input}\nResult: {tool_result}", session_id=session_id)
        log_event("chat_response", {"session_id": session_id, "response": response[:1000]})
        if is_cacheable(user_message):
            set_cached_response(key, response, used_tool, tool_result, "llm")
        return response, used_tool, tool_result, False, "llm"

    fallback = "I hit the tool loop limit. Please try again with a simpler request."
    store_memory(f"User: {user_message}\nAssistant: {fallback}", session_id=session_id)
    log_event("chat_fallback", {"session_id": session_id, "message": user_message})
    return fallback, used_tool, tool_result, False, "fallback"
