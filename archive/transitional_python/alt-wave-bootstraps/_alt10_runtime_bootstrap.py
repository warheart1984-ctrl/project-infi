#!/usr/bin/env python3
"""Bootstrap Alt-10 gates, tests, active docs, and proof stubs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ORGANS = [
    ("verification_gate_organ", "platform", "build_verification_gate_status"),
    ("memory_path_governance_organ", "platform", "build_memory_path_governance_status"),
    ("knowledge_authority_organ", "platform", "build_knowledge_authority_status"),
    ("scorpion_bridge_organ", "forensics", "build_scorpion_bridge_status"),
    ("mechanic_handoff_organ", "forensics", "build_mechanic_handoff_status"),
    ("forensic_triangulation_organ", "forensics", "build_forensic_triangulation_status"),
    ("immune_observe_organ", "nova", "build_immune_observe_status"),
    ("policy_gate_organ", "nova", "build_policy_gate_status"),
    ("predictor_immune_bridge_organ", "nova", "build_predictor_immune_bridge_status"),
]


def gate_script(gene: str) -> str:
    gate = gene.replace("_", "-")
    return f'''#!/usr/bin/env python3
"""{gene} governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_{gene}.py", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print("[{gate}-gate] FAIL")
        return 1
    print("[{gate}-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def test_py(gene: str, builder: str) -> str:
    return f'''"""Tests for {gene}."""

from __future__ import annotations

from src.{gene} import {builder}


def test_build_status():
    status = {builder}()
    assert status["{gene}_version"] == "{gene}.v1"
    assert status["read_only"] is True
    assert status["module_id"]
'''


def active_doc(gene: str, subdir: str) -> str:
    title = gene.replace("_", " ").title()
    gate = gene.replace("_", "-")
    api = gene.replace("_", "-")
    if gene == "memory_path_governance_organ":
        api = "memory-path-governance"
    elif gene == "forensic_triangulation_organ":
        api = "forensic-triangulation"
    elif gene == "predictor_immune_bridge_organ":
        api = "predictor-immune-bridge"
    elif gene == "verification_gate_organ":
        api = "verification-gate"
    elif gene == "knowledge_authority_organ":
        api = "knowledge-authority"
    elif gene == "scorpion_bridge_organ":
        api = "scorpion-bridge"
    elif gene == "mechanic_handoff_organ":
        api = "mechanic-handoff"
    elif gene == "immune_observe_organ":
        api = "immune-observe"
    elif gene == "policy_gate_organ":
        api = "policy-gate"
    proof = f"../../proof/{subdir}/{gene.upper()}_V1_PROOF.md"
    return f"""# {title}

Status: **mvp** (Alt-10 summon wave `alt10-summon-wave-2026-06`)

## Runtime

- Module: `src/{gene}.py`
- API: `GET /api/jarvis/{api}/status`
- Gate: `make {gate}-gate`

## Proof

[{gene.upper()}_V1_PROOF.md]({proof})
"""


def proof_md(gene: str, subdir: str) -> str:
    gate = gene.replace("_", "-")
    return f"""# {gene.replace('_', ' ').title()} V1 Proof

## Claims

| Claim | Label |
|-------|-------|
| Status API returns bounded snapshot | asserted |
| Organ surface is read-only | asserted |

## Reproduction

```bash
make {gate}-gate
python -m pytest tests/test_{gene}.py -q
```
"""


def main() -> None:
    for gene, subdir, builder in ORGANS:
        gate_name = gene.replace("_", "-")
        (ROOT / ".github/scripts" / f"check-{gate_name}-governance.py").write_text(
            gate_script(gene), encoding="utf-8"
        )
        (ROOT / "tests" / f"test_{gene}.py").write_text(test_py(gene, builder), encoding="utf-8")
        doc_dir = ROOT / "docs/subsystems" / subdir
        doc_dir.mkdir(parents=True, exist_ok=True)
        (doc_dir / f"{gene.upper()}.md").write_text(active_doc(gene, subdir), encoding="utf-8")
        proof_dir = ROOT / "docs/proof" / subdir
        proof_dir.mkdir(parents=True, exist_ok=True)
        (proof_dir / f"{gene.upper()}_V1_PROOF.md").write_text(
            proof_md(gene, subdir), encoding="utf-8"
        )
    print(f"[alt10-runtime] wrote {len(ORGANS)} gate/test/doc bundles")


if __name__ == "__main__":
    main()
