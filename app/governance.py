from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import BASE_DIR


@dataclass(frozen=True)
class GovernanceVerdict:
    allowed: bool
    rule: str
    reason: str

    def to_dict(self) -> dict:
        return {"allowed": self.allowed, "rule": self.rule, "reason": self.reason}


WRITE_ACTIONS = {"write_patch"}
SHELL_ACTIONS = {"run_command"}

BLOCKED_PATH_PARTS = {".git", ".local-secrets", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}

BLOCKED_COMMAND_FRAGMENTS = {
    "rm ", "del ", "erase ", "rmdir ", "remove-item", "format ", "shutdown",
    "restart-computer", "git reset", "git checkout", "git clean", "curl ", "wget ",
}

ALLOWED_COMMAND_PREFIXES = (
    "pytest", "python -m pytest", "python -m compileall", "rg",
    "git status", "git diff", "git log", "dir",
)


def resolve_project_path(path_text: str) -> Path:
    requested = (BASE_DIR / path_text).resolve()
    base = BASE_DIR.resolve()
    if requested != base and base not in requested.parents:
        raise ValueError("path is outside the ARIS workspace")
    if any(part in BLOCKED_PATH_PARTS for part in requested.parts):
        raise ValueError("path targets a blocked workspace area")
    return requested


def check_tool_action(tool_name: str, tool_input: str) -> GovernanceVerdict:
    if tool_name in WRITE_ACTIONS and not tool_input.strip().startswith("{"):
        return GovernanceVerdict(False, "structured_write_input", "write tools require structured JSON input")
    if tool_name in SHELL_ACTIONS:
        command = " ".join(tool_input.strip().split()).lower()
        if any(fragment in command for fragment in BLOCKED_COMMAND_FRAGMENTS):
            return GovernanceVerdict(False, "dangerous_command_fragment", "command contains a blocked fragment")
        if not command.startswith(ALLOWED_COMMAND_PREFIXES):
            return GovernanceVerdict(False, "command_allowlist", "command is outside the allowed set")
    return GovernanceVerdict(True, "preflight", "action passed ARIS preflight governance")
