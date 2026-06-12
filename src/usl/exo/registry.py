"""AAIS artifact registry for lifted machine-code models."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from src.cloud_forge.types import LawEnvelope
from src.usl.lift.types import ULLiftedModel


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class ArtifactRecord:
    artifact_id: str
    program_id: str
    artifact_hash: str
    slice_id: str | None = None
    signer: str | None = None
    registered_at: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArtifactRecord:
        return cls(
            artifact_id=str(data.get("artifact_id") or ""),
            program_id=str(data.get("program_id") or ""),
            artifact_hash=str(data.get("artifact_hash") or ""),
            slice_id=data.get("slice_id"),
            signer=data.get("signer"),
            registered_at=str(data.get("registered_at") or _utc_now_iso()),
        )


@dataclass
class EngineGraphStub:
    program_id: str
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EngineGraphStub:
        return cls(
            program_id=str(data.get("program_id") or ""),
            nodes=list(data.get("nodes") or []),
            edges=list(data.get("edges") or []),
        )


def _engine_graph_from_model(model: ULLiftedModel) -> EngineGraphStub:
    nodes: list[dict[str, Any]] = []
    for block in model.control.blocks:
        nodes.append(
            {
                "node_id": block.block_id,
                "kind": "basic_block",
                "vaddr": block.start_vaddr,
                "size": block.size,
                "terminator": block.terminator,
            }
        )
    for fn in model.control.functions:
        nodes.append(
            {
                "node_id": fn.function_id,
                "kind": "function",
                "entry_vaddr": fn.entry_vaddr,
                "blocks": list(fn.blocks),
            }
        )
    edges = [
        {
            "from": edge.from_block,
            "to": edge.to_block,
            "kind": edge.kind,
        }
        for edge in model.control.edges
    ]
    return EngineGraphStub(
        program_id=model.meta.program_id,
        nodes=nodes,
        edges=edges,
    )


class ArtifactStore(Protocol):
    def register(self, artifact_id: str, payload: dict[str, Any]) -> None:
        ...

    def get(self, artifact_id: str) -> dict[str, Any] | None:
        ...

    def list_artifact_ids(self, domain: str | None = None) -> list[str]:
        ...


class FileArtifactStore:
    """File-backed JSON store under ``root/artifacts/{artifact_id}.json``."""

    def __init__(self, root: Path) -> None:
        self._root = root / "artifacts"
        self._root.mkdir(parents=True, exist_ok=True)

    def register(self, artifact_id: str, payload: dict[str, Any]) -> None:
        path = self._root / f"{artifact_id}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get(self, artifact_id: str) -> dict[str, Any] | None:
        path = self._root / f"{artifact_id}.json"
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_artifact_ids(self, domain: str | None = None) -> list[str]:
        ids: list[str] = []
        for path in sorted(self._root.glob("*.json")):
            if domain is None:
                ids.append(path.stem)
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            record = data.get("record") or {}
            if record.get("slice_id") == domain:
                ids.append(path.stem)
        return ids


class SqliteArtifactStore:
    """SQLite-backed artifact store (``USL_REGISTRY_DB`` / guest profile persistence)."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                domain TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def register(self, artifact_id: str, payload: dict[str, Any]) -> None:
        domain = None
        record = payload.get("record") or {}
        if isinstance(record, dict):
            domain = record.get("slice_id")
        self._conn.execute(
            """
            INSERT INTO artifacts (id, domain, payload_json, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                domain=excluded.domain,
                payload_json=excluded.payload_json,
                created_at=excluded.created_at
            """,
            (
                artifact_id,
                domain,
                json.dumps(payload, sort_keys=True),
                _utc_now_iso(),
            ),
        )
        self._conn.commit()

    def get(self, artifact_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT payload_json FROM artifacts WHERE id = ?",
            (artifact_id,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def list_artifact_ids(self, domain: str | None = None) -> list[str]:
        if domain is None:
            rows = self._conn.execute(
                "SELECT id FROM artifacts ORDER BY id"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id FROM artifacts WHERE domain = ? ORDER BY id",
                (domain,),
            ).fetchall()
        return [str(row[0]) for row in rows]


class AAISRegistry:
    """Registry for lift artifacts, engine graphs, and optional persistence."""

    def __init__(self, *, store: ArtifactStore | None = None) -> None:
        self._artifacts: dict[str, ArtifactRecord] = {}
        self._graphs: dict[str, EngineGraphStub] = {}
        self._models: dict[str, ULLiftedModel] = {}
        self._store = store

    def register_lifted_model(
        self,
        model: ULLiftedModel,
        *,
        domain: str | None = None,
        signer: str | None = None,
        law_envelope: LawEnvelope | None = None,
    ) -> str:
        digest = hashlib.sha256(model.meta.program_id.encode("utf-8")).hexdigest()[:16]
        artifact_id = f"aais-lift-{digest}-{uuid.uuid4().hex[:8]}"
        record = ArtifactRecord(
            artifact_id=artifact_id,
            program_id=model.meta.program_id,
            artifact_hash=model.meta.provenance.artifact_hash,
            slice_id=domain,
            signer=signer,
        )
        graph = _engine_graph_from_model(model)
        self._artifacts[artifact_id] = record
        self._graphs[artifact_id] = graph
        self._models[artifact_id] = model
        if self._store is not None:
            payload: dict[str, Any] = {
                "record": record.to_dict(),
                "model": model.to_dict(),
                "engine_graph": graph.to_dict(),
            }
            if law_envelope is not None:
                payload["law_envelope"] = asdict(law_envelope)
            self._store.register(artifact_id, payload)
        return artifact_id

    def _hydrate_from_store(self, artifact_id: str) -> bool:
        if self._store is None:
            return False
        payload = self._store.get(artifact_id)
        if payload is None:
            return False
        record_raw = payload.get("record") or {}
        self._artifacts[artifact_id] = ArtifactRecord.from_dict(record_raw)
        graph_raw = payload.get("engine_graph") or {}
        self._graphs[artifact_id] = EngineGraphStub.from_dict(graph_raw)
        model_raw = payload.get("model") or {}
        self._models[artifact_id] = ULLiftedModel.from_dict(model_raw)
        return True

    def get_artifact(self, artifact_id: str) -> ArtifactRecord | None:
        if artifact_id not in self._artifacts:
            self._hydrate_from_store(artifact_id)
        return self._artifacts.get(artifact_id)

    def get_engine_graph(self, artifact_id: str) -> EngineGraphStub | None:
        if artifact_id not in self._graphs:
            self._hydrate_from_store(artifact_id)
        return self._graphs.get(artifact_id)

    def get_lifted_model(self, artifact_id: str) -> ULLiftedModel | None:
        if artifact_id not in self._models:
            self._hydrate_from_store(artifact_id)
        return self._models.get(artifact_id)

    def get_law_envelope(self, artifact_id: str) -> LawEnvelope | None:
        if self._store is None:
            return None
        payload = self._store.get(artifact_id)
        if payload is None:
            return None
        raw = payload.get("law_envelope")
        if not raw:
            return None
        return LawEnvelope.from_dict(raw)

    def list_by_domain(self, domain: str | None = None) -> list[ArtifactRecord]:
        if self._store is not None:
            ids = self._store.list_artifact_ids(domain)
            records: list[ArtifactRecord] = []
            for artifact_id in ids:
                record = self.get_artifact(artifact_id)
                if record is not None:
                    records.append(record)
            return records
        records = list(self._artifacts.values())
        if domain is None:
            return records
        return [r for r in records if r.slice_id == domain]


_DEFAULT_REGISTRY: AAISRegistry | None = None


def _registry_store_from_env() -> ArtifactStore | None:
    db_env = os.environ.get("USL_REGISTRY_DB", "").strip()
    if db_env:
        return SqliteArtifactStore(Path(db_env))
    dir_env = os.environ.get("USL_AAIS_REGISTRY_DIR", "").strip()
    if dir_env:
        return FileArtifactStore(Path(dir_env))
    return None


def get_default_registry() -> AAISRegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        store = _registry_store_from_env()
        _DEFAULT_REGISTRY = AAISRegistry(store=store)
    return _DEFAULT_REGISTRY
