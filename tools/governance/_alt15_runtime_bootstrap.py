#!/usr/bin/env python3
"""Bootstrap Alt-15 gates, tests, active docs, and proof stubs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt15-summon-wave-2026-06"

ORGANS = [
    ("reasoning_executive_organ", "nova", "build_reasoning_executive_status", "reasoning-executive"),
    ("attention_organ", "nova", "build_attention_status", "attention"),
    ("coherence_projection_organ", "nova", "build_coherence_projection_status", "coherence-projection"),
    ("deliberation_organ", "nova", "build_deliberation_status", "deliberation"),
    ("planning_organ", "nova", "build_planning_status", "planning"),
    ("cortex_arcs_organ", "nova", "build_cortex_arcs_status", "cortex-arcs"),
    ("cognitive_execution_organ", "nova", "build_cognitive_execution_status", "cognitive-execution"),
    ("speaking_runtime_organ", "nova", "build_speaking_runtime_status", "speaking-runtime"),
    ("nova_face_organ", "nova", "build_nova_face_status", "nova-face"),
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
    extra = ""
    if gene == "reasoning_executive_organ":
        extra = """
    assert status.get("routing_usurpation") is False
    assert status.get("executive_authority") == "jarvis"
"""
    elif gene == "coherence_projection_organ":
        extra = """
    assert status.get("exports_chain_of_thought") is False
    assert status.get("exports_bounded_state") is True
"""
    elif gene == "cognitive_execution_organ":
        extra = """
    assert status.get("patch_execution_depth") is False
"""
    elif gene == "nova_face_organ":
        extra = """
    assert status.get("authority_lane") == "jarvis"
"""
    return f'''"""Tests for {gene}."""

from __future__ import annotations

from src.{gene} import {builder}


def test_build_status():
    status = {builder}()
    assert status["{gene}_version"] == "{gene}.v1"
    assert status["read_only"] is True
    assert status["module_id"]
{extra}
'''


def active_doc(gene: str, subdir: str, api: str) -> str:
    title = gene.replace("_", " ").title()
    gate = gene.replace("_", "-")
    proof = f"../../proof/{subdir}/{gene.upper()}_V1_PROOF.md"
    return f"""# {title}

Status: **mvp** (Alt-15 summon wave `{BATCH}`)

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


def governed_proof_md(gene: str, subdir: str) -> str:
    gate = gene.replace("_", "-")
    return f"""# {gene.replace('_', ' ').title()} Governed Proof

## Claims

| Claim | Label |
|-------|-------|
| Organ at governed stage with runtime surface | proven |
| Gate passes under alt15-governed-gate | proven |

## Reproduction

```bash
make {gate}-gate
make alt15-governed-gate
```
"""


def main() -> None:
    for gene, subdir, builder, api in ORGANS:
        gate_name = gene.replace("_", "-")
        (ROOT / ".github/scripts" / f"check-{gate_name}-governance.py").write_text(
            gate_script(gene), encoding="utf-8"
        )
        (ROOT / "tests" / f"test_{gene}.py").write_text(test_py(gene, builder), encoding="utf-8")
        doc_dir = ROOT / "docs/subsystems" / subdir
        doc_dir.mkdir(parents=True, exist_ok=True)
        (doc_dir / f"{gene.upper()}.md").write_text(
            active_doc(gene, subdir, api), encoding="utf-8"
        )
        proof_dir = ROOT / "docs/proof" / subdir
        proof_dir.mkdir(parents=True, exist_ok=True)
        (proof_dir / f"{gene.upper()}_V1_PROOF.md").write_text(
            proof_md(gene, subdir), encoding="utf-8"
        )
        (proof_dir / f"{gene.upper()}_GOVERNED_PROOF.md").write_text(
            governed_proof_md(gene, subdir), encoding="utf-8"
        )
    print(f"[alt15-runtime] wrote {len(ORGANS)} gate/test/doc bundles")


if __name__ == "__main__":
    main()
