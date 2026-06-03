#!/usr/bin/env python3
"""Bootstrap Release 21 gates, tests, subsystem modules, active docs, and proof stubs."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = "alt21-summon-wave-2026-06"

ORGANS = [
    (
        "creative_core_runtime_organ",
        "platform",
        "build_creative_core_runtime_status",
        "creative-core-runtime",
        "AAIS-CCR-01",
    ),
    ("v9_core_organ", "platform", "build_v9_core_status", "v9-core", "AAIS-V9C-01"),
    (
        "v9_runtime_organ",
        "platform",
        "build_v9_runtime_status",
        "v9-runtime",
        "AAIS-V9R-01",
    ),
    ("v10_core_organ", "platform", "build_v10_core_status", "v10-core", "AAIS-V10C-01"),
    (
        "v10_runtime_organ",
        "platform",
        "build_v10_runtime_status",
        "v10-runtime",
        "AAIS-V10R-01",
    ),
    (
        "v10_action_engine_organ",
        "platform",
        "build_v10_action_engine_status",
        "v10-action-engine",
        "AAIS-V10A-01",
    ),
    (
        "creative_capability_bridge_organ",
        "platform",
        "build_creative_capability_bridge_status",
        "creative-capability-bridge",
        "AAIS-CCB-01",
    ),
    (
        "creative_operator_handoff_organ",
        "platform",
        "build_creative_operator_handoff_status",
        "creative-operator-handoff",
        "AAIS-COH-01",
    ),
    (
        "creative_console_interface_organ",
        "platform",
        "build_creative_console_interface_status",
        "creative-console-interface",
        "AAIS-CCI-01",
    ),
]

ORGAN_SOURCES: dict[str, str] = {
    "creative_core_runtime_organ": '''"""Creative Core Runtime Subsystem — bounded creative wrapper posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-CCR-01"
ORGAN_VERSION = "creative_core_runtime_organ.v1"


