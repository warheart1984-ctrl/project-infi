"""AI Factory build adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_factory.orchestrator import run_build


def run_ai_factory_build(
    *,
    spec_path: str,
    repo_root: Path | None = None,
    skip_pytest: bool = True,
) -> dict[str, Any]:
    result = run_build(
        spec_path=spec_path,
        repo_root=repo_root or Path("."),
        skip_pytest=skip_pytest,
    )
    return {
        "build_id": result.build_id,
        "output_dir": str(result.output_dir),
        "receipt": result.receipt,
        "hash_manifest": result.receipt.get("hash_manifest") or [],
    }
