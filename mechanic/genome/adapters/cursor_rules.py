"""Scan .cursor/rules and .cursor/skills."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from mechanic.genome.adapters.base import GenomeAdapter
from mechanic.genome.schema import add_edge, add_node


class CursorRulesAdapter(GenomeAdapter):
    adapter_id = "cursor_rules"

    def describe(self, repo_path: Path) -> dict[str, Any]:
        rules = repo_path / ".cursor" / "rules"
        skills = repo_path / ".cursor" / "skills"
        return {
            "adapter_id": self.adapter_id,
            "rules_exists": rules.is_dir(),
            "skills_exists": skills.is_dir(),
        }

    def extract(self, repo_path: Path, genome: dict[str, Any]) -> dict[str, Any]:
        found = 0
        for sub in ("rules", "skills"):
            base = repo_path / ".cursor" / sub
            if not base.is_dir():
                continue
            for path in sorted(base.rglob("*")):
                if not path.is_file():
                    continue
                rel = path.relative_to(repo_path).as_posix()
                node_id = f"agent:{_hash_rel(rel)}"
                add_node(
                    genome,
                    node_id=node_id,
                    node_type="agent_config",
                    label=path.name,
                    source_path=rel,
                    attrs={"cursor_kind": sub, "governed": True},
                )
                prompt_id = f"prompt:{_hash_rel(rel)}"
                add_node(
                    genome,
                    node_id=prompt_id,
                    node_type="prompt_asset",
                    label=path.name,
                    source_path=rel,
                    attrs={"from_cursor": sub},
                )
                add_edge(genome, source=node_id, target=prompt_id, edge_type="depends_on")
                found += 1
        return {"adapter_id": self.adapter_id, "nodes_added": found}


def _hash_rel(rel: str) -> str:
    return hashlib.sha256(rel.encode("utf-8")).hexdigest()[:12]
