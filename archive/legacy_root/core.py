"""
core.py — LLM wrapper + divine_core orchestrator + angel router
"""

import os
import uuid
import requests
from dotenv import load_dotenv

from memory import load_memory, save_memory, add_scene, update_character_emotions
from canon import CANON
from angels import (
    lore_angel, continuity_angel, emotion_angel,
    combat_angel, tone_angel, dialogue_angel, pacing_angel,
)

load_dotenv()

API_URL    = os.getenv("LLM_API_URL")
MODEL_NAME = os.getenv("LLM_MODEL_NAME")
API_KEY    = os.getenv("LLM_API_KEY")  # optional


# ---------------------------------------------------------------------------
# LLM wrapper — works with Ollama, LM Studio, Groq, Together, any OpenAI-
# compatible endpoint.  Just set the right values in .env
# ---------------------------------------------------------------------------

def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Single-turn chat-completion call.
    Handles both Ollama's response shape and the OpenAI-style shape.
    """
    if not API_URL:
        raise RuntimeError(
            "LLM_API_URL is not set. Copy .env.example to .env and fill it in."
        )

    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "stream": False,
    }

    response = requests.post(API_URL, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    data = response.json()

    # Ollama → {"message": {"content": "..."}}
    if "message" in data:
        return data["message"]["content"]

    # OpenAI-style → {"choices": [{"message": {"content": "..."}}]}
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Router — decides which angels are needed for a given prompt
# ---------------------------------------------------------------------------

ALL_ANGELS = [
    "DraftAngel",
    "LoreAngel",
    "CombatAngel",
    "DialogueAngel",
    "EmotionAngel",
    "ContinuityAngel",
    "PacingAngel",
    "ToneAngel",
]

def route_angels(user_prompt: str) -> list[str]:
    """
    Returns an ordered pipeline of angel names based on the prompt.
    DraftAngel is always first; ToneAngel always last.
    """
    up = user_prompt.lower()
    pipeline = ["DraftAngel", "LoreAngel"]

    if any(w in up for w in ["fight", "battle", "attack", "combat", "duel", "sword"]):
        pipeline.append("CombatAngel")

    pipeline.append("DialogueAngel")
    pipeline.append("EmotionAngel")
    pipeline.append("ContinuityAngel")
    pipeline.append("PacingAngel")
    pipeline.append("ToneAngel")

    return pipeline


# ---------------------------------------------------------------------------
# Divine Core — the orchestrator
# ---------------------------------------------------------------------------

def divine_core(
    user_prompt:    str,
    context:        str,
    location:       str = "Unknown",
    characters:     list[str] | None = None,
    debug_callback  = None,
) -> str:
    """
    Full pipeline:
      DraftAngel → LoreAngel → [CombatAngel] → DialogueAngel →
      EmotionAngel → ContinuityAngel → PacingAngel → ToneAngel

    debug_callback(msg: str) is called after each stage if provided
    (used by the GUI to show live angel logs).
    """
    if characters is None:
        characters = []

    def log(msg: str):
        if debug_callback:
            debug_callback(msg)

    log("[Core] Starting pipeline...")
    request_id = f"req-{uuid.uuid4()}"

    mem    = load_memory()
    style  = mem["style"]["tone"]
    banned = mem["style"]["banned_phrases"]
    motifs = mem["style"]["preferred_motifs"]

    pipeline = route_angels(user_prompt)
    log(f"[Router] Pipeline: {' → '.join(pipeline)}")

    # ── DraftAngel ──────────────────────────────────────────────────────────
    log("[DraftAngel] Generating raw draft...")
    draft_system = (
        "You are DraftAngel.\n\n"
        "Your job:\n"
        "- Continue the scene based ONLY on CONTEXT and PROMPT.\n"
        "- Produce raw narrative without polishing.\n"
        "- Do NOT enforce lore, tone, or continuity.\n"
        "- Do NOT explain your reasoning.\n\n"
        "Output:\nReturn ONLY the continuation text. No JSON. No commentary."
    )
    draft_user   = f"CONTEXT:\n{context}\n\nPROMPT:\n{user_prompt}"
    current_text = call_llm(draft_system, draft_user)
    log("[DraftAngel] Done.")

    # ── Sub-mind loop ────────────────────────────────────────────────────────
    for angel in pipeline[1:]:
        log(f"[{angel}] Running...")

        msg = {
            "envelope": {
                "request_id":   request_id,
                "sender":       "DivineCore",
                "receiver":     angel,
                "message_type": "Task",
            },
            "payload": {"input_text": current_text},
        }

        if angel == "LoreAngel":
            res = lore_angel(msg, CANON)

        elif angel == "ContinuityAngel":
            res = continuity_angel(msg)

        elif angel == "EmotionAngel":
            res = emotion_angel(msg, characters)
            # update emotional state in memory
            tags = res["payload"].get("emotion_tags", [])
            if tags:
                for name in characters:
                    mem = update_character_emotions(mem, name, tags)
                log(f"[EmotionAngel] Emotional state updated: {tags}")

        elif angel == "CombatAngel":
            res = combat_angel(msg, CANON)

        elif angel == "ToneAngel":
            res = tone_angel(msg, style, banned, motifs)

        elif angel == "DialogueAngel":
            res = dialogue_angel(msg)

        elif angel == "PacingAngel":
            res = pacing_angel(msg)

        else:
            continue

        revised = res["payload"].get("revised_text")
        if revised:
            current_text = revised

        log(f"[{angel}] Done.")

    # ── Persist scene to memory ──────────────────────────────────────────────
    mem = add_scene(mem, current_text, location, characters, summary=user_prompt)
    save_memory(mem)
    log("[Core] Memory updated.")

    return current_text
