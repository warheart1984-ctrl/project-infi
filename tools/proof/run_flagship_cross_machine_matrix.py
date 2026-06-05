#!/usr/bin/env python3
"""Run flagship cross-machine verification matrix and emit machine profile artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / ".runtime" / "cross_machine_matrix"
MANIFEST_PATH = PROJECT_ROOT / "docs" / "proof" / "aais-ul" / "cross_machine" / "REPLAY_MANIFEST.v1.json"

def _verification_commands() -> list[dict[str, str]]:
    python = sys.executable
    return [
        {
            "id": "ul_cisiv_core",
            "label": "UL/CISIV core pytest gate",
            "command": (
                f"{python} -m pytest tests/test_cisiv.py tests/test_run_ledger_cisiv.py "
                "tests/test_chat_turn_governance.py tests/test_forge_repo_governance.py "
                "tests/test_module_governance.py tests/test_aais_ul_substrate.py -q --tb=no"
            ),
        },
        {
            "id": "ul_drift",
            "label": "UL adapter drift check",
            "command": f"{python} -m tools.ul.drift",
        },
        {
            "id": "ul_smoke",
            "label": "UL smoke samples",
            "command": f"{python} -m tools.ul.smoke",
        },
        {
            "id": "naming_gate",
            "label": "Naming protocol gate",
            "command": f"{python} tools/naming_protocol_lint.py",
        },
        {
            "id": "genome_gate",
            "label": "Subsystem genome gate",
            "command": f"{python} tools/governance/check_subsystem_genome.py",
        },
        {
            "id": "memory_gateway",
            "label": "Memory board enforcer gate",
            "command": f"{python} -m pytest tests/test_memory_board_enforcer.py -q --tb=no",
        },
    ]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _machine_profile(role: str) -> dict[str, str]:
    return {
        "role": role,
        "hostname": platform.node(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "architecture": platform.machine(),
        "recorded_at_utc": _utc_now(),
    }


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _run_command(command: str, *, cwd: Path, env: dict[str, str] | None = None) -> dict[str, object]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=run_env,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    return {
        "command": command,
        "exit_code": completed.returncode,
        "passed": completed.returncode == 0,
        "output_sha256": _sha256_text(output),
        "output_tail": output[-4000:] if output else "",
    }


def _secondary_env() -> dict[str, str]:
    runtime_root = PROJECT_ROOT / ".runtime" / "cross_machine_matrix" / f"clean-{uuid.uuid4().hex}"
    runtime_root.mkdir(parents=True, exist_ok=True)
    return {
        "AAIS_DATA_DIR": str(runtime_root / "data"),
        "AAIS_RUNTIME_DIR": str(runtime_root / "runtime"),
        "AAIS_TEST_COLD_START": "1",
        "AAIS_GOVERNED_PIPELINE_CACHE_SEC": "0",
        "AAIS_COHERENCE_FABRIC_CACHE_SEC": "0",
    }


def run_matrix(*, role: str, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = _machine_profile(role)
    if role == "secondary":
        profile["profile_kind"] = "clean_runtime"
        profile["notes"] = "Independent clean runtime profile with isolated AAIS_DATA_DIR (REPO_PROOF_LAW secondary environment)."
    command_env = _secondary_env() if role == "secondary" else None
    results: list[dict[str, object]] = []
    for entry in _verification_commands():
        result = _run_command(entry["command"], cwd=PROJECT_ROOT, env=command_env)
        results.append(
            {
                "id": entry["id"],
                "label": entry["label"],
                **result,
            }
        )
    payload = {
        "manifest_version": "aais.flagship_cross_machine_matrix.v1",
        "machine": profile,
        "results": results,
        "overall_passed": all(bool(item["passed"]) for item in results),
    }
    slug = profile["hostname"].replace(" ", "_").lower() or role
    out_path = output_dir / f"{role}-{slug}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["artifact_path"] = str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    return payload


def compare_profiles(primary: dict[str, object], secondary: dict[str, object]) -> dict[str, object]:
    primary_results = {item["id"]: item for item in primary.get("results", [])}
    secondary_results = {item["id"]: item for item in secondary.get("results", [])}
    rows: list[dict[str, object]] = []
    for command_id in primary_results:
        primary_row = primary_results.get(command_id, {})
        secondary_row = secondary_results.get(command_id, {})
        rows.append(
            {
                "id": command_id,
                "primary_passed": primary_row.get("passed"),
                "secondary_passed": secondary_row.get("passed"),
                "hash_match": primary_row.get("output_sha256") == secondary_row.get("output_sha256"),
                "parity": bool(primary_row.get("passed")) and bool(secondary_row.get("passed")),
                "claim_label": "proven" if bool(primary_row.get("passed")) and bool(secondary_row.get("passed")) else "asserted",
            }
        )
    return {
        "compared_at_utc": _utc_now(),
        "primary_machine": primary.get("machine"),
        "secondary_machine": secondary.get("machine"),
        "rows": rows,
        "matrix_passed": all(row["parity"] for row in rows),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run AAIS flagship cross-machine verification matrix.")
    parser.add_argument("--role", choices=("primary", "secondary"), default="primary")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--compare", action="store_true", help="Compare primary vs secondary artifacts.")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    profile = run_matrix(role=args.role, output_dir=output_dir)
    print(f"flagship cross-machine matrix: role={args.role} passed={profile['overall_passed']}")
    print(f"artifact: {profile['artifact_path']}")

    if args.compare:
        primary_files = sorted(output_dir.glob("primary-*.json"))
        secondary_files = sorted(output_dir.glob("secondary-*.json"))
        if not primary_files or not secondary_files:
            print("compare: missing primary or secondary artifact")
            return 1
        primary = json.loads(primary_files[-1].read_text(encoding="utf-8"))
        secondary = json.loads(secondary_files[-1].read_text(encoding="utf-8"))
        comparison = compare_profiles(primary, secondary)
        compare_path = output_dir / "matrix_comparison.json"
        compare_path.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
        print(f"comparison: matrix_passed={comparison['matrix_passed']} artifact={compare_path}")
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "manifest_version": "aais.flagship_cross_machine_matrix.v1",
            "operational_status": "active" if comparison["matrix_passed"] else "debt",
            "primary_machine": comparison["primary_machine"],
            "secondary_machine": comparison["secondary_machine"],
            "comparison_artifact": str(compare_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "matrix_passed": comparison["matrix_passed"],
            "updated_at_utc": _utc_now(),
        }
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return 0 if comparison["matrix_passed"] else 1

    return 0 if profile["overall_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
