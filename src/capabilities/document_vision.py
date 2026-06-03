"""Governed document-vision capability adapter."""

from __future__ import annotations

from typing import Any

from src.capability_module import AAISCapabilityModule

DOCUMENT_VISION_COMPONENT_ID = "jarvis.capability.document_vision"


class DocumentVisionCapability(AAISCapabilityModule):
    module_name = "document_vision"
    supported_actions = frozenset({"extract_text"})

    def __init__(self) -> None:
        super().__init__(provider_name="aais_vision")
        self.handlers = {"extract_text": self._handle_extract}

    def _handle_extract(self, payload: dict[str, Any]) -> dict[str, Any]:
        from src.document_vision import DocumentVisionUnavailable, document_vision

        image = payload.get("image")
        if image is None:
            return self._err("extract_text", "InputError", "image payload is required")
        try:
            result = document_vision.extract_document_text(image)
        except DocumentVisionUnavailable as exc:
            return self._err("extract_text", "ProviderUnavailable", str(exc))
        return self._ok("extract_text", {"result": result})
