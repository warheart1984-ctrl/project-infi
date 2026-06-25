#!/usr/bin/env python3
"""Write Alt-12 governed proof stubs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PROOFS = [
    "OTEM_BOUNDED_ORGAN",
    "DIRECT_CHALLENGE_ORGAN",
    "ORCHESTRATION_SPINE_ORGAN",
    "OPERATOR_HEALTH_SENTINEL_ORGAN",
    "GOVERNED_REALTIME_LANE_ORGAN",
    "V8_RUNTIME_ORGAN",
    "PATCH_APPLY_ORGAN",
    "PATCH_EXECUTION_PREVIEW_ORGAN",
    "RUN_LEDGER_ORGAN",
]

TEMPLATE = """# {name} Governed Proof

## Verification

```bash
make alt12-governed-gate
```
"""


def main() -> None:
    for name in PROOFS:
        path = ROOT / "docs/proof/platform" / f"{name}_GOVERNED_PROOF.md"
        path.write_text(TEMPLATE.format(name=name.replace("_", " ").title()), encoding="utf-8")
    print(f"[alt12] wrote {len(PROOFS)} governed proofs")


if __name__ == "__main__":
    main()
