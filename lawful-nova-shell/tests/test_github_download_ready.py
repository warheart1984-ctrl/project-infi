from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_github_ten_minute_start_documents_node_and_desktop_download_path() -> None:
    readme = read("README.md")
    guide = read("GITHUB-10-MINUTE-START.md")

    assert "GITHUB-10-MINUTE-START.md" in readme
    assert "quickstart.ps1" in readme
    assert "quickstart.sh" in readme
    assert "Download ZIP" in guide
    assert "git clone" in guide
    assert "quickstart.ps1" in guide
    assert "quickstart.sh" in guide
    assert "nova/node" in guide
    assert "desktop" in guide
    assert "/node/status" in guide
    assert "http://127.0.0.1:8080" in guide


def test_quickstart_scripts_install_backend_desktop_and_start_node() -> None:
    windows = read("quickstart.ps1")
    unix = read("quickstart.sh")

    assert "pip install -e" in windows
    assert "npm install" in windows
    assert "python.exe -m nova.api" in windows
    assert "desktop" in windows
    assert "setup\\verify.ps1" in windows

    assert "pip install -e" in unix
    assert "npm install" in unix
    assert "python -m nova.api" in unix
    assert "desktop" in unix
    assert "setup/verify.sh" in unix


def test_github_smoke_workflow_proves_download_ready_path() -> None:
    workflow = read(".github/workflows/download-smoke.yml")

    assert "actions/setup-python" in workflow
    assert "actions/setup-node" in workflow
    assert "python -m pip install -e .[dev]" in workflow
    assert "python -m pytest tests -q" in workflow
    assert "npm test" in workflow
    assert "scripts/package_windows_program.py" in workflow
    assert "scripts/package_macos_shell.py" in workflow
