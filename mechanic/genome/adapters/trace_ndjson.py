"""Ingest optional NDJSON trace files into Process Genome nodes/edges."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from mechanic.genome.adapters.base import GenomeAdapter
from mechanic.genome.schema import add_edge, add_node


class TraceNdjsonAdapter(GenomeAdapter):
    adapter_id = "trace_ndjson"

    def describe(self, repo_path: Path) -> dict[str, Any]:
        trace_path = _resolve_trace_path(repo_path)
        return {
            "adapter_id": self.adapter_id,
            "trace_path": str(trace_path) if trace_path else None,
            "enabled": trace_path is not None,
        }

    def extract(self, repo_path: Path, genome: dict[str, Any]) -> dict[str, Any]:
        trace_path = _resolve_trace_path(repo_path)
        if trace_path is None or not trace_path.is_file():
            return {"adapter_id": self.adapter_id, "nodes_added": 0, "edges_added": 0, "skipped": True}

        nodes_added = 0
        edges_added = 0
        try:
            lines = trace_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return {"adapter_id": self.adapter_id, "nodes_added": 0, "edges_added": 0, "error": "read_failed"}

        for line_no, line in enumerate(lines, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                record = json.loads(text)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue

            record_type = str(record.get("type") or "").strip().lower()
            if record_type == "edge":
                source = str(record.get("source") or "").strip()
                target = str(record.get("target") or "").strip()
                edge_type = str(record.get("edge_type") or record.get("relation") or "calls")
                if source and target:
                    add_edge(genome, source=source, target=target, edge_type=edge_type, attrs={"trace_line": line_no})
                    edges_added += 1
                continue

            node_id = str(record.get("id") or record.get("node_id") or f"trace:{_hash_line(line_no, text)}")
            if record.get("tool_call") or record.get("tool"):
                add_node(
                    genome,
                    node_id=node_id,
                    node_type="tool_binding",
                    label=str(record.get("tool_call") or record.get("tool") or "tool_call"),
                    source_path=str(record.get("source_path") or trace_path.name),
                    attrs={
                        "trace_line": line_no,
                        "allowed_actions": record.get("allowed_actions"),
                        **({"raw": record.get("tool_call")} if record.get("tool_call") else {}),
                    },
                )
                nodes_added += 1
            elif record.get("model_call") or record.get("model"):
                add_node(
                    genome,
                    node_id=node_id,
                    node_type="model_call",
                    label=str(record.get("model_call") or record.get("model") or "model_call"),
                    source_path=str(record.get("source_path") or trace_path.name),
                    attrs={"trace_line": line_no, "audit": record.get("audit"), "trace_id": record.get("trace_id")},
                )
                nodes_added += 1
            elif record.get("human_step") or record.get("human"):
                add_node(
                    genome,
                    node_id=node_id,
                    node_type="human_control",
                    label=str(record.get("human_step") or record.get("human") or "human_step"),
                    source_path=str(record.get("source_path") or trace_path.name),
                    attrs={"trace_line": line_no},
                )
                nodes_added += 1

            parent = str(record.get("parent") or record.get("source") or "").strip()
            child = str(record.get("child") or record.get("target") or "").strip()
            if parent and child:
                add_edge(
                    genome,
                    source=parent,
                    target=child,
                    edge_type=str(record.get("edge_type") or "calls"),
                    attrs={"trace_line": line_no},
                )
                edges_added += 1

        return {
            "adapter_id": self.adapter_id,
            "trace_path": str(trace_path),
            "nodes_added": nodes_added,
            "edges_added": edges_added,
        }


def _resolve_trace_path(repo_path: Path) -> Path | None:
    explicit = os.environ.get("MECHANIC_TRACE_PATH", "").strip()
    if explicit:
        candidate = Path(explicit).expanduser()
        if not candidate.is_absolute():
            candidate = (repo_path / candidate).resolve()
        return candidate if candidate.is_file() else Path(explicit).expanduser()
    default = repo_path / "traces" / "session.ndjson"
    if default.is_file():
        return default
    return None


def _hash_line(line_no: int, text: str) -> str:
    payload = f"{line_no}:{text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]
