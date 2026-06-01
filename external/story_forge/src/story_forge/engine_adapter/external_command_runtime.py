from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from story_forge.engine_adapter.base_module import (
    AAISEngineModule,
    BoundaryExecutionError,
    InputValidationError,
    JsonDict,
    SemanticValidationError,
)


@dataclass(slots=True)
class ExternalCommandEngineConfig:
    command: str | list[str] | None = None
    workdir: str | Path | None = None
    timeout_seconds: float = 30.0
    environment: dict[str, str] = field(default_factory=dict)


class ExternalCommandEngineModule(AAISEngineModule):
    def __init__(
        self,
        config: ExternalCommandEngineConfig | None = None,
        *,
        logger=None,
    ) -> None:
        super().__init__(provider_name="external_command", logger=logger)
        self.config = config or ExternalCommandEngineConfig()

    def scene_build(
        self,
        layout_graph: dict[str, Any],
        geometry_registry: dict[str, Any],
        render_style: dict[str, Any],
    ) -> JsonDict:
        return self._execute(
            "scene_build",
            lambda: self._invoke(
                "scene_build",
                {
                    "layout_graph": layout_graph,
                    "geometry_registry": geometry_registry,
                    "render_style": render_style,
                },
            ),
        )

    def runtime_bind(
        self,
        scene_graph_handle: str,
        gameplay_hooks: dict[str, Any] | None,
    ) -> JsonDict:
        return self._execute(
            "runtime_bind",
            lambda: self._invoke(
                "runtime_bind",
                {
                    "scene_graph_handle": scene_graph_handle,
                    "gameplay_hooks": gameplay_hooks or {},
                },
            ),
        )

    def runtime_step(
        self,
        scene_graph_handle: str,
        game_systems: dict[str, Any],
        game_state: dict[str, Any],
    ) -> JsonDict:
        return self._execute(
            "runtime_step",
            lambda: self._invoke(
                "runtime_step",
                {
                    "scene_graph_handle": scene_graph_handle,
                    "game_systems": game_systems,
                    "game_state": game_state,
                },
            ),
        )

    def capture(
        self,
        scene_graph_handle: str,
        event: dict[str, Any],
    ) -> JsonDict:
        return self._execute(
            "capture",
            lambda: self._invoke(
                "capture",
                {
                    "scene_graph_handle": scene_graph_handle,
                    "event": event,
                },
            ),
        )

    def _invoke(self, action: str, payload: dict[str, Any]) -> JsonDict:
        command = self._normalized_command()
        request_payload = {
            "protocol": "story_forge.engine.external_command.v1",
            "module": "engine",
            "action": action,
            "payload": payload,
        }
        environment = os.environ.copy()
        if self.config.environment:
            environment.update(self.config.environment)
        try:
            completed = subprocess.run(
                command,
                input=json.dumps(request_payload),
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                cwd=str(self.config.workdir) if self.config.workdir is not None else None,
                env=environment,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise BoundaryExecutionError(
                f"External engine command timed out after {self.config.timeout_seconds} seconds."
            ) from exc
        except OSError as exc:
            raise BoundaryExecutionError(
                f"External engine command failed to start: {exc}"
            ) from exc

        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            stdout = (completed.stdout or "").strip()
            detail = stderr or stdout or f"exit code {completed.returncode}"
            raise BoundaryExecutionError(
                f"External engine command failed for {action}: {detail}"
            )

        raw_stdout = (completed.stdout or "").strip()
        if not raw_stdout:
            raise SemanticValidationError("External engine command returned no stdout payload.")

        try:
            decoded = json.loads(raw_stdout)
        except json.JSONDecodeError as exc:
            raise SemanticValidationError("External engine command returned invalid JSON.") from exc
        if not isinstance(decoded, dict):
            raise SemanticValidationError("External engine command must return a JSON object.")

        data = self._unwrap_response(decoded, action)
        self._validate_response(action, data)
        return data

    def _normalized_command(self) -> list[str]:
        command = self.config.command
        if isinstance(command, list):
            normalized = [str(part).strip() for part in command if str(part).strip()]
            if normalized:
                return normalized
        if isinstance(command, str) and command.strip():
            normalized = shlex.split(command, posix=False)
            if normalized:
                return normalized
        raise InputValidationError("External engine command is required.")

    def _unwrap_response(self, response: dict[str, Any], action: str) -> JsonDict:
        if "ok" not in response:
            return response
        if not bool(response.get("ok")):
            message = str(response.get("message", f"{action} failed") or f"{action} failed")
            error_type = str(response.get("error_type", "BoundaryError") or "BoundaryError")
            if error_type == InputValidationError.error_type:
                raise InputValidationError(message)
            if error_type == SemanticValidationError.error_type:
                raise SemanticValidationError(message)
            raise BoundaryExecutionError(message)
        data = response.get("data")
        if not isinstance(data, dict):
            raise SemanticValidationError("External engine command returned ok=true without a data object.")
        return data

    def _validate_response(self, action: str, data: JsonDict) -> None:
        required_by_action = {
            "scene_build": ("sceneGraphHandle",),
            "runtime_bind": ("systems", "initialState"),
            "runtime_step": ("updatedGameState", "runtimeDelta"),
            "capture": ("artifactReference",),
        }
        for key in required_by_action.get(action, ()):
            if key not in data:
                raise SemanticValidationError(
                    f"External engine response for {action} is missing '{key}'."
                )
