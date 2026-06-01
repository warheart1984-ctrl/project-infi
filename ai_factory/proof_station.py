"""Verification and proof station — orchestrate existing test lanes."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_factory.common import ClaimLabel, derive_claim_status, hash_manifest_entry, write_json
from ai_factory.spec import AIBuildSpec
from src.datetime_compat import UTC

PROOF_MANIFEST_VERSION = "ai_factory.proof_manifest.v1"


class ProofStationError(RuntimeError):
    """Raised when verification fails."""


def _run_command(cmd: list[str], *, repo_root: Path, label: str) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    ok = proc.returncode == 0
    return {
        "lane": label,
        "command": cmd,
        "passed": ok,
        "returncode": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-4000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
        "claim_label": "asserted" if ok else "rejected",
    }


def _default_test_lanes(*, require_agency: bool) -> list[tuple[str, list[str]]]:
    lanes: list[tuple[str, list[str]]] = [
        (
            "constitutional",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_nova_formal_spec.py",
                "tests/test_spark_pipeline.py",
                "-q",
            ],
        ),
        (
            "composed_turn",
            [sys.executable, "-m", "pytest", "tests/test_aais_composed_runtime.py", "-q"],
        ),
        (
            "capability_governance",
            [sys.executable, "-m", "pytest", "tests/test_capability_governance.py", "-q"],
        ),
        (
            "nova_cortex_gate",
            [sys.executable, ".github/scripts/check-nova-cortex-governance.py"],
        ),
        (
            "factory",
            [sys.executable, "-m", "pytest", "tests/test_ai_factory.py", "-q"],
        ),
    ]
    if require_agency:
        lanes.append(
            (
                "agency",
                [sys.executable, "-m", "pytest", "tests/test_intent_agency_evidence.py", "-q"],
            )
        )
    return lanes


def run_verification_lanes(
    *,
    repo_root: Path,
    spec: AIBuildSpec,
    skip_pytest: bool = False,
) -> list[dict[str, Any]]:
    if skip_pytest:
        return [
            {
                "lane": "skipped",
                "passed": True,
                "claim_label": "asserted",
                "note": "verification skipped by flag",
            }
        ]
    results: list[dict[str, Any]] = []
    for label, cmd in _default_test_lanes(require_agency=spec.oversight.require_agency_check):
        results.append(_run_command(cmd, repo_root=repo_root, label=label))
    return results


def build_proof_manifest(
    *,
    spec: AIBuildSpec,
    lane_results: list[dict[str, Any]],
    output_dir: Path,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at_utc or datetime.now(UTC).isoformat()
    lane_claims: list[ClaimLabel] = [
        str(item.get("claim_label") or ("asserted" if item.get("passed") else "rejected"))  # type: ignore[arg-type]
        for item in lane_results
    ]
    overall = derive_claim_status(lane_claims)
    constitutional_failed = any(
        not item.get("passed")
        for item in lane_results
        if item.get("lane") in {"constitutional", "nova_cortex_gate"}
    )
    deploy_blocked = spec.risk_level == "high" and constitutional_failed
    if deploy_blocked:
        overall = "rejected"

    proof_md = output_dir / "AI_PROOF_BUNDLE.md"
    manifest_path = output_dir / "proof_manifest.json"

    hash_manifest: list[dict[str, Any]] = []
    if proof_md.is_file():
        hash_manifest.append(
            hash_manifest_entry(
                artifact="proof_bundle_md",
                path=proof_md,
                claim_label=overall if overall != "rejected" else "rejected",
            )
        )

    return {
        "manifest_version": PROOF_MANIFEST_VERSION,
        "build_id": spec.build_id,
        "generated_at_utc": generated_at,
        "claim_label": overall,
        "risk_rating": spec.risk_level,
        "deploy_blocked": deploy_blocked,
        "verification_summary": {
            "lanes_run": len(lane_results),
            "lanes_passed": sum(1 for item in lane_results if item.get("passed")),
            "cross_machine_status": "inactive",
        },
        "lane_results": lane_results,
        "hash_manifest": sorted(hash_manifest, key=lambda item: str(item["artifact"])),
        "proof_bundle_ref": str(proof_md.resolve()) if proof_md.exists() else "AI_PROOF_BUNDLE.md",
    }


def render_proof_bundle_markdown(
    *,
    spec: AIBuildSpec,
    lane_results: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> str:
    lines = [
        "# AI Factory Proof Bundle v1",
        "",
        f"**Build ID:** `{spec.build_id}`",
        f"**Claim label:** `{manifest.get('claim_label')}`",
        f"**Risk rating:** `{manifest.get('risk_rating')}`",
        f"**Deploy blocked:** `{manifest.get('deploy_blocked')}`",
        "",
        "## Verification lanes",
        "",
    ]
    for item in lane_results:
        status = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- **{item.get('lane')}**: {status}")
        if item.get("command"):
            lines.append(f"  - Command: `{' '.join(str(x) for x in item['command'])}`")
    lines.extend(
        [
            "",
            "## Claim posture",
            "",
            "Single-machine pytest + governance scripts. Cross-machine replay: **inactive**.",
            "",
            "## Template",
            "",
            "See `templates/PROOF_BUNDLE_TEMPLATE.md`.",
            "",
        ]
    )
    return "\n".join(lines)


def run_proof_station(
    *,
    spec: AIBuildSpec,
    output_dir: Path,
    repo_root: Path,
    skip_pytest: bool = False,
    generated_at_utc: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    lane_results = run_verification_lanes(
        repo_root=repo_root,
        spec=spec,
        skip_pytest=skip_pytest,
    )
    failed = [item for item in lane_results if not item.get("passed")]
    manifest = build_proof_manifest(
        spec=spec,
        lane_results=lane_results,
        output_dir=output_dir,
        generated_at_utc=generated_at_utc,
    )
    proof_md_path = output_dir / "AI_PROOF_BUNDLE.md"
    proof_md_path.write_text(
        render_proof_bundle_markdown(spec=spec, lane_results=lane_results, manifest=manifest),
        encoding="utf-8",
    )
    manifest = build_proof_manifest(
        spec=spec,
        lane_results=lane_results,
        output_dir=output_dir,
        generated_at_utc=generated_at_utc,
    )
    manifest_path = output_dir / "proof_manifest.json"
    write_json(manifest_path, manifest)

    status = "ok" if not failed and not manifest.get("deploy_blocked") else "failed"
    receipt = {
        "station": "proof",
        "station_version": "ai_factory.proof_station.v1",
        "status": status,
        "build_id": spec.build_id,
        "claim_label": manifest.get("claim_label"),
        "deploy_blocked": manifest.get("deploy_blocked"),
        "lanes_passed": manifest["verification_summary"]["lanes_passed"],
        "lanes_run": manifest["verification_summary"]["lanes_run"],
        "outputs": {
            "proof_bundle": str(proof_md_path.resolve()),
            "proof_manifest": str(manifest_path.resolve()),
        },
        "trace": ["run_verification_lanes", "render_proof_bundle", "write_proof_manifest"],
    }
    if failed or manifest.get("deploy_blocked"):
        raise ProofStationError(
            f"proof station failed: {len(failed)} lane(s) failed, deploy_blocked={manifest.get('deploy_blocked')}"
        )
    return manifest, receipt
