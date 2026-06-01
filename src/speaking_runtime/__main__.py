"""CLI: python -m src.speaking_runtime \"your question\""""

from __future__ import annotations

import argparse
import json
import sys

from src.speaking_runtime import (
    DEFAULT_SYSTEM_PROMPT_EXPORT,
    SpeakingRuntimeSession,
    build_system_prompt,
    export_system_prompt_file,
    run_speaking_turn,
    speaking_runtime_spec,
    validate_reply,
)


def _placeholder_speak(session: SpeakingRuntimeSession) -> str:
    return (
        "This CLI scaffolds the Speaking Runtime without calling a model provider. "
        f"Frame kind: {session.frame_kind}. Goal: {session.goal}. "
        "For a full answer, use Jarvis with `speaking_runtime: true` in the chat request, "
        "or pass this turn to your model with the exported system prompt."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run or inspect the Speaking Runtime governed loop.",
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="User question to scaffold through Listen → Frame → Plan → Speak → Check.",
    )
    parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Print the canonical system prompt and exit.",
    )
    parser.add_argument(
        "--export-prompt",
        nargs="?",
        const=str(DEFAULT_SYSTEM_PROMPT_EXPORT),
        metavar="PATH",
        help="Write the system prompt to PATH (default: docs/runtime/SPEAKING_RUNTIME_SYSTEM_PROMPT.txt).",
    )
    parser.add_argument(
        "--spec",
        action="store_true",
        help="Print the speaking runtime JSON spec.",
    )
    parser.add_argument(
        "--validate",
        metavar="FILE",
        help="Validate a reply file against speaking-runtime invariants.",
    )
    args = parser.parse_args(argv)

    if args.export_prompt is not None:
        path = export_system_prompt_file(args.export_prompt)
        print(path)
        return 0

    if args.prompt_only:
        print(build_system_prompt())
        return 0

    if args.spec:
        print(json.dumps(speaking_runtime_spec(), indent=2))
        return 0

    if args.validate:
        text = open(args.validate, encoding="utf-8").read()
        print(json.dumps(validate_reply(text), indent=2))
        return 0

    if not args.question:
        parser.error("question is required unless --prompt-only, --export-prompt, --spec, or --validate is used")

    reply, session = run_speaking_turn(args.question, _placeholder_speak)
    print(reply)
    if not sys.stdout.isatty():
        return 0
    print("\n--- trace ---", file=sys.stderr)
    print(json.dumps(session.to_dict(), indent=2), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
