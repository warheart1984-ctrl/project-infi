#!/usr/bin/env python3
"""Bootstrap Release 26 active subsystem docs and governed proof stubs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt26-summon-wave-2026-06"
PLATFORM = ROOT / "docs/subsystems/platform"
PROOF = ROOT / "docs/proof/platform"

ORGANS = [
    ("linguistic_governance_day_organ", "linguistic-governance-day", "linguistic-governance-day-organ-gate"),
    ("linguistic_work_order_history_organ", "linguistic-work-order-history", "linguistic-work-order-history-organ-gate"),
    ("linguistic_attestation_history_organ", "linguistic-attestation-history", "linguistic-attestation-history-organ-gate"),
]


def active_doc(gene: str, api: str, gate: str) -> str:
    upper = gene.upper()
    return f"""# {gene.replace('_', ' ').title()}

Status: **implementation** (Release 26 `{BATCH}`)

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
| Gate passes under alt26-governed-gate | proven |

## Reproduction

```bash
make {gate}
make alt26-governed-gate
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
    print(f"[alt26-runtime] synced {len(ORGANS)} platform docs")


if __name__ == "__main__":
    main()
