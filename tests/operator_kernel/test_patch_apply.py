"""Tests for unified diff application fallbacks."""

from __future__ import annotations

from pathlib import Path

from operator_kernel.tools.patch import apply_unified_diff, ensure_git_repo


def test_modify_patch_hunk_fallback_without_git_apply(tmp_path: Path) -> None:
    ensure_git_repo(tmp_path)
    hello = tmp_path / "hello.py"
    hello.write_text('print("Hello World")\n', encoding="utf-8")
    diff = "\n".join(
        [
            "--- a/hello.py",
            "+++ b/hello.py",
            "@@ -1 +1 @@",
            '-print("Hello World")',
            '+print("Hello Jon")',
            "",
        ]
    )
    result = apply_unified_diff(tmp_path, "hello.py", diff)
    assert result["applied"] is True
    assert result["method"] in ("git_apply", "hunk_fallback")
    assert 'print("Hello Jon")' in hello.read_text(encoding="utf-8")


def test_new_file_plus_fallback(tmp_path: Path) -> None:
    ensure_git_repo(tmp_path)
    diff = "\n".join(
        [
            "--- /dev/null",
            "+++ b/greet.py",
            "@@ -0,0 +1,2 @@",
            "+print('hi')",
            "+",
        ]
    )
    result = apply_unified_diff(tmp_path, "greet.py", diff)
    assert result["applied"] is True
    assert (tmp_path / "greet.py").is_file()
