"""
killswitch_init.py — Wire the kill switch into AAIS at startup.

Call init_kill_switch() once when AAIS boots.
After that, any component can call get_kill_switch() to access it.
"""

from __future__ import annotations

from emergency_stop import get_kill_switch
from hooks import (
    EvolutionEngineHook,
    MemorySpineHook,
    SessionStateHook,
    GodBrainHook,
    LLMConnectionHook,
)


# ---------------------------------------------------------------------------
# Component handles — keep references so you can query them later
# ---------------------------------------------------------------------------

evolution_hook = EvolutionEngineHook()
memory_hook    = MemorySpineHook()
session_hook   = SessionStateHook()
god_brain_hook = GodBrainHook()
llm_hook       = LLMConnectionHook()


def init_kill_switch(engine=None, session_store: dict | None = None) -> None:
    """
    Wire all AAIS components into the kill switch.
    Call once at system startup, before any evolution or LLM calls.
    """
    ks = get_kill_switch()

    # Attach the real evolution engine if available
    if engine:
        evolution_hook.engine = engine

    # Attach the real session store if available
    if session_store:
        session_hook.session_store = session_store

    ks.register_hook(
        "evolution_engine",
        on_pause = evolution_hook.on_pause,
        on_stop  = evolution_hook.on_stop,
        on_kill  = evolution_hook.on_kill,
    )

    ks.register_hook(
        "memory_spine",
        on_pause = memory_hook.on_pause,
        on_stop  = memory_hook.on_stop,
        on_kill  = memory_hook.on_kill,
    )

    ks.register_hook(
        "session_state",
        on_pause = session_hook.on_pause,
        on_stop  = session_hook.on_stop,
        on_kill  = session_hook.on_kill,
    )

    ks.register_hook(
        "god_brain",
        on_pause = god_brain_hook.on_pause,
        on_stop  = god_brain_hook.on_stop,
        on_kill  = god_brain_hook.on_kill,
    )

    ks.register_hook(
        "llm_connection",
        on_pause = llm_hook.on_pause,
        on_stop  = llm_hook.on_stop,
        on_kill  = llm_hook.on_kill,
    )

    print("[AAIS] Kill switch initialized. Components registered:")
    for name in ks._hooks:
        print(f"  ✓ {name}")
    print()
    print("  Commands:")
    print("  ks.pause('reason')  — freeze, resumable")
    print("  ks.stop('reason')   — clean shutdown")
    print("  ks.kill('reason')   — hard terminate")
    print("  ks.resume()         — resume from pause")


# ---------------------------------------------------------------------------
# CLI — run directly for emergency control
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    ks = get_kill_switch()
    init_kill_switch()

    if len(sys.argv) < 2:
        print("Usage: python killswitch_init.py [pause|stop|kill|resume] [reason]")
        sys.exit(0)

    cmd    = sys.argv[1].lower()
    reason = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "CLI command"

    if cmd == "pause":
        ks.pause(reason)
    elif cmd == "stop":
        ks.stop(reason)
    elif cmd == "kill":
        ks.kill(reason)
    elif cmd == "resume":
        ks.resume()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
