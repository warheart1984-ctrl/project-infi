"""Known peer records after successful handshake."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.mesh.paths import mesh_dir

KNOWN_PEERS_FILENAME = "known_peers.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class KnownPeersStore:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        self._path = mesh_dir(base_dir) / KNOWN_PEERS_FILENAME

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get(self, node_id: str) -> dict | None:
        return self._load().get(node_id)

    def is_known(self, node_id: str) -> bool:
        return node_id in self._load()

    def register(
        self,
        node_id: str,
        *,
        fingerprint: str | None = None,
        verify_key: str = "",
        capabilities: list[str] | None = None,
        peer_url: str | None = None,
    ) -> dict:
        record = self.upsert(
            node_id,
            verify_key=verify_key,
            capabilities=capabilities,
            peer_url=peer_url,
            fingerprint=fingerprint,
        )
        return record

    def list_all(self) -> list[dict]:
        return list(self._load().values())

    def find_by_url(self, peer_url: str) -> dict | None:
        normalized = str(peer_url or "").strip().rstrip("/")
        if not normalized:
            return None
        for rec in self.list_all():
            url = str(rec.get("peer_url") or "").strip().rstrip("/")
            if url == normalized:
                return rec
        return None

    def peer_url_for_node_id(self, node_id: str) -> str | None:
        rec = self.get(node_id)
        if not rec:
            return None
        url = str(rec.get("peer_url") or "").strip().rstrip("/")
        return url or None

    def peer_has_capability(self, node_id: str, capability: str) -> bool:
        rec = self.get(node_id)
        if not rec:
            return False
        caps = rec.get("capabilities") or []
        return capability in caps

    def upsert(
        self,
        node_id: str,
        *,
        verify_key: str = "",
        capabilities: list[str] | None = None,
        peer_url: str | None = None,
        fingerprint: str | None = None,
    ) -> dict:
        data = self._load()
        existing = data.get(node_id) or {}
        record = {
            "node_id": node_id,
            "verify_key": verify_key or existing.get("verify_key") or "",
            "capabilities": capabilities if capabilities is not None else list(existing.get("capabilities") or []),
            "handshake_at": _utc_now(),
            "peer_url": peer_url or existing.get("peer_url"),
        }
        if fingerprint:
            record["fingerprint"] = fingerprint
        elif existing.get("fingerprint"):
            record["fingerprint"] = existing["fingerprint"]
        data[node_id] = record
        self._save(data)
        return record

    def snapshot(self) -> dict:
        return self._load()
