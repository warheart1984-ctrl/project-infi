"""Apply repo-level governance manifest to Process Genome (dogfood remediation)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mechanic.genome.adapters.base import GenomeAdapter
from mechanic.genome.schema import add_node

_MANIFEST_PATH = Path(".mechanic/governance_manifest.json")


class GovernanceManifestAdapter(GenomeAdapter):
    adapter_id = "governance_manifest"

    def describe(self, repo_path: Path) -> dict[str, Any]:
        manifest = repo_path / ".mechanic" / "governance_manifest.json"
        return {
            "adapter_id": self.adapter_id,
            "manifest_present": manifest.is_file(),
        }

    def extract(self, repo_path: Path, genome: dict[str, Any]) -> dict[str, Any]:
        manifest_path = repo_path / ".mechanic" / "governance_manifest.json"
        if not manifest_path.is_file():
            return {"adapter_id": self.adapter_id, "nodes_added": 0}

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        owner = str(
            manifest.get("decision_owner")
            or manifest.get("owner")
            or manifest.get("workflow_overrides", {}).get("default_decision_owner")
            or "meta-architect-ops"
        ).strip()
        repo_gov = dict(manifest.get("repo_governance") or {})

        add_node(
            genome,
            node_id="agent:repo-governance-owner",
            node_type="agent_config",
            label="Repo governance owner",
            source_path=str(manifest_path.relative_to(repo_path)).replace("\\", "/"),
            attrs={"decision_owner": owner, "owner": owner, "governed": True},
        )

        if repo_gov.get("human_control_required"):
            add_node(
                genome,
                node_id="human:repo-governance-hitl",
                node_type="human_control",
                label="Repo governance HITL gate",
                source_path=str(manifest_path.relative_to(repo_path)).replace("\\", "/"),
                attrs={"kind": "operator_review", "decision_owner": owner},
            )

        for marker in repo_gov.get("loop_boundary_markers") or []:
            add_node(
                genome,
                node_id=f"prompt:loop-boundary-{marker}",
                node_type="prompt_asset",
                label=f"loop boundary {marker}",
                source_path=str(manifest_path.relative_to(repo_path)).replace("\\", "/"),
                attrs={"content_hint": f"retry loop {marker}", "kind": "invariant_boundary"},
            )

        default_owner = str(manifest.get("workflow_overrides", {}).get("default_decision_owner") or owner)
        for node in genome.get("nodes") or []:
            if str(node.get("type")) != "workflow_automation":
                continue
            attrs = dict(node.get("attrs") or {})
            if not attrs.get("owner") and not attrs.get("decision_owner"):
                attrs["owner"] = default_owner
                attrs["decision_owner"] = default_owner
            if attrs.get("llm_hint") and repo_gov.get("high_impact_hitl"):
                attrs["high_impact"] = True
            node["attrs"] = attrs

        return {"adapter_id": self.adapter_id, "nodes_added": 3, "decision_owner": owner}
