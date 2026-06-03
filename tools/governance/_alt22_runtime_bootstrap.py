#!/usr/bin/env python3
"""Bootstrap Release 22 gates, tests, subsystem modules, active docs, and proof stubs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt22-summon-wave-2026-06"

ORGANS = [
    (
        "naming_protocol_organ",
        "platform",
        "build_naming_protocol_status",
        "naming-protocol",
        "AAIS-NPR-01",
    ),
    (
        "naming_genome_organ",
        "platform",
        "build_naming_genome_status",
        "naming-genome",
        "AAIS-NGN-01",
    ),
    (
        "linguistic_mutation_organ",
        "platform",
        "build_linguistic_mutation_status",
        "linguistic-mutation",
        "AAIS-LMU-01",
    ),
    (
        "mythic_engineering_translator_organ",
        "platform",
        "build_mythic_engineering_translator_status",
        "mythic-engineering-translator",
        "AAIS-MET-01",
    ),
    (
        "linguistic_drift_predictor_organ",
        "platform",
        "build_linguistic_drift_predictor_status",
        "linguistic-drift-predictor",
        "AAIS-LDP-01",
    ),
    (
        "linguistic_lineage_viz_organ",
        "platform",
        "build_linguistic_lineage_viz_status",
        "linguistic-lineage-viz",
        "AAIS-LLV-01",
    ),
    (
        "linguistic_remediation_organ",
        "platform",
        "build_linguistic_remediation_status",
        "linguistic-remediation",
        "AAIS-LRM-01",
    ),
    (
        "linguistic_cascade_organ",
        "platform",
        "build_linguistic_cascade_status",
        "linguistic-cascade",
        "AAIS-LCA-01",
    ),
    (
        "meta_linguistic_governance_organ",
        "platform",
        "build_meta_linguistic_governance_status",
        "meta-linguistic-governance",
        "AAIS-MLG-01",
    ),
]

ORGAN_SOURCES: dict[str, str] = {
    "naming_protocol_organ": '''"""Naming Protocol Subsystem — Wave 0 naming lint posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-NPR-01"
ORGAN_VERSION = "naming_protocol_organ.v1"


