"""Mesh topology: peers, seeds, and local routing table."""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.mesh.paths import mesh_dir
from src.mesh.runtime import mesh_data_dir

DEFAULT_MESH_CONFIG = {
    "version": "1.0",
    "node_name": "aais-mesh",
    "listen_port": 8000,
    "peers": [],
    "seeds": [],
    "gossip_interval_sec": 30,
    "require_handshake": False,
    "gossip_push": False,
    "capabilities": [
        "reasoning_evaluate",
        "falsity_sync",
        "invariant_propagate",
        "handshake",
    ],
    "adapters": {
        "aais_url": None,
        "urg_url": None,
    },
}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def mesh_config_path(base_dir: str | Path | None = None) -> Path:
    return mesh_dir(base_dir) / "mesh_config.json"


def _load_deploy_peers() -> list:
    peers_file = _project_root() / "deploy" / "mesh" / "peers.json"
    if not peers_file.exists():
        example = _project_root() / "deploy" / "mesh" / "peers.example.json"
        if example.exists():
            peers_file = example
        else:
            return []
    data = json.loads(peers_file.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return list(data.get("peers") or [])


def load_mesh_config(base_dir: str | Path | None = None) -> dict:
    merged = dict(DEFAULT_MESH_CONFIG)
    path = mesh_config_path(base_dir)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        merged.update(data)
        if "adapters" in data:
            merged["adapters"] = {**DEFAULT_MESH_CONFIG["adapters"], **data["adapters"]}

    env_peers = os.environ.get("MESH_PEERS_JSON")
    if env_peers:
        try:
            parsed = json.loads(env_peers)
            merged["peers"] = parsed if isinstance(parsed, list) else list(parsed.get("peers") or [])
        except json.JSONDecodeError:
            pass
    elif not merged.get("peers"):
        merged["peers"] = _load_deploy_peers()

    return merged


def save_mesh_config(config: dict, base_dir: str | Path | None = None) -> Path:
    path = mesh_config_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


def _peer_url(peer: str | dict) -> str | None:
    if isinstance(peer, str):
        url = peer.strip()
        return url.rstrip("/") if url else None
    if isinstance(peer, dict):
        url = str(peer.get("url") or "").strip()
        return url.rstrip("/") if url else None
    return None


def iter_peers(config: dict) -> list[dict]:
    records: list[dict] = []
    seen: set[str] = set()
    for raw in list(config.get("seeds", [])) + list(config.get("peers", [])):
        url = _peer_url(raw)
        if not url or url in seen:
            continue
        seen.add(url)
        verify_key = raw.get("verify_key") if isinstance(raw, dict) else None
        records.append({"url": url, "verify_key": verify_key})
    return records


def all_peer_urls(config: dict, base_dir: str | Path | None = None) -> list[str]:
    return [p["url"] for p in iter_all_peers(config, base_dir) if p.get("url")]


def iter_all_peers(config: dict, base_dir: str | Path | None = None) -> list[dict]:
    """Union of config peers/seeds and handshake-known peer URLs."""
    records: dict[str, dict] = {}
    for peer in iter_peers(config):
        url = peer["url"]
        records[url] = dict(peer)

    if base_dir is not None:
        try:
            from src.mesh.known_peers import KnownPeersStore

            for rec in KnownPeersStore(base_dir).list_all():
                url = str(rec.get("peer_url") or "").strip().rstrip("/")
                if not url:
                    continue
                entry = records.get(url, {"url": url})
                if rec.get("verify_key") and not entry.get("verify_key"):
                    entry["verify_key"] = rec["verify_key"]
                entry["node_id"] = rec.get("node_id")
                entry["capabilities"] = rec.get("capabilities") or entry.get("capabilities") or []
                records[url] = entry
        except Exception:
            pass

    return list(records.values())


def pinned_verify_key_for_url(config: dict, peer_url: str) -> str | None:
    normalized = peer_url.rstrip("/")
    for peer in iter_peers(config):
        if peer.get("url") == normalized and peer.get("verify_key"):
            return peer["verify_key"]
    return None


def pinned_verify_keys(config: dict) -> list[str]:
    keys: list[str] = []
    for peer in iter_peers(config):
        vk = peer.get("verify_key")
        if vk and vk not in keys:
            keys.append(vk)
    return keys


def verify_key_allowed(config: dict, verify_key: str | None) -> bool:
    pins = pinned_verify_keys(config)
    if not pins:
        return True
    return bool(verify_key and verify_key in pins)


def topology_snapshot(
    config: dict,
    identity: dict,
    *,
    peer_status: dict | None = None,
    base_dir: str | Path | None = None,
) -> dict:
    peer_details: list[dict] = []
    for peer in iter_all_peers(config, base_dir):
        detail = {"url": peer.get("url"), "capabilities": peer.get("capabilities") or []}
        if peer.get("node_id"):
            detail["node_id"] = peer["node_id"]
        peer_details.append(detail)

    return {
        "node_id": identity["node_id"],
        "node_name": config.get("node_name"),
        "listen_port": config.get("listen_port"),
        "capabilities": config.get("capabilities", []),
        "require_handshake": bool(config.get("require_handshake")),
        "peers": all_peer_urls(config, base_dir),
        "peer_details": peer_details,
        "peer_status": peer_status or {},
        "mesh_data_dir": str(mesh_data_dir()),
    }
