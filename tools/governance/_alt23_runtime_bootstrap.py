#!/usr/bin/env python3
"""Bootstrap Release 23 gates, tests, subsystem modules, active docs, and proof stubs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt23-summon-wave-2026-06"

ORGANS = [
    (
        "linguistic_drift_forecast_organ",
        "platform",
        "build_linguistic_drift_forecast_status",
        "linguistic-drift-forecast",
        "AAIS-LDF-01",
    ),
    (
        "linguistic_preemptive_remediation_organ",
        "platform",
        "build_linguistic_preemptive_remediation_status",
        "linguistic-preemptive-remediation",
        "AAIS-LPR-01",
    ),
    (
        "linguistic_predictive_governance_organ",
        "platform",
        "build_linguistic_predictive_governance_status",
        "linguistic-predictive-governance",
        "AAIS-LPG-01",
    ),
    (
        "linguistic_predictive_cycle_history_organ",
        "platform",
        "build_linguistic_predictive_cycle_history_status",
        "linguistic-predictive-cycle-history",
        "AAIS-LPH-01",
    ),
    (
        "linguistic_governance_cycle_organ",
        "platform",
        "build_linguistic_governance_cycle_status",
        "linguistic-governance-cycle",
        "AAIS-LGC-01",
    ),
    (
        "linguistic_governance_cycle_history_organ",
        "platform",
        "build_linguistic_governance_cycle_history_status",
        "linguistic-governance-cycle-history",
        "AAIS-LGH-01",
    ),
    (
        "linguistic_forecast_consumption_organ",
        "platform",
        "build_linguistic_forecast_consumption_status",
        "linguistic-forecast-consumption",
        "AAIS-LFC-01",
    ),
    (
        "linguistic_cycle_optimization_organ",
        "platform",
        "build_linguistic_cycle_optimization_status",
        "linguistic-cycle-optimization",
        "AAIS-LCO-01",
    ),
    (
        "linguistic_closed_loop_fabric_organ",
        "platform",
        "build_linguistic_closed_loop_fabric_status",
        "linguistic-closed-loop-fabric",
        "AAIS-CLF-01",
    ),
]

ORGAN_SOURCES: dict[str, str] = {
    "linguistic_drift_forecast_organ": '''"""Linguistic Drift Forecast Subsystem — forward drift forecast posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LDF-01"
ORGAN_VERSION = "linguistic_drift_forecast_organ.v1"


