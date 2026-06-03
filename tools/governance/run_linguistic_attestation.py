#!/usr/bin/env python3
"""CLI — build linguistic governance attestation digest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_governance_attestation_engine import (  # noqa: E402
    format_attestation_markdown,
    write_attestation,
)
from tools.linguistic_genome_lib import load_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Linguistic governance attestation")
    parser.add_argument("--markdown", action="store_true", help="Print operator summary")
    args = parser.parse_args()

    path = write_attestation(_ROOT)
    print(f"wrote {path.relative_to(_ROOT)}")

    if args.markdown:
        att = load_json(path)
        print()
        print(format_attestation_markdown(att))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
