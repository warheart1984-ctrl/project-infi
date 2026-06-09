"""Minimal AAIS mesh API server for local federation compose."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from src.mesh.api_routes import register_mesh_routes
from src.mesh.runtime import configure_mesh_dir
from src.mesh.topology import save_mesh_config


def create_app() -> Flask:
    base = os.environ.get("MESH_DATA_DIR") or os.environ.get("AAIS_RUNTIME_DIR", "/app/.runtime/mesh")
    configure_mesh_dir(base)
    cfg_path = Path(base) / "mesh_config.json"
    if not cfg_path.exists():
        save_mesh_config(
            {
                "node_name": os.environ.get("MESH_NODE_NAME", "aais-mesh"),
                "require_handshake": os.environ.get("MESH_REQUIRE_HANDSHAKE", "false").lower()
                == "true",
                "capabilities": [
                    "handshake",
                    "gossip",
                    "falsity_sync",
                    "invariant_propagate",
                    "reasoning_evaluate",
                ],
            },
            base,
        )

    application = Flask(__name__)
    register_mesh_routes(application)
    return application


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
