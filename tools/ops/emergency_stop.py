"""
emergency_stop.py — AAIS Hard Kill Switch
Three levels: PAUSE / STOP / KILL
"""

from __future__ import annotations

import json
import logging
import os
import signal
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable

logger = logging.getLogger("aais.killswitch")


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class StopLevel(Enum):
    PAUSE = "pause"   # freeze evolution, keep state, resumable
    STOP  = "stop"    # clean shutdown, save everything
    KILL  = "kill"    # hard stop, no saves, full termination


@dataclass
class KillSwitchState:
    level:      StopLevel | None = None
    triggered:  bool             = False
    timestamp:  str              = ""
    reason:     str              = ""
    log:        list[str]        = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "level":     self.level.value if self.level else None,
            "triggered": self.triggered,
            "timestamp": self.timestamp,
            "reason":    self.reason,
            "log":       self.log,
        }


# ---------------------------------------------------------------------------
# Kill Switch
# ---------------------------------------------------------------------------

class AAISKillSwitch:
    """
    Central kill switch for AAIS.

    Usage:
        ks = AAISKillSwitch()
        ks.register_hook("evolution_engine", my_pause_fn, my_stop_fn, my_kill_fn)

        # Later:
        ks.pause("Too many stagnation cycles")
        ks.stop("Operator request")
        ks.kill("EMERGENCY")
    """

    _instance: "AAISKillSwitch | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "AAISKillSwitch":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialised = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialised:
            return
        self._initialised = True

        self.state       = KillSwitchState()
        self._hooks:     dict[str, dict[str, Callable]] = {}
        self._log_path   = Path("aais_emergency_log.json")
        self._paused     = threading.Event()
        self._paused.set()   # not paused by default

        # Register OS signals so Ctrl-C triggers a clean STOP
        signal.signal(signal.SIGINT,  self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    # ── Registration ────────────────────────────────────────────────────────

    def register_hook(
        self,
        name:      str,
        on_pause:  Callable | None = None,
        on_stop:   Callable | None = None,
        on_kill:   Callable | None = None,
    ) -> None:
        """Register a component so it receives stop signals."""
        self._hooks[name] = {
            "pause": on_pause or (lambda: None),
            "stop":  on_stop  or (lambda: None),
            "kill":  on_kill  or (lambda: None),
        }
        self._log(f"[KillSwitch] Registered component: {name}")

    # ── Public API ───────────────────────────────────────────────────────────

    def pause(self, reason: str = "") -> None:
        """Freeze evolution. Keeps all state. Resumable."""
        if self.state.triggered and self.state.level in (StopLevel.STOP, StopLevel.KILL):
            self._log("[KillSwitch] Already at a higher stop level. Ignoring PAUSE.")
            return

        self._log(f"[KillSwitch] ⏸  PAUSE triggered — {reason}")
        self._set_state(StopLevel.PAUSE, reason)
        self._paused.clear()
        self._run_hooks("pause")
        self._write_log()

    def resume(self) -> None:
        """Resume from PAUSE."""
        if self.state.level != StopLevel.PAUSE:
            self._log("[KillSwitch] Cannot resume — not in PAUSE state.")
            return

        self._log("[KillSwitch] ▶  Resuming from PAUSE.")
        self.state.triggered = False
        self.state.level     = None
        self._paused.set()
        self._write_log()

    def stop(self, reason: str = "") -> None:
        """Clean shutdown. Saves all state before stopping."""
        self._log(f"[KillSwitch] 🛑  STOP triggered — {reason}")
        self._set_state(StopLevel.STOP, reason)
        self._paused.clear()
        self._run_hooks("stop")
        self._revoke_llm_access()
        self._write_log()

    def kill(self, reason: str = "") -> None:
        """Hard stop. No saves. Full termination."""
        self._log(f"[KillSwitch] ☠  KILL triggered — {reason}")
        self._set_state(StopLevel.KILL, reason)
        self._paused.clear()
        self._run_hooks("kill")
        self._revoke_llm_access()
        self._write_emergency_log()   # best-effort write
        os._exit(1)                   # hard exit, no cleanup

    def is_paused(self) -> bool:
        return not self._paused.is_set()

    def wait_if_paused(self) -> None:
        """Call this in hot loops to block when paused."""
        self._paused.wait()

    # ── Internal ─────────────────────────────────────────────────────────────

    def _set_state(self, level: StopLevel, reason: str) -> None:
        self.state.level     = level
        self.state.triggered = True
        self.state.timestamp = datetime.now(timezone.utc).isoformat()
        self.state.reason    = reason

    def _run_hooks(self, action: str) -> None:
        for name, hooks in self._hooks.items():
            try:
                self._log(f"[KillSwitch] → {action} hook: {name}")
                hooks[action]()
            except Exception as exc:
                self._log(f"[KillSwitch] ⚠ Hook {name}/{action} raised: {exc}")

    def _revoke_llm_access(self) -> None:
        """Null out LLM credentials from environment."""
        for key in ("LLM_API_KEY", "LLM_API_URL", "LLM_MODEL_NAME"):
            os.environ.pop(key, None)
        self._log("[KillSwitch] LLM credentials revoked from environment.")

    def _log(self, msg: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        entry = f"{ts}  {msg}"
        self.state.log.append(entry)
        logger.info(msg)
        print(entry)

    def _write_log(self) -> None:
        try:
            self._log_path.write_text(
                json.dumps(self.state.to_dict(), indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            self._log(f"[KillSwitch] Could not write log: {exc}")

    def _write_emergency_log(self) -> None:
        """Best-effort write for KILL — can't trust normal I/O."""
        try:
            self._log_path.write_text(
                json.dumps(self.state.to_dict(), indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass   # nothing we can do in KILL path

    def _signal_handler(self, signum: int, frame) -> None:
        sig_name = signal.Signals(signum).name
        self._log(f"[KillSwitch] OS signal received: {sig_name}")
        self.stop(reason=f"OS signal {sig_name}")


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

def get_kill_switch() -> AAISKillSwitch:
    return AAISKillSwitch()
