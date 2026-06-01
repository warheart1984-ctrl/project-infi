"""Optional screenshot and UI understanding helpers for AAIS image analysis."""

from __future__ import annotations

import os
import re
from statistics import mean

from src.logger import get_logger

logger = get_logger(__name__)

UI_VISION_ENV = "AAIS_ENABLE_UI_VISION"
SCREENSHOTISH_LABELS = {
    "chart",
    "code",
    "document",
    "poster",
    "screenshot",
    "text-heavy",
}
CODE_KEYWORDS = {
    "python": ("def ", "import ", "self", "return", "class ", "elif ", "None"),
    "javascript": ("function ", "const ", "let ", "=>", "console.", "export ", "import "),
    "typescript": ("interface ", "type ", ": string", ": number", "React.FC", "useState"),
    "json": ('{', '}', '":', '",', 'true', 'false', 'null'),
    "html": ("<div", "<span", "<html", "<body", "<script", "</"),
    "css": ("{", "}", "color:", "display:", "padding:", "margin:", "font-"),
}
NAV_HINTS = {
    "dashboard",
    "home",
    "settings",
    "history",
    "search",
    "profile",
    "save",
    "cancel",
    "submit",
    "login",
    "sign in",
}


def _truthy(value) -> bool:
    """Interpret common truthy env and request values."""
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _clip_text(text: str, limit: int = 220) -> str:
    """Return a bounded text preview."""
    normalized = " ".join(str(text or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _label_score(top_matches, label):
    """Get the match score for one label."""
    for match in top_matches or []:
        if match.get("label") == label:
            return float(match.get("score") or 0.0)
    return 0.0


class UIVisionUnavailable(RuntimeError):
    """Raised when UI understanding is disabled."""


class UIVision:
    """Heuristic UI understanding layered on top of image analysis."""

    def is_enabled(self) -> bool:
        """Return whether UI understanding is enabled for this deployment."""
        return _truthy(os.getenv(UI_VISION_ENV))

    def _require_enabled(self):
        """Gate UI understanding behind an explicit env opt-in."""
        if not self.is_enabled():
            raise UIVisionUnavailable("UI understanding is disabled for this deployment")

    @staticmethod
    def should_suggest_ui(top_matches=None):
        """Detect whether an image looks enough like a screenshot/UI to justify deeper analysis."""
        score = sum(
            float(match.get("score") or 0.0)
            for match in (top_matches or [])
            if match.get("label") in SCREENSHOTISH_LABELS
        )
        return score >= 0.2

    @staticmethod
    def _theme_from_image(image):
        """Infer whether a screenshot is predominantly light or dark."""
        from PIL import ImageStat

        rgb = image.convert("RGB").resize((96, 96))
        luminance = ImageStat.Stat(rgb.convert("L")).mean[0]
        theme = "dark" if luminance < 110 else "light"
        return theme, round(luminance / 255, 3)

    @staticmethod
    def _platform_hint(image_size, surface_type):
        """Infer likely platform from aspect ratio."""
        width, height = image_size
        aspect = width / max(height, 1)
        if surface_type == "code_screenshot" and aspect > 1.15:
            return "desktop"
        if aspect < 0.82:
            return "mobile"
        if aspect < 1.15:
            return "tablet"
        return "desktop"

    @staticmethod
    def _edge_density(image):
        """Estimate visual density from adjacent grayscale changes."""
        grayscale = image.convert("L").resize((72, 72))
        pixels = list(grayscale.tobytes())
        width, height = grayscale.size
        horizontal = []
        vertical = []

        for y in range(height):
            row_offset = y * width
            for x in range(width - 1):
                horizontal.append(
                    abs(pixels[row_offset + x] - pixels[row_offset + x + 1]) / 255.0
                )

        for y in range(height - 1):
            row_offset = y * width
            next_offset = (y + 1) * width
            for x in range(width):
                vertical.append(
                    abs(pixels[row_offset + x] - pixels[next_offset + x]) / 255.0
                )

        density = mean(horizontal + vertical) if horizontal or vertical else 0.0
        if density < 0.055:
            label = "minimal"
        elif density < 0.11:
            label = "moderate"
        else:
            label = "dense"

        return round(density, 3), label

    @staticmethod
    def _region_clues(image):
        """Infer rough layout clues like top bars, sidebars, and multi-panel regions."""
        from PIL import ImageStat

        rgb = image.convert("RGB").resize((120, 120))
        width, height = rgb.size

        def _crop_box(x0, y0, x1, y1):
            return rgb.crop((int(x0), int(y0), int(x1), int(y1)))

        top = ImageStat.Stat(_crop_box(0, 0, width, height * 0.14).convert("L")).mean[0]
        middle = ImageStat.Stat(_crop_box(width * 0.2, height * 0.2, width * 0.8, height * 0.8).convert("L")).mean[0]
        left = ImageStat.Stat(_crop_box(0, height * 0.12, width * 0.18, height).convert("L")).mean[0]
        center = ImageStat.Stat(_crop_box(width * 0.25, height * 0.2, width * 0.75, height * 0.8).convert("L")).mean[0]

        clues = []
        if abs(top - middle) > 18:
            clues.append("top bar or header")
        if abs(left - center) > 16:
            clues.append("left sidebar or dock")

        return clues

    @staticmethod
    def _readable_targets(ocr_result):
        """Extract short button/nav-like targets from OCR output."""
        text_preview = (ocr_result or {}).get("text_preview", "")
        lines = [line.strip() for line in str(text_preview).splitlines() if line.strip()]
        targets = []

        for line in lines:
            words = re.findall(r"[A-Za-z0-9][A-Za-z0-9./_-]*", line)
            if 0 < len(words) <= 4:
                joined = " ".join(words)
                lowered = joined.lower()
                if lowered in targets:
                    continue
                if any(hint in lowered for hint in NAV_HINTS) or len(joined) <= 24:
                    targets.append(joined)
            if len(targets) >= 6:
                break

        return targets

    @staticmethod
    def _infer_code_language(ocr_result):
        """Guess the code language from OCR text when the screenshot looks code-like."""
        text = str((ocr_result or {}).get("text_preview", "")).lower()
        if not text:
            return None

        ranked = []
        for language, patterns in CODE_KEYWORDS.items():
            score = sum(text.count(pattern.lower()) for pattern in patterns)
            ranked.append((score, language))

        ranked.sort(reverse=True)
        best_score, best_language = ranked[0]
        return best_language if best_score > 0 else None

    @staticmethod
    def _infer_surface_type(top_matches, ocr_result):
        """Infer the screenshot family from labels and optional OCR text."""
        code_score = _label_score(top_matches, "code")
        screenshot_score = _label_score(top_matches, "screenshot")
        chart_score = _label_score(top_matches, "chart")
        document_score = _label_score(top_matches, "document") + _label_score(top_matches, "text-heavy")
        ocr_text = str((ocr_result or {}).get("text_preview", "")).lower()
        code_hint_count = sum(
            1
            for token in ("def ", "class ", "import ", "const ", "function ", "{", "}", "=>")
            if token in ocr_text
        )

        if code_score >= 0.12 or (screenshot_score >= 0.12 and code_hint_count >= 2):
            return "code_screenshot"
        if chart_score >= 0.15:
            return "dashboard_or_chart"
        if screenshot_score + document_score >= 0.22:
            return "ui_screenshot"
        if document_score >= 0.18:
            return "document_capture"
        return "general_image"

    @staticmethod
    def _panel_estimate(image, density_label, surface_type, layout_clues, readable_targets):
        """Guess how many major UI regions are visible."""
        width, height = image.size
        aspect = width / max(height, 1)
        if density_label == "dense":
            estimate = 4 if aspect > 1.1 else 3
        elif density_label == "moderate":
            estimate = 3 if aspect > 1.1 else 2
        else:
            estimate = 1

        if surface_type in {"ui_screenshot", "dashboard_or_chart", "code_screenshot"}:
            estimate = max(estimate, 2)
        if len(layout_clues or []) >= 2:
            estimate = max(estimate, 3)
        if len(readable_targets or []) >= 4:
            estimate = max(estimate, 2)

        return min(estimate, 6)

    @staticmethod
    def _build_summary(surface_type, platform_hint, theme, layout_clues, readable_targets, code_language, panel_estimate, density_label):
        """Render a compact operator-facing UI summary."""
        surface_phrase = {
            "code_screenshot": "a code screenshot",
            "dashboard_or_chart": "a dashboard or chart-oriented screenshot",
            "ui_screenshot": "an application UI screenshot",
            "document_capture": "a document-like screen capture",
            "general_image": "a general image rather than a clear UI surface",
        }.get(surface_type, "a screen-like image")

        sentence = (
            f"This most likely looks like {surface_phrase} on a {platform_hint} layout "
            f"with a {theme} theme and {density_label} visual density."
        )

        detail_bits = [f"It appears to contain about {panel_estimate} major interface region(s)."]
        if layout_clues:
            detail_bits.append(f"Likely layout clues: {', '.join(layout_clues)}.")
        if code_language:
            detail_bits.append(f"The code-like content reads most like {code_language}.")
        if readable_targets:
            detail_bits.append(
                f"Short readable targets include: {', '.join(readable_targets[:4])}."
            )

        return " ".join([sentence] + detail_bits)

    def analyze(self, image, top_matches=None, ocr_result=None):
        """Produce a screenshot/UI-oriented read from image structure and OCR cues."""
        self._require_enabled()

        theme, luminance = self._theme_from_image(image)
        density_score, density_label = self._edge_density(image)
        layout_clues = self._region_clues(image)
        surface_type = self._infer_surface_type(top_matches or [], ocr_result or {})
        platform_hint = self._platform_hint(image.size, surface_type)
        readable_targets = self._readable_targets(ocr_result or {})
        code_language = (
            self._infer_code_language(ocr_result or {})
            if surface_type == "code_screenshot"
            else None
        )
        panel_estimate = self._panel_estimate(
            image,
            density_label,
            surface_type,
            layout_clues,
            readable_targets,
        )

        return {
            "requested": True,
            "status": "available",
            "surface_type": surface_type,
            "platform_hint": platform_hint,
            "theme": theme,
            "average_luminance": luminance,
            "visual_density": density_score,
            "density_label": density_label,
            "panel_estimate": panel_estimate,
            "layout_clues": layout_clues,
            "readable_targets": readable_targets,
            "code_language": code_language,
            "document_like": bool((ocr_result or {}).get("document_like")) or self.should_suggest_ui(top_matches),
            "summary": self._build_summary(
                surface_type,
                platform_hint,
                theme,
                layout_clues,
                readable_targets,
                code_language,
                panel_estimate,
                density_label,
            ),
        }

    def describe_unavailable(self, requested=False, top_matches=None, message=None):
        """Return a consistent payload when UI understanding is off."""
        return {
            "requested": bool(requested),
            "status": "unavailable",
            "surface_type": None,
            "platform_hint": None,
            "theme": None,
            "average_luminance": None,
            "visual_density": None,
            "density_label": None,
            "panel_estimate": None,
            "layout_clues": [],
            "readable_targets": [],
            "code_language": None,
            "document_like": self.should_suggest_ui(top_matches),
            "summary": message or "UI understanding is wired, but currently disabled.",
        }


ui_vision = UIVision()
