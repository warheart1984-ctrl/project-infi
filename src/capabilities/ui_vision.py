"""Governed UI-vision capability adapter."""

from __future__ import annotations

from typing import Any

from src.capability_module import AAISCapabilityModule

UI_VISION_COMPONENT_ID = "jarvis.capability.ui_vision"


class UiVisionCapability(AAISCapabilityModule):
    module_name = "ui_vision"
    supported_actions = frozenset({"analyze_screenshot"})

    def __init__(self) -> None:
        super().__init__(provider_name="aais_vision")
        self.handlers = {"analyze_screenshot": self._handle_analyze}

    def _handle_analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        from src.ui_vision import UIVisionUnavailable, ui_vision

        image = payload.get("image")
        if image is None:
            return self._err("analyze_screenshot", "InputError", "image payload is required")
        try:
            result = ui_vision.analyze_ui(image)
        except UIVisionUnavailable as exc:
            return self._err("analyze_screenshot", "ProviderUnavailable", str(exc))
        except Exception as exc:
            return self._err("analyze_screenshot", "ExecutionError", str(exc))
        return self._ok("analyze_screenshot", {"result": result})
