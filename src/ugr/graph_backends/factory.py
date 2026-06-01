"""Graph query backend factory — JSONL canonical + optional SQLite projection."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


UGR_GRAPH_QUERY_BACKEND_ENV = "UGR_GRAPH_QUERY_BACKEND"
DEFAULT_QUERY_BACKEND = "jsonl_memory"


def _default_config_path() -> Path:
    env_path = os.getenv("UGR_GRAPH_BACKEND_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "graph-backend.json"


def load_graph_backend_config(config_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path else _default_config_path()
    if not path.exists():
        return {
            "config_version": "0.1",
            "canonical_backend": "jsonl",
            "query_backend": DEFAULT_QUERY_BACKEND,
            "selected_external_db": "sqlite",
        }
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_query_backend_name(config: dict[str, Any] | None = None) -> str:
    cfg = dict(config or load_graph_backend_config())
    env_override = os.getenv(UGR_GRAPH_QUERY_BACKEND_ENV, "").strip().lower()
    if env_override:
        return env_override
    return str(cfg.get("query_backend") or DEFAULT_QUERY_BACKEND).strip().lower()


def create_query_backend(
    *,
    runtime_root: str | Path,
    config: dict[str, Any] | None = None,
):
    backend_name = resolve_query_backend_name(config)
    cfg = dict(config or load_graph_backend_config())
    if backend_name in {"jsonl", "jsonl_memory", "memory"}:
        return None
    if backend_name == "sqlite":
        from src.ugr.graph_backends.sqlite_backend import SQLiteGraphBackend

        return SQLiteGraphBackend(runtime_root=runtime_root, config=cfg)
    raise ValueError(f"unsupported graph query backend: {backend_name}")
