"""Map replay emitters to subsystem genomes and repo paths."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GENOME_DIR = _REPO_ROOT / "governance" / "subsystem_genomes"

_KIND_DEFAULTS: dict[str, dict[str, str]] = {
    "ledger_transition": {
        "subsystem_id": "urg.mission_runtime",
        "module": "src.ugr.mission.mission_runtime",
        "genome_ref": "governance/subsystem_genomes/urg_mission_runtime.genome.v1.json",
    },
    "mission_receipt": {
        "subsystem_id": "urg.mission_receipt",
        "module": "src.ugr.mission.mission_receipt",
        "genome_ref": "governance/subsystem_genomes/urg_mission_runtime.genome.v1.json",
    },
    "deliberation": {
        "subsystem_id": "ugr.unified_runtime",
        "module": "src.ugr.unified_runtime",
        "genome_ref": "",
    },
    "lineage_node": {
        "subsystem_id": "cisiv_operator_lineage_console",
        "module": "src.ul_lineage",
        "genome_ref": "governance/subsystem_genomes/cisiv_operator_lineage_console.genome.v1.json",
    },
    "law_event": {
        "subsystem_id": "project_infi_law_organ",
        "module": "src.project_infi_law",
        "genome_ref": "governance/subsystem_genomes/project_infi_law_organ.genome.v1.json",
    },
    "jarvis_run_step": {
        "subsystem_id": "run_ledger_organ",
        "module": "src.run_ledger",
        "genome_ref": "governance/subsystem_genomes/run_ledger_organ.genome.v1.json",
    },
    "slingshot_receipt": {
        "subsystem_id": "slingshot",
        "module": "slingshot.impact",
        "genome_ref": "governance/subsystem_genomes/slingshot_organ.genome.v1.json",
    },
    "capability_audit": {
        "subsystem_id": "capability_service_bridge",
        "module": "src.capability_service_bridge",
        "genome_ref": "governance/subsystem_genomes/capability_service_bridge.genome.v1.json",
    },
    "invariant_check": {
        "subsystem_id": "invariant_engine_organ",
        "module": "src.invariant_engine_organ",
        "genome_ref": "governance/subsystem_genomes/invariant_engine_organ.genome.v1.json",
    },
    "cognitive_step": {
        "subsystem_id": "governed_direct_pipeline",
        "module": "src.api",
        "genome_ref": "governance/subsystem_genomes/governed_direct_pipeline.genome.v1.json",
    },
    "otem_gate": {
        "subsystem_id": "otem_bounded_organ",
        "module": "src.otem_runtime",
        "genome_ref": "governance/subsystem_genomes/otem_bounded_organ.genome.v1.json",
    },
    "nova_coherence": {
        "subsystem_id": "coherence_projection_organ",
        "module": "src.operator_cognition_coherence_fabric",
        "genome_ref": "governance/subsystem_genomes/coherence_projection_organ.genome.v1.json",
    },
    "intent_agency": {
        "subsystem_id": "intent_agency_organ",
        "module": "src.intent_agency_organ",
        "genome_ref": "governance/subsystem_genomes/intent_agency_organ.genome.v1.json",
    },
    "platform_job": {
        "subsystem_id": "platform",
        "module": "platform.jobs.registry",
        "genome_ref": "",
    },
}


def _load_genome_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    if not _GENOME_DIR.is_dir():
        return index
    for path in sorted(_GENOME_DIR.glob("*.genome.v1.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        gene = str((payload.get("identity") or {}).get("gene") or path.stem)
        surfaces = []
        for surface in (payload.get("runtime") or {}).get("surface") or []:
            if isinstance(surface, dict):
                surfaces.append(surface)
        index[gene] = {
            "genome_ref": str(path.relative_to(_REPO_ROOT)).replace("\\", "/"),
            "surfaces": surfaces,
            "display_name": (payload.get("identity") or {}).get("display_name") or gene,
        }
    return index


_GENOME_INDEX: dict[str, dict[str, Any]] | None = None


def genome_index() -> dict[str, dict[str, Any]]:
    global _GENOME_INDEX
    if _GENOME_INDEX is None:
        _GENOME_INDEX = _load_genome_index()
    return _GENOME_INDEX


def resolve_emitter(kind: str, *, module: str | None = None) -> dict[str, str]:
    base = dict(_KIND_DEFAULTS.get(kind) or {})
    if module:
        base["module"] = module
    gene = base.get("subsystem_id") or ""
    entry = genome_index().get(gene.replace(".", "_"), genome_index().get(gene, {}))
    if entry and not base.get("genome_ref"):
        base["genome_ref"] = entry.get("genome_ref") or ""
    return {
        "subsystem_id": str(base.get("subsystem_id") or "unknown"),
        "module": str(base.get("module") or ""),
        "genome_ref": str(base.get("genome_ref") or ""),
    }


def jump_target(emitter: dict[str, Any]) -> dict[str, Any]:
    """UI-facing emitter jump metadata."""
    gene = str(emitter.get("subsystem_id") or "")
    entry = genome_index().get(gene, {})
    surfaces = list(entry.get("surfaces") or [])
    api_paths = [s.get("path") for s in surfaces if s.get("kind") == "api"]
    module_paths = [s.get("path") for s in surfaces if s.get("kind") == "module"]
    return {
        "subsystem_id": gene,
        "module": emitter.get("module"),
        "genome_ref": emitter.get("genome_ref") or entry.get("genome_ref"),
        "display_name": entry.get("display_name") or gene,
        "api_paths": api_paths,
        "module_paths": module_paths,
        "proof_hint": f"docs/proof/{gene.replace('_', '-')}/" if gene else "",
    }


LIVE_FORK_ALLOWLIST = frozenset(
    {
        "cisiv_operator_lineage_console",
        "invariant_engine_organ",
        "project_infi_law_organ",
        "capability_service_bridge",
    }
)


def live_fork_allowed(subsystem_id: str) -> bool:
    return subsystem_id in LIVE_FORK_ALLOWLIST
