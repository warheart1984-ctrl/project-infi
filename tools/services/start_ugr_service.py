"""Start one UGR mesh service or the full local cluster."""

from __future__ import annotations

import argparse
import sys
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ugr.cloud.mesh_config import DEFAULT_SERVICES, load_mesh_config
from src.ugr.cloud.services import (
    create_causal_graph_app,
    create_convergence_app,
    create_embryo_gateway_app,
    create_embryo_v1_gateway_app,
    create_graph_index_app,
    create_ingestion_app,
    create_lane_worker_app,
    create_ledger_app,
    create_model_pool_app,
    create_orchestrator_app,
    create_platform_app,
    create_policy_app,
)


SERVICE_FACTORIES = {
    "orchestrator": create_orchestrator_app,
    "policy": create_policy_app,
    "ledger": create_ledger_app,
    "lane_worker": create_lane_worker_app,
    "convergence": create_convergence_app,
    "ingestion": create_ingestion_app,
    "platform": create_platform_app,
    "graph_index": create_graph_index_app,
    "model_pool": create_model_pool_app,
    "embryo_gateway": create_embryo_gateway_app,
    "causal_graph": create_causal_graph_app,
    "embryo_v1_gateway": create_embryo_v1_gateway_app,
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="UGR cloud mesh service launcher")
    parser.add_argument(
        "service",
        choices=[*SERVICE_FACTORIES.keys(), "cluster"],
        help="Service to start, or 'cluster' for all mesh nodes",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="Override mesh default port")
    parser.add_argument("--mesh-config", default="", help="Path to mesh JSON config")
    return parser.parse_args(argv)


def _default_port(service: str, mesh_config: str) -> int:
    if mesh_config:
        mesh = load_mesh_config(mesh_config)
    else:
        mesh = load_mesh_config()
    return int((mesh.services.get(service) or DEFAULT_SERVICES.get(service) or {}).get("port") or 8090)


def _run_app(app, host: str, port: int) -> None:
    app.run(host=host, port=port, threaded=True, use_reloader=False)


def start_cluster(host: str, mesh_config: str) -> None:
    mesh = load_mesh_config(mesh_config or None)
    threads: list[threading.Thread] = []
    for name in (
        "policy",
        "ledger",
        "convergence",
        "lane_worker",
        "ingestion",
        "platform",
        "graph_index",
        "model_pool",
        "embryo_gateway",
        "causal_graph",
        "embryo_v1_gateway",
        "orchestrator",
    ):
        spec = mesh.services.get(name) or DEFAULT_SERVICES[name]
        port = int(spec.get("port") or 8090)
        service_host = host if host != "127.0.0.1" else str(spec.get("host") or host)
        app = SERVICE_FACTORIES[name]()
        thread = threading.Thread(
            target=_run_app,
            args=(app, service_host, port),
            name=f"ugr-{name}",
            daemon=True,
        )
        thread.start()
        threads.append(thread)
        time.sleep(0.3)
    print(f"UGR cluster started ({mesh.cluster_id}) — orchestrator http://{host}:{mesh.services['orchestrator']['port']}/v1/deliberate")
    while True:
        time.sleep(3600)


def main(argv=None) -> None:
    args = parse_args(argv)
    if args.service == "cluster":
        start_cluster(args.host, args.mesh_config)
        return
    port = args.port or _default_port(args.service, args.mesh_config)
    app = SERVICE_FACTORIES[args.service]()
    _run_app(app, args.host, port)


if __name__ == "__main__":
    main()
