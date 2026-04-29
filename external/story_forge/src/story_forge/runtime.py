from __future__ import annotations

from pathlib import Path
from typing import Protocol

from story_forge.cli_output import format_visual_artifact_line, format_visual_recall_lines
from story_forge.models import OutputPackage, Scene


class RuntimeInterface(Protocol):
    def display_scene(self, scene: Scene) -> None: ...
    def present_choices(self, scene: Scene) -> None: ...
    def capture_input(self) -> str: ...
    def save_state(self, path: str | Path, payload: str) -> None: ...
    def load_state(self, path: str | Path) -> str: ...


class ConsoleRuntime:
    def display_scene(self, scene: Scene) -> None:
        print()
        print(scene.text)
        print()

    def present_choices(self, scene: Scene) -> None:
        for index, choice in enumerate(scene.choices, start=1):
            print(f"{index}. {choice}")

    def capture_input(self) -> str:
        return input("> ").strip()

    def save_state(self, path: str | Path, payload: str) -> None:
        Path(path).write_text(payload, encoding="utf-8")

    def load_state(self, path: str | Path) -> str:
        return Path(path).read_text(encoding="utf-8")

def render_output(runtime: RuntimeInterface, package: OutputPackage) -> None:
    scene = package.scene
    if package.presentation is not None:
        scene = Scene(
            text=package.presentation.text,
            characters=list(package.scene.characters),
            choices=list(package.scene.choices),
            tone=package.scene.tone,
            consequence_tags=list(package.scene.consequence_tags),
        )
    runtime.display_scene(scene)
    lumen_state = package.state_summary.get("lumen", {}) or {}
    if not lumen_state.get("rendered_visual_recall", False):
        for line in format_visual_recall_lines(package.state_summary.get("visual_recall")):
            print(line)
        artifact_line = format_visual_artifact_line(package.state_summary.get("visual_artifact"))
        if artifact_line is not None:
            print(artifact_line)
    runtime.present_choices(package.scene)
    if package.ending:
        print()
        print(f"Ending triggered: {package.ending.ending_type}")
        print(package.ending.summary)
