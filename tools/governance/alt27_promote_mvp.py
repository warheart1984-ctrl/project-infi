#!/usr/bin/env python3
"""Stamp Release 27 batch; promote subsystems to MVP when not yet governed."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

BATCH = "alt27-summon-wave-2026-06"

ALT27_SPECS: dict[str, dict] = {
    "cisiv_operator_lineage_console": {
        "active_doc": "docs/runtime/UL_LINEAGE_CONSOLE.md",
        "prototype_proof": "docs/proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md",
        "v1_proof": "docs/proof/aais-ul/UL_LINEAGE_CONSOLE_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/ul_lineage.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/ul_lineage.py"},
            {"kind": "module", "path": "src/ul_lineage_console_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/ul-lineage-console/status"},
            {"kind": "gate", "path": "make lineage-gate"},
        ],
    },
    "forensic_triangulation": {
        "active_doc": "docs/subsystems/forensics/TRIANGULATION.md",
        "prototype_proof": "docs/proof/forensics/TRIANGULATION_V1_PROOF.md",
        "v1_proof": "docs/proof/forensics/TRIANGULATION_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/forensic_triangulation_organ.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/forensic_triangulation_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/forensic-triangulation/status"},
            {"kind": "gate", "path": "make triangulation-gate"},
        ],
    },
    "capability_service_bridge": {
        "active_doc": "docs/subsystems/platform/CAPABILITY_SERVICE_BRIDGE.md",
        "prototype_proof": "docs/proof/platform/CAPABILITY_SERVICE_BRIDGE_V1_PROOF.md",
        "v1_proof": "docs/proof/platform/CAPABILITY_SERVICE_BRIDGE_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/capability_service_bridge.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/capability_service_bridge.py"},
            {"kind": "api", "path": "GET /api/jarvis/capability-bridge/status"},
            {"kind": "gate", "path": "make capability-bridge-gate"},
        ],
    },
    "jarvis_memory_board": {
        "active_doc": "docs/subsystems/platform/JARVIS_MEMORY_BOARD.md",
        "prototype_proof": "docs/proof/platform/JARVIS_MEMORY_BOARD_V1_PROOF.md",
        "v1_proof": "docs/proof/platform/JARVIS_MEMORY_BOARD_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/jarvis_memory_board.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/jarvis_memory_board.py"},
            {"kind": "api", "path": "GET /api/jarvis/memory/board"},
            {"kind": "gate", "path": "make memory-board-gate"},
        ],
    },
    "governed_direct_pipeline": {
        "active_doc": "docs/runtime/GOVERNED_DIRECT_PIPELINE.md",
        "prototype_proof": "docs/proof/platform/GOVERNED_DIRECT_PIPELINE_V1_PROOF.md",
        "v1_proof": "docs/proof/platform/GOVERNED_DIRECT_PIPELINE_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/governed_direct_pipeline.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/governed_direct_pipeline.py"},
            {"kind": "api", "path": "GET /api/jarvis/pipeline/{turn_id}"},
            {"kind": "gate", "path": "make governed-pipeline-gate"},
        ],
    },
    "recipe_module": {
        "active_doc": "docs/subsystems/platform/RECIPE_MODULE.md",
        "prototype_proof": "docs/proof/platform/RECIPE_MODULE_V1_PROOF.md",
        "v1_proof": "docs/proof/platform/RECIPE_MODULE_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/recipe_module.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/recipe_module.py"},
            {"kind": "module", "path": "src/recipe_module_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/recipe-module/status"},
            {"kind": "gate", "path": "make recipe-module-organ-gate"},
        ],
    },
    "imagine_generator": {
        "active_doc": "docs/subsystems/storyforge/IMAGINE_GENERATOR.md",
        "prototype_proof": "docs/proof/storyforge/IMAGINE_GENERATOR_V1_PROOF.md",
        "v1_proof": "docs/proof/storyforge/IMAGINE_GENERATOR_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/imagine_generator.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/imagine_generator.py"},
            {"kind": "module", "path": "src/imagine_generator_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/imagine-generator/status"},
            {"kind": "gate", "path": "make imagine-generator-organ-gate"},
        ],
    },
    "narrative_trust_pack": {
        "active_doc": "docs/subsystems/storyforge/NARRATIVE_TRUST_PACK.md",
        "prototype_proof": "docs/proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md",
        "v1_proof": "docs/proof/storyforge/NARRATIVE_TRUST_PACK_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/narrative_trust_pack_organ.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/narrative_trust_pack_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/narrative-trust-pack/status"},
            {"kind": "gate", "path": "make narrative-trust-pack-organ-gate"},
        ],
    },
    "human_voice_extraction": {
        "active_doc": "docs/subsystems/speakers/HUMAN_VOICE_EXTRACTION.md",
        "prototype_proof": "docs/proof/speakers/HUMAN_VOICE_EXTRACTION_V1_PROOF.md",
        "v1_proof": "docs/proof/speakers/HUMAN_VOICE_EXTRACTION_V1_PROOF.md",
        "surface_prototype": [
            {"kind": "module", "path": "src/human_voice_extraction.py", "isolated": True},
        ],
        "surface_mvp": [
            {"kind": "module", "path": "src/human_voice_extraction.py"},
            {"kind": "module", "path": "src/human_voice_extraction_organ.py"},
            {"kind": "api", "path": "GET /api/jarvis/human-voice-extraction/status"},
            {"kind": "gate", "path": "make human-voice-extraction-organ-gate"},
        ],
    },
}


def _load(gene: str) -> dict:
    path = _ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _save(gene: str, data: dict) -> None:
    path = _ROOT / "governance/subsystem_genomes" / f"{gene}.genome.v1.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _stamp_batch(data: dict, order: int) -> None:
    data.setdefault("activation", {})["batch_id"] = BATCH
    data["activation"]["order"] = order
    data["activation"]["notes"] = f"Release 27 wave {order}"


def prepare_prototype(gene: str, spec: dict) -> None:
    data = _load(gene)
    data.setdefault("runtime", {})["surface"] = spec["surface_prototype"]
    data.setdefault("proof", {})["bundles"] = [spec["prototype_proof"]]
    _save(gene, data)


def prepare_mvp(gene: str, spec: dict) -> None:
    data = _load(gene)
    data.setdefault("runtime", {})["surface"] = spec["surface_mvp"]
    data.setdefault("proof", {})["bundles"] = [spec["v1_proof"]]
    data.setdefault("ssp", {})["active_doc"] = spec["active_doc"]
    data.setdefault("ssp", {})["summon_eligible"] = False
    _save(gene, data)


def main() -> int:
    engine = PromotionEngine(_ROOT)
    for order, (gene, spec) in enumerate(ALT27_SPECS.items(), start=1):
        data = _load(gene)
        _stamp_batch(data, order)
        _save(gene, data)
        stage = (data.get("identity") or {}).get("stage")
        if stage == "governed":
            print(f"[alt27] {gene} already governed (batch stamped)")
            continue
        prepare_prototype(gene, spec)
        d1 = engine.evaluate(gene)
        if not d1.passed:
            print(f"[alt27] {gene} prototype blocked: {d1.failures}")
            return 1
        d1_apply = engine.apply(d1)
        if not d1_apply.passed:
            print(f"[alt27] {gene} prototype apply failed: {d1_apply.failures}")
            return 1
        prepare_mvp(gene, spec)
        d2 = engine.evaluate(gene)
        if not d2.passed:
            print(f"[alt27] {gene} mvp blocked: {d2.failures}")
            return 1
        d2_apply = engine.apply(d2)
        if not d2_apply.passed:
            print(f"[alt27] {gene} mvp apply failed: {d2_apply.failures}")
            return 1
        print(f"[alt27] {gene} promoted to mvp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
