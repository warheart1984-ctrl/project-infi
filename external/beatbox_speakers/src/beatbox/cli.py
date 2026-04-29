"""Small CLI for running the BeatBox score lane from JSON input."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from beatbox.lanes.beatbox_lane import BeatboxLane
from beatbox.scene_state_builder import build_score_request_from_shot_list


def _load_json(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Input JSON must be an object.")
    return payload


def _score_command(input_path: str) -> int:
    payload = _load_json(input_path)
    shots = payload.get("shots")
    if not isinstance(shots, list):
        raise ValueError("Input JSON must include a 'shots' array.")

    request = build_score_request_from_shot_list(
        shots=shots,
        session_id=str(payload.get("session_id") or "beatbox_session"),
        scene_id=str(payload.get("scene_id") or "scene_001"),
        tone=str(payload.get("tone") or "dark_fantasy"),
        target=str(payload.get("target") or "movie"),
        output_path=str(payload.get("output_path") or ""),
    )

    result = BeatboxLane.from_env().score(request)
    print(
        json.dumps(
            {
                "ok": result.ok,
                "mode": result.mode,
                "error_type": result.error_type,
                "message": result.message,
                "details": result.details,
                "data": result.data.to_payload() if result.data else None,
            },
            indent=2,
        )
    )
    return 0 if result.ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BeatBox score mode from a shot-list JSON file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    score_parser = subparsers.add_parser("score", help="Score a shot-list JSON file.")
    score_parser.add_argument("input", help="Path to a JSON file containing session_id, scene_id, and shots.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "score":
        return _score_command(args.input)

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
