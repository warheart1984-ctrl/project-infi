"""Governed media processor family capability adapters."""

from __future__ import annotations

from typing import Any

from src.capability_module import AAISCapabilityModule

MEDIA_PROCESSOR_COMPONENT_ID = "jarvis.media_processor_family"


class AudioAnalyzeCapability(AAISCapabilityModule):
    module_name = "audio_analyze"
    supported_actions = frozenset({"analyze"})

    def __init__(self) -> None:
        super().__init__(provider_name="aais_media")
        self.handlers = {"analyze": self._handle_analyze}

    def _handle_analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        from src.audio_processor import AudioProcessor

        path = str(payload.get("path") or "").strip()
        if not path:
            return self._err("analyze", "InputError", "path is required")
        result = AudioProcessor.extract_features(path)
        return self._ok("analyze", {"analysis": result})


class VideoAnalyzeCapability(AAISCapabilityModule):
    module_name = "video_analyze"
    supported_actions = frozenset({"analyze"})

    def __init__(self) -> None:
        super().__init__(provider_name="aais_media")
        self.handlers = {"analyze": self._handle_analyze}

    def _handle_analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        from src.video_processor import VideoProcessor

        path = str(payload.get("path") or "").strip()
        if not path:
            return self._err("analyze", "InputError", "path is required")
        processor = VideoProcessor()
        result = processor.get_video_info(path)
        return self._ok("analyze", {"analysis": result})


class ImageTransformCapability(AAISCapabilityModule):
    module_name = "image_transform"
    supported_actions = frozenset({"transform"})

    def __init__(self) -> None:
        super().__init__(provider_name="aais_media")
        self.handlers = {"transform": self._handle_transform}

    def _handle_transform(self, payload: dict[str, Any]) -> dict[str, Any]:
        from PIL import Image

        from src.image_processor import ImageProcessor

        path = str(payload.get("path") or "").strip()
        if not path:
            return self._err("transform", "InputError", "path is required")
        scale = int(payload.get("scale") or 2)
        with Image.open(path) as image:
            result = ImageProcessor.upscale(image, scale_factor=scale)
        return self._ok("transform", {"width": result.size[0], "height": result.size[1]})
