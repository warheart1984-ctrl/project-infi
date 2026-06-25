#!/usr/bin/env python3
"""
verify_alpha_cycle.py

Run the Alpha cryptographic verification invariant on a PEL record + claim:

  recomputed_hash(pel.raw) == pel.primary_hash

Exit codes:
  0 = verified
  1 = failed or error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.cori.pel.models import Claim, PELRecord  # noqa: E402
from src.cori.pel.pel_verify import verify_pel_record  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Alpha PEL record + claim verifier")
    parser.add_argument("--pel", type=str, required=True, help="Path to PELRecord JSON")
    parser.add_argument("--claim", type=str, required=True, help="Path to Claim JSON")
    parser.add_argument("--json", action="store_true", help="Output VerificationRecord as JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    pel = PELRecord.model_validate_json(Path(args.pel).read_text(encoding="utf-8"))
    claim = Claim.model_validate_json(Path(args.claim).read_text(encoding="utf-8"))
    verif = verify_pel_record(pel, claim)

    if args.json:
        print(json.dumps(verif.model_dump(mode="json"), indent=2))
    else:
        print(f"[ALPHA] {verif.status.upper()}: {verif.details.get('message', '')}")

    return 0 if verif.status == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
