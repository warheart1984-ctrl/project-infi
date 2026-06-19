from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_unix_nova_shim_is_tracked_and_executable() -> None:
    shim = ROOT / "bin" / "nova"

    assert shim.exists()
    assert shim.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash")
    result = subprocess.run(
        ["git", "ls-files", "-s", "--", "bin/nova"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("100755 ")


def test_unix_bootstrap_supports_non_interactive_local_install() -> None:
    bootstrap = read("setup/bootstrap.sh")

    assert "--non-interactive" in bootstrap
    assert "-m venv" in bootstrap
    assert "pip install -e" in bootstrap
    assert re.search(r'set_nova_var\s+"NOVA_CLI"\s+"Nova CLI command"\s+"\$REPO_ROOT/bin/nova"', bootstrap)
    assert "read -rp" in bootstrap
    assert "if [[ \"$NON_INTERACTIVE\" == true ]]" in bootstrap


def test_unix_shell_profile_prefers_repo_local_nova_shim() -> None:
    profile = read("config/.zshrc")

    assert "LAWFUL_NOVA_REPO_ROOT" in profile
    assert 'export PATH="$LAWFUL_NOVA_REPO_ROOT/bin:$PATH"' in profile
    assert 'NOVA="${NOVA_CLI:-$LAWFUL_NOVA_REPO_ROOT/bin/nova}"' in profile


def test_unix_verifier_can_discover_repo_local_python_and_nova() -> None:
    verify = read("setup/verify.sh")

    assert "get_candidate_repo_roots" in verify
    assert "get_repo_python" in verify
    assert "get_repo_nova_cli" in verify
    assert "Nova CLI repo shim reachable" in verify
    assert "Python .venv" in verify


def test_shell_scripts_are_lf_only() -> None:
    for path in [
        "bin/nova",
        "setup/bootstrap.sh",
        "setup/install_linux.sh",
        "setup/install_macos.sh",
        "setup/install_nova.sh",
        "setup/verify.sh",
        "config/.zshrc",
        "config/.novarc",
    ]:
        data = (ROOT / path).read_bytes()
        assert b"\r\n" not in data, path
