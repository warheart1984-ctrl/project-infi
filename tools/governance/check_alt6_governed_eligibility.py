#!/usr/bin/env python3
"""Alt-6 governed promotion eligibility — fabric minimum lane DNA + awakened registry."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.adaptive_lane_organ import wake_adaptive_lanes
from src.governance_organs.genome_engine import GenomeEngine

FABRIC_MINIMUM_GENES = (
    "adaptive_lane_organ",
    "operator_profile_organ",
    "capability_service_bridge",
    "recipe_module_organ",
    "governed_direct_pipeline",
)

GOVERNED_PROOF = _ROOT / "docs/proof/platform/ADAPTIVE_LANE_GOVERNED_PROOF.md"


def _valid_operator_lanes(gov: dict[str, Any], gene: str) -> list[str]:
    errors: list[str] = []
    lanes = gov.get("operator_lanes")
    if not lanes:
        errors.append(f"{gene} missing operator_lanes")
        return errors
    if not isinstance(lanes, list):
        errors.append(f"{gene} operator_lanes must be array")
        return errors
    for index, lane in enumerate(lanes):
        if not isinstance(lane, dict):
            errors.append(f"{gene} operator_lanes[{index}] must be object")
            continue
        if not str(lane.get("lane_id") or "").strip():
            errors.append(f"{gene} operator_lanes[{index}] missing lane_id")
        if not lane.get("capabilities"):
            errors.append(f"{gene} operator_lanes[{index}] missing capabilities")
    return errors


def _adaptive_lane_maturity_tags(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for entry in (data.get("governance") or {}).get("invariants") or []:
        if isinstance(entry, str):
            errors.append("adaptive_lane_organ invariants must be maturity-tagged objects")
            break
        if isinstance(entry, dict) and not entry.get("maturity"):
            errors.append("adaptive_lane_organ invariant missing maturity")
    return errors


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    GenomeEngine.reload(root)
    reg = GenomeEngine.registry()
    errors: list[str] = []

    for gene in FABRIC_MINIMUM_GENES:
        data = reg.genomes.get(gene)
        if not data:
            errors.append(f"missing genome: {gene}")
            continue
        errors.extend(_valid_operator_lanes(data.get("governance") or {}, gene))

    organ = reg.genomes.get("adaptive_lane_organ")
    if organ:
        errors.extend(_adaptive_lane_maturity_tags(organ))

    if not GOVERNED_PROOF.is_file():
        errors.append(f"missing governed proof bundle: {GOVERNED_PROOF.relative_to(root)}")

    report = wake_adaptive_lanes(root)
    if not report.get("awakened"):
        errors.append("adaptive lanes not awakened")
    if str(report.get("authority_lane") or "") != "operator":
        errors.append(
            f"authority_lane must be operator (got {report.get('authority_lane')!r})"
        )
    genes_with_lanes = set(report.get("genes_with_lanes") or [])
    missing = [gene for gene in FABRIC_MINIMUM_GENES if gene not in genes_with_lanes]
    if missing:
        errors.append(f"awakened registry missing fabric genes: {', '.join(missing)}")
    lane_ids = {lane.get("lane_id") for lane in report.get("lanes") or []}
    if "operator" not in lane_ids:
        errors.append("awakened registry missing merged operator lane")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt6-governed-gate] FAIL: {err}")
        return 1
    print(
        f"[alt6-governed-gate] PASS: fabric minimum "
        f"({len(FABRIC_MINIMUM_GENES)} genes) awakened and eligible"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
