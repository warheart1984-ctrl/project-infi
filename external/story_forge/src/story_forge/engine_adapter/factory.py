from __future__ import annotations

import os
from pathlib import Path
import sys

from story_forge.engine_adapter.base_module import AAISEngineModule, InputValidationError
from story_forge.engine_adapter.deterministic_runtime import (
    DeterministicEngineConfig,
    DeterministicEngineModule,
)
from story_forge.engine_adapter.external_command_runtime import (
    ExternalCommandEngineConfig,
    ExternalCommandEngineModule,
)
from story_forge.engine_adapter.scene_archive_runtime import (
    SceneArchiveEngineConfig,
    SceneArchiveEngineModule,
)

DEFAULT_ENGINE_PROVIDER = "filesystem_scene_archive"
DETERMINISTIC_ENGINE_PROVIDER = "deterministic"
EXTERNAL_COMMAND_ENGINE_PROVIDER = "external_command"

_DETERMINISTIC_PROVIDER_ALIASES = {
    DETERMINISTIC_ENGINE_PROVIDER,
    "deterministic_runtime",
}
_EXTERNAL_COMMAND_PROVIDER_ALIASES = {
    EXTERNAL_COMMAND_ENGINE_PROVIDER,
    "command",
    "external",
}
_SCENE_ARCHIVE_PROVIDER_ALIASES = {
    DEFAULT_ENGINE_PROVIDER,
    "filesystem",
    "scene_archive",
}


def available_engine_providers() -> list[str]:
    return [
        DETERMINISTIC_ENGINE_PROVIDER,
        DEFAULT_ENGINE_PROVIDER,
        EXTERNAL_COMMAND_ENGINE_PROVIDER,
    ]


def create_engine_module(
    provider_name: str | None = None,
    *,
    runtime_root: str | Path | None = None,
    capture_root: str | Path | None = None,
    score_step_base: int = 6,
    command: str | list[str] | None = None,
    command_workdir: str | Path | None = None,
    timeout_seconds: float = 30.0,
    logger=None,
) -> AAISEngineModule:
    normalized = str(provider_name or DEFAULT_ENGINE_PROVIDER).strip().lower()
    if normalized in _DETERMINISTIC_PROVIDER_ALIASES:
        return DeterministicEngineModule(
            DeterministicEngineConfig(
                capture_root=capture_root,
                score_step_base=score_step_base,
            ),
            logger=logger,
        )
    if normalized in _EXTERNAL_COMMAND_PROVIDER_ALIASES:
        resolved_command = command or _default_external_command(
            runtime_root=runtime_root,
            capture_root=capture_root,
            score_step_base=score_step_base,
        )
        resolved_environment = _default_external_environment() if command is None else {}
        return ExternalCommandEngineModule(
            ExternalCommandEngineConfig(
                command=resolved_command,
                workdir=command_workdir,
                timeout_seconds=timeout_seconds,
                environment=resolved_environment,
            ),
            logger=logger,
        )
    if normalized in _SCENE_ARCHIVE_PROVIDER_ALIASES:
        return SceneArchiveEngineModule(
            SceneArchiveEngineConfig(
                root_dir=runtime_root,
                capture_root=capture_root,
                score_step_base=score_step_base,
            ),
            logger=logger,
        )
    supported = ", ".join(available_engine_providers())
    raise InputValidationError(
        f"Unknown engine provider '{provider_name}'. Supported providers: {supported}."
    )


def _default_external_command(
    *,
    runtime_root: str | Path | None,
    capture_root: str | Path | None,
    score_step_base: int,
) -> list[str]:
    if getattr(sys, "frozen", False):
        command: list[str] = [sys.executable, "--engine-host"]
    else:
        command = [sys.executable, "-m", "story_forge.engine_host"]

    command.extend(["--provider", DEFAULT_ENGINE_PROVIDER])
    if runtime_root is not None:
        command.extend(["--runtime-root", str(runtime_root)])
    if capture_root is not None:
        command.extend(["--capture-root", str(capture_root)])
    if int(score_step_base) != 6:
        command.extend(["--score-step-base", str(int(score_step_base))])
    return command


def _default_external_environment() -> dict[str, str]:
    if getattr(sys, "frozen", False):
        return {}
    src_root = Path(__file__).resolve().parents[2]
    existing = os.environ.get("PYTHONPATH", "").strip()
    python_path = str(src_root)
    if existing:
        python_path = os.pathsep.join([python_path, existing])
    return {"PYTHONPATH": python_path}
