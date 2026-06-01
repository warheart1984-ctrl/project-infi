"""Generate markdown operator reports from Mechanic case artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_case_artifacts(case_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    genome_path = case_dir / "process_genome.v1.json"
    scan_path = case_dir / "mechanic_scan.v1.json"
    if not genome_path.is_file():
        raise ValueError(f"missing process_genome.v1.json in {case_dir}")
    if not scan_path.is_file():
        raise ValueError(f"missing mechanic_scan.v1.json in {case_dir}")
    genome = json.loads(genome_path.read_text(encoding="utf-8"))
    scan = json.loads(scan_path.read_text(encoding="utf-8"))
    return genome, scan


def generate_report_markdown(
    *,
    case_id: str,
    genome: dict[str, Any],
    scan: dict[str, Any],
    case_dir: Path | None = None,
) -> str:
    drifts = list(scan.get("drifts") or [])
    lines: list[str] = [
        f"# AI Mechanic Report — `{case_id}`",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **Claim** | `{scan.get('claim_label', 'asserted')}` |",
        f"| **Drift count** | {scan.get('drift_count', len(drifts))} |",
        f"| **Genome hash** | `{genome.get('genome_hash', '')}` |",
        f"| **Scan hash** | `{scan.get('scan_hash', '')}` |",
        "",
        "## Drift codes",
        "",
        "| Code | Severity | MA-13 | Summary |",
        "|------|----------|-------|---------|",
    ]
    for drift in drifts:
        code = str(drift.get("code") or "")
        severity = str(drift.get("severity") or "")
        ma13 = str(drift.get("ma13_class") or "—")
        summary = str(drift.get("drift_summary") or "").replace("|", "\\|")
        lines.append(f"| {code} | {severity} | {ma13} | {summary} |")

    lines.extend(["", "## Top evidence", ""])
    for drift in drifts[:8]:
        evidence = drift.get("evidence") or {}
        if evidence:
            lines.append(f"- **{drift.get('code')}**: `{json.dumps(evidence, sort_keys=True)}`")

    severity_counts = Counter(str(d.get("severity") or "unknown") for d in drifts)
    ma13_counts = Counter(str(d.get("ma13_class") or "—") for d in drifts)
    lines.extend(
        [
            "",
            "## Severity summary",
            "",
            ", ".join(f"{k}: {v}" for k, v in sorted(severity_counts.items())),
            "",
            "## MA-13 class summary",
            "",
            ", ".join(f"{k}: {v}" for k, v in sorted(ma13_counts.items())),
            "",
            "## Rebuild artifacts",
            "",
        ]
    )
    artifact_names = (
        "target_workflow.v1.json",
        "patch_plan.v1.json",
        "MECHANIC_RUNTIME_PROFILE.json",
        "reconstruction_plan.v1.json",
    )
    base = case_dir or Path(".runtime/mechanic") / case_id
    for name in artifact_names:
        path = base / name
        status = "present" if path.is_file() else "missing"
        lines.append(f"- `{name}` — {status}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "Rebuild and apply proposals are **provisional** (MA-13). Raw `apply` mode remains blocked.",
            "",
        ]
    )
    return "\n".join(lines)


def build_report_payload(*, case_id: str, case_dir: Path) -> dict[str, Any]:
    genome, scan = load_case_artifacts(case_dir)
    markdown = generate_report_markdown(case_id=case_id, genome=genome, scan=scan, case_dir=case_dir)
    return {
        "mode": "report",
        "case_id": case_id,
        "drift_count": scan.get("drift_count", len(scan.get("drifts") or [])),
        "report_markdown": markdown,
        "claim_label": "asserted",
        "safety_state": "dry_run_only",
    }
