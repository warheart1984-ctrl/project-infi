"""Document Vision Organ — read-only OCR/document vision posture."""

# Mythic: Document Vision Organ
# Engineering: DocumentVisionEngine
from __future__ import annotations

import importlib.util
from typing import Any

from src.document_vision import DOCUMENT_VISION_ENV, document_vision

MODULE_ID = "AAIS-DVO-01"
ORGAN_VERSION = "document_vision_organ.v1"


def _ocr_engine_available() -> bool:
    if not document_vision.is_enabled():
        return False
    return importlib.util.find_spec("pytesseract") is not None


def build_document_vision_status() -> dict[str, Any]:
    enabled = document_vision.is_enabled()
    ocr_ok = _ocr_engine_available()
    summary = f"enabled={int(enabled)};ocr={int(ocr_ok)};read_only=1"[:128]
    return {
        "document_vision_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "document_vision_enabled": enabled,
        "env_var": DOCUMENT_VISION_ENV,
        "ocr_engine_available": ocr_ok,
        "bridge_safe": True,
        "proposal_only": True,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
