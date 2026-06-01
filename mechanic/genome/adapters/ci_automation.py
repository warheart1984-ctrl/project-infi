"""Scan CI workflows and Makefile LLM targets."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from mechanic.genome.adapters.base import GenomeAdapter
from mechanic.genome.schema import add_node

_LLM_HINTS = re.compile(r"openai|anthropic|llm|gpt|claude|chat\.completions", re.I)


class CiAutomationAdapter(GenomeAdapter):
    adapter_id = "ci_automation"

    def describe(self, repo_path: Path) -> dict[str, Any]:
        gh = repo_path / ".github" / "workflows"
        return {
            "adapter_id": self.adapter_id,
            "github_workflows": gh.is_dir(),
            "makefile": (repo_path / "Makefile").is_file(),
        }

    def extract(self, repo_path: Path, genome: dict[str, Any]) -> dict[str, Any]:
        found = 0
        wf_dir = repo_path / ".github" / "workflows"
        if wf_dir.is_dir():
            for path in sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml")):
                text = path.read_text(encoding="utf-8", errors="replace")
                rel = path.relative_to(repo_path).as_posix()
                node_id = f"ci:{_hash_rel(rel)}"
                attrs: dict[str, Any] = {"kind": "github_workflow"}
                if _LLM_HINTS.search(text):
                    attrs["llm_hint"] = True
                    mc_id = f"model:{node_id}"
                    add_node(
                        genome,
                        node_id=mc_id,
                        node_type="model_call",
                        label="ci_llm_step",
                        source_path=rel,
                        attrs={"inferred": True},
                    )
                add_node(
                    genome,
                    node_id=node_id,
                    node_type="workflow_automation",
                    label=path.name,
                    source_path=rel,
                    attrs=attrs,
                )
                found += 1
        makefile = repo_path / "Makefile"
        if makefile.is_file():
            text = makefile.read_text(encoding="utf-8", errors="replace")
            if _LLM_HINTS.search(text):
                node_id = "ci:makefile-llm"
                add_node(
                    genome,
                    node_id=node_id,
                    node_type="workflow_automation",
                    label="Makefile",
                    source_path="Makefile",
                    attrs={"llm_hint": True},
                )
                found += 1
        return {"adapter_id": self.adapter_id, "nodes_added": found}


def _hash_rel(rel: str) -> str:
    return hashlib.sha256(rel.encode("utf-8")).hexdigest()[:12]
