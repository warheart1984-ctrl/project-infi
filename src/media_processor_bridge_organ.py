"""Media Processor Bridge Organ — governed bridge over barebones media processors."""

# Mythic: Media Processor Bridge Organ
# Engineering: MediaProcessorBridgePosture
from __future__ import annotations

from pathlib import Path
from typing import Any

MODULE_ID = "AAIS-MPB-01"
ORGAN_VERSION = "media_processor_bridge_organ.v1"

PROCESSOR_SEEDS = (
    "audio_processor",
    "image_processor",
    "video_processor",
    "batch_processor",
    "text_classifier",
)


def _processor_present(root: Path, name: str) -> bool:
    return (root / "src" / f"{name}.py").is_file()


def build_media_processor_bridge_status(*, root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[1]
    genome = root / "governance/subsystem_genomes/media_processor_bridge_organ.genome.v1.json"
    present = {name: _processor_present(root, name) for name in PROCESSOR_SEEDS}
    ready = all(present.values()) and genome.is_file()
    summary = f"processors={sum(present.values())}/{len(PROCESSOR_SEEDS)};bridge={int(ready)}"[:128]
    return {
        "media_processor_bridge_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "processor_seeds": present,
        "parent_genome_present": genome.is_file(),
        "bridge_safe": True,
        "proposal_only": True,
        "operator_gated": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }


def execute_media_processor_bridge(
    processor: str,
    args: dict[str, Any] | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Read-only or proposal-only bridge action per processor seed."""
    root = root or Path(__file__).resolve().parents[1]
    name = str(processor or "").strip().lower()
    if name not in PROCESSOR_SEEDS:
        return {
            "ok": False,
            "processor": name,
            "error": "unsupported processor",
            "claim_label": "blocked",
        }
    if not _processor_present(root, name):
        return {
            "ok": False,
            "processor": name,
            "error": "processor module missing",
            "claim_label": "blocked",
        }
    payload = dict(args or {})
    return {
        "ok": True,
        "processor": name,
        "action": str(payload.get("action") or "inspect"),
        "proposal_only": True,
        "side_effects": False,
        "claim_label": "asserted",
        "message": f"{name} bridge inspect (proposal-only)",
    }
