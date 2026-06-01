"""HTTP clients for UGR service mesh."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.ugr.cloud.mesh_config import UGRMeshConfig, load_mesh_config


class UGRMeshClients:
    """Call decomposed UGR services over the internal mesh."""

    def __init__(self, mesh: UGRMeshConfig | None = None, *, mesh_token: str | None = None, timeout: float = 30.0):
        self.mesh = mesh or load_mesh_config()
        self.mesh_token = mesh_token
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "X-UGR-Service-Client": "ugr-mesh"}
        if self.mesh_token:
            headers["X-UGR-Mesh-Token"] = self.mesh_token
        return headers

    def _request(self, service: str, path: str, payload: dict[str, Any] | None = None, *, method: str = "POST") -> dict[str, Any]:
        url = f"{self.mesh.base_url(service).rstrip('/')}{path}"
        headers = self._headers()
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        elif method == "GET":
            headers = {key: value for key, value in headers.items() if key != "Content-Type"}
        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{service} HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"{service} unreachable at {url}: {exc}") from exc

    def health(self, service: str) -> dict[str, Any]:
        return self._request(service, "/health", None, method="GET")

    def route_bridge(self, packet: dict[str, Any], *, runtime_context: str = "live_runtime") -> dict[str, Any]:
        return self._request(
            "policy",
            "/v1/bridge/route",
            {"packet": packet, "runtime_context": runtime_context},
        )

    def run_lanes(self, trace_id: str, lane_specs: list[dict[str, Any]], shared_context: dict[str, Any]) -> list[dict[str, Any]]:
        result = self._request(
            "lane_worker",
            "/v1/lanes/run",
            {
                "trace_id": trace_id,
                "lane_specs": lane_specs,
                "shared_context": shared_context,
            },
        )
        return list(result.get("lane_results") or [])

    def converge(self, trace_id: str, lane_results: list[dict[str, Any]], request: dict[str, Any], policy_context: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "convergence",
            "/v1/convergence/merge",
            {
                "trace_id": trace_id,
                "lane_results": lane_results,
                "request": request,
                "policy_context": policy_context,
            },
        )

    def append_claim(self, claim: dict[str, Any]) -> dict[str, Any]:
        return self._request("ledger", "/v1/ledger/claims", {"claim": claim})

    def query_related(self, terms: list[str], *, limit: int = 20) -> list[dict[str, Any]]:
        result = self._request(
            "ledger",
            "/v1/ledger/query",
            {"terms": terms, "limit": limit},
        )
        return list(result.get("matches") or [])

    def make_claim_id(self, subject: str, predicate: str, object_value: str, source_lane: str) -> str:
        result = self._request(
            "ledger",
            "/v1/ledger/claim-id",
            {
                "subject": subject,
                "predicate": predicate,
                "object": object_value,
                "source_lane": source_lane,
            },
        )
        return str(result.get("claim_id") or "")
