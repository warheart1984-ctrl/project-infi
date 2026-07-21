from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from runtime.state import SovereignRuntimeContext


def _sha256(value: Any) -> str:
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _surface_dict(ctx: SovereignRuntimeContext, key: str) -> dict[str, Any]:
    surface = ctx.surface_by_key(key) if hasattr(ctx, "surface_by_key") else None
    if surface is None:
        return {}
    return {
        "key": surface.key,
        "title": surface.title,
        "subtitle": surface.subtitle,
        "backend": surface.backend,
        "frontend": surface.frontend,
        "route": surface.route,
        "tone": surface.tone,
        "focus_label": surface.focus_label,
    }


def build_timeline_payload(ctx: SovereignRuntimeContext, epoch: int) -> dict[str, Any]:
    codex = getattr(ctx, "codex", None)
    federation = getattr(ctx, "federation", None)
    bootstrapped = bool(getattr(federation, "bootstrapped", False))
    lane_start = max(epoch - 1, 0)
    lanes = []
    for offset in range(4):
        lane_epoch = lane_start + offset
        lanes.append(
            {
                "label": f"Epoch {lane_epoch:03d}",
                "epoch": lane_epoch,
                "progress": min(100, 40 + offset * 12),
            }
        )
    return {
        "surface": _surface_dict(ctx, "timeline"),
        "epoch": epoch,
        "replay_mode": "governed" if bootstrapped else "offline",
        "continuity_sync": "armed" if bootstrapped else "pending",
        "codex_base": str(getattr(codex, "base", "")),
        "lanes": lanes,
        "signals": {
            "continuity": "stable" if bootstrapped else "warming",
            "alignment": "synchronized" if bootstrapped else "idle",
        },
    }


def build_shader_update_payload(ctx: SovereignRuntimeContext, body: dict[str, Any]) -> dict[str, Any]:
    resonance = _coerce_float(body.get("resonance"), default=0.5)
    pulse_frequency = _coerce_float(
        body.get("pulse_frequency", body.get("pulseFrequency")), default=1.0
    )
    rotation = str(body.get("rotation", "stable"))
    density = str(body.get("density", "medium"))
    glow = round(min(max(resonance, 0.0), 1.0) * 100.0, 2)
    return {
        "surface": _surface_dict(ctx, "shader"),
        "accepted": True,
        "parameters": {
            "resonance": resonance,
            "pulse_frequency": pulse_frequency,
            "rotation": rotation,
            "density": density,
        },
        "render_state": {
            "glow_intensity": glow,
            "harmonic_mode": "deterministic",
        },
    }


def build_organism_state_payload(ctx: SovereignRuntimeContext) -> dict[str, Any]:
    codex = getattr(ctx, "codex", None)
    federation = getattr(ctx, "federation", None)
    specs = getattr(codex, "specs", {})
    conformance = getattr(codex, "conformance", {})
    bootstrapped = bool(getattr(federation, "bootstrapped", False))
    return {
        "surface": _surface_dict(ctx, "monitor"),
        "node_vitality": 88 if bootstrapped else 61,
        "lineage": {
            "spec_families": sorted(specs.keys()),
            "conformance_families": sorted(conformance.keys()),
            "evolution_step": len(specs) + len(conformance),
        },
        "telemetry": {
            "mode": "summary",
            "status": "online" if bootstrapped else "pending",
            "organism_map": "ready",
        },
    }


def build_consensus_votes_payload(ctx: SovereignRuntimeContext) -> dict[str, Any]:
    federation = getattr(ctx, "federation", None)
    bootstrapped = bool(getattr(federation, "bootstrapped", False))
    favor = 14 if bootstrapped else 9
    pending = 3 if bootstrapped else 6
    return {
        "surface": _surface_dict(ctx, "consensus"),
        "quorum": "reached" if bootstrapped else "warming",
        "votes": {
            "favor": favor,
            "pending": pending,
            "total": favor + pending,
        },
        "promotion_cycle": "v2.0",
    }


def build_ledger_blocks_payload(ctx: SovereignRuntimeContext) -> dict[str, Any]:
    codex = getattr(ctx, "codex", None)
    conformance = sorted(getattr(codex, "conformance", {}).keys())
    blocks = [
        {
            "index": 31,
            "label": "Receipt 031",
            "lineage_signature": "conformance receipt",
        },
        {
            "index": 32,
            "label": "Receipt 032",
            "lineage_signature": "lineage signature",
        },
        {
            "index": 33,
            "label": "Receipt 033",
            "lineage_signature": "bootstrap summary",
        },
    ]
    return {
        "surface": _surface_dict(ctx, "ledger"),
        "immutable": True,
        "proof_blocks": blocks,
        "conformance_families": conformance,
        "chain_length": len(blocks),
    }


