"""Promote a governed Jarvis LoRA adapter after eval_passed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.jarvis_lora_promotion_store import get_adapter, promote_adapter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, help="Adapter run_id UUID.")
    parser.add_argument(
        "--promoted-by",
        default="operator",
        help="Operator identity recorded in promotion_record.",
    )
    parser.add_argument(
        "--print-env",
        action="store_true",
        help="Print promotion env block after successful promotion.",
    )
    args = parser.parse_args()

    existing = get_adapter(args.run_id)
    if not existing:
        raise SystemExit(f"Adapter not found for run_id={args.run_id}")

    result = promote_adapter(args.run_id, promoted_by=args.promoted_by)
    print(json.dumps(result, indent=2))

    if args.print_env:
        print("\n# Promotion env")
        for key, value in result["promotion_env"].items():
            print(f'$env:{key}="{value}"')


if __name__ == "__main__":
    main()
