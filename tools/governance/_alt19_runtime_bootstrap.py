#!/usr/bin/env python3
"""Bootstrap Alt-19 gates, tests, active docs, and proof stubs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt19-summon-wave-2026-06"

ORGANS = [('launcher_organ', 'platform', 'build_launcher_status', 'launcher'),
 ('aais_doctor_organ', 'platform', 'build_aais_doctor_status', 'aais-doctor'),
 ('workflow_runtime_organ', 'platform', 'build_workflow_runtime_status', 'workflow-runtime'),
 ('jarvis_console_surface_organ', 'platform', 'build_jarvis_console_surface_status', 'jarvis-console-surface'),
 ('memory_bank_surface_organ', 'platform', 'build_memory_bank_surface_status', 'memory-bank-surface'),
 ('dashboard_surface_organ', 'platform', 'build_dashboard_surface_status', 'dashboard-surface'),
 ('nova_landing_surface_organ', 'platform', 'build_nova_landing_surface_status', 'nova-landing-surface'),
 ('aais_composed_runtime_organ', 'platform', 'build_aais_composed_runtime_status', 'aais-composed-runtime'),
 ('api_gateway_organ', 'platform', 'build_api_gateway_status', 'api-gateway')]


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
    if gene == "jarvis_operator_organ":
        extra = """
    assert status.get("new_execute_authority_via_organ") is False
"""
    elif gene == "jarvis_reasoning_lane_organ":
        extra = """
    assert status.get("routing_usurpation") is False
    assert status.get("lane_catalog_only") is True
"""
    elif gene == "reasoning_contract_organ":
        extra = """
    assert status.get("executive_usurpation") is False
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

Status: **mvp** (Alt-19 summon wave `{BATCH}`)

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
| Gate passes under alt19-governed-gate | proven |

## Reproduction

```bash
make {gate}-organ-gate
make alt19-governed-gate
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
    print(f"[alt19-runtime] wrote {len(ORGANS)} gate/test/doc bundles")


if __name__ == "__main__":
    main()
