#!/usr/bin/env python3
"""Portable entrypoint for PyInstaller terminal desktop builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _install_root() -> Path:
    """Directory beside the exe (or script) — holds .env and runtime data."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _bundle_root() -> Path:
    """PyInstaller extract dir when frozen; otherwise same as install root."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass).resolve()
    return _install_root()


def _resolve_project_root() -> Path:
    return _install_root()


def _load_dotenv(root: Path) -> None:
    env_path = root / ".env"
    if not env_path.is_file():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path, override=False)
    except ImportError:
        pass


def _default_data_dir(root: Path) -> Path:
    data = root / ".runtime" / "aais-data"
    data.mkdir(parents=True, exist_ok=True)
    return data


def main() -> int:
    install = _install_root()
    bundle = _bundle_root()
    os.chdir(install)
    for entry in (bundle, install):
        entry_str = str(entry)
        if entry_str not in sys.path:
            sys.path.insert(0, entry_str)

    _load_dotenv(install)

    data_dir = os.getenv("JARVIS_DATA_DIR") or str(_default_data_dir(install))
    os.environ.setdefault("JARVIS_DATA_DIR", data_dir)

    argv = list(sys.argv[1:])
    if not argv or argv[0] in {"-h", "--help"}:
        argv = [
            "start",
            "--no-browser",
            "--preset",
            "production",
            "--data-dir",
            data_dir,
        ]
    elif argv[0] not in {"start", "prepare", "doctor"}:
        argv = ["start", *argv]

    if "--data-dir" not in argv:
        argv.extend(["--data-dir", data_dir])
    if argv[0] == "start" and "--no-browser" not in argv:
        argv.append("--no-browser")
    if argv[0] == "start" and "--preset" not in argv:
        argv.extend(["--preset", "production"])

    from aais.launcher import main as launcher_main

    return int(launcher_main(argv) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
