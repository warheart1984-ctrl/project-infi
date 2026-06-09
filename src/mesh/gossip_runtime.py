"""Gossip daemon lifecycle, per-peer backoff, and health snapshots."""

from __future__ import annotations

import atexit
import random
import threading
import time
from datetime import datetime, timezone

_BACKOFF: dict[str, dict] = {}
_LAST_RUN: dict[str, float] = {}
_LAST_RESULTS: list[dict] = []
_DAEMON_STOP = threading.Event()
_DAEMON_THREAD: threading.Thread | None = None
_LOCK = threading.Lock()

_INITIAL_BACKOFF_SEC = 5.0
_MAX_BACKOFF_SEC = 300.0


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_gossip_run(results: list[dict], base_key: str) -> None:
    with _LOCK:
        _LAST_RUN[base_key] = time.monotonic()
        _LAST_RESULTS[:] = list(results)
        for item in results:
            url = str(item.get("peer") or "")
            if not url:
                continue
            state = _BACKOFF.setdefault(url, {"failures": 0, "until": 0.0})
            if item.get("ok"):
                state["failures"] = 0
                state["until"] = 0.0
            else:
                state["failures"] = int(state.get("failures") or 0) + 1
                delay = min(
                    _MAX_BACKOFF_SEC,
                    _INITIAL_BACKOFF_SEC * (2 ** (state["failures"] - 1)),
                )
                jitter = random.uniform(0, delay * 0.2)
                state["until"] = time.monotonic() + delay + jitter


def is_peer_in_backoff(peer_url: str) -> bool:
    state = _BACKOFF.get(peer_url.rstrip("/"))
    if not state:
        return False
    return time.monotonic() < float(state.get("until") or 0)


def backoff_snapshot() -> dict[str, dict]:
    now = time.monotonic()
    out: dict[str, dict] = {}
    for url, state in _BACKOFF.items():
        until = float(state.get("until") or 0)
        out[url] = {
            "failures": int(state.get("failures") or 0),
            "in_backoff": now < until,
            "backoff_until_sec": max(0.0, until - now) if now < until else 0.0,
        }
    return out


def gossip_health_snapshot(base_key: str, *, daemon_alive: bool) -> dict:
    with _LOCK:
        last = _LAST_RUN.get(base_key)
        return {
            "gossip_daemon_alive": daemon_alive,
            "last_gossip_run_at": _utc_now_iso() if last else None,
            "last_results_count": len(_LAST_RESULTS),
            "peer_backoff": backoff_snapshot(),
        }


def start_gossip_daemon(base_dir: str, identity_fn, config_fn, gossip_all_fn) -> None:
    global _DAEMON_THREAD
    config = config_fn()
    interval = int(config.get("gossip_interval_sec") or 0)
    if interval <= 0:
        return
    if _DAEMON_THREAD and _DAEMON_THREAD.is_alive():
        return

    base_key = str(base_dir)

    def _loop() -> None:
        while not _DAEMON_STOP.is_set():
            if _DAEMON_STOP.wait(interval):
                break
            try:
                results = gossip_all_fn(base_dir, identity_fn(), config_fn())
                record_gossip_run(results, base_key)
            except Exception:
                record_gossip_run([{"ok": False, "peer": "*", "error": "gossip_all_failed"}], base_key)

    _DAEMON_THREAD = threading.Thread(target=_loop, daemon=True, name="mesh-gossip-daemon")
    _DAEMON_THREAD.start()
    atexit.register(stop_gossip_daemon)


def stop_gossip_daemon() -> None:
    _DAEMON_STOP.set()
