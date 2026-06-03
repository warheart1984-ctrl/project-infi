#!/usr/bin/env python3
"""Bootstrap Alt-12 gates, tests, active docs, and proof stubs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ORGANS = [
    ("otem_bounded_organ", "platform", "build_otem_bounded_status", "otem-bounded"),
    ("direct_challenge_organ", "platform", "build_direct_challenge_status", "direct-challenge"),
    ("orchestration_spine_organ", "platform", "build_orchestration_spine_status", "orchestration-spine"),
    ("operator_health_sentinel_organ", "platform", "build_operator_health_sentinel_organ_status", "operator-health-sentinel"),
    ("governed_realtime_lane_organ", "platform", "build_governed_realtime_lane_status", "governed-realtime-lane"),
    ("v8_runtime_organ", "platform", "build_v8_runtime_status", "v8-runtime"),
    ("patch_apply_organ", "platform", "build_patch_apply_status", "patch-apply"),
    ("patch_execution_preview_organ", "platform", "build_patch_execution_preview_status", "patch-execution-preview"),
    ("run_ledger_organ", "platform", "build_run_ledger_status", "run-ledger"),
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


def active_doc(gene: str, subdir: str, api: str) -> str:
    title = gene.replace("_", " ").title()
    gate = gene.replace("_", "-")
    proof = f"../../proof/{subdir}/{gene.upper()}_V1_PROOF.md"
    return f"""# {title}

Status: **mvp** (Alt-12 summon wave `alt12-summon-wave-2026-06`)

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
    print(f"[alt12-runtime] wrote {len(ORGANS)} gate/test/doc bundles")


if __name__ == "__main__":
    main()
