"""Bridge FalsityRegistry to mesh gossip ledger shape."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.mesh.paths import mesh_dir
from src.mesh.topology import load_mesh_config
from src.rls.falsity_registry import FalsityRegistry
from src.rls.reasoning_graph import claim_fingerprint

LEDGER_FILENAME = "falsity_ledger.jsonl"
REGISTRY_FILENAME = "rls_falsity_registry.jsonl"

_ADAPTERS: dict[str, "FalsityMeshAdapter"] = {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_claim(claim: str) -> str:
    return claim_fingerprint(claim)


def _entry_fingerprint(entry: dict) -> str | None:
    return entry.get("claim_fingerprint") or entry.get("claim_hash")


def _normalize_entry(entry: dict) -> dict:
    fp = _entry_fingerprint(entry)
    out = dict(entry)
    if fp:
        out["claim_fingerprint"] = fp
        out["claim_hash"] = fp
    return out


def _mesh_registry_path(base_dir: str | Path | None) -> Path:
    return mesh_dir(base_dir) / REGISTRY_FILENAME


def _gossip_max_claim_bytes(base_dir: str | Path | None) -> int:
    config = load_mesh_config(base_dir)
    return int(config.get("gossip_max_claim_bytes") or 2048)


def get_falsity_mesh_adapter(base_dir: str | Path | None = None) -> "FalsityMeshAdapter":
    key = str(mesh_dir(base_dir).resolve())
    adapter = _ADAPTERS.get(key)
    if adapter is None:
        adapter = FalsityMeshAdapter(base_dir)
        _ADAPTERS[key] = adapter
    return adapter


class FalsityMeshAdapter:
    """Gossip-facing falsity ledger backed by mesh JSONL + FalsityRegistry."""

    def __init__(self, base_dir: str | Path | None = None, registry: FalsityRegistry | None = None):
        root = mesh_dir(base_dir)
        root.mkdir(parents=True, exist_ok=True)
        self.base_dir = root
        self.path = root / LEDGER_FILENAME
        if not self.path.exists():
            self.path.touch()
        self._registry = registry or FalsityRegistry(_mesh_registry_path(base_dir))

    @property
    def registry(self) -> FalsityRegistry:
        return self._registry

    def _read_all(self) -> list[dict]:
        entries: list[dict] = []
        if not self.path.exists():
            return entries
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(_normalize_entry(json.loads(line)))
            except json.JSONDecodeError:
                continue
        return entries

    def head_hash(self) -> str:
        entries = self._read_all()
        if not entries:
            return hashlib.sha256(b"empty").hexdigest()
        last = json.dumps(entries[-1], sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(last.encode("utf-8")).hexdigest()

    def is_falsified(self, claim: str) -> bool:
        if self._registry.is_falsified(claim):
            return True
        fp = hash_claim(claim)
        if self._registry.is_falsified_fingerprint(fp):
            return True
        for entry in self._read_all():
            if _entry_fingerprint(entry) == fp:
                return True
        return False

    def append(
        self,
        claim: str,
        *,
        reason: str = "rejected_locally",
        source_node: str | None = None,
        sync_mode: str = "with_claim_text",
    ) -> dict:
        fp = hash_claim(claim)
        if not self._registry.is_falsified(claim):
            self._registry.record_falsified(
                text=claim,
                reason=reason,
                rejection_source="mesh_falsity",
            )
        max_bytes = _gossip_max_claim_bytes(self.base_dir)
        claim_text = claim[:max_bytes] if claim else ""
        entry = {
            "claim_fingerprint": fp,
            "claim_hash": fp,
            "claim_preview": claim[:120],
            "claim_text": claim_text,
            "sync_mode": sync_mode,
            "reason": reason,
            "source_node": source_node,
            "timestamp": _utc_now(),
            "epistemic_state": "rejected",
            "rejection_source": "mesh_falsity",
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, separators=(",", ":")) + "\n")
        return entry

    def append_from_reject(
        self,
        claim: str,
        *,
        reason: str = "rls_rejected",
        source_node: str | None = None,
    ) -> dict | None:
        if not claim or not claim.strip():
            return None
        if self.is_falsified(claim):
            return None
        return self.append(claim, reason=reason, source_node=source_node)

    def _apply_remote_entry(self, entry: dict) -> None:
        sync_mode = str(entry.get("sync_mode") or "with_claim_text")
        claim_text = str(entry.get("claim_text") or "").strip()
        preview = str(entry.get("claim_preview") or "").strip()
        fp = _entry_fingerprint(entry)
        if not fp:
            return
        if sync_mode == "fingerprint_only" or (not claim_text and not preview):
            if not self._registry.is_falsified_fingerprint(fp):
                self._registry.record_falsified_fingerprint(
                    fingerprint=fp,
                    reason=str(entry.get("reason") or "mesh_gossip_merge"),
                    sync_mode="fingerprint_only",
                    rejection_source=str(entry.get("rejection_source") or "mesh_falsity"),
                )
            return
        text = claim_text or preview
        if text and not self._registry.is_falsified(text):
            self._registry.record_falsified(
                text=text,
                reason=str(entry.get("reason") or "mesh_gossip_merge"),
                rejection_source=str(entry.get("rejection_source") or "mesh_falsity"),
            )
        text_fp = hash_claim(text) if text else None
        if fp and fp != text_fp and not self._registry.is_falsified_fingerprint(fp):
            self._registry.record_falsified_fingerprint(
                fingerprint=fp,
                reason=str(entry.get("reason") or "mesh_gossip_merge"),
                sync_mode=str(entry.get("sync_mode") or "with_claim_text"),
                rejection_source=str(entry.get("rejection_source") or "mesh_falsity"),
            )

    def merge_entries(self, remote_entries: list[dict]) -> dict:
        local_fps = {_entry_fingerprint(e) for e in self._read_all() if _entry_fingerprint(e)}
        added = 0
        for raw in remote_entries:
            entry = _normalize_entry(raw)
            fp = _entry_fingerprint(entry)
            if not fp or fp in local_fps:
                continue
            self._apply_remote_entry(entry)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, separators=(",", ":")) + "\n")
            local_fps.add(fp)
            added += 1
        return {"added": added, "head": self.head_hash()}

    def export_since_head(self, known_head: str | None) -> list[dict]:
        entries = self._read_all()
        if not known_head or known_head == hashlib.sha256(b"empty").hexdigest():
            return entries
        for idx, entry in enumerate(entries):
            snapshot = hashlib.sha256(
                json.dumps(entry, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            if snapshot == known_head:
                return entries[idx + 1 :]
        return entries
