from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from story_forge.engine_adapter.base_module import (
    AAISEngineModule,
    InputValidationError,
    JsonDict,
)
from story_forge.engine_adapter.runtime_core import (
    build_runtime_bind_payload,
    build_runtime_step_payload,
    build_scene_payload,
    stable_hash,
)


def _default_capture_root() -> Path:
    return Path(__file__).resolve().parents[3] / ".runtime" / "text_to_3d_world" / "captures"


@dataclass(slots=True)
class DeterministicEngineConfig:
    capture_root: str | Path | None = None
    score_step_base: int = 6


class DeterministicEngineModule(AAISEngineModule):
    def __init__(
        self,
        config: DeterministicEngineConfig | None = None,
        *,
        logger=None,
    ) -> None:
        super().__init__(provider_name="deterministic_runtime", logger=logger)
        self.config = config or DeterministicEngineConfig()
        self.capture_root = (
            Path(self.config.capture_root)
            if self.config.capture_root is not None
            else _default_capture_root()
        )
        self.capture_root.mkdir(parents=True, exist_ok=True)
        self.active_scenes: dict[str, JsonDict] = {}

    def scene_build(
        self,
        layout_graph: dict[str, Any],
        geometry_registry: dict[str, Any],
        render_style: dict[str, Any],
    ) -> JsonDict:
        return self._execute(
            "scene_build",
            lambda: self._scene_build(layout_graph, geometry_registry, render_style),
        )

    def runtime_bind(
        self,
        scene_graph_handle: str,
        gameplay_hooks: dict[str, Any] | None,
    ) -> JsonDict:
        return self._execute(
            "runtime_bind",
            lambda: self._runtime_bind(scene_graph_handle, gameplay_hooks or {}),
        )

    def runtime_step(
        self,
        scene_graph_handle: str,
        game_systems: dict[str, Any],
        game_state: dict[str, Any],
    ) -> JsonDict:
        return self._execute(
            "runtime_step",
            lambda: self._runtime_step(scene_graph_handle, game_systems, game_state),
        )

    def capture(
        self,
        scene_graph_handle: str,
        event: dict[str, Any],
    ) -> JsonDict:
        return self._execute(
            "capture",
            lambda: self._capture(scene_graph_handle, event),
        )

    def _scene_build(
        self,
        layout_graph: dict[str, Any],
        geometry_registry: dict[str, Any],
        render_style: dict[str, Any],
    ) -> JsonDict:
        self._require_mapping("layout_graph", layout_graph)
        self._require_mapping("geometry_registry", geometry_registry)
        self._require_mapping("render_style", render_style)

        scene = build_scene_payload(layout_graph, geometry_registry, render_style)
        scene_graph_handle = scene["sceneGraphHandle"]
        self.active_scenes[scene_graph_handle] = deepcopy(scene)
        return {
            "sceneGraphHandle": scene_graph_handle,
            "scene": deepcopy(scene),
        }

    def _runtime_bind(
        self,
        scene_graph_handle: str,
        gameplay_hooks: dict[str, Any],
    ) -> JsonDict:
        scene = self._require_scene(scene_graph_handle)
        self._require_mapping("gameplay_hooks", gameplay_hooks)

        return build_runtime_bind_payload(
            scene,
            gameplay_hooks,
            system_prefix="deterministic",
        )

    def _runtime_step(
        self,
        scene_graph_handle: str,
        game_systems: dict[str, Any],
        game_state: dict[str, Any],
    ) -> JsonDict:
        scene = self._require_scene(scene_graph_handle)
        self._require_mapping("game_systems", game_systems)
        self._require_mapping("game_state", game_state)

        updated_game_state, runtime_delta = build_runtime_step_payload(
            scene,
            game_state,
            score_step_base=self.config.score_step_base,
            transition_type="single_tick",
        )

        return {
            "updatedGameState": updated_game_state,
            "runtimeDelta": runtime_delta,
        }

    def _capture(
        self,
        scene_graph_handle: str,
        event: dict[str, Any],
    ) -> JsonDict:
        self._require_scene(scene_graph_handle)
        self._require_mapping("event", event)

        event_id = str(
            event.get("eventId")
            or event.get("transitionId")
            or stable_hash(event)[:12]
        )
        artifact_path = self.capture_root / f"{scene_graph_handle}_{event_id}.json"
        payload = {
            "sceneGraphHandle": scene_graph_handle,
            "event": deepcopy(event),
            "observational": True,
        }
        artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return {
            "artifactReference": str(artifact_path),
            "observational": True,
        }

    def _require_scene(self, scene_graph_handle: str) -> JsonDict:
        if not isinstance(scene_graph_handle, str) or not scene_graph_handle.strip():
            raise InputValidationError("scene_graph_handle is required.")
        handle = scene_graph_handle.strip()
        if handle not in self.active_scenes:
            raise InputValidationError(f"Unknown scene_graph_handle: {handle}")
        return self.active_scenes[handle]

    def _require_mapping(self, name: str, value: object) -> None:
        if not isinstance(value, dict):
            raise InputValidationError(f"{name} must be a dictionary.")
