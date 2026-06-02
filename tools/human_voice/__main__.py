"""CLI inspect helper for Human Voice Extraction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.human_voice_extraction import extract_from_fixture


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect human voice extraction")
    parser.add_argument("--extraction-id", default="notes-demo-redacted", help="Fixture name")
    args = parser.parse_args()

    pack = extract_from_fixture(args.extraction_id)
    print(json.dumps({"extraction_id": pack["extraction_id"], "traits": pack["voice_profile"]["traits"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
