"""Governance gate for operator kernel tools.

For constitutional bootloader (ledger, amendments, observer replay), see
``governance_gate`` / ``constitutional_substrate.governance_gate``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from operator_kernel.contracts import LawReceipt, TaskConstraints
import json


@dataclass(frozen=True)
class GovernanceVerdict:
    allowed: bool
    rule: str
    reason: str
    revised_args: dict[str, Any] | None = None

    @property
    def verdict(self) -> Literal["allow", "deny", "revise"]:
        if self.revised_args is not None:
            return "revise"
        return "allow" if self.allowed else "deny"


WRITE_ACTIONS = frozenset({"write_patch", "apply_patch"})
SHELL_ACTIONS = frozenset({"run_command", "run_tests"})
GIT_WRITE_ACTIONS = frozenset({"git_commit"})

BLOCKED_PATH_PARTS = frozenset({
    ".git", ".local-secrets", "__pycache__", "node_modules", ".venv", "venv", "dist", "build",
})

BLOCKED_COMMAND_FRAGMENTS = (
    "rm ", "del ", "erase ", "rmdir ", "remove-item", "format ", "shutdown",
    "restart-computer", "git reset", "git checkout", "git clean", "curl ", "wget ",
)

DEFAULT_COMMAND_PREFIXES = (
    "pytest", "python -m pytest", "python -m compileall", "rg",
    "git status", "git diff", "git log", "dir", "powershell", "pwsh",
)


class GovernanceGate:
    def __init__(self, workspace_root: Path, command_allowlist_id: str = "default_dev"):
        self.workspace_root = workspace_root.resolve()
        self.command_allowlist_id = command_allowlist_id

    def check_tool(
        self,
        name: str,
        args: dict[str, Any],
        constraints: TaskConstraints,
        tool_call_id: str | None = None,
    ) -> tuple[GovernanceVerdict, LawReceipt]:
        """Map workspace tool invocations to governance_check."""
        subject = ""
        diff = ""
        if name == "write_patch":
            action = "write_patch"
            subject = str(args.get("path") or "")
            diff = str(args.get("diff") or "")
        elif name in {"run_command", "run_tests"}:
            action = "run_command"
            subject = str(args.get("command") or ("pytest" if name == "run_tests" else ""))
        elif name == "git_commit":
            action = "git_commit"
            subject = str(args.get("message") or "")
        elif name == "search_code":
            action = "search_code"
            subject = str(args.get("query") or "")
        elif name in {"list_files", "read_file", "git_status", "git_diff"}:
            action = "read_file" if name == "read_file" else "list_files"
            subject = str(args.get("path") or args.get("pattern") or "")
        else:
            action = name
            subject = json.dumps(args)[:500]
        return self.governance_check(
            action,
            subject,
            diff=diff,
            constraints=constraints,
            tool_call_id=tool_call_id,
        )

    def resolve_path(self, path_text: str) -> Path:
        requested = (self.workspace_root / path_text).resolve()
        base = self.workspace_root
        if requested != base and base not in requested.parents:
            raise ValueError("path is outside the workspace")
        if any(part in BLOCKED_PATH_PARTS for part in requested.parts):
            raise ValueError("path targets a blocked workspace area")
        return requested

    def governance_check(
        self,
        action: str,
        subject: str,
        *,
        diff: str = "",
        risk_context: dict[str, Any] | None = None,
        constraints: TaskConstraints | None = None,
        tool_call_id: str | None = None,
    ) -> tuple[GovernanceVerdict, LawReceipt]:
        risk_context = risk_context or {}
        constraints = constraints or TaskConstraints()
        verdict = self._evaluate(action, subject, diff=diff, constraints=constraints, risk_context=risk_context)
        receipt = LawReceipt(
            tool_call_id=tool_call_id,
            capability=action,
            rsl="SATISFIED" if verdict.allowed or verdict.verdict == "revise" else "RSL-DENIED",
            verdict=verdict.verdict,
            reasons=[verdict.reason] if verdict.reason else [],
            invariants=[verdict.rule],
        )
        return verdict, receipt

    def _evaluate(
        self,
        action: str,
        subject: str,
        *,
        diff: str,
        constraints: TaskConstraints,
        risk_context: dict[str, Any],
    ) -> GovernanceVerdict:
        if constraints.read_only and action in WRITE_ACTIONS | SHELL_ACTIONS | GIT_WRITE_ACTIONS:
            return GovernanceVerdict(False, "read_only", f"{action} blocked by read_only constraint")

        if action in WRITE_ACTIONS:
            if not subject.strip():
                return GovernanceVerdict(False, "missing_path", "write_patch requires a path")
            try:
                self.resolve_path(subject)
            except ValueError as exc:
                return GovernanceVerdict(False, "path_jail", str(exc))
            if not diff.strip():
                return GovernanceVerdict(False, "empty_diff", "write_patch requires a non-empty diff")

        if action in SHELL_ACTIONS:
            if not constraints.allow_shell:
                return GovernanceVerdict(False, "shell_disabled", "shell execution is disabled")
            command = subject.strip()
            verdict = self._check_command(command)
            if not verdict.allowed:
                return verdict

        if action in GIT_WRITE_ACTIONS:
            if not constraints.allow_git_commit:
                return GovernanceVerdict(False, "git_commit_disabled", "git commit is disabled")

        if action == "search_code" and not subject.strip():
            return GovernanceVerdict(False, "empty_query", "search_code requires a query")

        return GovernanceVerdict(True, "preflight", "action passed governance preflight")

    def _check_command(self, command: str) -> GovernanceVerdict:
        normalized = " ".join(command.strip().split()).lower()
        if any(fragment in normalized for fragment in BLOCKED_COMMAND_FRAGMENTS):
            return GovernanceVerdict(False, "dangerous_command_fragment", "command contains a blocked fragment")
        if not normalized.startswith(DEFAULT_COMMAND_PREFIXES):
            return GovernanceVerdict(False, "command_allowlist", "command is outside the allowed set")
        return GovernanceVerdict(True, "command_allowlist", "command allowed")
