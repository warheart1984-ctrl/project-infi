"""Tool executor wiring."""

from __future__ import annotations

from pathlib import Path

from operator_kernel.contracts import TaskConstraints, ToolResult
from operator_kernel.governance_gate import GovernanceGate
from operator_kernel.tools import git_tools, patch, search, shell, workspace
from operator_kernel.tools.registry import build_registry, tool_schemas


class ToolExecutor:
    def __init__(self, workspace_root: Path, gate: GovernanceGate):
        self.workspace_root = workspace_root
        self.gate = gate
        self.workspace = workspace.WorkspaceTools(workspace_root, gate)
        self._handlers = build_registry({
            "list_files": lambda **kw: self.workspace.list_files(**kw),
            "read_file": lambda **kw: self.workspace.read_file(**kw),
            "search_code": lambda **kw: search.search_code(self.workspace_root, **kw),
            "write_patch": lambda **kw: patch.apply_unified_diff(self.workspace_root, kw["path"], kw["diff"]),
            "run_command": lambda **kw: shell.run_command(self.workspace_root, kw["command"]),
            "run_tests": lambda **kw: shell.run_tests(self.workspace_root, kw.get("target", "")),
            "git_status": lambda **kw: git_tools.git_status(self.workspace_root),
            "git_diff": lambda **kw: git_tools.git_diff(self.workspace_root, kw.get("path", "")),
            "git_commit": lambda **kw: git_tools.git_commit(self.workspace_root, kw["message"]),
        })

    def tool_catalog(self) -> list[dict]:
        """JSON-schema tool definitions for the lawful brain."""
        return tool_schemas()

    def execute(
        self,
        name: str,
        args: dict,
        constraints: TaskConstraints,
        tool_call_id: str = "",
    ) -> ToolResult:
        tid = tool_call_id or f"tc-{name}"
        if name not in self._handlers:
            return ToolResult(id=tid, ok=False, error=f"Unknown tool: {name}")
        if constraints.read_only and name in {"write_patch", "run_command", "run_tests", "git_commit"}:
            return ToolResult(id=tid, ok=False, error=f"{name} blocked by read_only")
        try:
            data = self._handlers[name](**args)
            return ToolResult(id=tid, ok=True, data=data if isinstance(data, dict) else {"result": data})
        except Exception as exc:
            return ToolResult(id=tid, ok=False, error=str(exc))
