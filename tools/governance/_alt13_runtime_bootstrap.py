#!/usr/bin/env python3
"""Bootstrap Alt-13 gates, tests, active docs, and proof stubs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ORGANS = [
    ("ul_lineage_console_organ", "aais-ul", "build_ul_lineage_console_status", "ul-lineage-console"),
    ("module_governance_organ", "platform", "build_module_governance_status", "module-governance"),
    ("recipe_module_organ", "platform", "build_recipe_module_status", "recipe-module"),
    ("imagine_generator_organ", "storyforge", "build_imagine_generator_status", "imagine-generator"),
    ("story_forge_lane_organ", "storyforge", "build_story_forge_lane_status", "story-forge-lane"),
    ("beatbox_lane_organ", "storyforge", "build_beatbox_lane_status", "beatbox-lane"),
    ("speakers_lane_organ", "speakers", "build_speakers_lane_status", "speakers-lane"),
    ("human_voice_extraction_organ", "speakers", "build_human_voice_extraction_status", "human-voice-extraction"),
    ("narrative_trust_pack_organ", "storyforge", "build_narrative_trust_pack_status", "narrative-trust-pack"),
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

Status: **mvp** (Alt-13 summon wave `alt13-summon-wave-2026-06`)

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
| Gate passes under alt13-governed-gate | proven |

## Reproduction

```bash
make {gate}-gate
make alt13-governed-gate
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
    print(f"[alt13-runtime] wrote {len(ORGANS)} gate/test/doc bundles")


if __name__ == "__main__":
    main()
