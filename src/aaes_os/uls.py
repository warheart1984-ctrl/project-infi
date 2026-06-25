"""Unified Linguistic Surface — input normalization and trace summarization."""

# Mythic: ULS
# Engineering: UnifiedLinguisticSurface
from __future__ import annotations

from src.aaes_os.models import TraceEvent
from src.aaes_os.pipeline_types import AAESStep

# Back-compat alias
UnifiedLanguageSurface = None  # set after class definition


class UnifiedLinguisticSurface:
    """Stub ULS; delegates semantic work to future adapters."""

    def normalize_input(self, raw: str) -> str:
        if raw is None:
            raise TypeError("raw must be str")
        text = str(raw).strip()
        if not text:
            raise ValueError("raw input is empty after normalization")
        return " ".join(text.split())

    def semantic_compare(self, left: str, right: str) -> float:
        if not isinstance(left, str) or not isinstance(right, str):
            raise TypeError("left and right must be str")
        left_norm = self.normalize_input(left) if left.strip() else ""
        right_norm = self.normalize_input(right) if right.strip() else ""
        if not left_norm or not right_norm:
            return 0.0
        if left_norm == right_norm:
            return 1.0
        left_tokens = set(left_norm.lower().split())
        right_tokens = set(right_norm.lower().split())
        if not left_tokens or not right_tokens:
            return 0.0
        overlap = len(left_tokens & right_tokens)
        union = len(left_tokens | right_tokens)
        return round(overlap / union, 4)

    def summarize_trace(
        self,
        *,
        steps: list[AAESStep],
        events: list[TraceEvent] | None = None,
    ) -> str:
        if not isinstance(steps, list):
            raise TypeError("steps must be list")
        parts = [f"{row.step_type.value}: {row.summary}" for row in steps]
        if events:
            parts.append(f"trace_events={len(events)}")
        if not parts:
            return "empty trace"
        return " | ".join(parts)


UnifiedLanguageSurface = UnifiedLinguisticSurface
