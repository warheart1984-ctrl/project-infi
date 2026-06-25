"""Governance gate unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from operator_kernel.contracts import TaskConstraints
from operator_kernel.governance_gate import GovernanceGate


@pytest.fixture
def gate(tmp_path: Path) -> GovernanceGate:
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "src").mkdir()
    (ws / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    return GovernanceGate(ws)


def test_read_only_blocks_write_patch(gate: GovernanceGate) -> None:
    constraints = TaskConstraints(read_only=True)
    verdict, receipt = gate.check_tool(
        "write_patch",
        {"path": "src/main.py", "diff": "--- a\n+++ b\n"},
        constraints,
    )
    assert verdict.verdict == "deny"
    assert receipt.verdict == "deny"


def test_read_only_blocks_run_command(gate: GovernanceGate) -> None:
    constraints = TaskConstraints(read_only=True, allow_shell=True)
    verdict, _ = gate.check_tool(
        "run_command",
        {"command": "pytest"},
        constraints,
    )
    assert verdict.verdict == "deny"


def test_path_escape_denied(gate: GovernanceGate) -> None:
    constraints = TaskConstraints(read_only=False)
    verdict, _ = gate.check_tool(
        "write_patch",
        {"path": "../../../etc/passwd", "diff": "--- a\n+++ b\n"},
        constraints,
    )
    assert verdict.verdict == "deny"


def test_dangerous_command_denied(gate: GovernanceGate) -> None:
    constraints = TaskConstraints(allow_shell=True)
    verdict, _ = gate.check_tool(
        "run_command",
        {"command": "rm -rf /"},
        constraints,
    )
    assert verdict.verdict == "deny"


def test_allowed_pytest_command(gate: GovernanceGate) -> None:
    constraints = TaskConstraints(allow_shell=True)
    verdict, receipt = gate.check_tool(
        "run_command",
        {"command": "pytest tests/"},
        constraints,
    )
    assert verdict.verdict == "allow"
    assert receipt.rsl == "SATISFIED"


def test_git_commit_disabled_by_default(gate: GovernanceGate) -> None:
    constraints = TaskConstraints()
    verdict, _ = gate.check_tool(
        "git_commit",
        {"message": "wip"},
        constraints,
    )
    assert verdict.verdict == "deny"


def test_resolve_path_blocks_git_dir(gate: GovernanceGate) -> None:
    with pytest.raises(ValueError, match="blocked"):
        gate.resolve_path(".git/config")
