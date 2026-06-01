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
                attrs={"has_graph": "nodes" in payload or "steps" in payload},
            )
            found += 1
            steps = payload.get("steps") or payload.get("nodes") or []
            if isinstance(steps, list):
                for index, step in enumerate(steps):
                    if not isinstance(step, dict):
                        continue
                    step_type = str(step.get("type") or step.get("action") or "")
                    if "ai" in step_type.lower() or step_type == "ai.analyze":
                        mc_id = f"model:{wf_id}:{index}"
                        add_node(
                            genome,
                            node_id=mc_id,
                            node_type="model_call",
                            label=step_type or "ai_step",
                            source_path=rel,
                            attrs={"workflow_step_index": index},
                        )
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
                        add_edge(genome, source=wf_id, target=hc_id, edge_type="escalates_to_human")
        return {"adapter_id": self.adapter_id, "nodes_added": found}


def _hash_rel(rel: str) -> str:
    return hashlib.sha256(rel.encode("utf-8")).hexdigest()[:12]
