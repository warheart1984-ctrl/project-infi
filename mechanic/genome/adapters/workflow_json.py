"""Scan workflow JSON graphs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from mechanic.genome.adapters.base import GenomeAdapter
from mechanic.genome.schema import add_edge, add_node


class WorkflowJsonAdapter(GenomeAdapter):
    adapter_id = "workflow_json"

    def describe(self, repo_path: Path) -> dict[str, Any]:
        return {"adapter_id": self.adapter_id, "search_globs": ["**/workflows/**", "**/workflow*.json"]}

    def extract(self, repo_path: Path, genome: dict[str, Any]) -> dict[str, Any]:
        found = 0
        candidates: list[Path] = []
        for pattern in ("workflows",):
            candidates.extend(repo_path.rglob(f"**/{pattern}/**/*.json"))
        for path in repo_path.rglob("workflow*.json"):
            if path not in candidates:
                candidates.append(path)
        for path in sorted(set(candidates)):
            if not path.is_file():
                continue
            rel = path.relative_to(repo_path).as_posix()
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            wf_id = f"workflow:{_hash_rel(rel)}"
            add_node(
                genome,
                node_id=wf_id,
                node_type="workflow_automation",
                label=path.name,
                source_path=rel,
                attrs=_workflow_attrs(payload),
            )
            owner = str(payload.get("owner") or payload.get("decision_owner") or "").strip()
            if owner:
                add_node(
                    genome,
                    node_id=f"agent:{wf_id}",
                    node_type="agent_config",
                    label=owner,
                    source_path=rel,
                    attrs={"owner": owner},
                )
            found += 1
            steps = payload.get("steps") or payload.get("nodes") or []
            if isinstance(steps, list):
                step_nodes: dict[str, str] = {}
                pending_validations: list[tuple[str, str]] = []
                for index, step in enumerate(steps):
                    if not isinstance(step, dict):
                        continue
                    step_type = str(step.get("type") or step.get("action") or "")
                    step_key = str(step.get("id") or step.get("name") or index)
                    if "ai" in step_type.lower() or step_type == "ai.analyze":
                        mc_id = f"model:{wf_id}:{index}"
                        add_node(
                            genome,
                            node_id=mc_id,
                            node_type="model_call",
                            label=step_type or "ai_step",
                            source_path=rel,
                            attrs=_step_attrs(step, index),
                        )
                        step_nodes[step_key] = mc_id
                        add_edge(genome, source=wf_id, target=mc_id, edge_type="calls")
                    if step_type in {"manual", "approval", "human_review"}:
                        hc_id = f"human:{wf_id}:{index}"
                        add_node(
                            genome,
                            node_id=hc_id,
                            node_type="human_control",
                            label=step_type,
                            source_path=rel,
                            attrs={"workflow_step_index": index},
                        )
                        step_nodes[step_key] = hc_id
                        add_edge(genome, source=wf_id, target=hc_id, edge_type="escalates_to_human")
                    if step_type in {"exception", "fallback", "error_handler"}:
                        exc_id = f"exc:{wf_id}:{index}"
                        add_node(
                            genome,
                            node_id=exc_id,
                            node_type="exception_path",
                            label=step_type,
                            source_path=rel,
                            attrs={"workflow_step_index": index},
                        )
                        step_nodes[step_key] = exc_id
                    if step_type in {"validation", "validator", "validate", "policy_validation"}:
                        val_id = f"validate:{wf_id}:{index}"
                        add_node(
                            genome,
                            node_id=val_id,
                            node_type="human_control",
                            label=step_type,
                            source_path=rel,
                            attrs={"workflow_step_index": index, "control": "validation"},
                        )
                        step_nodes[step_key] = val_id
                        target = str(step.get("target") or step.get("validates") or "")
                        if target:
                            pending_validations.append((val_id, target))
                for validator_id, target_key in pending_validations:
                    target_id = step_nodes.get(target_key)
                    if target_id:
                        add_edge(genome, source=validator_id, target=target_id, edge_type="validates")
        return {"adapter_id": self.adapter_id, "nodes_added": found}


def _hash_rel(rel: str) -> str:
    return hashlib.sha256(rel.encode("utf-8")).hexdigest()[:12]


def _workflow_attrs(payload: dict[str, Any]) -> dict[str, Any]:
    attrs: dict[str, Any] = {"has_graph": "nodes" in payload or "steps" in payload}
    for key in ("owner", "decision_owner", "high_impact", "rollback_plan", "rollback_token"):
        if payload.get(key):
            attrs[key] = payload[key]
    return attrs


def _step_attrs(step: dict[str, Any], index: int) -> dict[str, Any]:
    attrs: dict[str, Any] = {"workflow_step_index": index}
    for key in ("audit", "trace_id"):
        if step.get(key):
            attrs[key] = step[key]
    return attrs
