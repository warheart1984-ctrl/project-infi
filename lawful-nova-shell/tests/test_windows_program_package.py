from __future__ import annotations

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_windows_program_quickstart_documents_desktop_and_node_backend() -> None:
    guide = (ROOT / "WINDOWS-DESKTOP.md").read_text(encoding="utf-8")

    assert "desktop" in guide
    assert "nova/node" in guide
    assert "npm install" in guide
    assert "npm start" in guide
    assert "setup\\verify.ps1" in guide
    assert "python -m nova.api" in guide


def test_windows_program_zip_includes_desktop_and_governed_node_backend(tmp_path) -> None:
    from scripts.package_windows_program import create_windows_program_zip

    archive = tmp_path / "nova-desktop-windows.zip"
    create_windows_program_zip(ROOT, archive)

    assert archive.exists()
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())

        required = {
            "nova-desktop-windows/WINDOWS-DESKTOP.md",
            "nova-desktop-windows/GITHUB-10-MINUTE-START.md",
            "nova-desktop-windows/quickstart.ps1",
            "nova-desktop-windows/desktop/main.js",
            "nova-desktop-windows/desktop/preload.js",
            "nova-desktop-windows/desktop/package.json",
            "nova-desktop-windows/desktop/package-lock.json",
            "nova-desktop-windows/desktop/renderer/index.html",
            "nova-desktop-windows/desktop/core/node-client.js",
            "nova-desktop-windows/nova/api.py",
            "nova-desktop-windows/nova/node/evidence.py",
            "nova-desktop-windows/nova/node/tools/routes.py",
            "nova-desktop-windows/setup/bootstrap.ps1",
            "nova-desktop-windows/setup/verify.ps1",
            "nova-desktop-windows/pyproject.toml",
            "nova-desktop-windows/requirements.txt",
            "nova-desktop-windows/policy.yaml",
        }
        assert required.issubset(names)
        assert not any("/node_modules/" in name for name in names)
        assert not any(name.startswith("nova-desktop-windows/.runtime/") for name in names)
        assert not any(name.startswith("nova-desktop-windows/desktop/dist/") for name in names)
        assert not any("/__pycache__/" in name for name in names)
