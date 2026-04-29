from __future__ import annotations

import json
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


def _default_archive_root() -> Path:
    return Path(__file__).resolve().parents[3] / ".runtime" / "text_to_3d_world" / "scene_archive"


@dataclass(slots=True)
class SceneArchiveEngineConfig:
    root_dir: str | Path | None = None
    capture_root: str | Path | None = None
    score_step_base: int = 6


class SceneArchiveEngineModule(AAISEngineModule):
    def __init__(
        self,
        config: SceneArchiveEngineConfig | None = None,
        *,
        logger=None,
    ) -> None:
        super().__init__(provider_name="filesystem_scene_archive", logger=logger)
        self.config = config or SceneArchiveEngineConfig()
        self.root_dir = (
            Path(self.config.root_dir)
            if self.config.root_dir is not None
            else _default_archive_root()
        )
        self.scene_root = self.root_dir / "scenes"
        self.runtime_root = self.root_dir / "runtime"
        self.capture_root = (
            Path(self.config.capture_root)
            if self.config.capture_root is not None
            else self.root_dir / "captures"
        )
        self.scene_root.mkdir(parents=True, exist_ok=True)
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.capture_root.mkdir(parents=True, exist_ok=True)

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
        scene_dir = self.scene_root / scene["sceneGraphHandle"]
        scene_dir.mkdir(parents=True, exist_ok=True)
        scene_path = scene_dir / "scene.json"
        self._write_json(scene_path, scene)
        return {
            "sceneGraphHandle": scene["sceneGraphHandle"],
            "scene": scene,
            "sceneArchiveReference": str(scene_path),
        }

    def _runtime_bind(
        self,
        scene_graph_handle: str,
        gameplay_hooks: dict[str, Any],
    ) -> JsonDict:
        scene = self._require_scene(scene_graph_handle)
        self._require_mapping("gameplay_hooks", gameplay_hooks)

        bind_payload = build_runtime_bind_payload(
            scene,
            gameplay_hooks,
            system_prefix="scene_archive",
        )
        bind_dir = self.runtime_root / scene_graph_handle
        bind_dir.mkdir(parents=True, exist_ok=True)
        binding_path = bind_dir / "binding.json"
        binding_payload = {
            "sceneGraphHandle": scene_graph_handle,
            **bind_payload,
        }
        self._write_json(binding_path, binding_payload)
        bind_payload["bindingReference"] = str(binding_path)
        return bind_payload

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
            transition_type="single_tick_archive",
        )
        tick = int(updated_game_state.get("tick", 0) or 0)
        tick_dir = self.runtime_root / scene_graph_handle / "ticks"
        tick_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = tick_dir / f"tick_{tick:04d}.json"
        snapshot_payload = {
            "sceneGraphHandle": scene_graph_handle,
            "gameSystems": game_systems,
            "updatedGameState": updated_game_state,
            "runtimeDelta": runtime_delta,
        }
        self._write_json(snapshot_path, snapshot_payload)
        return {
            "updatedGameState": updated_game_state,
            "runtimeDelta": runtime_delta,
            "snapshotReference": str(snapshot_path),
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
        capture_dir = self.capture_root / scene_graph_handle
        capture_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = capture_dir / f"{event_id}.json"
        payload = {
            "sceneGraphHandle": scene_graph_handle,
            "event": event,
            "observational": True,
            "provider": self.provider_name,
        }
        self._write_json(artifact_path, payload)
        return {
            "artifactReference": str(artifact_path),
            "observational": True,
        }

    def _require_scene(self, scene_graph_handle: str) -> JsonDict:
        handle = str(scene_graph_handle or "").strip()
        if not handle:
            raise InputValidationError("scene_graph_handle is required.")
        scene_path = self.scene_root / handle / "scene.json"
        if not scene_path.exists():
            raise InputValidationError(f"Unknown scene_graph_handle: {handle}")
        try:
            scene = json.loads(scene_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise InputValidationError(f"Scene archive is unreadable for handle: {handle}") from exc
        if not isinstance(scene, dict):
            raise InputValidationError(f"Scene archive is invalid for handle: {handle}")
        return scene

    def _require_mapping(self, name: str, value: object) -> None:
        if not isinstance(value, dict):
            raise InputValidationError(f"{name} must be a dictionary.")

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
