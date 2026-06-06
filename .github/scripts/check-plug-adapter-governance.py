#!/usr/bin/env python3
"""Plug adapter runtime governance gate."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    required = [
        root / "schemas" / "plug_adapter.v1.json",
        root / "src" / "plug_adapter_runtime.py",
        root / "governance" / "subsystem_genomes" / "plug_adapter_runtime.genome.v1.json",
    ]
    for path in required:
        if not path.is_file():
            print(f"[plug-adapter-gate] FAIL: missing {path.relative_to(root)}")
            return 1
    api = (root / "src" / "api.py").read_text(encoding="utf-8")
    if "/api/operator/plugins/libraries" not in api:
        print("[plug-adapter-gate] FAIL: missing plugins API")
        return 1
    env = dict(os.environ)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_plug_discovery.py",
            "tests/test_plug_adapter_runtime.py",
            "tests/test_mcp_bridge.py",
            "tests/test_workflow_plugin_catalog.py",
            "tests/test_library_registry.py",
            "-q",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        return 1
    print("[plug-adapter-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
