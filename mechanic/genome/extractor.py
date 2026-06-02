"""Repo crawl → Process Genome."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.datetime_compat import UTC

from mechanic.common import GENOME_SCHEMA_VERSION, hash_text, json_stable
from mechanic.genome.adapters.base import run_adapters
from mechanic.genome.schema import empty_genome, validate_genome


def extract_process_genome(
    *,
    case_id: str,
    repo_path: str | Path,
    adapter_ids: list[str] | None = None,
    trace_path: str | Path | None = None,
) -> dict[str, Any]:
    import os

    root = Path(repo_path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"repo-path is not a directory: {root}")
    previous_trace_path = os.environ.get("MECHANIC_TRACE_PATH")
    if trace_path:
        os.environ["MECHANIC_TRACE_PATH"] = str(trace_path)
    else:
        os.environ.pop("MECHANIC_TRACE_PATH", None)
    try:
        genome = empty_genome(case_id=case_id, repo_path=str(root))
        run_adapters(root, genome, adapter_ids=adapter_ids)
    finally:
        if previous_trace_path is None:
            os.environ.pop("MECHANIC_TRACE_PATH", None)
        else:
            os.environ["MECHANIC_TRACE_PATH"] = previous_trace_path
    profile_path = root / ".mechanic-profile.json"
    profile_meta: dict[str, Any] = {}
    if profile_path.is_file():
        try:
            loaded = json.loads(profile_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                profile_meta = loaded
        except (OSError, json.JSONDecodeError):
            pass
    genome["metadata"] = {
        "extracted_at_utc": datetime.now(UTC).isoformat(),
        "node_count": len(genome.get("nodes") or []),
        "edge_count": len(genome.get("edges") or []),
        **profile_meta,
    }
    genome["genome_hash"] = hash_text(json_stable({"nodes": genome["nodes"], "edges": genome["edges"]}))
    validate_genome(genome)
    return genome
