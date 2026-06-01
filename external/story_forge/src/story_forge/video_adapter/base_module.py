from __future__ import annotations

from story_forge.image_adapter.base_module import (
    AAISCapabilityModule,
    APIExecutionError,
    BoundaryExecutionError,
    InputValidationError,
    JsonDict,
    SemanticValidationError,
)

__all__ = [
    "AAISCapabilityModule",
    "AAISVideoModule",
    "APIExecutionError",
    "BoundaryExecutionError",
    "InputValidationError",
    "JsonDict",
    "SemanticValidationError",
]


class AAISVideoModule(AAISCapabilityModule):
    module_name = "video"

    def _action_failure_message(self, action: str) -> str:
        mapping = {
            "generate": "Video generation failed",
            "status": "Video status lookup failed",
            "edit": "Video edit failed",
            "extend": "Video extension failed",
        }
        return mapping.get(action, "Video action failed")
