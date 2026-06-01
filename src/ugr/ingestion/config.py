"""Curated source configuration for UGR governed ingestion."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


INGESTION_CONFIG_VERSION = "0.1"
SUPPORTED_SOURCE_TYPES = frozenset({"arxiv", "github_releases", "rss"})


def _default_config_path() -> Path:
    env_path = os.getenv("UGR_INGESTION_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "deploy" / "ugr" / "ingestion.sources.json"


@dataclass(frozen=True)
class IngestionSource:
    source_id: str
    source_type: str
    enabled: bool
    tenant_scope: str
    options: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "enabled": self.enabled,
            "tenant_scope": self.tenant_scope,
            "options": dict(self.options),
        }


class IngestionConfig:
    """Load and validate curated ingestion sources."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else _default_config_path()
        self._payload = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"config_version": INGESTION_CONFIG_VERSION, "sources": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    @property
    def sources(self) -> dict[str, IngestionSource]:
        parsed: dict[str, IngestionSource] = {}
        for source_id, spec in dict(self._payload.get("sources") or {}).items():
            source_type = str(spec.get("type") or "").strip().lower()
            if source_type not in SUPPORTED_SOURCE_TYPES:
                continue
            parsed[source_id] = IngestionSource(
                source_id=str(source_id),
                source_type=source_type,
                enabled=bool(spec.get("enabled", False)),
                tenant_scope=str(spec.get("tenant_scope") or "global"),
                options={key: value for key, value in spec.items() if key not in {"type", "enabled", "tenant_scope"}},
            )
        return parsed

    def get(self, source_id: str) -> IngestionSource | None:
        return self.sources.get(source_id)

    def enabled_sources(self) -> list[IngestionSource]:
        return [source for source in self.sources.values() if source.enabled]
