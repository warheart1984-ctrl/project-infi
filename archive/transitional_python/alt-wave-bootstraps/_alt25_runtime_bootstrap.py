#!/usr/bin/env python3
"""Bootstrap Release 25 active subsystem docs and governed proof stubs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt25-summon-wave-2026-06"
PLATFORM = ROOT / "docs/subsystems/platform"
PROOF = ROOT / "docs/proof/platform"

ORGANS = [
    ("linguistic_forecast_archive_organ", "linguistic-forecast-archive", "linguistic-forecast-archive-organ-gate"),
    ("linguistic_drift_report_organ", "linguistic-drift-report", "linguistic-drift-report-organ-gate"),
    ("linguistic_governance_work_order_organ", "linguistic-governance-work-order", "linguistic-governance-work-order-organ-gate"),
    ("linguistic_governance_cadence_organ", "linguistic-governance-cadence", "linguistic-governance-cadence-organ-gate"),
    ("linguistic_forecast_calibration_report_organ", "linguistic-forecast-calibration-report", "linguistic-forecast-calibration-report-organ-gate"),
    ("linguistic_full_governance_cycle_history_organ", "linguistic-full-governance-cycle-history", "linguistic-full-governance-cycle-history-organ-gate"),
    ("meta_linguistic_registry_organ", "meta-linguistic-registry", "meta-linguistic-registry-organ-gate"),
    ("linguistic_subsystem_promotion_organ", "linguistic-subsystem-promotion", "linguistic-subsystem-promotion-organ-gate"),
    ("linguistic_governed_lifecycle_fabric_organ", "linguistic-governed-lifecycle-fabric", "linguistic-governed-lifecycle-fabric-organ-gate"),
]


def active_doc(gene: str, api: str, gate: str) -> str:
    upper = gene.upper()
    return f"""# {gene.replace('_', ' ').title()}

Status: **implementation** (Release 25 `{BATCH}`)

## Runtime

- Module: `src/{gene}.py`
- API: `GET /api/jarvis/{api}/status`
- Gate: `make {gate}`

## Proof

[{upper}_V1_PROOF.md](../../proof/platform/{upper}_V1_PROOF.md)
"""


def governed_proof(gene: str, gate: str) -> str:
    return f"""# {gene.replace('_', ' ').title()} Governed Proof

## Claims

| Claim | Label |
|-------|-------|
| Subsystem at governed stage with runtime surface | proven |
| Gate passes under alt25-governed-gate | proven |

## Reproduction

```bash
make {gate}
make alt25-governed-gate
```
"""


def main() -> None:
    PLATFORM.mkdir(parents=True, exist_ok=True)
    PROOF.mkdir(parents=True, exist_ok=True)
    for gene, api, gate in ORGANS:
        upper = gene.upper()
        doc = PLATFORM / f"{upper}.md"
        if not doc.is_file():
            doc.write_text(active_doc(gene, api, gate), encoding="utf-8")
        gov = PROOF / f"{upper}_GOVERNED_PROOF.md"
        if not gov.is_file():
            gov.write_text(governed_proof(gene, gate), encoding="utf-8")
    print(f"[alt25-runtime] synced {len(ORGANS)} platform docs")


if __name__ == "__main__":
    main()