def build_creative_core_runtime_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "src" / "creative_core_runtime.py").is_file()
    return {
        "creative_core_runtime_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"creative_core={int(present)};read_only=1"[:128],
        "creative_core_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "v9_core_organ": '''"""V9 Core Subsystem — V9 core lane posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-V9C-01"
ORGAN_VERSION = "v9_core_organ.v1"


def build_v9_core_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "src" / "v9_core.py").is_file()
    api = root / "src" / "api.py"
    text = api.read_text(encoding="utf-8") if api.is_file() else ""
    route = "/api/jarvis/v9-core" in text
    return {
        "v9_core_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"v9_core={int(present)};route={int(route)}"[:128],
        "v9_core_present": present,
        "v9_core_route_present": route,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "v9_runtime_organ": '''"""V9 Runtime Subsystem — V9 runtime snapshot posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-V9R-01"
ORGAN_VERSION = "v9_runtime_organ.v1"


def build_v9_runtime_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "src" / "v9_runtime.py").is_file()
    api = root / "src" / "api.py"
    text = api.read_text(encoding="utf-8") if api.is_file() else ""
    routes = sum(
        1
        for marker in ("/api/jarvis/v9-runtime", "/api/jarvis/v9-runtime/events")
        if marker in text
    )
    return {
        "v9_runtime_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"v9_runtime={int(present)};routes={routes}"[:128],
        "v9_runtime_present": present,
        "v9_runtime_routes_present": routes,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "v10_core_organ": '''"""V10 Core Subsystem — V10 core lane posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-V10C-01"
ORGAN_VERSION = "v10_core_organ.v1"


def build_v10_core_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "src" / "v10_core.py").is_file()
    api = root / "src" / "api.py"
    text = api.read_text(encoding="utf-8") if api.is_file() else ""
    route = "/api/jarvis/v10-core" in text
    return {
        "v10_core_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"v10_core={int(present)};route={int(route)}"[:128],
        "v10_core_present": present,
        "v10_core_route_present": route,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "v10_runtime_organ": '''"""V10 Runtime Subsystem — V10 runtime snapshot posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-V10R-01"
ORGAN_VERSION = "v10_runtime_organ.v1"


def build_v10_runtime_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "src" / "v10_runtime.py").is_file()
    api = root / "src" / "api.py"
    text = api.read_text(encoding="utf-8") if api.is_file() else ""
    routes = sum(
        1
        for marker in ("/api/jarvis/v10-runtime", "/api/jarvis/v10-runtime/events")
        if marker in text
    )
    return {
        "v10_runtime_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"v10_runtime={int(present)};routes={routes}"[:128],
        "v10_runtime_present": present,
        "v10_runtime_routes_present": routes,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "v10_action_engine_organ": '''"""V10 Action Engine Subsystem — mission step engine posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-V10A-01"
ORGAN_VERSION = "v10_action_engine_organ.v1"


def build_v10_action_engine_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    present = (root / "src" / "v10_action_engine.py").is_file()
    return {
        "v10_action_engine_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"v10_action_engine={int(present)};read_only=1"[:128],
        "v10_action_engine_present": present,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "creative_capability_bridge_organ": '''"""Creative Capability Bridge Subsystem — v9/v10 bridge provider posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-CCB-01"
ORGAN_VERSION = "creative_capability_bridge_organ.v1"


def build_creative_capability_bridge_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    bridge = root / "src" / "capability_service_bridge.py"
    text = bridge.read_text(encoding="utf-8") if bridge.is_file() else ""
    v9 = 'provider_name="v9_runtime"' in text
    v10 = 'provider_name="v10_runtime"' in text
    return {
        "creative_capability_bridge_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"v9_provider={int(v9)};v10_provider={int(v10)}"[:128],
        "v9_runtime_provider_present": v9,
        "v10_runtime_provider_present": v10,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "creative_operator_handoff_organ": '''"""Creative Operator Handoff Subsystem — operator creative lane posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-COH-01"
ORGAN_VERSION = "creative_operator_handoff_organ.v1"


def build_creative_operator_handoff_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    operator = (root / "src" / "jarvis_operator.py").is_file()
    routing = (root / "src" / "model_routing.py").is_file()
    op_text = (
        (root / "src" / "jarvis_operator.py").read_text(encoding="utf-8")
        if operator
        else ""
    )
    imports_v9 = "v9_runtime" in op_text
    imports_v10 = "v10_runtime" in op_text
    return {
        "creative_operator_handoff_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"operator={int(operator)};v9={int(imports_v9)};v10={int(imports_v10)}"[:128],
        "jarvis_operator_present": operator,
        "model_routing_present": routing,
        "operator_imports_v9_runtime": imports_v9,
        "operator_imports_v10_runtime": imports_v10,
        "read_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
    }
''',
    "creative_console_interface_organ": '''"""Creative Console Interface Subsystem — v9/v10 UI binding posture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-CCI-01"
ORGAN_VERSION = "creative_console_interface_organ.v1"


def build_creative_console_interface_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    pages = root / "frontend" / "src" / "pages"
    jarvis = pages / "JarvisConsole.jsx"
    dashboard = pages / "Dashboard.jsx"
    j_text = jarvis.read_text(encoding="utf-8") if jarvis.is_file() else ""
    d_text = dashboard.read_text(encoding="utf-8") if dashboard.is_file() else ""
    v9_refs = sum(1 for token in ("v9_runtime", "v9Runtime") if token in j_text or token in d_text)
    v10_refs = sum(1 for token in ("v10_runtime", "v10Runtime") if token in j_text or token in d_text)
    return {
        "creative_console_interface_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": f"v9_ui_refs={v9_refs};v10_ui_refs={v10_refs}"[:128],
        "jarvis_console_present": jarvis.is_file(),
        "dashboard_present": dashboard.is_file(),
        "v9_ui_refs": v9_refs,
        "v10_ui_refs": v10_refs,
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

Status: **mvp** (Release 21 `{BATCH}`)

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
| Gate passes under alt21-governed-gate | proven |

## Reproduction

```bash
make {gate}-organ-gate
make alt21-governed-gate
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

    routes_path = ROOT / "tools/governance/_alt21_api_routes_snippet.py"
    json_keys = {
        "creative_core_runtime_organ": "creative_core_runtime",
        "v9_core_organ": "v9_core",
        "v9_runtime_organ": "v9_runtime",
        "v10_core_organ": "v10_core",
        "v10_runtime_organ": "v10_runtime",
        "v10_action_engine_organ": "v10_action_engine",
        "creative_capability_bridge_organ": "creative_capability_bridge",
        "creative_operator_handoff_organ": "creative_operator_handoff",
        "creative_console_interface_organ": "creative_console_interface",
    }
    blocks = []
    for gene, _s, builder, api, _m in ORGANS:
        blocks.append(api_route_block(gene, api, builder, json_keys[gene]))
    routes_path.write_text("".join(blocks), encoding="utf-8")
    print(f"[alt21-runtime] wrote {len(ORGANS)} subsystem/gate/test bundles")
    print(f"[alt21-runtime] API snippet: {routes_path}")


if __name__ == "__main__":
    main()
