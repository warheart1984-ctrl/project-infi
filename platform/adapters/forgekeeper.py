"""Forgekeeper dry-run plan adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from forge.forgekeeper import DryRunPlan, ForgekeeperRequest, build_dry_run_plan


def run_forgekeeper_plan(
    *,
    plan_id: str,
    scope: str = ".",
    proof_dir: Path | None = None,
) -> dict[str, Any]:
    proof = proof_dir or Path("docs/proof/bumblebee-forge")
    proof.mkdir(parents=True, exist_ok=True)
    request = ForgekeeperRequest(plan_id=plan_id, goal="platform-plan", scope=scope)
    plan: DryRunPlan = build_dry_run_plan(request)
    out_path = proof / f"{plan_id}_plan.json"
    out_path.write_text(json.dumps(plan.to_dict(), sort_keys=True, indent=2), encoding="utf-8")
    return {
        "plan_id": plan_id,
        "plan_path": str(out_path),
        "artifact_dir": str(proof),
        "plan": plan.to_dict(),
    }
