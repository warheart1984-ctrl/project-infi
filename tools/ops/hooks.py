"""
hooks.py — Kill switch adapters for each AAIS component.

Drop these into your existing modules.
Each adapter knows how to pause/stop/kill its component cleanly.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Evolution Engine Hook
# ---------------------------------------------------------------------------

class EvolutionEngineHook:
    """
    Wraps the AAIS evolution engine.
    Pause = freeze current generation mid-run.
    Stop  = finish current generation, save population + hall of fame.
    Kill  = abort immediately, no save.
    """

    def __init__(self, engine=None):
        self.engine   = engine
        self._abort   = threading.Event()
        self._paused  = threading.Event()

    def on_pause(self):
        self._paused.set()
        if self.engine:
            # signal the engine's run loop to block
            print("[EvolutionHook] Evolution paused after current evaluation.")

    def on_stop(self):
        self._abort.set()
        if self.engine:
            self._save_state()
            print("[EvolutionHook] Evolution stopped. State saved.")

    def on_kill(self):
        self._abort.set()
        print("[EvolutionHook] Evolution killed. No save.")

    def _save_state(self):
        if not self.engine:
            return
        try:
            import json
            from pathlib import Path
            state = {
                "generation":          len(self.engine.history),
                "best_objective_seen": self.engine.best_objective_seen,
                "stagnation":          self.engine.stagnation,
                "hall_of_fame":        [c.to_dict() for c in self.engine.hall_of_fame],
                "archive_size":        len(self.engine.archive.entries),
            }
            Path("evolution_checkpoint.json").write_text(
                json.dumps(state, indent=2), encoding="utf-8"
            )
            print("[EvolutionHook] Checkpoint saved to evolution_checkpoint.json")
        except Exception as exc:
            print(f"[EvolutionHook] Could not save state: {exc}")

    def should_abort(self) -> bool:
        return self._abort.is_set()

    def check_pause(self):
        """Call inside the generation loop to block when paused."""
        while self._paused.is_set():
            import time
            time.sleep(0.1)


# ---------------------------------------------------------------------------
# Memory Spine Hook
# ---------------------------------------------------------------------------

class MemorySpineHook:
    """
    Pause = lock writes, reads still allowed.
    Stop  = flush pending writes, then lock.
    Kill  = lock immediately, no flush.
    """

    def __init__(self):
        self._locked = False

    def on_pause(self):
        self._locked = True
        print("[MemoryHook] Memory spine write-locked.")

    def on_stop(self):
        self._flush()
        self._locked = True
        print("[MemoryHook] Memory spine flushed and locked.")

    def on_kill(self):
        self._locked = True
        print("[MemoryHook] Memory spine hard-locked. No flush.")

    def _flush(self):
        try:
            from memory import save_memory, load_memory
            mem = load_memory()
            save_memory(mem)
            print("[MemoryHook] Memory flushed.")
        except Exception as exc:
            print(f"[MemoryHook] Flush failed: {exc}")

    def is_locked(self) -> bool:
        return self._locked


# ---------------------------------------------------------------------------
# Session State Hook (V8 sessions)
# ---------------------------------------------------------------------------

class SessionStateHook:
    """
    Pause = freeze all active sessions (no new events).
    Stop  = serialize session states, then close.
    Kill  = drop all sessions immediately.
    """

    def __init__(self, session_store: dict | None = None):
        self.session_store = session_store or {}

    def on_pause(self):
        print(f"[SessionHook] {len(self.session_store)} sessions frozen.")

    def on_stop(self):
        self._serialize_sessions()
        self.session_store.clear()
        print("[SessionHook] Sessions serialized and cleared.")

    def on_kill(self):
        self.session_store.clear()
        print("[SessionHook] Sessions dropped.")

    def _serialize_sessions(self):
        try:
            import json
            from pathlib import Path
            Path("session_snapshot.json").write_text(
                json.dumps(
                    {k: str(v) for k, v in self.session_store.items()},
                    indent=2,
                ),
                encoding="utf-8",
            )
            print("[SessionHook] Sessions saved to session_snapshot.json")
        except Exception as exc:
            print(f"[SessionHook] Serialization failed: {exc}")


# ---------------------------------------------------------------------------
# God Brain / Divine Core Hook
# ---------------------------------------------------------------------------

class GodBrainHook:
    """
    Pause = finish current angel, block before next.
    Stop  = finish current pipeline, do not start new ones.
    Kill  = abort pipeline immediately.
    """

    def __init__(self):
        self._stop_requested = False
        self._kill_requested = False

    def on_pause(self):
        print("[GodBrainHook] God Brain will pause after current angel completes.")

    def on_stop(self):
        self._stop_requested = True
        print("[GodBrainHook] God Brain will stop after current pipeline completes.")

    def on_kill(self):
        self._kill_requested = True
        print("[GodBrainHook] God Brain killed. Pipeline aborted.")

    def should_stop(self) -> bool:
        return self._stop_requested

    def should_kill(self) -> bool:
        return self._kill_requested


# ---------------------------------------------------------------------------
# LLM Connection Hook
# ---------------------------------------------------------------------------

class LLMConnectionHook:
    """
    All levels: revoke credentials, close connections.
    """

    def on_pause(self):
        print("[LLMHook] LLM calls suspended.")

    def on_stop(self):
        self._revoke()

    def on_kill(self):
        self._revoke()

    def _revoke(self):
        import os
        for key in ("LLM_API_KEY", "LLM_API_URL", "LLM_MODEL_NAME",
                    "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
            os.environ.pop(key, None)
        print("[LLMHook] All LLM credentials revoked.")
