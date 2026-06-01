from __future__ import annotations
import ast
import operator as op
import io
import contextlib
from datetime import datetime
import hashlib
import requests
from app.config import BASE_DIR

_ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.FloorDiv: op.floordiv,
}

_BLOCKED_PYTHON_FRAGMENTS = [
    "__import__",
    "open(",
    "exec(",
    "eval(",
    "compile(",
    "import os",
    "import sys",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
]

_TOOL_CACHE: dict[str, str] = {}

def _cache_key(name: str, value: str) -> str:
    return hashlib.sha256(f"{name}::{value}".encode("utf-8")).hexdigest()

def _get_tool_cache(name: str, value: str):
    try:
        from src.cloud_forge.cache_bridge import bridge_l0_get

        bridged = bridge_l0_get(name, value)
        if bridged is not None:
            return bridged
    except Exception:
        pass
    return _TOOL_CACHE.get(_cache_key(name, value))

def _set_tool_cache(name: str, value: str, result: str):
    try:
        from src.cloud_forge.cache_bridge import bridge_l0_set

        if bridge_l0_set(name, value, result) is not None:
            return
    except Exception:
        pass
    _TOOL_CACHE[_cache_key(name, value)] = result

def safe_calculate(expression: str) -> str:
    cached = _get_tool_cache("calculator", expression)
    if cached is not None:
        return cached
    try:
        node = ast.parse(expression, mode="eval").body
        result = str(_eval_node(node))
        _set_tool_cache("calculator", expression, result)
        return result
    except Exception as exc:
        return f"Calculator error: {exc}"

def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Unsupported expression")

def current_time() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")

def safe_python(code: str) -> str:
    lowered = code.lower()
    for fragment in _BLOCKED_PYTHON_FRAGMENTS:
        if fragment in lowered:
            return f"Python error: blocked pattern '{fragment}'"

    cached = _get_tool_cache("python", code)
    if cached is not None:
        return cached

    allowed_builtins = {
        "print": print,
        "range": range,
        "len": len,
        "sum": sum,
        "min": min,
        "max": max,
        "sorted": sorted,
        "enumerate": enumerate,
        "list": list,
        "str": str,
        "int": int,
        "float": float,
        "abs": abs,
    }

    stdout = io.StringIO()
    try:
        compiled = compile(code, "<jarvis_python>", "exec")
        with contextlib.redirect_stdout(stdout):
            exec(compiled, {"__builtins__": allowed_builtins}, {})
        output = stdout.getvalue().strip() or "Python ran successfully with no output."
        _set_tool_cache("python", code, output)
        return output
    except Exception as exc:
        return f"Python error: {exc}"

def read_file(path_text: str) -> str:
    cached = _get_tool_cache("read_file", path_text)
    if cached is not None:
        return cached
    try:
        requested = (BASE_DIR / path_text).resolve()
        base = BASE_DIR.resolve()
        if base not in requested.parents and requested != base:
            return "File error: path is outside allowed project directory."
        if not requested.exists():
            return "File error: file not found."
        if requested.is_dir():
            return "File error: path is a directory."
        if requested.stat().st_size > 150_000:
            return "File error: file too large."
        result = requested.read_text(encoding="utf-8", errors="replace")
        _set_tool_cache("read_file", path_text, result)
        return result
    except Exception as exc:
        return f"File error: {exc}"

def list_files(path_text: str) -> str:
    key = path_text.strip()
    cached = _get_tool_cache("list_files", key)
    if cached is not None:
        return cached
    try:
        root = (BASE_DIR / key).resolve() if key else BASE_DIR.resolve()
        base = BASE_DIR.resolve()
        if base not in root.parents and root != base:
            return "List files error: path is outside allowed project directory."
        if not root.exists():
            return "List files error: path not found."
        if root.is_file():
            return root.name
        entries = []
        for item in sorted(root.iterdir())[:80]:
            prefix = "[D]" if item.is_dir() else "[F]"
            entries.append(f"{prefix} {item.name}")
        result = "\n".join(entries) if entries else "Directory is empty."
        _set_tool_cache("list_files", key, result)
        return result
    except Exception as exc:
        return f"List files error: {exc}"

def web_search(query: str) -> str:
    cached = _get_tool_cache("web_search", query)
    if cached is not None:
        return cached
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
            timeout=8
        )
        data = resp.json()
        abstract = data.get("AbstractText") or ""
        related = data.get("RelatedTopics") or []

        snippets = []
        if abstract:
            snippets.append(f"Summary: {abstract}")

        for item in related[:5]:
            if isinstance(item, dict):
                text = item.get("Text")
                if text:
                    snippets.append(f"- {text}")

        result = "\n".join(snippets[:6]) if snippets else "Web search found no strong instant-answer results for that query."
        _set_tool_cache("web_search", query, result)
        return result
    except Exception as exc:
        return f"Web search error: {exc}"

TOOLS = {
    "calculator": safe_calculate,
    "time": lambda _: current_time(),
    "python": safe_python,
    "read_file": read_file,
    "list_files": list_files,
    "web_search": web_search,
}

TOOL_SPECS = [
    {"name": "calculator", "description": "Evaluate math expressions.", "usage": "Use for exact arithmetic."},
    {"name": "time", "description": "Get current local server time.", "usage": "Use for time requests."},
    {"name": "python", "description": "Run a small restricted Python snippet.", "usage": "Use for tiny safe code tasks only."},
    {"name": "read_file", "description": "Read a text file inside the project directory.", "usage": "Use for local project files."},
    {"name": "list_files", "description": "List files in a local project directory.", "usage": "Use to inspect local project structure."},
    {"name": "web_search", "description": "Look up lightweight web info using DuckDuckGo instant answers.", "usage": "Use for outside/current info."},
]
