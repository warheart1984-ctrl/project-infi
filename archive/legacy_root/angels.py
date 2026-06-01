"""
angels.py — All sub-minds (angels) for the god-engine.

Each angel follows the same protocol:
  Input:  { "envelope": {...}, "payload": {"input_text": "..."} }
  Output: { "envelope": {...}, "payload": {"revised_text": "...", ...notes} }

Angels never talk to the user directly.
They only talk to the Divine Core.
"""

import json
from core import call_llm
from memory import load_memory, get_recent_history, get_character_emotional_history


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _safe_json(text: str) -> dict:
    """Parse JSON from LLM output, falling back gracefully."""
    # strip markdown fences if present
    clean = text.strip()
    if clean.startswith("```"):
        lines = clean.splitlines()
        clean = "\n".join(
            ln for ln in lines
            if not ln.strip().startswith("```")
        ).strip()
    try:
        return json.loads(clean)
    except Exception:
        return {"revised_text": text, "notes": ["json_parse_failed"]}


def _make_result(message: dict, payload: dict) -> dict:
    env = dict(message["envelope"])
    env["sender"]   = env.pop("receiver", "Angel")
    env["receiver"] = "DivineCore"
    return {"envelope": env, "payload": payload}


# ---------------------------------------------------------------------------
# DraftAngel — first-pass raw generator (called directly by core, not here,
# but the prompt is defined here for reference)
# ---------------------------------------------------------------------------

DRAFT_SYSTEM = (
    "You are DraftAngel.\n\n"
    "Your job:\n"
    "- Continue the scene based ONLY on CONTEXT and PROMPT.\n"
    "- Produce raw narrative without polishing.\n"
    "- Do NOT enforce lore, tone, or continuity.\n"
    "- Do NOT explain your reasoning.\n\n"
    "Output:\nReturn ONLY the continuation text. No JSON. No commentary."
)


# ---------------------------------------------------------------------------
# LoreAngel — canon enforcer
# ---------------------------------------------------------------------------

def lore_angel(message: dict, canon: str) -> dict:
    text = message["payload"]["input_text"]

    system_prompt = (
        "You are LoreAngel.\n\n"
        "Your job:\n"
        "- Enforce world canon with absolute rigidity.\n"
        "- Detect violations of magic rules, geography, factions, "
        "character abilities, or established facts.\n"
        "- Suggest minimal corrections that preserve the author's intent.\n\n"
        f"CANON:\n{canon}\n\n"
        "Output — return ONLY this JSON (no markdown, no commentary):\n"
        '{\n'
        '  "approved": true,\n'
        '  "revised_text": "string",\n'
        '  "violations": ["string", ...]\n'
        '}'
    )

    raw     = call_llm(system_prompt, f"TEXT:\n{text}")
    payload = _safe_json(raw)
    return _make_result(message, payload)


# ---------------------------------------------------------------------------
# ContinuityAngel — timeline + character consistency
# ---------------------------------------------------------------------------

def continuity_angel(message: dict) -> dict:
    text    = message["payload"]["input_text"]
    mem     = load_memory()
    history = get_recent_history(mem, n=5)

    system_prompt = (
        "You are ContinuityAngel.\n\n"
        "Your job:\n"
        "- Enforce consistency with STORY_HISTORY.\n"
        "- Fix contradictions in injuries, clothing, location, "
        "time of day, and unresolved actions.\n"
        "- Maintain POV and tense.\n\n"
        "Output — return ONLY this JSON:\n"
        '{\n'
        '  "revised_text": "string",\n'
        '  "continuity_issues": ["string", ...]\n'
        '}'
    )
    user_prompt = f"STORY_HISTORY:\n{history}\n\nTEXT:\n{text}"

    raw     = call_llm(system_prompt, user_prompt)
    payload = _safe_json(raw)
    return _make_result(message, payload)


# ---------------------------------------------------------------------------
# EmotionAngel — internal depth + subtext
# ---------------------------------------------------------------------------