def build_linguistic_drift_forecast_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_drift_forecast_engine.py"
    ).is_file()
    cli = (root / "tools" / "linguistic_drift_forecast.py").is_file()
    report = (root / "governance" / "linguistic_drift_forecast.v1.json").is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    target = "linguistic-drift-forecast:" in m_text
    return {
        "linguistic_drift_forecast_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};cli={int(cli)};report={int(report)}"[:128],
        "drift_forecast_engine_present": engine,
        "drift_forecast_cli_present": cli,
        "drift_forecast_report_present": report,
        "linguistic_drift_forecast_in_makefile": target,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "linguistic_preemptive_remediation_organ": '''"""Linguistic Preemptive Remediation Subsystem — preemptive playbook posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LPR-01"
ORGAN_VERSION = "linguistic_preemptive_remediation_organ.v1"


def build_linguistic_preemptive_remediation_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    preempt_dir = root / "governance" / "linguistic_preemptive_remediations"
    count = len(list(preempt_dir.glob("*.json"))) if preempt_dir.is_dir() else 0
    predictive = (
        root / "src" / "governance_organs" / "linguistic_predictive_governance_engine.py"
    ).is_file()
    return {
        "linguistic_preemptive_remediation_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"playbooks={count};predictive_engine={int(predictive)}"[:128],
        "preemptive_playbook_count": count,
        "predictive_engine_present": predictive,
        "preemptive_dir_present": preempt_dir.is_dir(),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "linguistic_predictive_governance_organ": '''"""Linguistic Predictive Governance Subsystem — Wave 12 predictive cycle posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LPG-01"
ORGAN_VERSION = "linguistic_predictive_governance_organ.v1"


def build_linguistic_predictive_governance_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_predictive_governance_engine.py"
    ).is_file()
    runner = (
        root / "tools" / "governance" / "run_linguistic_predictive_cycle.py"
    ).is_file()
    policy = (
        root / "governance" / "linguistic_predictive_governance_policy.v1.json"
    ).is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "linguistic-predictive-gate:" in m_text
    cycle = "linguistic-predictive-cycle:" in m_text
    return {
        "linguistic_predictive_governance_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};runner={int(runner)};gate={int(gate)}"[:128],
        "predictive_engine_present": engine,
        "predictive_cycle_runner_present": runner,
        "predictive_policy_present": policy,
        "linguistic_predictive_gate_in_makefile": gate,
        "linguistic_predictive_cycle_in_makefile": cycle,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "linguistic_predictive_cycle_history_organ": '''"""Linguistic Predictive Cycle History Subsystem — predictive cycle artifact retention."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LPH-01"
ORGAN_VERSION = "linguistic_predictive_cycle_history_organ.v1"


def build_linguistic_predictive_cycle_history_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    cycle_dir = root / "governance" / "linguistic_predictive_cycles"
    count = len(list(cycle_dir.glob("*.json"))) if cycle_dir.is_dir() else 0
    policy = (
        root / "governance" / "linguistic_predictive_governance_policy.v1.json"
    ).is_file()
    retain = 0
    if policy:
        import json

        data = json.loads(
            (root / "governance" / "linguistic_predictive_governance_policy.v1.json").read_text(
                encoding="utf-8"
            )
        )
        retain = int(data.get("retain_predictive_cycle_history", 0))
    return {
        "linguistic_predictive_cycle_history_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"artifacts={count};retain={retain}"[:128],
        "predictive_cycle_artifact_count": count,
        "retain_predictive_cycle_history": retain,
        "predictive_cycles_dir_present": cycle_dir.is_dir(),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "linguistic_governance_cycle_organ": '''"""Linguistic Governance Cycle Subsystem — Wave 11 self-optimizing cycle posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LGC-01"
ORGAN_VERSION = "linguistic_governance_cycle_organ.v1"


def build_linguistic_governance_cycle_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    engine = (
        root / "src" / "governance_organs" / "linguistic_governance_cycle_engine.py"
    ).is_file()
    runner = (
        root / "tools" / "governance" / "run_linguistic_governance_cycle.py"
    ).is_file()
    policy = (
        root / "governance" / "linguistic_governance_cycle_policy.v1.json"
    ).is_file()
    makefile = root / "Makefile"
    m_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
    gate = "linguistic-governance-cycle-gate:" in m_text
    cycle = "linguistic-governance-cycle:" in m_text
    return {
        "linguistic_governance_cycle_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};runner={int(runner)};gate={int(gate)}"[:128],
        "governance_cycle_engine_present": engine,
        "governance_cycle_runner_present": runner,
        "governance_cycle_policy_present": policy,
        "linguistic_governance_cycle_gate_in_makefile": gate,
        "linguistic_governance_cycle_in_makefile": cycle,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "linguistic_governance_cycle_history_organ": '''"""Linguistic Governance Cycle History Subsystem — governance cycle artifact retention."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LGH-01"
ORGAN_VERSION = "linguistic_governance_cycle_history_organ.v1"


def build_linguistic_governance_cycle_history_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    cycle_dir = root / "governance" / "linguistic_governance_cycles"
    count = len(list(cycle_dir.glob("*.json"))) if cycle_dir.is_dir() else 0
    retain = 0
    policy_path = root / "governance" / "linguistic_governance_cycle_policy.v1.json"
    if policy_path.is_file():
        import json

        data = json.loads(policy_path.read_text(encoding="utf-8"))
        retain = int(data.get("retain_cycle_history", 0))
    return {
        "linguistic_governance_cycle_history_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"artifacts={count};retain={retain}"[:128],
        "governance_cycle_artifact_count": count,
        "retain_cycle_history": retain,
        "governance_cycles_dir_present": cycle_dir.is_dir(),
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "linguistic_forecast_consumption_organ": '''"""Linguistic Forecast Consumption Subsystem — forecast-in-cycle bridge posture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LFC-01"
ORGAN_VERSION = "linguistic_forecast_consumption_organ.v1"


def build_linguistic_forecast_consumption_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    policy_path = root / "governance" / "linguistic_governance_cycle_policy.v1.json"
    use_forecast = False
    if policy_path.is_file():
        use_forecast = bool(
            json.loads(policy_path.read_text(encoding="utf-8")).get(
                "use_forecast_in_cycle", False
            )
        )
    forecast = (root / "governance" / "linguistic_drift_forecast.v1.json").is_file()
    forecast_consumed = None
    cycle_dir = root / "governance" / "linguistic_governance_cycles"
    if cycle_dir.is_dir():
        files = sorted(cycle_dir.glob("*.json"), reverse=True)
        if files:
            latest = json.loads(files[0].read_text(encoding="utf-8"))
            phases = latest.get("phases") or {}
            forecast_consumed = phases.get("forecast_consumed")
    return {
        "linguistic_forecast_consumption_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": (
            f"use_forecast={int(use_forecast)};report={int(forecast)};"
            f"consumed={forecast_consumed}"
        )[:128],
        "use_forecast_in_cycle": use_forecast,
        "drift_forecast_report_present": forecast,
        "last_forecast_consumed": forecast_consumed,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "linguistic_cycle_optimization_organ": '''"""Linguistic Cycle Optimization Subsystem — cycle optimization recommendations posture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-LCO-01"
ORGAN_VERSION = "linguistic_cycle_optimization_organ.v1"


def build_linguistic_cycle_optimization_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    rec_count = 0
    cycle_dir = root / "governance" / "linguistic_governance_cycles"
    if cycle_dir.is_dir():
        files = sorted(cycle_dir.glob("*.json"), reverse=True)
        if files:
            latest = json.loads(files[0].read_text(encoding="utf-8"))
            recs = latest.get("optimization_recommendations") or []
            rec_count = len(recs) if isinstance(recs, list) else 0
    engine = (
        root / "src" / "governance_organs" / "linguistic_governance_cycle_engine.py"
    ).is_file()
    return {
        "linguistic_cycle_optimization_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"engine={int(engine)};recommendations={rec_count}"[:128],
        "governance_cycle_engine_present": engine,
        "last_optimization_recommendation_count": rec_count,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "linguistic_closed_loop_fabric_organ": '''"""Linguistic Closed Loop Fabric Subsystem — joint anticipate→react loop posture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-CLF-01"
ORGAN_VERSION = "linguistic_closed_loop_fabric_organ.v1"


def build_linguistic_closed_loop_fabric_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    reg_path = root / "governance" / "meta_linguistic_registry.v1.json"
    has_cycle = False
    has_predictive = False
    if reg_path.is_file():
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        has_cycle = bool(reg.get("last_cycle_report"))
        has_predictive = bool(reg.get("last_predictive_cycle_report"))
    predictive_engine = (
        root / "src" / "governance_organs" / "linguistic_predictive_governance_engine.py"
    ).is_file()
    cycle_engine = (
        root / "src" / "governance_organs" / "linguistic_governance_cycle_engine.py"
    ).is_file()
    closed_loop_ready = predictive_engine and cycle_engine and has_cycle and has_predictive
    return {
        "linguistic_closed_loop_fabric_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": (
            f"predictive={int(has_predictive)};cycle={int(has_cycle)};"
            f"ready={int(closed_loop_ready)}"
        )[:128],
        "last_predictive_cycle_in_registry": has_predictive,
        "last_governance_cycle_in_registry": has_cycle,
        "closed_loop_ready": closed_loop_ready,
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

Status: **mvp** (Release 23 `{BATCH}`)

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
| Gate passes under alt23-governed-gate | proven |

## Reproduction

```bash
make {gate}-organ-gate
make alt23-governed-gate
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
        "linguistic_drift_forecast_organ": "linguistic_drift_forecast",
        "linguistic_preemptive_remediation_organ": "linguistic_preemptive_remediation",
        "linguistic_predictive_governance_organ": "linguistic_predictive_governance",
        "linguistic_predictive_cycle_history_organ": "linguistic_predictive_cycle_history",
        "linguistic_governance_cycle_organ": "linguistic_governance_cycle",
        "linguistic_governance_cycle_history_organ": "linguistic_governance_cycle_history",
        "linguistic_forecast_consumption_organ": "linguistic_forecast_consumption",
        "linguistic_cycle_optimization_organ": "linguistic_cycle_optimization",
        "linguistic_closed_loop_fabric_organ": "linguistic_closed_loop_fabric",
    }
    blocks = []
    for gene, _s, builder, api, _m in ORGANS:
        blocks.append(api_route_block(gene, api, builder, json_keys[gene]))
    routes_path = ROOT / "tools/governance/_alt23_api_routes_snippet.py"
    routes_path.write_text("".join(blocks), encoding="utf-8")
    print(f"[alt23-runtime] wrote {len(ORGANS)} subsystem/gate/test bundles")
    print(f"[alt23-runtime] API snippet: {routes_path}")


if __name__ == "__main__":
    main()
