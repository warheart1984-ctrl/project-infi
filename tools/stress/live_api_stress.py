#!/usr/bin/env python
"""
Live AAIS Stress Test Script (MVP plumbing verification tool)
- Hammers core health, 100+ subsystem status endpoints (the governed 'systems'),
- Chat session creation + messages (mock mode),
- Workflow surfaces,
- Concurrent load using threads + requests.

Run while the AAIS server is live:
  python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser
  python tools/stress/live_api_stress.py

This was created during the initial live stress session and is useful for
regression testing the legacy bridge, capability wiring, and subsystem surfaces.
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
import threading
import traceback
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import requests
except ImportError:
    print("requests not available; falling back to urllib")
    import urllib.request as urllibreq
    import urllib.error as urlliberr
    requests = None

BASE = os.environ.get("AAIS_STRESS_BASE", "http://127.0.0.1:8000")
LEGACY = f"{BASE}/legacy_api"
TIMEOUT = 15
CONCURRENCY = int(os.environ.get("AAIS_STRESS_CONC", "8"))
ITERATIONS = int(os.environ.get("AAIS_STRESS_ITERS", "3"))
RESULTS = defaultdict(list)
ERRORS = Counter()

SUBSYSTEM_STATUSES = [
    "/api/jarvis/capability-bridge/status",
    "/api/jarvis/ul-substrate/status",
    "/api/jarvis/safety-envelope/status",
    "/api/jarvis/adaptive-lanes/status",
    "/api/jarvis/coherence-fabric/status",
    "/api/jarvis/reflection-runtime/status",
    "/api/jarvis/memory-runtime/status",
    "/api/jarvis/continuity-witness/status",
    "/api/jarvis/narrative-continuity/status",
    "/api/jarvis/intent-agency/status",
    "/api/jarvis/phase-gate/status",
    "/api/jarvis/realtime-predictor/status",
    "/api/jarvis/invariant-engine/status",
    "/api/jarvis/verification-gate/status",
    "/api/jarvis/knowledge-authority/status",
    "/api/jarvis/scorpion-bridge/status",
    "/api/jarvis/mechanic-handoff/status",
    "/api/jarvis/forensic-triangulation/status",
    "/api/jarvis/immune-observe/status",
    "/api/jarvis/policy-gate/status",
    "/api/jarvis/predictor-immune-bridge/status",
    "/api/jarvis/cognitive-bridge/status",
    "/api/jarvis/governed-event-chain/status",
    "/api/jarvis/tracing-spine/status",
    "/api/jarvis/aris-boundary/status",
    "/api/jarvis/capability-module/status",
    "/api/jarvis/patchforge/status",
    "/api/jarvis/change-scope/status",
    "/api/jarvis/patch-verification/status",
    "/api/jarvis/otem-bounded/status",
    "/api/jarvis/direct-challenge/status",
    "/api/jarvis/orchestration-spine/status",
    "/api/jarvis/operator-health-sentinel/status",
    "/api/jarvis/governed-realtime-lane/status",
    "/api/jarvis/v8-runtime/status",
    "/api/jarvis/patch-apply/status",
    "/api/jarvis/patch-execution-preview/status",
    "/api/jarvis/run-ledger/status",
    "/api/jarvis/ul-lineage-console/status",
    "/api/jarvis/module-governance/status",
    "/api/jarvis/recipe-module/status",
    "/api/jarvis/imagine-generator/status",
    "/api/jarvis/story-forge-lane/status",
    "/api/jarvis/beatbox-lane/status",
    "/api/jarvis/speakers-lane/status",
    "/api/jarvis/human-voice-extraction/status",
    "/api/jarvis/story-forge-launcher/status",
    "/api/jarvis/movie-renderer-lane/status",
    "/api/jarvis/text-game-to-video/status",
    "/api/jarvis/game-front-door/status",
    "/api/jarvis/text-to-3d-world-lane/status",
    "/api/jarvis/world-pack-lane/status",
    "/api/jarvis/media-processor-bridge/status",
    "/api/jarvis/narrative-trust-pack/status",
    "/api/jarvis/document-vision/status",
    "/api/jarvis/ui-vision/status",
    "/api/jarvis/perception-gateway/status",
    "/api/jarvis/spatial-reasoning/status",
    "/api/jarvis/mystic-engine/status",
    "/api/jarvis/perception-lane/status",
    "/api/jarvis/route-choice/status",
    "/api/jarvis/specialist-route/status",
    "/api/jarvis/provider-route/status",
    "/api/jarvis/reasoning-executive/status",
    "/api/jarvis/attention/status",
    "/api/jarvis/coherence-projection/status",
    "/api/jarvis/deliberation/status",
    "/api/jarvis/planning/status",
    "/api/jarvis/cortex-arcs/status",
    "/api/jarvis/cognitive-execution/status",
    "/api/jarvis/speaking-runtime/status",
    "/api/jarvis/nova-face/status",
    "/api/jarvis/ai-factory/status",
    "/api/jarvis/cogos-runtime-bridge/status",
    "/api/jarvis/wolf-rehydration/status",
    "/api/jarvis/forge-contractor/status",
    "/api/jarvis/forge-eval/status",
    "/api/jarvis/evolve-engine/status",
    "/api/jarvis/slingshot/status",
    "/api/jarvis/operator-workbench/status",
    "/api/jarvis/workflow-shell/status",
    "/api/jarvis/jarvis-protocol/status",
    "/api/jarvis/reasoning-contract/status",
    "/api/jarvis/jarvis-reasoning-lane/status",
    "/api/jarvis/conversation-memory/status",
    "/api/jarvis/continuity-substrate/status",
    "/api/jarvis/jarvis-operator/status",
    "/api/jarvis/anti-drift/status",
    "/api/jarvis/prompt-assembly/status",
    "/api/jarvis/output-integrity/status",
    "/api/jarvis/project-infi-state-machine/status",
    "/api/jarvis/project-infi-law/status",
    "/api/jarvis/run-ledger-binding/status",
    "/api/jarvis/chat-turn-governance/status",
    "/api/jarvis/aais-ul-substrate/status",
    "/api/jarvis/aris-integration/status",
    "/api/jarvis/governance-layer/status",
    "/api/jarvis/security-protocol/status",
    "/api/jarvis/system-guard/status",
    # Additional from earlier waves / README
    "/api/jarvis/operator-profile/status",
    "/api/jarvis/memory-board/status",
    "/api/jarvis/pipeline/status",  # may 404 or need id
]

OPERATOR_SURFACES = [
    "/api/operator/ledger",
    "/api/operator/ledger/digest",
    "/api/operator/ledger/query",
    "/api/operator/plugins",
    "/api/operator/plugins/libraries",
    "/api/operator/plugins/workflows",
    "/api/operator/organs",
    "/api/operator/brain",
    "/api/operator/brain/sessions",
    "/api/operator/replay/operator_session/global/timeline",
    "/api/jarvis/operator-decision-ledger/status",
]


def discover_jarvis_status_paths() -> list[str]:
    """Harvest GET /api/jarvis/*/status routes from Flask url_map."""
    from src.api import app

    paths = sorted(
        {
            rule.rule
            for rule in app.url_map.iter_rules()
            if rule.rule.startswith("/api/jarvis/")
            and rule.rule.endswith("/status")
            and "GET" in (rule.methods or set())
        }
    )
    return paths or list(SUBSYSTEM_STATUSES)


def resolve_status_paths(*, auto_discover: bool = False) -> list[str]:
    if auto_discover or os.environ.get("AAIS_STRESS_AUTO_DISCOVER", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }:
        return discover_jarvis_status_paths()
    return list(SUBSYSTEM_STATUSES)


def _http_get(path: str) -> dict[str, Any]:
    url = f"{LEGACY}{path}" if path.startswith("/api/jarvis") else f"{BASE}{path}"
    start = time.time()
    try:
        if requests:
            r = requests.get(url, timeout=TIMEOUT)
            dur = time.time() - start
            return {"ok": r.status_code < 500, "status": r.status_code, "dur": dur, "len": len(r.text or "")}
        else:
            req = urllibreq.Request(url)
            with urllibreq.urlopen(req, timeout=TIMEOUT) as resp:
                body = resp.read()
                dur = time.time() - start
                return {"ok": resp.status < 500, "status": resp.status, "dur": dur, "len": len(body)}
    except Exception as e:
        dur = time.time() - start
        return {"ok": False, "error": str(e)[:200], "dur": dur}

def stress_endpoint(path: str, iters: int = 1) -> list[dict]:
    res = []
    for _ in range(iters):
        res.append(_http_get(path))
    return res

def create_chat_session() -> dict | None:
    url = f"{LEGACY}/api/chat/sessions"
    payload = {"system_prompt": "You are a stress-test Jarvis. Be terse."}
    try:
        if requests:
            r = requests.post(url, json=payload, timeout=TIMEOUT)
            if r.status_code < 300:
                return r.json()
        else:
            data = json.dumps(payload).encode()
            req = urllibreq.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllibreq.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read())
    except Exception as e:
        ERRORS["chat_session_create"] += 1
        return None

def send_chat_message(session_id: str, msg: str = "Summarize the current subsystem status in one sentence.") -> dict:
    url = f"{LEGACY}/api/chat/sessions/{session_id}/message"
    payload = {"message": msg, "response_mode": "operator"}
    start = time.time()
    try:
        if requests:
            r = requests.post(url, json=payload, timeout=TIMEOUT)
            dur = time.time() - start
            return {"ok": r.status_code < 500, "status": r.status_code, "dur": dur}
        else:
            data = json.dumps(payload).encode()
            req = urllibreq.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllibreq.urlopen(req, timeout=TIMEOUT) as resp:
                dur = time.time() - start
                return {"ok": resp.status < 500, "status": resp.status, "dur": dur}
    except Exception as e:
        dur = time.time() - start
        return {"ok": False, "error": str(e)[:150], "dur": dur}

def stress_chat_turns(n_sessions: int = 2, msgs_per: int = 2):
    for i in range(n_sessions):
        sess = create_chat_session()
        if not sess or "session_id" not in sess:
            continue
        sid = sess["session_id"]
        for _ in range(msgs_per):
            res = send_chat_message(sid)
            RESULTS["chat_message"].append(res)

def worker(paths: list[str], iters: int):
    for p in paths:
        try:
            res_list = stress_endpoint(p, iters)
            RESULTS[p].extend(res_list)
        except Exception:
            ERRORS[p] += 1
            traceback.print_exc(limit=1)

def run_stress(*, auto_discover: bool = False):
    print(f"AAIS Live Stress starting against {BASE}")
    print(f"Concurrency={CONCURRENCY} iters_per_endpoint={ITERATIONS}")
    start_all = time.time()

    status_paths = resolve_status_paths(auto_discover=auto_discover)

    # 1. Basic surfaces
    basic = ["/health", "/health/details", "/app", "/legacy_api/api/jarvis/providers"]
    for p in basic:
        RESULTS[p] = stress_endpoint(p, ITERATIONS * 2)

    # 1b. Operator product seam surfaces
    print(f"Stressing {len(OPERATOR_SURFACES)} operator endpoints...")
    for p in OPERATOR_SURFACES:
        RESULTS[p] = stress_endpoint(p, max(1, ITERATIONS))

    # 2. Subsystem status barrage (the "every system")
    print(f"Stressing {len(status_paths)} subsystem status endpoints...")
    chunk = max(1, len(status_paths) // CONCURRENCY)
    chunks = [status_paths[i:i+chunk] for i in range(0, len(status_paths), chunk)]

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = [ex.submit(worker, ch, ITERATIONS) for ch in chunks]
        for f in as_completed(futs):
            f.result()

    # 3. Chat stress (live mock turns)
    print("Stressing chat sessions + messages (mock)...")
    stress_chat_turns(n_sessions=max(2, CONCURRENCY//2), msgs_per=2)

    # 4. Workflow surfaces (light)
    wf_paths = ["/workflows/approvals", "/workflows/templates"]
    for p in wf_paths:
        RESULTS[p] = stress_endpoint(p, max(1, ITERATIONS//2))

    total_dur = time.time() - start_all

    # Summarize
    print("\n=== STRESS SUMMARY ===")
    ok_count = 0
    err_count = 0
    durs = []
    for k, lst in RESULTS.items():
        for item in lst:
            if item.get("ok"):
                ok_count += 1
            else:
                err_count += 1
            if "dur" in item:
                durs.append(item["dur"])
    avg = sum(durs)/len(durs) if durs else 0
    p95 = sorted(durs)[int(len(durs)*0.95)] if durs else 0

    print(f"Total requests recorded: {ok_count + err_count}")
    print(f"OK: {ok_count}  ERR/5xx: {err_count}")
    print(f"Avg latency: {avg*1000:.1f}ms  p95: {p95*1000:.1f}ms")
    print(f"Wall time: {total_dur:.1f}s")

    if ERRORS:
        print("Error counters:", dict(ERRORS))

    # Sample failing subsystems
    bad = []
    for k, lst in list(RESULTS.items()):
        fails = [x for x in lst if not x.get("ok")]
        if fails:
            bad.append((k, len(fails), fails[0].get("status") or fails[0].get("error")))
    if bad:
        print("\nSample failing or slow endpoints (first 10):")
        for b in bad[:10]:
            print("  ", b)

    # Write report
    report = {
        "base": BASE,
        "concurrency": CONCURRENCY,
        "iterations": ITERATIONS,
        "auto_discover": auto_discover or os.environ.get("AAIS_STRESS_AUTO_DISCOVER", "").strip().lower() in {
            "1",
            "true",
            "yes",
        },
        "status_endpoint_count": len(status_paths),
        "operator_endpoint_count": len(OPERATOR_SURFACES),
        "wall_sec": round(total_dur, 2),
        "total_requests": ok_count + err_count,
        "ok": ok_count,
        "err": err_count,
        "avg_latency_ms": round(avg * 1000, 1),
        "p95_latency_ms": round(p95 * 1000, 1),
        "errors": dict(ERRORS),
        "failing_samples": bad[:15],
    }
    out_path = os.path.join(os.getcwd(), "ci-artifacts", "live_stress_report.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport written to {out_path}")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AAIS live API stress harness")
    parser.add_argument(
        "--auto-discover",
        action="store_true",
        help="Harvest /api/jarvis/*/status routes from Flask url_map instead of static list",
    )
    args = parser.parse_args()
    run_stress(auto_discover=args.auto_discover)
