#!/usr/bin/env python3
"""Write Alt-10 governed proof stubs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PROOFS = [
    ("platform", "VERIFICATION_GATE_ORGAN"),
    ("platform", "MEMORY_PATH_GOVERNANCE_ORGAN"),
    ("platform", "KNOWLEDGE_AUTHORITY_ORGAN"),
    ("forensics", "SCORPION_BRIDGE_ORGAN"),
    ("forensics", "MECHANIC_HANDOFF_ORGAN"),
    ("forensics", "FORENSIC_TRIANGULATION_ORGAN"),
    ("nova", "IMMUNE_OBSERVE_ORGAN"),
    ("nova", "POLICY_GATE_ORGAN"),
    ("nova", "PREDICTOR_IMMUNE_BRIDGE_ORGAN"),
]

TEMPLATE = """# {name} Governed Proof

## Verification

```bash
make alt10-governed-gate
```
"""


def main() -> None:
    for subdir, name in PROOFS:
        path = ROOT / "docs/proof" / subdir / f"{name}_GOVERNED_PROOF.md"
        path.write_text(TEMPLATE.format(name=name.replace("_", " ").title()), encoding="utf-8")
    print(f"[alt10] wrote {len(PROOFS)} governed proofs")


if __name__ == "__main__":
    main()
