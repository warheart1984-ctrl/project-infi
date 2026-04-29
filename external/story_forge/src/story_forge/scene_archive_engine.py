from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from story_forge.engine_adapter.scene_archive_runtime import (
    SceneArchiveEngineConfig,
    SceneArchiveEngineModule,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Story Forge scene archive engine.")
    parser.add_argument(
        "--runtime-root",
        default=None,
        help="Optional runtime root directory for scene archive artifacts.",
    )
    parser.add_argument(
        "--capture-root",
        default=None,
        help="Optional capture root directory for scene archive captures.",
    )
    parser.add_argument(
        "--score-step-base",
        type=int,
        default=6,
        help="Base narrative score delta for each runtime step.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    module = SceneArchiveEngineModule(
        SceneArchiveEngineConfig(
            root_dir=args.runtime_root,
            capture_root=args.capture_root,
            score_step_base=args.score_step_base,
        )
    )

    try:
        request = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print(json.dumps(_error("InputError", "Scene archive engine input must be valid JSON.")))
        return 0

    if not isinstance(request, dict):
        print(json.dumps(_error("InputError", "Scene archive engine input must be a JSON object.")))
        return 0

    action = str(request.get("action", "")).strip()
    payload = request.get("payload", {})
    if not isinstance(payload, dict):
        print(json.dumps(_error("InputError", "Scene archive engine payload must be a JSON object.")))
        return 0

    result = _dispatch(module, action, payload)
    print(json.dumps(result))
    return 0


def _dispatch(module: SceneArchiveEngineModule, action: str, payload: dict[str, Any]) -> dict[str, Any]:
    if action == "scene_build":
        return module.scene_build(
            payload.get("layout_graph", {}),
            payload.get("geometry_registry", {}),
            payload.get("render_style", {}),
        )
    if action == "runtime_bind":
        return module.runtime_bind(
            payload.get("scene_graph_handle", ""),
            payload.get("gameplay_hooks", {}),
        )
    if action == "runtime_step":
        return module.runtime_step(
            payload.get("scene_graph_handle", ""),
            payload.get("game_systems", {}),
            payload.get("game_state", {}),
        )
    if action == "capture":
        return module.capture(
            payload.get("scene_graph_handle", ""),
            payload.get("event", {}),
        )
    return _error("InputError", f"Unsupported scene archive engine action '{action}'.")


def _error(error_type: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "module": "engine",
        "error_type": error_type,
        "message": message,
        "details": {},
    }


if __name__ == "__main__":
    raise SystemExit(main())
