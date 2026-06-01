"""AST scan for Python LLM call sites."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Any

from mechanic.genome.adapters.base import GenomeAdapter
from mechanic.genome.adapters._gitignore import load_gitignore_patterns, path_is_ignored
from mechanic.genome.schema import add_node

_LLM_MODULES = frozenset({"openai", "anthropic"})
_LLM_ATTRS = frozenset(
    {
        "ChatCompletion",
        "completions",
        "messages",
        "create",
    }
)
_SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".runtime",
    "venv",
    ".venv",
    "mechanic",
}


class PythonLlmAdapter(GenomeAdapter):
    adapter_id = "python_llm_calls"

    def describe(self, repo_path: Path) -> dict[str, Any]:
        return {"adapter_id": self.adapter_id, "modules": sorted(_LLM_MODULES)}

    def extract(self, repo_path: Path, genome: dict[str, Any]) -> dict[str, Any]:
        patterns = load_gitignore_patterns(repo_path)
        found = 0
        for path in sorted(repo_path.rglob("*.py")):
            if not path.is_file():
                continue
            rel = path.relative_to(repo_path).as_posix()
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if path_is_ignored(rel, patterns):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (OSError, SyntaxError):
                continue
            hits = _find_llm_calls(tree)
            for line_no, hint in hits:
                node_id = f"pyllm:{_hash_rel(f'{rel}:{line_no}')}"
                add_node(
                    genome,
                    node_id=node_id,
                    node_type="model_call",
                    label=hint,
                    source_path=rel,
                    attrs={"line": line_no},
                )
                found += 1
            exc_nodes = _find_exception_handlers(tree)
            for line_no in exc_nodes:
                node_id = f"exc:{_hash_rel(f'{rel}:{line_no}')}"
                add_node(
                    genome,
                    node_id=node_id,
                    node_type="exception_path",
                    label="try_except",
                    source_path=rel,
                    attrs={"line": line_no},
                )
        return {"adapter_id": self.adapter_id, "nodes_added": found}


def _find_llm_calls(tree: ast.AST) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            hint = _call_hint(node)
            if hint:
                hits.append((node.lineno, hint))
    return hits


def _call_hint(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Attribute):
        if func.attr in _LLM_ATTRS:
            return func.attr
        if isinstance(func.value, ast.Name) and func.value.id in _LLM_MODULES:
            return f"{func.value.id}.{func.attr}"
    if isinstance(func, ast.Name) and func.id in {"god_brain", "jarvis_modular"}:
        return func.id
    return None


def _find_exception_handlers(tree: ast.AST) -> list[int]:
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            lines.append(node.lineno)
    return lines


def _hash_rel(rel: str) -> str:
    return hashlib.sha256(rel.encode("utf-8")).hexdigest()[:12]
