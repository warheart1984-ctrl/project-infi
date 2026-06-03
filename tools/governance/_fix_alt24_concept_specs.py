#!/usr/bin/env python3
"""Repair Release 24 ideas_pending concept specs for global ssp-gate."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt24-summon-wave-2026-06"

SPECS = [
    (
        "LINGUISTIC_FORECAST_CALIBRATION_ORGAN",
        "linguistic_forecast_calibration_organ",
        "AAIS-LFC-02",
        "Read-only forecast-vs-reality calibration posture (Wave 13).",
        "src/governance_organs/linguistic_forecast_calibration_engine.py",
        "GET /api/jarvis/linguistic-forecast-calibration/status",
    ),
    (
        "LINGUISTIC_GOVERNANCE_QUEUE_ORGAN",
        "linguistic_governance_queue_organ",
        "AAIS-LGQ-01",
        "Read-only prescriptive queue and work-order posture (Wave 13–14).",
        "src/governance_organs/linguistic_governance_queue_engine.py",
        "GET /api/jarvis/linguistic-governance-queue/status",
    ),
    (
        "LINGUISTIC_FULL_GOVERNANCE_CYCLE_ORGAN",
        "linguistic_full_governance_cycle_organ",
        "AAIS-LFG-01",
        "Read-only full calibrate→predict→react→queue→attest cycle posture.",
        "src/governance_organs/linguistic_full_governance_cycle_engine.py",
        "GET /api/jarvis/linguistic-full-governance-cycle/status",
    ),
    (
        "LINGUISTIC_GOVERNANCE_ATTESTATION_ORGAN",
        "linguistic_governance_attestation_organ",
        "AAIS-LGA-01",
        "Read-only unified attestation digest and closed_loop_score (Wave 14).",
        "src/governance_organs/linguistic_governance_attestation_engine.py",
        "GET /api/jarvis/linguistic-governance-attestation/status",
    ),
]


def body(name: str, gene: str, module_id: str, purpose: str, wraps: str, api: str) -> str:
    return f"""# {name.replace('_', ' ').title()}

CISIV stage: **concept**

Status: pending — Release 24 (`{BATCH}`).

## 1. Purpose

{purpose}

Wraps: [`{wraps}`](../../{wraps}).

## 2. Authority And Precedence

Law > Blueprint > Contract > Implementation. Read-only subsystem surface.

## 3. Non-Goals

- No autonomous mutation authority via subsystem API

## 4. Subsystem Contract

Schema: [schemas/{gene}.v1.json](./schemas/{gene}.v1.json)

| Field | Role |
|-------|------|
| `module_id` | `{module_id}` |

## 5. Runtime (Proposed)

- `{api}`

## 6. Failsafe

Bounded snapshot when upstream idle.

## 7. Proof Posture (Concept)

| Claim | Label |
|-------|-------|
| Schema covers required fields | `asserted` | Schema + this document |
| Status API | `none_yet` | Requires MVP |

## 8. CISIV Path

| Stage | Deliverable |
|-------|-------------|
| Concept | This document + schema |
| Verification | V1 proof + gate |

## 9. Related

- [AAIS_META_LINGUISTIC_GOVERNANCE.md](../../contracts/AAIS_META_LINGUISTIC_GOVERNANCE.md)
"""


def main() -> None:
    ideas = ROOT / "docs/_future/ideas_pending"
    for spec in SPECS:
        (ideas / f"{spec[0]}.md").write_text(body(*spec), encoding="utf-8")
    print("[fix-alt24] repaired 4 concept specs")


if __name__ == "__main__":
    main()
