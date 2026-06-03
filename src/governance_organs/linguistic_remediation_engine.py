"""Linguistic remediation engine — Wave 9 drift-driven playbooks."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import repo_root
from tools.linguistic_drift_predictor import DriftScore, score_gene


def _bump_patch_version(version: str) -> str:
    if not version:
        return "1.0.1"
    parts = version.split(".")
    if len(parts) >= 3 and parts[2].isdigit():
        parts[2] = str(int(parts[2]) + 1)
        return ".".join(parts[:3])
    return f"{version}.1"


def build_playbook(score: DriftScore, root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    from tools.linguistic_genome_lib import extract_source_layers, load_genome

    genome = load_genome(score.gene, root)
    actions: list[dict[str, Any]] = []
    if not genome:
        return {
            "linguistic_remediation_playbook_version": "linguistic_remediation_playbook.v1",
            "gene": score.gene,
            "drift_band": score.band,
            "drift_risk": score.drift_risk,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "actions": [],
        }

    ssp = genome.get("ssp") or {}
    mythic = ssp.get("mythic_label", "")
    eng = ssp.get("engineering_class", "")
    module = ""
    for entry in (genome.get("runtime") or {}).get("surface") or []:
        if isinstance(entry, dict) and entry.get("kind") == "module":
            module = entry.get("path") or ""
            break

    if score.signals.get("alignment_gap", 0) >= 40 and module:
        src = extract_source_layers(root / module)
        if not (src.get("header") or {}).get("engineering"):
            snippet = (
                f"# Mythic: {mythic}\n"
                f"# Engineering: {eng}\n"
                f"# Responsibilities: TBD\n"
                f"# Non-responsibilities: TBD\n"
                f"# Invariants: TBD\n"
            )
            actions.append(
                {
                    "kind": "wave2_header",
                    "path": module,
                    "snippet": snippet,
                }
            )

    if score.band in {"medium", "high"} and mythic:
        safe_mythic = mythic.replace("'", "\\'")
        actions.append(
            {
                "kind": "translator_rerun",
                "command": f"make translate-mythic MYTHIC='{safe_mythic}'",
            }
        )

    if score.band == "high" and eng and mythic:
        mp_id = f"MP-LING-DRAFT-{score.gene.upper().replace('-', '_')[:24]}"
        mp_id = re.sub(r"[^A-Z0-9-]", "", mp_id)[:32] or "MP-LING-DRAFT"
        new_version = _bump_patch_version(ssp.get("linguistic_version", "1.0.0"))
        delta = {
            "mutation_kind": "linguistic_layer",
            "gene": score.gene,
            "backward_compatible": True,
            "before": {
                "mythic_label": mythic,
                "engineering_class": eng,
            },
            "after": {
                "mythic_label": mythic,
                "engineering_class": eng,
            },
            "bump_linguistic_version": new_version,
            "touch_source_header": True,
        }
        delta_path = f"schemas/deltas/{score.gene}_{mp_id}_linguistic.json"
        actions.append(
            {
                "kind": "mp_ling_draft",
                "proposal_id": mp_id,
                "delta_path": delta_path,
                "delta": delta,
                "note": "DRAFT ONLY — operator must review before apply",
            }
        )

    for rec in score.recommendations:
        actions.append({"kind": "recommendation", "text": rec})

    return {
        "linguistic_remediation_playbook_version": "linguistic_remediation_playbook.v1",
        "gene": score.gene,
        "drift_band": score.band,
        "drift_risk": score.drift_risk,
        "signals": score.signals,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actions": actions,
    }


def write_playbook(
    score: DriftScore,
    root: Path | None = None,
    *,
    write_delta_files: bool = False,
) -> Path:
    root = root or repo_root()
    playbook = build_playbook(score, root)
    out_dir = root / "governance/linguistic_remediations"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{score.gene}.v1.json"
    out_path.write_text(json.dumps(playbook, indent=2) + "\n", encoding="utf-8")

    if write_delta_files:
        for action in playbook.get("actions") or []:
            if action.get("kind") == "mp_ling_draft" and action.get("delta"):
                delta_path = root / action["delta_path"]
                delta_path.parent.mkdir(parents=True, exist_ok=True)
                delta_path.write_text(
                    json.dumps(action["delta"], indent=2) + "\n",
                    encoding="utf-8",
                )
    return out_path


def playbook_exists(gene: str, root: Path | None = None) -> bool:
    root = root or repo_root()
    return (root / "governance/linguistic_remediations" / f"{gene}.v1.json").is_file()