def build_audio_pulse_payload(
    ctx: SovereignRuntimeContext, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    body = body or {}
    resonance = _coerce_float(body.get("resonance"), default=0.72)
    pulse_frequency = _coerce_float(
        body.get("pulse_frequency", body.get("pulseFrequency")), default=1.5
    )
    assets_path = body.get("assets_path") or os.environ.get("AUDIO_RES_PATH", "")
    waveform = str(body.get("waveform", "sine"))
    return {
        "surface": _surface_dict(ctx, "mandala"),
        "accepted": True,
        "soundscape": {
            "resonance": resonance,
            "pulse_frequency": pulse_frequency,
            "waveform": waveform,
            "assets_path": assets_path,
        },
        "composition": {
            "mode": "harmonic",
            "output": "synthesized",
        },
    }


def _ulx_bridge(ctx: SovereignRuntimeContext):
    return getattr(ctx, "ulx", None)


def _default_ulx_snapshot(ctx: SovereignRuntimeContext) -> dict[str, Any]:
    bridge = _ulx_bridge(ctx)
    source = str(getattr(bridge, "source", "") or "")
    updated_at = datetime.now(timezone.utc).isoformat()
    selection = {
        "start": 0,
        "end": 0,
        "text": "",
    }
    evidence_receipt = _build_ulx_evidence_receipt(source, selection, "bootstrap", 0, updated_at)
    snapshot = {
        "surface": _surface_dict(ctx, "ulx"),
        "origin": "bootstrap",
        "revision": 0,
        "updatedAt": updated_at,
        "source": source,
        "sourceHash": "",
        "selection": selection,
        "selectionText": "",
        "evidenceReceipt": evidence_receipt,
        "receiptId": evidence_receipt["receiptId"],
        "replayId": evidence_receipt["replayId"],
        "verificationStatus": evidence_receipt["verificationStatus"],
    }
    snapshot["sourceHash"] = _sha256(snapshot["source"])
    return snapshot


def _normalize_ulx_selection(body: dict[str, Any] | None) -> dict[str, Any]:
    body = body or {}
    start = _coerce_int(body.get("start", body.get("selectionStart")), default=0)
    end = _coerce_int(body.get("end", body.get("selectionEnd")), default=0)
    if end < start:
        start, end = end, start
    text = str(body.get("text", body.get("selectionText", "")))
    return {
        "start": max(start, 0),
        "end": max(end, 0),
        "text": text,
    }


def _build_ulx_evidence_receipt(
    source: str,
    selection: dict[str, Any],
    origin: str,
    revision: int,
    updated_at: str,
) -> dict[str, Any]:
    selection_payload = {
        "start": _coerce_int(selection.get("start"), default=0),
        "end": _coerce_int(selection.get("end"), default=0),
        "text": str(selection.get("text", "")),
    }
    if selection_payload["end"] < selection_payload["start"]:
        selection_payload["start"], selection_payload["end"] = (
            selection_payload["end"],
            selection_payload["start"],
        )
    source_hash = _sha256(source)
    selection_hash = _sha256(
        json.dumps(selection_payload, sort_keys=True, separators=(",", ":"))
    )
    receipt_seed = json.dumps(
        {
            "origin": origin,
            "revision": revision,
            "sourceHash": source_hash,
            "selectionHash": selection_hash,
            "updatedAt": updated_at,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    receipt_hash = _sha256(receipt_seed)
    receipt_id = f"ulxrcpt-{receipt_hash[:16]}"
    replay_id = f"ulx-replay-{source_hash[:12]}-{selection_hash[:12]}-r{revision:04d}"
    return {
        "receiptId": receipt_id,
        "replayId": replay_id,
        "sourceHash": source_hash,
        "selectionHash": selection_hash,
        "verificationStatus": "verified",
        "evidenceStatus": "linked",
        "issuedAt": updated_at,
        "replayable": True,
        "proof": {
            "kind": "ulx-source-selection",
            "algorithm": "sha256",
            "payloadHash": receipt_hash,
        },
    }


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _current_ulx_snapshot(ctx: SovereignRuntimeContext) -> dict[str, Any]:
    snapshot = getattr(ctx, "ulx_snapshot", None)
    if not isinstance(snapshot, dict):
        snapshot = _default_ulx_snapshot(ctx)
        ctx.ulx_snapshot = snapshot
    return snapshot


def build_ulx_snapshot_payload(
    ctx: SovereignRuntimeContext, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    current = _current_ulx_snapshot(ctx)
    if body is None:
        return current

    body = body or {}
    source = str(body.get("source", current.get("source", "")))
    selection = _normalize_ulx_selection(body.get("selection"))
    if not selection["text"] and body.get("selectionText") is not None:
        selection["text"] = str(body.get("selectionText", ""))
    updated_at = datetime.now(timezone.utc).isoformat()
    revision = int(current.get("revision", 0)) + 1
    origin = str(body.get("origin", current.get("origin", "unknown")))
    evidence_receipt = _build_ulx_evidence_receipt(
        source,
        selection,
        origin,
        revision,
        updated_at,
    )
    snapshot = {
        "surface": _surface_dict(ctx, "ulx"),
        "origin": origin,
        "revision": revision,
        "updatedAt": updated_at,
        "source": source,
        "sourceHash": evidence_receipt["sourceHash"],
        "selection": selection,
        "selectionText": selection["text"],
        "evidenceReceipt": evidence_receipt,
        "receiptId": evidence_receipt["receiptId"],
        "replayId": evidence_receipt["replayId"],
        "verificationStatus": evidence_receipt["verificationStatus"],
    }
    ctx.ulx_snapshot = snapshot
    return snapshot


def build_ulx_manifest_payload(ctx: SovereignRuntimeContext) -> dict[str, Any]:
    bridge = _ulx_bridge(ctx)
    if bridge is None:
        return {
            "surface": _surface_dict(ctx, "ulx"),
            "available": False,
            "error": "ulx bridge unavailable",
        }
    return {
        "surface": _surface_dict(ctx, "ulx"),
        "available": True,
        "bridge": bridge.manifest(),
        "snapshot": _current_ulx_snapshot(ctx),
    }


def build_ulx_compile_payload(
    ctx: SovereignRuntimeContext, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    bridge = _ulx_bridge(ctx)
    if bridge is None:
        return {
            "surface": _surface_dict(ctx, "ulx"),
            "command": "compile",
            "accepted": False,
            "error": "ulx bridge unavailable",
        }
    body = body or {}
    source = str(body.get("source", "")).strip()
    result = bridge.compile(source or None)
    return {
        "surface": _surface_dict(ctx, "ulx"),
        **result,
    }


def build_ulx_run_payload(
    ctx: SovereignRuntimeContext, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    bridge = _ulx_bridge(ctx)
    if bridge is None:
        return {
            "surface": _surface_dict(ctx, "ulx"),
            "command": "run",
            "accepted": False,
            "error": "ulx bridge unavailable",
        }
    body = body or {}
    source = str(body.get("source", "")).strip()
    result = bridge.run(source or None)
    return {
        "surface": _surface_dict(ctx, "ulx"),
        **result,
    }


def build_ulx_trace_payload(
    ctx: SovereignRuntimeContext, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    bridge = _ulx_bridge(ctx)
    if bridge is None:
        return {
            "surface": _surface_dict(ctx, "ulx"),
            "command": "trace",
            "accepted": False,
            "error": "ulx bridge unavailable",
        }
    body = body or {}
    source = str(body.get("source", "")).strip()
    result = bridge.trace(source or None)
    return {
        "surface": _surface_dict(ctx, "ulx"),
        **result,
    }


def build_router_evaluation_payload(
    ctx: SovereignRuntimeContext, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    body = body or {}
    prompt = str(body.get("prompt", body.get("task", "")))
    prompt_tokens = max(0, len(prompt.split()))
    evidence_ids = [str(item) for item in body.get("evidence_ids", body.get("evidenceIds", [])) if str(item).strip()]
    request_id = str(body.get("request_id", body.get("requestId", ""))) or f"router-{prompt_tokens:04d}"
    route_class = str(body.get("route_class", body.get("routeClass", "standard"))).strip() or "standard"
    bias = str(body.get("bias", "balanced")).strip() or "balanced"
    bootstrapped = bool(getattr(getattr(ctx, "federation", None), "bootstrapped", False))
    arch_loaded = bool(getattr(ctx, "architect", None))
    codex_loaded = bool(getattr(ctx, "codex", None))

    governance_score = 0.92 if bootstrapped else 0.68
    cost_score = 0.86 if prompt_tokens < 120 else 0.61
    performance_score = 0.90 if prompt_tokens < 220 else 0.67
    trust_score = 0.84 if evidence_ids else 0.57
    if route_class == "replay":
        trust_score += 0.07
        governance_score += 0.03
    if bias == "cost":
        cost_score += 0.08
        performance_score -= 0.04
    elif bias == "performance":
        performance_score += 0.08
        cost_score -= 0.03
    elif bias == "governance":
        governance_score += 0.08
        trust_score += 0.02

    governance_score = round(min(max(governance_score, 0.0), 1.0), 3)
    cost_score = round(min(max(cost_score, 0.0), 1.0), 3)
    performance_score = round(min(max(performance_score, 0.0), 1.0), 3)
    trust_score = round(min(max(trust_score, 0.0), 1.0), 3)

    route_evaluation = {
        "governance": round(governance_score * 0.3, 3),
        "cost": round(cost_score * 0.2, 3),
        "performance": round(performance_score * 0.2, 3),
        "trust": round(trust_score * 0.3, 3),
    }
    total = round(sum(route_evaluation.values()), 3)
    blocked = governance_score < 0.5 or (trust_score < 0.6 and len(evidence_ids) < 2)
    if blocked:
        selected_model = "none"
        backend = "router-guard"
        model_decision = "blocked"
        reason = "governance or trust thresholds were not met"
    elif prompt_tokens > 220:
        selected_model = "codex-reasoning-large"
        backend = "reasoning-large"
        model_decision = "promote-large"
        reason = "prompt size favors the larger reasoning surface"
    elif route_class == "replay":
        selected_model = "codex-reasoning-audit"
        backend = "replay-verifier"
        model_decision = "audit-route"
        reason = "replay class requests use the audit surface"
    elif bias == "performance":
        selected_model = "codex-reasoning-fast"
        backend = "fast-path"
        model_decision = "speed-route"
        reason = "performance bias selected the fast reasoning surface"
    else:
        selected_model = "codex-reasoning-standard"
        backend = "standard-path"
        model_decision = "standard-route"
        reason = "balanced routing selected the standard reasoning surface"

    return {
        "surface": _surface_dict(ctx, "consensus"),
        "requestId": request_id,
        "promptTokens": prompt_tokens,
        "selectedModel": selected_model,
        "backend": backend,
        "modelDecision": model_decision,
        "routeEvaluation": route_evaluation,
        "total": total,
        "blocked": blocked,
        "reason": reason,
        "evidenceIds": evidence_ids,
        "routeClass": route_class,
        "bias": bias,
        "context": {
            "codex_loaded": codex_loaded,
            "architect_loaded": arch_loaded,
            "bootstrapped": bootstrapped,
        },
    }


def _architect(ctx: SovereignRuntimeContext) -> Any:
    return getattr(ctx, "architect", None)


def build_prime_architect_payload(ctx: SovereignRuntimeContext) -> dict[str, Any]:
    architect = _architect(ctx)
    commands = list(getattr(architect, "command_manifest", ()))
    return {
        "surface": _surface_dict(ctx, "mandala"),
        "architect": {
            "loaded": architect is not None,
            "commands": commands,
            "summary": list(getattr(architect, "summary_lines", lambda: [])()) if architect is not None else [],
        },
    }


def build_prime_architect_action_payload(
    ctx: SovereignRuntimeContext, action: str, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    body = body or {}
    architect = _architect(ctx)
    if architect is None:
        return {
            "surface": _surface_dict(ctx, "mandala"),
            "action": action,
            "accepted": False,
            "error": "prime architect runtime unavailable",
        }

    if action == "approve_selected":
        result = architect.approve_selected(
            selected=body.get("selected"),
            parent_id=body.get("parent_id"),
        )
    elif action == "trace":
        result = architect.trace_lineage(body.get("chain_id"))
    elif action == "replay":
        result = architect.verify_replay(body.get("chain_id"))
    else:
        return {
            "surface": _surface_dict(ctx, "mandala"),
            "action": action,
            "accepted": False,
            "error": f"unknown prime architect action: {action}",
        }

    return {
        "surface": _surface_dict(ctx, "mandala"),
        "action": action,
        "accepted": True,
        "result": result,
    }


def build_runtime_manifest(ctx: SovereignRuntimeContext) -> dict[str, Any]:
    return {
        "app_name": getattr(ctx, "app_name", "Sovereign IDE"),
        "launcher_command": getattr(ctx, "launcher_command", "sovereign-ide"),
        "summary": list(ctx.summary_lines()) if hasattr(ctx, "summary_lines") else [],
        "surfaces": [
            _surface_dict(ctx, surface.key)
            for surface in getattr(ctx, "surface_definitions", ())
        ],
    }


def _coerce_float(value: Any, default: float) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


class SovereignIdeApiServer:
    def __init__(self, ctx: SovereignRuntimeContext, host: str = "127.0.0.1", port: int = 8787):
        self.ctx = ctx
        self.host = host
        self.port = port
        self._httpd = ThreadingHTTPServer((host, port), self._build_handler())
        self._httpd.sovereign_api = self  # type: ignore[attr-defined]
        self.port = int(self._httpd.server_address[1])
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> threading.Thread:
        thread = threading.Thread(target=self._httpd.serve_forever, name="sovereign-ide-api", daemon=True)
        thread.start()
        self._thread = thread
        return thread

    def serve_forever(self) -> None:
        self._httpd.serve_forever()

    def close(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _build_handler(self):
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:  # pragma: no cover - quiet server
                return None

            def do_OPTIONS(self) -> None:  # noqa: N802
                self.send_response(HTTPStatus.NO_CONTENT)
                server._set_cors_headers(self)
                self.end_headers()

            def do_GET(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)
                if parsed.path == "/health":
                    server._send_json(self, HTTPStatus.OK, build_runtime_manifest(server.ctx))
                    return
                if parsed.path == "/api/timeline":
                    epoch = int(query.get("epoch", ["0"])[0])
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_timeline_payload(server.ctx, epoch),
                    )
                    return
                if parsed.path == "/api/organism/state":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_organism_state_payload(server.ctx),
                    )
                    return
                if parsed.path == "/api/consensus/votes":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_consensus_votes_payload(server.ctx),
                    )
                    return
                if parsed.path == "/api/ledger/blocks":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_ledger_blocks_payload(server.ctx),
                    )
                    return
                if parsed.path == "/api/ulx/manifest":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_ulx_manifest_payload(server.ctx),
                    )
                    return
                if parsed.path == "/api/ulx/snapshot":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_ulx_snapshot_payload(server.ctx),
                    )
                    return
                server._send_error(self, HTTPStatus.NOT_FOUND, "unknown endpoint")

            def do_POST(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                body = self._read_json_body()
                if parsed.path == "/api/shader/update":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_shader_update_payload(server.ctx, body),
                    )
                    return
                if parsed.path == "/api/audio/pulse":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_audio_pulse_payload(server.ctx, body),
                    )
                    return
                if parsed.path == "/api/router/evaluate":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_router_evaluation_payload(server.ctx, body),
                    )
                    return
                if parsed.path == "/api/prime-architect/manifest":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_prime_architect_payload(server.ctx),
                    )
                    return
                if parsed.path == "/api/prime-architect/approve-selected":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_prime_architect_action_payload(server.ctx, "approve_selected", body),
                    )
                    return
                if parsed.path == "/api/prime-architect/trace":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_prime_architect_action_payload(server.ctx, "trace", body),
                    )
                    return
                if parsed.path == "/api/prime-architect/replay":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_prime_architect_action_payload(server.ctx, "replay", body),
                    )
                    return
                if parsed.path == "/api/ulx/compile":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_ulx_compile_payload(server.ctx, body),
                    )
                    return
                if parsed.path == "/api/ulx/run":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_ulx_run_payload(server.ctx, body),
                    )
                    return
                if parsed.path == "/api/ulx/trace":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_ulx_trace_payload(server.ctx, body),
                    )
                    return
                if parsed.path == "/api/ulx/snapshot":
                    server._send_json(
                        self,
                        HTTPStatus.OK,
                        build_ulx_snapshot_payload(server.ctx, body),
                    )
                    return
                server._send_error(self, HTTPStatus.NOT_FOUND, "unknown endpoint")

            def _read_json_body(self) -> dict[str, Any]:
                content_length = int(self.headers.get("Content-Length", "0"))
                if content_length <= 0:
                    return {}
                raw = self.rfile.read(content_length)
                if not raw:
                    return {}
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except json.JSONDecodeError:
                    return {}
                return payload if isinstance(payload, dict) else {}

        return Handler

    def _send_json(self, handler: BaseHTTPRequestHandler, status: HTTPStatus, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        handler.send_response(status)
        self._set_cors_headers(handler)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(encoded)))
        handler.end_headers()
        handler.wfile.write(encoded)

    def _send_error(self, handler: BaseHTTPRequestHandler, status: HTTPStatus, message: str) -> None:
        self._send_json(handler, status, {"error": message, "status": int(status)})

    def _set_cors_headers(self, handler: BaseHTTPRequestHandler) -> None:
        handler.send_header("Access-Control-Allow-Origin", "*")
        handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        handler.send_header("Access-Control-Allow-Headers", "Content-Type")
