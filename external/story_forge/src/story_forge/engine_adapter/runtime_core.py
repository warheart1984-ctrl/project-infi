from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from typing import Any

JsonDict = dict[str, Any]


def stable_hash(payload: object) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(serialized.encode("utf-8")).hexdigest()


def build_scene_payload(
    layout_graph: dict[str, Any],
    geometry_registry: dict[str, Any],
    render_style: dict[str, Any],
) -> JsonDict:
    build_signature = stable_hash(
        {
            "layout_graph": layout_graph,
            "geometry_registry": geometry_registry,
            "render_style": render_style,
        }
    )
    scene_graph_handle = f"scene_{build_signature[:12]}"
    return {
        "sceneGraphHandle": scene_graph_handle,
        "buildSignature": build_signature,
        "layoutGraph": deepcopy(layout_graph),
        "geometryRegistry": deepcopy(geometry_registry),
        "renderStyle": deepcopy(render_style),
        "nodeCount": len(layout_graph.get("nodes", [])),
        "geometryCount": len(geometry_registry),
    }


def build_runtime_bind_payload(
    scene: dict[str, Any],
    gameplay_hooks: dict[str, Any],
    *,
    system_prefix: str,
) -> JsonDict:
    systems = {
        "movement": f"{system_prefix}_traversal",
        "interaction": f"{system_prefix}_interaction",
        "thresholds": f"{system_prefix}_thresholds",
    }
    if gameplay_hooks:
        systems["gameplayHooks"] = deepcopy(gameplay_hooks)

    initial_state = {
        "status": "INIT",
        "meters": {
            "stability": max(0, 100 - (int(scene.get("nodeCount", 0)) * 2)),
            "wonder": min(100, 20 + (int(scene.get("geometryCount", 0)) * 5)),
        },
        "narrativeScore": 0,
        "tick": 0,
        "sceneGraphHandle": scene["sceneGraphHandle"],
        "transitions": [],
    }
    return {
        "systems": systems,
        "initialState": initial_state,
    }


def build_runtime_step_payload(
    scene: dict[str, Any],
    game_state: dict[str, Any],
    *,
    score_step_base: int,
    transition_type: str,
) -> tuple[JsonDict, JsonDict]:
    updated_game_state = deepcopy(game_state)
    previous_status = str(updated_game_state.get("status", "INIT") or "INIT")
    previous_tick = int(updated_game_state.get("tick", 0) or 0)
    previous_score = int(updated_game_state.get("narrativeScore", 0) or 0)
    next_tick = previous_tick + 1
    score_delta = int(score_step_base) + max(1, int(scene.get("nodeCount", 0)))
    next_status = "RUNNING" if previous_status == "INIT" else previous_status

    updated_game_state["status"] = next_status
    updated_game_state["tick"] = next_tick
    updated_game_state["sceneGraphHandle"] = scene["sceneGraphHandle"]
    updated_game_state["narrativeScore"] = previous_score + score_delta
    meters = deepcopy(updated_game_state.get("meters", {}))
    meters["stability"] = int(meters.get("stability", 100))
    meters["wonder"] = int(meters.get("wonder", 0))
    updated_game_state["meters"] = meters

    runtime_delta = {
        "transition_id": f"{scene['sceneGraphHandle']}:tick:{next_tick}",
        "transition_type": transition_type,
        "sceneGraphHandle": scene["sceneGraphHandle"],
        "previous_status": previous_status,
        "status": next_status,
        "tick": next_tick,
        "score_before": previous_score,
        "score_after": updated_game_state["narrativeScore"],
        "score_delta": score_delta,
    }
    transitions = list(updated_game_state.get("transitions", []))
    transitions.append(runtime_delta)
    updated_game_state["transitions"] = transitions[-12:]
    return updated_game_state, runtime_delta
