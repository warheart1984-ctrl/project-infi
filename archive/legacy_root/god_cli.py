"""
god_cli.py — Command-line interface for the god-engine.

Usage:
  python god_cli.py                    # text mode, context from memory
  python god_cli.py --docs DOC_ID      # pulls context from Google Doc
  python god_cli.py --voice            # voice input mode
  python god_cli.py --docs DOC_ID --voice --speak  # full voice pipeline
"""

import sys
import os
import time
import argparse

from core     import divine_core
from memory   import load_memory
from utils    import auto_detect_characters

# optional imports — fail gracefully
try:
    from gdocs import get_document_text, append_text
    GDOCS_AVAILABLE = True
except ImportError:
    GDOCS_AVAILABLE = False

try:
    from voice import speak as _speak
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    from stt import listen_once
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False


BANNER = r"""
===========================================
  THE FALLEN VEIL — GOD-ENGINE
===========================================
  Type your prompt and press Enter.
  Type 'voice' to speak your prompt.
  Type 'exit' or 'quit' to exit.
-------------------------------------------
"""


def stream_text(text: str, delay: float = 0.025) -> None:
    """Print text line-by-line with a small delay (fake streaming)."""
    for line in text.splitlines():
        print(line)
        time.sleep(delay)
    print()


def speak(text: str) -> None:
    if TTS_AVAILABLE:
        _speak(text)
    else:
        print("[TTS not available — install pyttsx3]")


def debug_print(msg: str) -> None:
    """Simple inline debug callback for CLI mode."""
    print(f"  {msg}")


def get_context(doc_id: str | None, mem: dict) -> str:
    if doc_id and GDOCS_AVAILABLE:
        print("[Pulling context from Google Doc...]")
        try:
            full_text = get_document_text(doc_id)
            return full_text[-4000:]
        except Exception as e:
            print(f"[Google Docs error: {e} — falling back to memory]")

    scenes = mem["timeline"]["scenes"]
    if scenes:
        return "".join(s["text_excerpt"] for s in scenes[-5:])
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Fallen Veil God-Engine CLI")
    parser.add_argument("--docs",  metavar="DOC_ID", help="Google Doc ID for context")
    parser.add_argument("--voice", action="store_true", help="Enable voice input")
    parser.add_argument("--speak", action="store_true", help="Enable voice output (TTS)")
    args = parser.parse_args()

    print(BANNER)

    while True:
        raw = input("\nYou> ").strip()

        if raw.lower() in ("exit", "quit", "q"):
            print("Exiting god-engine.")
            break

        # ── get prompt ──────────────────────────────────────────────────────
        if raw.lower() == "voice" or args.voice:
            if not STT_AVAILABLE:
                print("[STT not available — install SpeechRecognition + pyaudio]")
                continue
            user_prompt = listen_once()
            if not user_prompt:
                continue
            print(f"You (voice)> {user_prompt}")
        else:
            user_prompt = raw

        if not user_prompt:
            continue

        # ── build context ───────────────────────────────────────────────────
        mem        = load_memory()
        context    = get_context(args.docs, mem)
        characters = auto_detect_characters(context)

        print(f"\n[Characters detected: {characters}]")
        print("[God-Engine is thinking...]\n")

        # ── run engine ──────────────────────────────────────────────────────
        result = divine_core(
            user_prompt   = user_prompt,
            context       = context,
            location      = "Unknown",
            characters    = characters,
            debug_callback= debug_print,
        )

        print("\nGod-Engine>\n")
        stream_text(result)
        print("-------------------------------------------")

        # ── optionally append to Google Doc ─────────────────────────────────
        if args.docs and GDOCS_AVAILABLE:
            try:
                append_text(args.docs, result)
                print("[Scene appended to Google Doc]")
            except Exception as e:
                print(f"[Could not append to doc: {e}]")

        # ── optionally speak ─────────────────────────────────────────────────
        if args.speak:
            speak(result)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting god-engine.")
        sys.exit(0)