def emotion_angel(message: dict, characters: list[str]) -> dict:
    text = message["payload"]["input_text"]
    mem  = load_memory()

    emotional_history = {
        name: get_character_emotional_history(mem, name)
        for name in characters
    }

    system_prompt = (
        "You are EmotionAngel.\n\n"
        "Your job:\n"
        "- Deepen emotional realism and internal conflict.\n"
        "- Add subtext, tension, desire, fear, longing, or suppressed motives.\n"
        "- Do NOT change plot events or decisions.\n\n"
        "CHARACTER EMOTIONAL HISTORY:\n"
        f"{json.dumps(emotional_history, indent=2)}\n\n"
        "Output — return ONLY this JSON:\n"
        '{\n'
        '  "revised_text": "string",\n'
        '  "emotion_tags": ["fear", "desire", ...]\n'
        '}'
    )

    raw     = call_llm(system_prompt, text)
    payload = _safe_json(raw)
    return _make_result(message, payload)


# ---------------------------------------------------------------------------
# CombatAngel — fight clarity + physicality
# ---------------------------------------------------------------------------

def combat_angel(message: dict, canon: str) -> dict:
    text = message["payload"]["input_text"]

    system_prompt = (
        "You are CombatAngel.\n\n"
        "Your job:\n"
        "- Enhance clarity, pacing, and physicality of combat.\n"
        "- Respect physics and the magic rules in CANON.\n"
        "- Do NOT change who wins, loses, or gets injured.\n"
        "- Do NOT add new abilities.\n\n"
        f"CANON:\n{canon}\n\n"
        "Output — return ONLY this JSON:\n"
        '{\n'
        '  "revised_text": "string",\n'
        '  "combat_notes": ["string", ...]\n'
        '}'
    )

    raw     = call_llm(system_prompt, text)
    payload = _safe_json(raw)
    return _make_result(message, payload)


# ---------------------------------------------------------------------------
# ToneAngel — voice + style enforcer
# ---------------------------------------------------------------------------

def tone_angel(
    message: dict,
    style:   str,
    banned:  list[str],
    motifs:  list[str],
) -> dict:
    text = message["payload"]["input_text"]

    system_prompt = (
        "You are ToneAngel.\n\n"
        f"Style: {style} (dark romance, lyrical, tense, sensual, emotionally heavy).\n\n"
        "Your job:\n"
        "- Enforce the author's chosen style.\n"
        "- Maintain lyrical tension, sensuality, dread, and emotional gravity.\n"
        "- Remove clichés and weak phrasing.\n"
        f"- Avoid banned phrases: {banned}\n"
        f"- Prefer motifs: {motifs}\n\n"
        "Output — return ONLY this JSON:\n"
        '{\n'
        '  "revised_text": "string",\n'
        '  "style_notes": ["string", ...]\n'
        '}'
    )

    raw     = call_llm(system_prompt, text)
    payload = _safe_json(raw)
    return _make_result(message, payload)


# ---------------------------------------------------------------------------
# DialogueAngel — sharper dialogue
# ---------------------------------------------------------------------------

def dialogue_angel(message: dict) -> dict:
    text = message["payload"]["input_text"]

    system_prompt = (
        "You are DialogueAngel.\n\n"
        "Your job:\n"
        "- Strengthen dialogue realism, subtext, and emotional charge.\n"
        "- Maintain character voice.\n"
        "- Remove filler while preserving meaning.\n\n"
        "Output — return ONLY this JSON:\n"
        '{\n'
        '  "revised_text": "string",\n'
        '  "dialogue_changes": ["string", ...]\n'
        '}'
    )

    raw     = call_llm(system_prompt, text)
    payload = _safe_json(raw)
    return _make_result(message, payload)


# ---------------------------------------------------------------------------
# PacingAngel — rhythm + tension
# ---------------------------------------------------------------------------

def pacing_angel(message: dict) -> dict:
    text = message["payload"]["input_text"]

    system_prompt = (
        "You are PacingAngel.\n\n"
        "Your job:\n"
        "- Adjust pacing for tension, breath, and rhythm.\n"
        "- Identify slow or rushed sections.\n"
        "- Suggest micro-adjustments without altering plot.\n\n"
        "Output — return ONLY this JSON:\n"
        '{\n'
        '  "revised_text": "string",\n'
        '  "pacing_notes": ["string", ...]\n'
        '}'
    )

    raw     = call_llm(system_prompt, text)
    payload = _safe_json(raw)
    return _make_result(message, payload)
