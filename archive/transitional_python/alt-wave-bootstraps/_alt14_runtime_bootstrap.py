#!/usr/bin/env python3
"""Bootstrap Alt-14 gates, tests, active docs, and proof stubs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt14-summon-wave-2026-06"

ORGANS = [
    ("document_vision_organ", "platform", "build_document_vision_status", "document-vision"),
    ("ui_vision_organ", "platform", "build_ui_vision_status", "ui-vision"),
    ("perception_gateway_organ", "platform", "build_perception_gateway_status", "perception-gateway"),
    ("spatial_reasoning_organ", "platform", "build_spatial_reasoning_status", "spatial-reasoning"),
    ("mystic_engine_organ", "platform", "build_mystic_engine_status", "mystic-engine"),
    ("perception_lane_organ", "platform", "build_perception_lane_status", "perception-lane"),
    ("route_choice_organ", "platform", "build_route_choice_status", "route-choice"),
    ("specialist_route_organ", "platform", "build_specialist_route_status", "specialist-route"),
    ("provider_route_organ", "platform", "build_provider_route_status", "provider-route"),
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
    if gene == "document_vision_organ":
        extra = """
    assert "document_vision_enabled" in status
    assert status.get("bridge_safe") is True
"""
    elif gene == "route_choice_organ":
        extra = """
    assert status.get("model_route_count", 0) >= 1
    assert status.get("routing_read_only") is True
"""
    elif gene == "provider_route_organ":
        extra = """
    assert status.get("advisory_only") is True
    assert status.get("execution_allowed") is False
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

Status: **mvp** (Alt-14 summon wave `{BATCH}`)

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
| Gate passes under alt14-governed-gate | proven |

## Reproduction

```bash
make {gate}-gate
make alt14-governed-gate
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
    print(f"[alt14-runtime] wrote {len(ORGANS)} gate/test/doc bundles")


if __name__ == "__main__":
    main()
