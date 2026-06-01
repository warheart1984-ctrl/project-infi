#!/usr/bin/env python3
"""AAIS-UL diagnostic toolkit entrypoint."""

from __future__ import annotations

import sys

from tools.ul import api_check, drift, probe, scan, smoke

COMMANDS = {
    "probe": probe.main,
    "scan": scan.main,
    "drift": drift.main,
    "smoke": smoke.main,
    "api-check": api_check.main,
}


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in {"-h", "--help"}:
        _print_help()
        return 0 if args and args[0] in {"-h", "--help"} else 2

    command = args[0]
    handler = COMMANDS.get(command)
    if handler is None:
        print(f"ul toolkit: unknown command {command!r}")
        _print_help()
        return 2
    return handler(args[1:])


def _print_help() -> None:
    print(
        "\n".join(
            [
                "AAIS-UL toolkit",
                "",
                "Usage:",
                "  python -m tools.ul probe [--file PATH | --json TEXT] [--wrap]",
                "  python -m tools.ul scan [--paths src ...] [--min-returns N]",
                "  python -m tools.ul drift",
                "  python -m tools.ul smoke [--no-pytest] [--no-wrap]",
                "  python -m tools.ul api-check [--base-url URL]",
                "",
                "Examples:",
                "  python -m tools.ul probe --file tools/ul/fixtures/forge_contractor_ok.json --wrap",
                "  python -m tools.ul scan --paths src",
                "  python -m tools.ul smoke",
            ]
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
