#!/usr/bin/env python
"""
Cross-platform helper to start the optional AAIS contractors for local MVP/dev.

Usage examples:
    python scripts/start_contractors.py                  # start all three
    python scripts/start_contractors.py --forge --evolve # Forge + Evolve (skips ForgeEval)
    python scripts/start_contractors.py --all --no-fg    # start and exit (background)

Contractors:
  - Forge      :6060  (repo mutation / patch contractor)
  - ForgeEval  :6061  (evaluation service used by Evolve)
  - Evolve     :6062  (evolution / search contractor)

These are optional. Core AAIS (chat, OTEM, workflows) works without them.
When present, the capability bridge and evolve-engine status surfaces become live.

The script uses plain subprocess so it works on Windows without fragile pipes.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]


def _python() -> str:
    return sys.executable


def start_forge() -> subprocess.Popen:
    cmd = [
        _python(), "-m", "flask",
        "--app", "forge.main:app",
        "run",
        "--host", "127.0.0.1",
        "--port", "6060",
        "--no-reload",
    ]
    env = os.environ.copy()
    env["FLASK_ENV"] = env.get("FLASK_ENV", "development")
    p = subprocess.Popen(cmd, cwd=ROOT, env=env)
    print(f"[forge] started PID={p.pid}  http://127.0.0.1:6060/health")
    return p


def start_forge_eval() -> subprocess.Popen:
    cmd = [
        _python(), "-m", "flask",
        "--app", "forge_eval.main:app",
        "run",
        "--host", "127.0.0.1",
        "--port", "6061",
        "--no-reload",
    ]
    env = os.environ.copy()
    p = subprocess.Popen(cmd, cwd=ROOT, env=env)
    print(f"[forge_eval] started PID={p.pid}  http://127.0.0.1:6061/health")
    return p


def start_evolve() -> subprocess.Popen:
    cmd = [
        _python(), "-m", "flask",
        "--app", "evolve_engine.main:app",
        "run",
        "--host", "127.0.0.1",
        "--port", "6062",
        "--no-reload",
    ]
    env = os.environ.copy()
    # Evolve will default to looking for ForgeEval on 6061
    p = subprocess.Popen(cmd, cwd=ROOT, env=env)
    print(f"[evolve] started PID={p.pid}   http://127.0.0.1:6062/health")
    return p


def wait_for_health(url: str, timeout: float = 8.0) -> bool:
    import urllib.request
    import urllib.error

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as resp:
                if 200 <= resp.status < 500:
                    return True
        except Exception:
            pass
        time.sleep(0.4)
    return False


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start AAIS contractors (Forge, ForgeEval, Evolve).")
    parser.add_argument("--forge", action="store_true", help="Start Forge on :6060")
    parser.add_argument("--forge-eval", action="store_true", help="Start ForgeEval on :6061")
    parser.add_argument("--evolve", action="store_true", help="Start Evolve on :6062")
    parser.add_argument("--all", action="store_true", help="Start all three (default if none specified)")
    parser.add_argument("--no-wait", action="store_true", help="Do not wait for /health after start")
    parser.add_argument("--no-fg", action="store_true", help="Start and return immediately (background mode)")

    args = parser.parse_args(argv or sys.argv[1:])

    start_forge_flag = args.forge or args.all or not any([args.forge, args.forge_eval, args.evolve])
    start_fe_flag = args.forge_eval or args.all or not any([args.forge, args.forge_eval, args.evolve])
    start_evo_flag = args.evolve or args.all or not any([args.forge, args.forge_eval, args.evolve])

    procs: List[subprocess.Popen] = []

    if start_forge_flag:
        try:
            procs.append(start_forge())
        except Exception as exc:
            print(f"[forge] failed to start: {exc}")

    if start_fe_flag:
        try:
            procs.append(start_forge_eval())
        except Exception as exc:
            print(f"[forge_eval] failed to start: {exc}")

    if start_evo_flag:
        try:
            procs.append(start_evolve())
        except Exception as exc:
            print(f"[evolve] failed to start: {exc}")

    if not args.no_wait:
        print("\nWaiting for health endpoints (up to ~8s each)...")
        if start_forge_flag:
            wait_for_health("http://127.0.0.1:6060/health")
        if start_fe_flag:
            wait_for_health("http://127.0.0.1:6061/health")
        if start_evo_flag:
            wait_for_health("http://127.0.0.1:6062/health")

    print("\nContractors started. Use Ctrl-C or taskkill to stop.")
    print("Recommended for local MVP testing:")
    print("  python -m aais start --preset mock --no-browser")
    print("  python scripts/start_contractors.py")

    if args.no_fg:
        return 0

    # Keep the script alive so the child processes stay attached to this console on Windows.
    try:
        while True:
            time.sleep(1.0)
            # optional: could poll and restart, but for MVP keep simple
    except KeyboardInterrupt:
        print("\nShutting down contractors...")
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        time.sleep(0.5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
