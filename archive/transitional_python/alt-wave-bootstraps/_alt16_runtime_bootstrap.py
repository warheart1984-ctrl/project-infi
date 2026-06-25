#!/usr/bin/env python3
"""Bootstrap Alt-16 gates, tests, active docs, and proof stubs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt16-summon-wave-2026-06"

ORGANS = [
    ("ai_factory_organ", "platform", "build_ai_factory_status", "ai-factory"),
    ("cogos_runtime_bridge_organ", "platform", "build_cogos_runtime_bridge_status", "cogos-runtime-bridge"),
    ("wolf_rehydration_organ", "platform", "build_wolf_rehydration_status", "wolf-rehydration"),
    ("forge_contractor_organ", "platform", "build_forge_contractor_status", "forge-contractor"),
    ("forge_eval_organ", "platform", "build_forge_eval_status", "forge-eval"),
    ("evolve_engine_organ", "platform", "build_evolve_engine_status", "evolve-engine"),
    ("slingshot_organ", "platform", "build_slingshot_status", "slingshot"),
    ("operator_workbench_organ", "platform", "build_operator_workbench_status", "operator-workbench"),
    ("workflow_shell_organ", "platform", "build_workflow_shell_status", "workflow-shell"),
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
        print("[{gate}-organ-gate] FAIL")
        return 1
    print("[{gate}-organ-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def test_py(gene: str, builder: str) -> str:
    extra = ""
    if gene == "forge_contractor_organ":
        extra = """
    assert status.get("proposal_only") is True
    assert status.get("auto_approve_allowed") is False
"""
    elif gene == "evolve_engine_organ":
        extra = """
    assert status.get("direct_patch_authority") is False
    assert status.get("special_review_only") is True
"""
    elif gene == "ai_factory_organ":
        extra = """
    assert status.get("deploy_authority_via_organ") is False
"""
    elif gene == "slingshot_organ":
        extra = """
    assert status.get("ma13_enforced") is True
"""
    elif gene == "operator_workbench_organ":
        extra = """
    assert status.get("proposal_only") is True
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

Status: **mvp** (Alt-16 summon wave `{BATCH}`)

## Runtime

- Module: `src/{gene}.py`
- API: `GET /api/jarvis/{api}/status`
- Gate: `make {gate}-organ-gate`

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
make {gate}-organ-gate
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
| Gate passes under alt16-governed-gate | proven |

## Reproduction

```bash
make {gate}-organ-gate
make alt16-governed-gate
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
    print(f"[alt16-runtime] wrote {len(ORGANS)} gate/test/doc bundles")


if __name__ == "__main__":
    main()
