"""Flask routes for peer mesh on AAIS."""

from __future__ import annotations

import logging

from flask import jsonify, request

from src.mesh.capabilities_enforcement import check_gossip_capability
from src.mesh.evaluate_hooks import get_mesh_peer_id, mesh_base_dir
from src.mesh.gossip import (
    MESH_PEER_HEADER,
    build_gossip_response,
    gossip_all,
    handle_inbound_ack,
    handle_inbound_hello,
)
from src.mesh.gossip_runtime import gossip_health_snapshot, start_gossip_daemon
from src.mesh.identity import load_or_create_identity, node_fingerprint, public_node_record
from src.mesh.invariants import InvariantStore
from src.mesh.invariants_adapter import build_export_bundle
from src.mesh.known_peers import KnownPeersStore
from src.mesh.runtime import mesh_base
from src.mesh.topology import load_mesh_config, topology_snapshot
from src.mesh.trust import TrustStore

logger = logging.getLogger(__name__)

_gossip_started = False


def _base() -> str:
    return mesh_base_dir()


def _identity() -> dict:
    return load_or_create_identity(_base())


def _config() -> dict:
    return load_mesh_config(_base())


def _trust() -> TrustStore:
    return TrustStore(_base())


def _invariants() -> InvariantStore:
    return InvariantStore(_base())


def _ensure_gossip_daemon() -> None:
    global _gossip_started
    if _gossip_started:
        return
    _gossip_started = True
    start_gossip_daemon(_base(), _identity, _config, gossip_all)


def register_mesh_routes(app) -> None:
    """Register /api/mesh/* routes on the AAIS Flask app."""
    _ensure_gossip_daemon()

    @app.route("/api/mesh/handshake", methods=["POST"])
    def mesh_handshake():
        hello = request.get_json(silent=True) or {}
        if hello.get("phase") != "HELLO":
            return jsonify({"phase": "ERROR", "reason": "expected_HELLO"}), 400
        challenge = handle_inbound_hello(_base(), _identity(), _config(), hello)
        return jsonify(challenge)

    @app.route("/api/mesh/handshake/ack", methods=["POST"])
    def mesh_handshake_ack():
        ack = request.get_json(silent=True) or {}
        peer_url = request.headers.get("X-Mesh-Peer-Url")
        if peer_url:
            peer_url = str(peer_url).strip().rstrip("/")
        result = handle_inbound_ack(_base(), _identity(), _config(), ack, peer_url=peer_url)
        peer_id = result.get("peer_node_id")
        trust = _trust()
        if result.get("ok") and peer_id:
            trust.record(peer_id, "handshake_ok")
        elif peer_id:
            trust.record(peer_id, "handshake_fail")
        return jsonify(result)

    @app.route("/api/mesh/gossip", methods=["POST"])
    def mesh_gossip():
        peer_id = get_mesh_peer_id(request)
        if peer_id:
            allowed, reason = check_gossip_capability(peer_id, _base())
            if not allowed:
                return jsonify({"error": reason}), 403
        body = request.get_json(silent=True) or {}
        return jsonify(build_gossip_response(_base(), body))

    @app.route("/api/mesh/gossip/run", methods=["POST"])
    def mesh_gossip_run():
        results = gossip_all(_base(), _identity(), _config())
        return jsonify({"results": results})

    @app.route("/api/mesh/topology", methods=["GET"])
    def mesh_topology():
        trust = _trust()
        return jsonify(
            topology_snapshot(
                _config(),
                _identity(),
                base_dir=_base(),
                peer_status={pid: rec.get("score") for pid, rec in trust.snapshot().items()},
            )
        )

    @app.route("/api/mesh/identity", methods=["GET"])
    def mesh_identity():
        identity = _identity()
        cfg = _config()
        record = public_node_record(identity, capabilities=cfg.get("capabilities"))
        return jsonify(
            {
                "node_id": identity["node_id"],
                "fingerprint": node_fingerprint(identity),
                "verify_key": record["verify_key"],
                "node_name": cfg.get("node_name"),
            }
        )

    @app.route("/api/mesh/trust", methods=["GET"])
    def mesh_trust():
        return jsonify(_trust().snapshot())

    @app.route("/api/mesh/known-peers", methods=["GET"])
    def mesh_known_peers():
        return jsonify({"peers": KnownPeersStore(_base()).list_all()})

    @app.route("/api/mesh/health", methods=["GET"])
    def mesh_health():
        from src.mesh.gossip_runtime import _DAEMON_THREAD

        daemon_alive = bool(_DAEMON_THREAD and _DAEMON_THREAD.is_alive())
        return jsonify(
            {
                "node_id": _identity()["node_id"],
                "mesh_data_dir": mesh_base(),
                **gossip_health_snapshot(_base(), daemon_alive=daemon_alive),
            }
        )

    @app.route("/api/mesh/invariants", methods=["GET"])
    def mesh_invariants():
        bundle = build_export_bundle(_base())
        return jsonify(bundle)

    logger.info("Mesh routes registered (data dir: %s)", mesh_base())
