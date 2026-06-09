"""Build Synthetic Mind bundle after AI Factory promote (host payload staging retired with Wolf CoG OS)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from ai_factory.orchestrator import FactoryBuildError


def stage_synthetic_mind_bundle(
    *,
    repo_root: Path,
    build_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Build the portable Synthetic Mind bundle under artifacts/."""
    repo = repo_root.expanduser().resolve()
    script = repo / "scripts" / "cogos" / "build_synthetic_mind_bundle.py"
    bundle_dir = repo / "artifacts" / "synthetic-mind-bundle"

    receipt: dict[str, Any] = {
        "stage": "synthetic_mind_bundle",
        "build_id": build_id,
        "dry_run": dry_run,
        "bundle_dir": str(bundle_dir),
        "claim_label": "asserted",
    }
    if dry_run:
        receipt["status"] = "skipped_dry_run"
        return receipt

    if not script.is_file():
        raise FactoryBuildError(f"missing bundle builder: {script}")

    env = {**__import__("os").environ, "COGOS_AI_FACTORY_BUILD_ID": build_id}
    proc = subprocess.run(
        [sys.executable, str(script), str(bundle_dir)],
        cwd=str(repo),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise FactoryBuildError(
            f"synthetic mind bundle build failed: {proc.stderr or proc.stdout}"
        )

    manifest = bundle_dir / "synthetic_mind_manifest.json"
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
        receipt["bundle_sha256"] = data.get("bundle_sha256")
        receipt["family_id"] = data.get("family_id")

    receipt["status"] = "built"
    receipt["payload_stage_mode"] = "bundle_only"
    return receipt


# Back-compat alias for callers that still use the old name.
stage_synthetic_mind_after_wolf_deploy = stage_synthetic_mind_bundle
