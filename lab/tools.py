"""Governed lab instruments — sole execution gateway."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TYPE_CHECKING

from lab.governance import (
    GovernanceDenied,
    check_command_allowed,
    check_instrument_allowed,
    check_write_allowed,
    resolve_workspace_path,
    sanitized_subprocess_env,
    validate_allowed_paths,
)
from lab.spec import InstrumentSpec, LabProjectSpec
from lab.worktree import python_executable

if TYPE_CHECKING:
    from lab.session import LabSession


@dataclass(slots=True)
class ToolInvocationReceipt:
    tool: str
    status: str
    args: dict[str, Any] = field(default_factory=dict)
    returncode: int | None = None
    stdout_tail: str = ""
    stderr_tail: str = ""
    reason: str = ""
    violation_class: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "status": self.status,
            "args": self.args,
            "returncode": self.returncode,
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
            "reason": self.reason,
            "violation_class": self.violation_class,
        }


def _instrument_by_name(spec: LabProjectSpec, name: str) -> InstrumentSpec | None:
    for item in spec.instruments:
        if item.name == name:
            return item
    return None


def tool_schema(spec: LabProjectSpec, instrument: InstrumentSpec) -> dict[str, Any]:
    if instrument.kind == "filesystem_read":
        return {
            "name": instrument.name,
            "description": "Read a file under the lab workspace",
            "parameters": {"path": {"type": "string", "required": True}},
        }
    if instrument.kind == "filesystem_write":
        return {
            "name": instrument.name,
            "description": "Write a file under the lab workspace",
            "parameters": {
                "path": {"type": "string", "required": True},
                "content": {"type": "string", "required": True},
            },
        }
    if instrument.kind == "filesystem_list":
        return {
            "name": instrument.name,
            "description": "List directory under workspace",
            "parameters": {"path": {"type": "string", "required": False, "default": "."}},
        }
    if instrument.kind == "grep":
        return {
            "name": instrument.name,
            "description": "Search files with ripgrep (governed argv)",
            "parameters": {
                "pattern": {"type": "string", "required": True},
                "path": {"type": "string", "required": False, "default": "."},
            },
        }
    if instrument.kind == "forge_bridge":
        if instrument.name == "create_patch_review":
            return {
                "name": instrument.name,
                "description": "Create a review-first patch review linked to this lab session",
                "parameters": {"goal": {"type": "string", "required": True}},
            }
        return {
            "name": instrument.name,
            "description": "Build a review-first patch plan from the lab workspace",
            "parameters": {"goal": {"type": "string", "required": True}},
        }
    return {
        "name": instrument.name,
        "description": f"Run instrument: {' '.join(instrument.command)}",
        "parameters": {
            "paths": {"type": "array", "items": {"type": "string"}, "required": False},
            "extra_args": {"type": "array", "items": {"type": "string"}, "required": False},
        },
        "max_runtime_s": instrument.max_runtime_s,
        "allowed_paths": instrument.allowed_paths,
    }


def list_tool_schemas(spec: LabProjectSpec) -> list[dict[str, Any]]:
    return [tool_schema(spec, item) for item in spec.instruments]


def _run_subprocess(
    cmd: list[str],
    *,
    cwd: Path,
    timeout_s: int,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_s,
        env=env,
    )


def invoke_tool(
    session: LabSession,
    name: str,
    *,
    args: dict[str, Any] | None = None,
) -> ToolInvocationReceipt:
    """Execute a governed instrument for an active session."""
    payload = dict(args or {})
    spec = session.spec
    instrument = _instrument_by_name(spec, name)
    if instrument is None:
        receipt = ToolInvocationReceipt(
            tool=name,
            status="denied",
            args=payload,
            reason=f"unknown instrument: {name}",
        )
        session.record_tool(receipt)
        return receipt

    workspace = session.workspace
    spine = session.spine_profile

    try:
        check_instrument_allowed(spec, instrument, spine_profile=spine)
        if instrument.kind == "filesystem_read":
            return _read_file(session, instrument, payload)
        if instrument.kind == "filesystem_write":
            return _write_file(session, instrument, payload)
        if instrument.kind == "filesystem_list":
            return _list_dir(session, instrument, payload)
        if instrument.kind == "grep":
            return _grep(session, instrument, payload)
        if instrument.kind == "forge_bridge":
            return _forge_bridge(session, instrument, payload)
        return _run_command_instrument(session, instrument, payload)
    except GovernanceDenied as exc:
        receipt = ToolInvocationReceipt(
            tool=name,
            status="denied",
            args=payload,
            reason=str(exc),
            violation_class=exc.violation_class,
        )
        session.record_tool(receipt)
        return receipt
    except subprocess.TimeoutExpired:
        receipt = ToolInvocationReceipt(
            tool=name,
            status="timeout",
            args=payload,
            reason=f"exceeded max_runtime_s={instrument.max_runtime_s}",
        )
        session.record_tool(receipt)
        return receipt


def _read_file(
    session: LabSession,
    instrument: InstrumentSpec,
    args: dict[str, Any],
) -> ToolInvocationReceipt:
    rel = str(args.get("path") or "")
    if not rel:
        receipt = ToolInvocationReceipt(tool=instrument.name, status="denied", args=args, reason="path required")
        session.record_tool(receipt)
        return receipt
    target = resolve_workspace_path(session.workspace, rel)
    if not target.is_file():
        receipt = ToolInvocationReceipt(
            tool=instrument.name,
            status="failed",
            args=args,
            reason=f"file not found: {rel}",
        )
        session.record_tool(receipt)
        return receipt
    content = target.read_text(encoding="utf-8", errors="replace")
    session.record_file_read(rel)
    receipt = ToolInvocationReceipt(
        tool=instrument.name,
        status="ok",
        args=args,
        stdout_tail=content[:4000],
    )
    session.record_tool(receipt)
    return receipt


def _write_file(
    session: LabSession,
    instrument: InstrumentSpec,
    args: dict[str, Any],
) -> ToolInvocationReceipt:
    rel = str(args.get("path") or "")
    content = args.get("content")
    if not rel:
        receipt = ToolInvocationReceipt(tool=instrument.name, status="denied", args=args, reason="path required")
        session.record_tool(receipt)
        return receipt
    if content is None:
        receipt = ToolInvocationReceipt(
            tool=instrument.name, status="denied", args=args, reason="content required"
        )
        session.record_tool(receipt)
        return receipt
    check_write_allowed(
        session.spec,
        rel,
        confirmations=session.confirmations,
        instrument=instrument,
    )
    target = resolve_workspace_path(session.workspace, rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = str(content)
    target.write_text(text, encoding="utf-8")
    session.record_file_write(rel)
    session.ensure_experiment()
    receipt = ToolInvocationReceipt(tool=instrument.name, status="ok", args={"path": rel, "bytes": len(text)})
    session.record_tool(receipt)
    return receipt


def _list_dir(
    session: LabSession,
    instrument: InstrumentSpec,
    args: dict[str, Any],
) -> ToolInvocationReceipt:
    rel = str(args.get("path") or ".")
    target = resolve_workspace_path(session.workspace, rel)
    if not target.is_dir():
        receipt = ToolInvocationReceipt(
            tool=instrument.name, status="failed", args=args, reason=f"not a directory: {rel}"
        )
        session.record_tool(receipt)
        return receipt
    names = sorted(p.name for p in target.iterdir())[:200]
    receipt = ToolInvocationReceipt(
        tool=instrument.name,
        status="ok",
        args=args,
        stdout_tail=json.dumps(names),
    )
    session.record_tool(receipt)
    return receipt


def _grep(
    session: LabSession,
    instrument: InstrumentSpec,
    args: dict[str, Any],
) -> ToolInvocationReceipt:
    pattern = str(args.get("pattern") or "")
    rel = str(args.get("path") or ".")
    if not pattern:
        receipt = ToolInvocationReceipt(
            tool=instrument.name, status="denied", args=args, reason="pattern required"
        )
        session.record_tool(receipt)
        return receipt
    target = resolve_workspace_path(session.workspace, rel)
    cmd = ["rg", "--line-number", "--max-count", "50", pattern, str(target)]
    check_command_allowed(session.spec, cmd)
    env = sanitized_subprocess_env(session.spec)
    proc = _run_subprocess(cmd, cwd=session.workspace, timeout_s=instrument.max_runtime_s, env=env)
    receipt = ToolInvocationReceipt(
        tool=instrument.name,
        status="ok" if proc.returncode in (0, 1) else "failed",
        args=args,
        returncode=proc.returncode,
        stdout_tail=(proc.stdout or "")[-4000:],
        stderr_tail=(proc.stderr or "")[-2000:],
    )
    session.record_tool(receipt)
    return receipt


def _forge_bridge(
    session: LabSession,
    instrument: InstrumentSpec,
    args: dict[str, Any],
) -> ToolInvocationReceipt:
    from lab.forge_bridge import create_lab_patch_plan, create_lab_patch_review

    goal = str(args.get("goal") or "").strip()
    if not goal:
        receipt = ToolInvocationReceipt(
            tool=instrument.name,
            status="denied",
            args=args,
            reason="goal required",
            violation_class="II",
        )
        session.record_tool(receipt)
        return receipt

    if instrument.name == "create_patch_review":
        payload = create_lab_patch_review(session, goal=goal)
        receipt = ToolInvocationReceipt(
            tool=instrument.name,
            status="ok",
            args=args,
            stdout_tail=json.dumps(
                {
                    "review_id": (payload.get("review") or {}).get("id")
                    or (payload.get("review") or {}).get("review_id"),
                    "plan_id": (payload.get("patch_plan") or {}).get("plan_id"),
                    "review_ids": payload.get("review_ids"),
                }
            )[:4000],
        )
        session.record_tool(receipt)
        return receipt

    plan = create_lab_patch_plan(session, goal=goal)
    receipt = ToolInvocationReceipt(
        tool=instrument.name,
        status="ok",
        args=args,
        stdout_tail=json.dumps({"plan_id": plan.get("plan_id"), "target_files": plan.get("target_files")})[:4000],
    )
    session.record_tool(receipt)
    return receipt


def _run_command_instrument(
    session: LabSession,
    instrument: InstrumentSpec,
    args: dict[str, Any],
) -> ToolInvocationReceipt:
    if not instrument.command:
        receipt = ToolInvocationReceipt(
            tool=instrument.name, status="denied", args=args, reason="instrument has no command"
        )
        session.record_tool(receipt)
        return receipt

    paths = list(args.get("paths") or [])
    extra = [str(x) for x in list(args.get("extra_args") or [])]
    validate_allowed_paths(instrument, session.workspace, paths if paths else ["."])

    cmd = list(instrument.command)
    if cmd and cmd[0] == "python":
        cmd[0] = python_executable()
    cmd.extend(extra)
    cmd.extend(paths)

    check_command_allowed(session.spec, cmd)
    env = sanitized_subprocess_env(session.spec)
    proc = _run_subprocess(
        cmd,
        cwd=session.workspace,
        timeout_s=instrument.max_runtime_s,
        env=env,
    )
    ok = proc.returncode == 0
    if instrument.name.startswith("run_") and "pytest" in instrument.name:
        session.record_test(
            {
                "instrument": instrument.name,
                "paths": paths,
                "passed": ok,
                "returncode": proc.returncode,
            }
        )

    receipt = ToolInvocationReceipt(
        tool=instrument.name,
        status="ok" if ok else "failed",
        args=args,
        returncode=proc.returncode,
        stdout_tail=(proc.stdout or "")[-4000:],
        stderr_tail=(proc.stderr or "")[-2000:],
    )
    session.record_tool(receipt)
    return receipt
