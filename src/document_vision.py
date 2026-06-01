"""Optional OCR/document-vision helpers for AAIS image analysis."""

from __future__ import annotations

import os
import re

from src.logger import get_logger

logger = get_logger(__name__)

DOCUMENT_VISION_ENV = "AAIS_ENABLE_DOCUMENT_VISION"
TESSERACT_CMD_ENV = "TESSERACT_CMD"
OCR_TEXTLIKE_LABELS = {
    "chart",
    "code",
    "document",
    "poster",
    "screenshot",
    "text-heavy",
}


def _truthy(value) -> bool:
    """Interpret common truthy env and request values."""
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _clip_text(text: str, limit: int = 1600) -> str:
    """Return a bounded text preview."""
    normalized = str(text or "").strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


class DocumentVisionUnavailable(RuntimeError):
    """Raised when OCR is disabled or the OCR engine is unavailable."""


class DocumentVision:
    """Optional OCR service that can be layered onto image analysis."""

    def __init__(self):
        self._pytesseract = None

    def is_enabled(self) -> bool:
        """Return whether OCR is enabled for this deployment."""
        return _truthy(os.getenv(DOCUMENT_VISION_ENV))

    def _load_engine(self):
        """Import and validate the OCR engine only when needed."""
        if not self.is_enabled():
            raise DocumentVisionUnavailable(
                "Document vision is disabled for this deployment"
            )

        if self._pytesseract is not None:
            return self._pytesseract

        try:
            import pytesseract
        except ImportError as exc:
            raise DocumentVisionUnavailable(
                "Document vision requires pytesseract in the advanced extras"
            ) from exc

        configured_cmd = os.getenv(TESSERACT_CMD_ENV, "").strip()
        if configured_cmd:
            pytesseract.pytesseract.tesseract_cmd = configured_cmd

        try:
            pytesseract.get_tesseract_version()
        except Exception as exc:
            raise DocumentVisionUnavailable(
                "Document vision requires the Tesseract OCR binary to be installed"
            ) from exc

        self._pytesseract = pytesseract
        return self._pytesseract

    @staticmethod
    def should_suggest_ocr(top_matches=None):
        """Detect whether an image is likely to benefit from OCR."""
        matches = top_matches or []
        score = sum(
            float(match.get("score") or 0.0)
            for match in matches
            if match.get("label") in OCR_TEXTLIKE_LABELS
        )
        return score >= 0.18

    @staticmethod
    def preprocess_image(image):
        """Prepare an image for OCR with simple high-value cleanup."""
        from PIL import Image, ImageFilter, ImageOps

        processed = image.convert("L")
        processed = ImageOps.autocontrast(processed)

        width, height = processed.size
        if max(width, height) < 1400:
            scale = max(2, int(1400 / max(width, height)))
            processed = processed.resize(
                (width * scale, height * scale),
                resample=Image.Resampling.LANCZOS,
            )

        processed = processed.filter(ImageFilter.MedianFilter(size=3))
        processed = processed.point(lambda pixel: 255 if pixel > 165 else 0)
        return processed

    @staticmethod
    def _group_ocr_lines(data):
        """Collapse pytesseract word-level data into lines."""
        lines = {}

        for index, raw_text in enumerate(data.get("text", [])):
            text = str(raw_text or "").strip()
            if not text:
                continue

            try:
                confidence = float(data.get("conf", [])[index])
            except (TypeError, ValueError, IndexError):
                confidence = -1.0

            if confidence < 0:
                continue

            key = (
                data.get("block_num", [0])[index],
                data.get("par_num", [0])[index],
                data.get("line_num", [0])[index],
            )
            lines.setdefault(key, []).append({"text": text, "confidence": confidence})

        normalized_lines = []
        confidences = []
        for words in lines.values():
            line_text = " ".join(word["text"] for word in words).strip()
            if not line_text:
                continue
            normalized_lines.append(line_text)
            confidences.extend(word["confidence"] for word in words)

        return normalized_lines, confidences

    @staticmethod
    def _summarize_text(lines):
        """Produce a compact OCR summary from extracted lines."""
        if not lines:
            return "OCR ran, but it did not find readable text."

        joined = " ".join(lines)
        words = re.findall(r"\S+", joined)
        if not words:
            return "OCR ran, but it did not find readable text."

        return (
            f"OCR found {len(words)} words across {len(lines)} lines. "
            f"Preview: {_clip_text(joined, limit=180)}"
        )

    def extract_document_text(self, image, top_matches=None, max_preview_chars=1800):
        """Extract OCR text from an image with light preprocessing."""
        pytesseract = self._load_engine()
        processed = self.preprocess_image(image)
        data = pytesseract.image_to_data(
            processed,
            config="--oem 3 --psm 6",
            output_type=pytesseract.Output.DICT,
        )
        lines, confidences = self._group_ocr_lines(data)
        full_text = "\n".join(lines).strip()
        average_confidence = (
            round(sum(confidences) / len(confidences), 2) if confidences else None
        )
        word_count = len(re.findall(r"\S+", full_text))

        return {
            "requested": True,
            "status": "available" if full_text else "no_text",
            "engine": "pytesseract",
            "document_like": self.should_suggest_ocr(top_matches),
            "summary": self._summarize_text(lines),
            "text_preview": _clip_text(full_text, limit=max_preview_chars),
            "line_count": len(lines),
            "word_count": word_count,
            "average_confidence": average_confidence,
        }

    def describe_unavailable(self, requested=False, top_matches=None, message=None):
        """Return a consistent OCR status payload when OCR is off or unavailable."""
        summary = message or (
            "Document vision is available in the codebase, but it is currently disabled."
        )
        return {
            "requested": bool(requested),
            "status": "unavailable",
            "engine": "pytesseract",
            "document_like": self.should_suggest_ocr(top_matches),
            "summary": summary,
            "text_preview": "",
            "line_count": 0,
            "word_count": 0,
            "average_confidence": None,
        }


document_vision = DocumentVision()
