"""Normalize third-party AI platform trace exports into Mechanic NDJSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

TraceSource = Literal["generic", "langsmith", "n8n", "make", "cursor"]


def import_trace_file(*, source: TraceSource, input_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    source_path = Path(input_path)
    target = Path(output_path)
    payload = _load_trace_payload(source_path)
    records = normalize_trace_records(source=source, payload=payload, source_name=source_path.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")
    return {
        "schema_version": "mechanic.trace_import.v1",
        "source": source,
        "input_path": str(source_path),
        "output_path": str(target),
        "record_count": len(records),
    }


def normalize_trace_records(*, source: TraceSource, payload: Any, source_name: str = "trace") -> list[dict[str, Any]]:
    items = _as_records(payload)
    records: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        normalized = _normalize_one(source=source, item=item, index=index, source_name=source_name)
        if normalized:
            records.append(normalized)
    return records


def _load_trace_payload(path: Path) -> Any:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".ndjson":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def _as_records(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("runs", "events", "executions", "steps", "trace"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        return [payload]
    return []


def _normalize_one(*, source: TraceSource, item: dict[str, Any], index: int, source_name: str) -> dict[str, Any] | None:
    record_id = str(item.get("id") or item.get("run_id") or item.get("nodeId") or item.get("step_id") or f"{source}:{index}")
    kind = str(item.get("type") or item.get("event") or item.get("kind") or item.get("node_type") or "").lower()
    name = str(item.get("name") or item.get("tool") or item.get("model") or item.get("label") or kind or source)
    base = {
        "id": f"trace:{source}:{record_id}",
        "source_path": source_name,
        "trace_id": str(item.get("trace_id") or item.get("traceId") or item.get("session_id") or ""),
        "source_system": source,
    }
    parent = item.get("parent") or item.get("parent_run_id") or item.get("parentId")
    if parent:
        base["parent"] = f"trace:{source}:{parent}"
        base["child"] = base["id"]

    if _looks_like_model(source, item, kind):
        return {
            **base,
            "model_call": name,
            "model": str(item.get("model") or item.get("model_name") or name),
            "audit": item.get("audit") or item.get("metadata") or {},
        }
    if _looks_like_tool(source, item, kind):
        return {
            **base,
            "tool_call": name,
            "tool": str(item.get("tool") or item.get("app") or item.get("operation") or name),
            "allowed_actions": item.get("allowed_actions") or item.get("actions"),
        }
    if _looks_like_human(item, kind):
        return {**base, "human_step": name}
    if "workflow" in kind or source in {"n8n", "make"}:
        return {**base, "tool_call": name, "tool": name}
    return None


def _looks_like_model(source: TraceSource, item: dict[str, Any], kind: str) -> bool:
    return bool(
        "llm" in kind
        or "model" in kind
        or item.get("model")
        or item.get("model_name")
        or (source == "langsmith" and str(item.get("run_type") or "").lower() == "llm")
    )


def _looks_like_tool(source: TraceSource, item: dict[str, Any], kind: str) -> bool:
    return bool(
        "tool" in kind
        or item.get("tool")
        or item.get("operation")
        or source in {"n8n", "make", "cursor"}
    )


def _looks_like_human(item: dict[str, Any], kind: str) -> bool:
    return bool("human" in kind or "approval" in kind or item.get("human") or item.get("approver"))
