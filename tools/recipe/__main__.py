"""CLI inspect helper for Recipe Module packs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.recipe_module import draft_mission_fields, evaluate_gates, load_recipe_by_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect governed recipe packs")
    parser.add_argument("--recipe-id", required=True, help="Recipe pack id (e.g. onboarding-v1)")
    parser.add_argument("--signoff-ack", action="store_true", help="Simulate human signoff ack")
    args = parser.parse_args()

    pack = load_recipe_by_id(args.recipe_id)
    gate_result = evaluate_gates(pack, {"signoff_ack": args.signoff_ack})
    payload = {
        "recipe_id": pack.get("recipe_id"),
        "claim_label": pack.get("claim_label"),
        "gates": gate_result,
        "mission_draft": draft_mission_fields(pack),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if gate_result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