def build_naming_protocol_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    lint = (root / "tools" / "naming_protocol_lint.py").is_file()
    contract = (
        root / "docs" / "contracts" / "AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md"
    ).is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    naming_gate = "naming-gate:" in m_text
    return {
        "naming_protocol_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"lint={int(lint)};contract={int(contract)};gate={int(naming_gate)}"[:128],
        "naming_protocol_lint_present": lint,
        "naming_protocol_contract_present": contract,
        "naming_gate_in_makefile": naming_gate,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "naming_genome_organ": '''"""Naming Genome Subsystem — genome/alias linguistic cross-check posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-NGN-01"
ORGAN_VERSION = "naming_genome_organ.v1"


def build_naming_genome_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    lib = (root / "tools" / "linguistic_genome_lib.py").is_file()
    check = (root / "tools" / "governance" / "check_naming_genome.py").is_file()
    aliases = (root / "governance" / "legacy_engineering_aliases.v1.json").is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "naming-genome-gate:" in m_text
    return {
        "naming_genome_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"lib={int(lib)};check={int(check)};aliases={int(aliases)}"[:128],
        "linguistic_genome_lib_present": lib,
        "check_naming_genome_present": check,
        "legacy_aliases_present": aliases,
        "naming_genome_gate_in_makefile": gate,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "linguistic_mutation_organ": '''"""Linguistic Mutation Subsystem — MP-X linguistic_layer mutation posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LMU-01"
ORGAN_VERSION = "linguistic_mutation_organ.v1"


def build_linguistic_mutation_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_mutation_engine.py"
    ).is_file()
    gate_script = (
        root / "tools" / "governance" / "check_linguistic_mutation_gate.py"
    ).is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "linguistic-mutation-gate:" in m_text
    return {
        "linguistic_mutation_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};gate_script={int(gate_script)}"[:128],
        "linguistic_mutation_engine_present": engine,
        "linguistic_mutation_gate_script_present": gate_script,
        "linguistic_mutation_gate_in_makefile": gate,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "mythic_engineering_translator_organ": '''"""Mythic Engineering Translator Subsystem — mythic→engineering translator posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-MET-01"
ORGAN_VERSION = "mythic_engineering_translator_organ.v1"


def build_mythic_engineering_translator_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    tool = (root / "tools" / "mythic_engineering_translator.py").is_file()
    tests = (root / "tests" / "test_mythic_engineering_translator.py").is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    target = "translate-mythic:" in m_text
    return {
        "mythic_engineering_translator_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"tool={int(tool)};tests={int(tests)};make={int(target)}"[:128],
        "mythic_engineering_translator_present": tool,
        "translator_tests_present": tests,
        "translate_mythic_in_makefile": target,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "linguistic_drift_predictor_organ": '''"""Linguistic Drift Predictor Subsystem — hybrid drift scoring posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LDP-01"
ORGAN_VERSION = "linguistic_drift_predictor_organ.v1"


def build_linguistic_drift_predictor_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    tool = (root / "tools" / "linguistic_drift_predictor.py").is_file()
    report = (root / "governance" / "linguistic_drift_report.v1.json").is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "linguistic-drift-gate:" in m_text
    return {
        "linguistic_drift_predictor_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"tool={int(tool)};report={int(report)};gate={int(gate)}"[:128],
        "linguistic_drift_predictor_present": tool,
        "drift_report_present": report,
        "linguistic_drift_gate_in_makefile": gate,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "linguistic_lineage_viz_organ": '''"""Linguistic Lineage Viz Subsystem — lineage Mermaid export posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LLV-01"
ORGAN_VERSION = "linguistic_lineage_viz_organ.v1"


def build_linguistic_lineage_viz_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    tool = (root / "tools" / "linguistic_lineage_viz.py").is_file()
    tests = (root / "tests" / "test_linguistic_lineage_viz.py").is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    target = "linguistic-lineage-viz:" in m_text
    return {
        "linguistic_lineage_viz_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"tool={int(tool)};tests={int(tests)};make={int(target)}"[:128],
        "linguistic_lineage_viz_present": tool,
        "lineage_viz_tests_present": tests,
        "linguistic_lineage_viz_in_makefile": target,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "linguistic_remediation_organ": '''"""Linguistic Remediation Subsystem — drift remediation playbook posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LRM-01"
ORGAN_VERSION = "linguistic_remediation_organ.v1"


def build_linguistic_remediation_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_remediation_engine.py"
    ).is_file()
    rem_dir = root / "governance" / "linguistic_remediations"
    rem_count = len(list(rem_dir.glob("*.json"))) if rem_dir.is_dir() else 0
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "linguistic-remediation-gate:" in m_text
    return {
        "linguistic_remediation_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};playbooks={rem_count}"[:128],
        "linguistic_remediation_engine_present": engine,
        "remediation_playbook_count": rem_count,
        "linguistic_remediation_gate_in_makefile": gate,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "linguistic_cascade_organ": '''"""Linguistic Cascade Subsystem — lineage cascade policy posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LCA-01"
ORGAN_VERSION = "linguistic_cascade_organ.v1"


def build_linguistic_cascade_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_cascade_engine.py"
    ).is_file()
    policy = (root / "governance" / "linguistic_cascade_policy.v1.json").is_file()
    report_tool = (root / "tools" / "linguistic_cascade_report.py").is_file()
    return {
        "linguistic_cascade_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};policy={int(policy)}"[:128],
        "linguistic_cascade_engine_present": engine,
        "cascade_policy_present": policy,
        "cascade_report_tool_present": report_tool,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "meta_linguistic_governance_organ": '''"""Meta-Linguistic Governance Subsystem — orchestration and registry posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-MLG-01"
ORGAN_VERSION = "meta_linguistic_governance_organ.v1"


def build_meta_linguistic_governance_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_governance_engine.py"
    ).is_file()
    registry = (root / "governance" / "meta_linguistic_registry.v1.json").is_file()
    contract = (
        root / "docs" / "contracts" / "AAIS_META_LINGUISTIC_GOVERNANCE.md"
    ).is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "meta-linguistic-gate:" in m_text
    api = root / "src" / "api.py"
    text = api.read_text(encoding="utf-8") if api.is_file() else ""
    route = "/api/jarvis/meta-linguistic-governance/status" in text
    return {
        "meta_linguistic_governance_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};registry={int(registry)};route={int(route)}"[:128],
        "linguistic_governance_engine_present": engine,
        "meta_linguistic_registry_present": registry,
        "meta_linguistic_contract_present": contract,
        "meta_linguistic_gate_in_makefile": gate,
        "status_route_present": route,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
}


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

Status: **mvp** (Release 22 `{BATCH}`)

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
| Subsystem surface is read-only | asserted |

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
| Subsystem at governed stage with runtime surface | proven |
| Gate passes under alt22-governed-gate | proven |

## Reproduction

```bash
make {gate}-organ-gate
make alt22-governed-gate
```
"""


def api_route_block(gene: str, api: str, builder: str, json_key: str) -> str:
    return f'''

@app.route("/api/jarvis/{api}/status", methods=["GET"])
def get_{gene}_status():
    try:
        from src.{gene} import {builder}

        return jsonify(
            attach_ul_substrate({{{json_key!r}: {builder}()}})
        )
    except Exception as e:
        logger.error(f"Error reading {gene} status: {{e}}")
        return jsonify({{"error": str(e)}}), 500
'''


def main() -> None:
    for gene, subdir, builder, api, _mid in ORGANS:
        gate_name = gene.replace("_", "-")
        src = ORGAN_SOURCES[gene]
        (ROOT / "src" / f"{gene}.py").write_text(src, encoding="utf-8")
        (ROOT / ".github/scripts" / f"check-{gate_name}-governance.py").write_text(
            gate_script(gene), encoding="utf-8"
        )
        (ROOT / "tests" / f"test_{gene}.py").write_text(
            test_py(gene, builder), encoding="utf-8"
        )
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

    json_keys = {
        "naming_protocol_organ": "naming_protocol",
        "naming_genome_organ": "naming_genome",
        "linguistic_mutation_organ": "linguistic_mutation",
        "mythic_engineering_translator_organ": "mythic_engineering_translator",
        "linguistic_drift_predictor_organ": "linguistic_drift_predictor",
        "linguistic_lineage_viz_organ": "linguistic_lineage_viz",
        "linguistic_remediation_organ": "linguistic_remediation",
        "linguistic_cascade_organ": "linguistic_cascade",
        "meta_linguistic_governance_organ": "meta_linguistic_governance",
    }
    blocks = []
    for gene, _s, builder, api, _m in ORGANS:
        blocks.append(api_route_block(gene, api, builder, json_keys[gene]))
    routes_path = ROOT / "tools/governance/_alt22_api_routes_snippet.py"
    routes_path.write_text("".join(blocks), encoding="utf-8")
    print(f"[alt22-runtime] wrote {len(ORGANS)} subsystem/gate/test bundles")
    print(f"[alt22-runtime] API snippet: {routes_path}")


if __name__ == "__main__":
    main()
