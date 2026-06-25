"""Patch application helpers."""

from __future__ import annotations

import difflib
import re
import subprocess
from pathlib import Path

_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def build_unified_diff_from_text(path: str, old_content: str, new_content: str) -> str:
    """Build a unified diff between two file contents."""
    rel = path.replace("\\", "/").lstrip("/")
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    if not old_lines and old_content and not old_content.endswith("\n"):
        old_lines = [old_content]
    if not new_lines and new_content and not new_content.endswith("\n"):
        new_lines = [new_content]
    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
            lineterm="",
        )
    )
    if not diff_lines:
        return ""
    return "\n".join(diff_lines) + "\n"


def preview_patch(path: str, old_content: str, new_content: str) -> dict[str, str]:
    diff = build_unified_diff_from_text(path, old_content, new_content)
    return {"path": path, "diff": diff}


def ensure_git_repo(workspace_root: Path) -> None:
    """Initialize a git repo in the workspace when missing (for git apply)."""
    if (workspace_root / ".git").exists():
        return
    workspace_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init"],
        cwd=str(workspace_root),
        capture_output=True,
        text=True,
        check=False,
    )
    subprocess.run(
        ["git", "config", "user.email", "operator-kernel@local"],
        cwd=str(workspace_root),
        capture_output=True,
        text=True,
        check=False,
    )
    subprocess.run(
        ["git", "config", "user.name", "Operator Kernel"],
        cwd=str(workspace_root),
        capture_output=True,
        text=True,
        check=False,
    )


def _apply_plus_lines_fallback(workspace_root: Path, path: str, diff: str) -> dict:
    """Apply a unified diff by writing lines marked with '+' (fallback when git apply fails)."""
    rel = path.replace("\\", "/").lstrip("/")
    lines: list[str] = []
    for line in diff.splitlines():
        if line.startswith("@@") or line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("+"):
            lines.append(line[1:])
        elif line.startswith(" "):
            lines.append(line[1:])
    target = (workspace_root / rel).resolve()
    base = workspace_root.resolve()
    if target != base and base not in target.parents:
        raise ValueError("path is outside the workspace")
    target.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines)
    if content and not content.endswith("\n"):
        content += "\n"
    target.write_text(content, encoding="utf-8")
    return {"path": rel, "applied": True, "method": "filesystem_fallback"}


def apply_unified_diff(workspace_root: Path, path: str, diff: str) -> dict:
    workspace_root.mkdir(parents=True, exist_ok=True)
    ensure_git_repo(workspace_root)
    proc = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "-"],
        cwd=str(workspace_root),
        input=diff,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return {"path": path, "applied": True, "method": "git_apply", "stderr": proc.stderr.strip()}
    try:
        if _looks_like_new_file_diff(diff):
            return _apply_plus_lines_fallback(workspace_root, path, diff)
        return _apply_unified_hunks_fallback(workspace_root, path, diff)
    except Exception as fallback_exc:
        raise RuntimeError(
            proc.stderr.strip() or proc.stdout.strip() or "git apply failed"
        ) from fallback_exc


def _looks_like_new_file_diff(diff: str) -> bool:
    has_plus = False
    has_minus_body = False
    for line in diff.splitlines():
        if line.startswith("+++") and "/dev/null" not in line:
            has_plus = True
        if line.startswith("-") and not line.startswith("---"):
            has_minus_body = True
    return has_plus and not has_minus_body


def _apply_unified_hunks_to_text(original: str, diff: str) -> str:
    """Apply unified diff hunks to file text when git apply is unavailable."""
    orig_lines = original.splitlines()
    result: list[str] = []
    orig_idx = 0
    diff_lines = diff.splitlines()
    i = 0
    while i < len(diff_lines):
        line = diff_lines[i]
        if not line.startswith("@@"):
            i += 1
            continue
        m = _HUNK_HEADER.match(line)
        if not m:
            i += 1
            continue
        old_start = int(m.group(1)) - 1
        while orig_idx < old_start and orig_idx < len(orig_lines):
            result.append(orig_lines[orig_idx])
            orig_idx += 1
        i += 1
        while i < len(diff_lines) and not diff_lines[i].startswith("@@"):
            hline = diff_lines[i]
            if hline.startswith(" "):
                if orig_idx < len(orig_lines):
                    result.append(orig_lines[orig_idx])
                    orig_idx += 1
                else:
                    result.append(hline[1:])
            elif hline.startswith("-"):
                orig_idx += 1
            elif hline.startswith("+"):
                result.append(hline[1:])
            elif hline.startswith("\\"):
                pass
            i += 1
    while orig_idx < len(orig_lines):
        result.append(orig_lines[orig_idx])
        orig_idx += 1
    if not result:
        return ""
    out = "\n".join(result)
    if original.endswith("\n") or not original:
        out += "\n"
    return out


def _apply_unified_hunks_fallback(workspace_root: Path, path: str, diff: str) -> dict:
    """Apply a modify-style unified diff by parsing @@ hunks."""
    rel = path.replace("\\", "/").lstrip("/")
    target = (workspace_root / rel).resolve()
    base = workspace_root.resolve()
    if target != base and base not in target.parents:
        raise ValueError("path is outside the workspace")
    original = target.read_text(encoding="utf-8") if target.is_file() else ""
    new_text = _apply_unified_hunks_to_text(original, diff)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(new_text, encoding="utf-8")
    return {"path": rel, "applied": True, "method": "hunk_fallback"}
