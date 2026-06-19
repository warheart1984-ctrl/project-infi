"""Load YAML LSG bundles into LongScaleGraphStore JSONL records."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml

from nova.lawful_llm import LongScaleGraphStore, MemoryFact

BUNDLE_MARKER_PREFIX = "lsg-bundle:"


def resolve_repo_root() -> Path:
    env_root = os.environ.get("LAWFUL_NOVA_REPO_ROOT") or os.environ.get("NOVA_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path.cwd().resolve()


def default_lsg_bundle_path() -> Path:
    override = os.environ.get("NOVA_LSG_PATH")
    if override:
        return Path(override).resolve()
    return resolve_repo_root() / "lsg" / "LSG-CORE.v1.yaml"


def default_lsg_store_path() -> Path:
    override = os.environ.get("NOVA_LSG_STORE")
    if override:
        return Path(override).resolve()
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or ".").expanduser()
    return home / ".nova" / "lsg" / "local.jsonl"


def _bundle_marker(bundle_id: str, version: str) -> str:
    return f"{BUNDLE_MARKER_PREFIX}{bundle_id}@{version}"


def _iter_store_records(store_path: Path) -> list[dict[str, Any]]:
    if not store_path.exists():
        return []
    records: list[dict[str, Any]] = []
    with store_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            cleaned = line.strip()
            if not cleaned:
                continue
            records.append(json.loads(cleaned))
    return records


def bundle_already_loaded(store_path: Path, *, bundle_id: str, version: str) -> bool:
    marker = _bundle_marker(bundle_id, version)
    for record in _iter_store_records(store_path):
        if record.get("source_ref") == marker:
            return True
    return False


def _fact_to_triples(fact: dict[str, Any]) -> list[MemoryFact]:
    kind = str(fact.get("kind") or "").strip().lower()
    if kind == "triple":
        source = str(fact.get("source") or "").strip()
        relation = str(fact.get("relation") or "").strip()
        target = str(fact.get("target") or "").strip()
        if source and relation and target:
            return [(source, relation, target)]
        return []

    if kind == "pattern":
        source = str(fact.get("source") or "conversation").strip()
        relation = str(fact.get("relation") or "responds_to").strip()
        match = fact.get("match") or []
        if isinstance(match, str):
            match = [match]
        triples: list[MemoryFact] = []
        for phrase in match:
            phrase_text = str(phrase).strip()
            if phrase_text:
                triples.append((source, relation, phrase_text))
        target = str(fact.get("target") or "").strip()
        if target:
            triples.append((source, relation, target))
        return triples

    return []


def compile_bundle_facts(bundle: dict[str, Any]) -> list[MemoryFact]:
    facts = bundle.get("facts") or []
    triples: list[MemoryFact] = []
    for fact in facts:
        if isinstance(fact, dict):
            triples.extend(_fact_to_triples(fact))
    return triples


def load_lsg_bundle(
    bundle_path: Path | str,
    *,
    tenant_id: str = "local",
    store_path: Path | str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Seed JSONL store from a YAML bundle. Idempotent unless force=True."""
    path = Path(bundle_path).resolve()
    store = LongScaleGraphStore(store_path or default_lsg_store_path())
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    bundle_id = str(raw.get("bundle_id") or path.stem)
    version = str(raw.get("version") or "1.0")
    marker = _bundle_marker(bundle_id, version)

    if not force and bundle_already_loaded(store.path, bundle_id=bundle_id, version=version):
        return {
            "bundle_id": bundle_id,
            "version": version,
            "store_path": str(store.path),
            "loaded": False,
            "fact_count": len(_iter_store_records(store.path)),
            "reason": "already_loaded",
        }

    triples = compile_bundle_facts(raw)
    for source, relation, target in triples:
        store.add_fact(
            tenant_id=tenant_id,
            source=source,
            relation=relation,
            target=target,
            confidence=1.0,
            source_ref=marker,
        )

    return {
        "bundle_id": bundle_id,
        "version": version,
        "store_path": str(store.path),
        "loaded": True,
        "triples_seeded": len(triples),
        "fact_count": len(_iter_store_records(store.path)),
    }


def ensure_lsg_store(
    *,
    tenant_id: str = "local",
    bundle_path: Path | str | None = None,
) -> LongScaleGraphStore:
    """Return a store, seeding from the default bundle when empty or unmarked."""
    store_path = default_lsg_store_path()
    bundle = Path(bundle_path) if bundle_path else default_lsg_bundle_path()
    if bundle.exists():
        load_lsg_bundle(bundle, tenant_id=tenant_id, store_path=store_path)
    return LongScaleGraphStore(store_path)


def lsg_status() -> dict[str, Any]:
    store_path = default_lsg_store_path()
    bundle_path = default_lsg_bundle_path()
    records = _iter_store_records(store_path)
    bundle_id = None
    version = None
    if bundle_path.exists():
        raw = yaml.safe_load(bundle_path.read_text(encoding="utf-8")) or {}
        bundle_id = str(raw.get("bundle_id") or bundle_path.stem)
        version = str(raw.get("version") or "1.0")
    loaded = False
    if bundle_id and version:
        loaded = bundle_already_loaded(store_path, bundle_id=bundle_id, version=version)
    return {
        "lsg_loaded": loaded,
        "bundle_id": bundle_id,
        "bundle_version": version,
        "bundle_path": str(bundle_path),
        "store_path": str(store_path),
        "record_count": len(records),
    }
