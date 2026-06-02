"""Stage Synthetic Mind bundle into Wolf payload after AI Factory promote."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ai_factory.orchestrator import FactoryBuildError


def _bash_path(path: Path) -> str:
    resolved = path.expanduser().resolve()
    if os.name != "nt":
        return resolved.as_posix()
    drive = resolved.drive.rstrip(":").lower()
    rest = resolved.as_posix()[len(resolved.drive):].lstrip("/")
    if drive:
        return f"/mnt/{drive}/{rest}"
    return resolved.as_posix()


def stage_synthetic_mind_after_wolf_deploy(
    *,
    repo_root: Path,
    build_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Invoke build-synthetic-mind-bundle.sh and stage into wolf payload cache."""
    repo = repo_root.expanduser().resolve()
    script = repo / "scripts" / "cogos" / "build_synthetic_mind_bundle.py"
    bundle_dir = repo / "wolf-cog-os" / "artifacts" / "synthetic-mind-bundle"
    stage_script = repo / "wolf-cog-os" / "scripts" / "stage-nova-cortex-into-payload.sh"

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
        [__import__("sys").executable, str(script), str(bundle_dir)],
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

    wolf_payload = repo / "wolf-cog-os" / "payload"
    cache_env = os.environ.get("COGOS_PAYLOAD_CACHE")
    payload_cache = Path(cache_env) if cache_env else Path.home() / ".cogos-payload-cache"
    if not (payload_cache / "opt" / "cogos").is_dir() and (wolf_payload / "opt" / "cogos").is_dir():
        payload_cache = wolf_payload
    if payload_cache.resolve() == wolf_payload.resolve():
        manifest = bundle_dir / "synthetic_mind_manifest.json"
        if manifest.is_file():
            target = wolf_payload / "opt" / "cogos" / "config" / "synthetic_mind_manifest.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(manifest, target)
        receipt["payload_cache"] = str(payload_cache)
        receipt["payload_stage_mode"] = "repo_payload_only"
    elif stage_script.is_file():
        proc2 = subprocess.run(
            ["bash", _bash_path(stage_script), _bash_path(payload_cache), _bash_path(wolf_payload)],
            cwd=str(repo),
            text=True,
            capture_output=True,
            check=False,
        )
        if proc2.returncode != 0:
            raise FactoryBuildError(
                f"synthetic mind payload stage failed: {proc2.stderr or proc2.stdout}"
            )
        receipt["payload_cache"] = str(payload_cache)

    manifest = bundle_dir / "synthetic_mind_manifest.json"
    if manifest.is_file():
        import json

        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
        receipt["bundle_sha256"] = data.get("bundle_sha256")
        receipt["family_id"] = data.get("family_id")

    receipt["status"] = "staged"
    return receipt
