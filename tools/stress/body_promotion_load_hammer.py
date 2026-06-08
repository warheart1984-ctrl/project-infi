#!/usr/bin/env python
"""Body promotion load hammer — Stage 19 SLO for civilizational + FCE observe paths."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DEFAULT_BASE = "http://127.0.0.1:8000"
PROMOTION_ROUTES = [
    ("GET", "/legacy_api/api/operator/civilizations"),
    ("GET", "/legacy_api/api/operator/federated-epochs"),
    ("POST", "/legacy_api/api/operator/civilizations/observe", {"session_id": "load", "window_days": 7}),
    ("POST", "/legacy_api/api/operator/federated-epochs/observe", {"session_id": "load", "window_days": 7}),
]

# Stage 19 load SLO (local pilot; tighten for production federation-live)
P95_MS_SLO = 2500
ERROR_RATE_SLO = 0.05


def _one_probe(base: str, method: str, path: str, payload: dict | None) -> tuple[float, int | None]:
    url = f"{base.rstrip('/')}{path}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            _ = resp.read()
            elapsed_ms = (time.perf_counter() - start) * 1000
            return elapsed_ms, resp.status
    except urllib.error.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return elapsed_ms, exc.code
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return elapsed_ms, None


def run_load_hammer(*, base: str, rounds: int, workers: int) -> dict:
    latencies: list[float] = []
    errors = 0
    total = 0
    tasks: list[tuple[str, str, dict | None]] = []
    for _ in range(rounds):
        for method, path, *rest in PROMOTION_ROUTES:
            payload = rest[0] if rest else None
            tasks.append((method, path, payload))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_one_probe, base, m, p, pl) for m, p, pl in tasks]
        for fut in as_completed(futures):
            ms, status = fut.result()
            latencies.append(ms)
            total += 1
            if status is None or status >= 500:
                errors += 1

    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies, default=0)
    error_rate = errors / total if total else 1.0
    slo_ok = p95 <= P95_MS_SLO and error_rate <= ERROR_RATE_SLO
    return {
        "base": base,
        "rounds_per_route": rounds,
        "workers": workers,
        "total_probes": total,
        "errors": errors,
        "error_rate": round(error_rate, 4),
        "latency_ms": {
            "p50": round(statistics.median(latencies), 2) if latencies else None,
            "p95": round(p95, 2),
            "max": round(max(latencies, default=0), 2),
        },
        "slo": {
            "p95_ms_max": P95_MS_SLO,
            "error_rate_max": ERROR_RATE_SLO,
            "passed": slo_ok,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args(argv)

    summary = run_load_hammer(base=args.base, rounds=args.rounds, workers=args.workers)
    out = ROOT / "ci-artifacts" / "body_promotion_load_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Report: {out}")
    return 0 if summary["slo"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
