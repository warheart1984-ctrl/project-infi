"""Minimal YAML parser for Forge pipeline specs."""
from __future__ import annotations

from pathlib import Path

LIST_CONTAINER_KEYS = frozenset({"include", "exclude", "cloud_formats", "enable", "disable", "overlays"})


def parse_simple_yaml(path: Path) -> dict[str, object]:
    root: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(-1, root)]
    list_key: str | None = None
    list_indent = -1

    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if line.startswith("- "):
            if list_key is None:
                continue
            parent = stack[-1][1]
            items = parent.setdefault(list_key, [])
            if isinstance(items, list):
                items.append(line[2:].strip().strip("'\""))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        while stack and indent <= stack[-1][0]:
            stack.pop()
            if list_indent >= indent:
                list_key = None
        parent = stack[-1][1]
        if value == "":
            if key in LIST_CONTAINER_KEYS:
                parent[key] = []
                list_key = key
                list_indent = indent
            else:
                child: dict[str, object] = {}
                parent[key] = child
                stack.append((indent, child))
                list_key = None
                list_indent = indent
        else:
            if value.lower() in {"true", "false"}:
                parent[key] = value.lower() == "true"
            else:
                parent[key] = value
            list_key = None
    return root


def nested_get(spec: dict[str, object], *keys: str) -> str:
    cur: object = spec
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return ""
        cur = cur[key]
    if isinstance(cur, dict):
        return ""
    return str(cur) if cur is not None else ""
