"""CRK-1 Drift Visualizer — founder-independent ASCII CE/SE continuity dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field

DRIFT_VISUALIZER_VERSION = "1.0"

EXPOSURE_CHARS = (
    (0.7, "█"),
    (0.4, "▇"),
    (0.1, "▂"),
    (0.0, "░"),
)


def exposure_to_char(value: float) -> str:
    """Map normalized exposure to canonical glyph."""
    clamped = max(0.0, min(1.0, value))
    for threshold, glyph in EXPOSURE_CHARS:
        if clamped >= threshold:
            return glyph
    return "░"


def render_exposure_row(values: list[float]) -> str:
    return "".join(exposure_to_char(value) for value in values)


def _normalize_series(values: list[float]) -> list[float]:
    if not values:
        return []
    peak = max(values)
    if peak <= 0:
        return [0.0 for _ in values]
    return [min(1.0, value / peak) for value in values]


@dataclass
class DriftTimeline:
    """CE/SE exposure series over discrete timeline ticks."""

    ce_values: list[float] = field(default_factory=list)
    se_values: list[float] = field(default_factory=list)
    labels: list[str] | None = None

    @property
    def length(self) -> int:
        return max(len(self.ce_values), len(self.se_values))

    def timeline_labels(self) -> list[str]:
        if self.labels and len(self.labels) == self.length:
            return self.labels
        return [f"t{index}" for index in range(self.length)]


class DriftVisualizer:
    """Render CE(S) and SE(S) drift as canonical ASCII plots."""

    version: str = DRIFT_VISUALIZER_VERSION

    def __init__(self, timeline: DriftTimeline | None = None) -> None:
        self.timeline = timeline or DriftTimeline()

    @classmethod
    def from_monitor_history(
        cls,
        history: list[dict[str, float]],
        *,
        ce_values: list[float] | None = None,
    ) -> DriftVisualizer:
        se_values = [item.get("se", 0.0) for item in history]
        ce = list(ce_values or [])
        if ce and len(ce) != len(se_values):
            ce = ce[: len(se_values)]
        while len(ce) < len(se_values):
            ce.append(ce[-1] if ce else se_values[len(ce)])
        return cls(DriftTimeline(ce_values=ce, se_values=se_values))

    @classmethod
    def from_mutation_ledger(cls, ledger: object) -> DriftVisualizer:
        from src.crk1.mutation_ledger import CRK1MutationLedger

        if not isinstance(ledger, CRK1MutationLedger):
            raise TypeError("ledger must be CRK1MutationLedger")
        ce_values: list[float] = []
        se_values: list[float] = []
        for entry in ledger.entries:
            ce_values.append(entry.exposure_before.ce)
            se_values.append(entry.exposure_before.se)
        if ledger.entries:
            last = ledger.entries[-1]
            ce_values.append(last.exposure_after.ce)
            se_values.append(last.exposure_after.se)
        return cls(DriftTimeline(ce_values=ce_values, se_values=se_values))

    def render(self) -> str:
        timeline = self.timeline
        labels = timeline.timeline_labels()
        ce_norm = _normalize_series(timeline.ce_values)
        se_norm = _normalize_series(timeline.se_values)
        label_line = "  ".join(f"{label:>4}" for label in labels)
        ce_row = render_exposure_row(ce_norm)
        se_row = render_exposure_row(se_norm)
        lines = [
            "CRK‑1 Drift Visualizer",
            f"Version: {self.version}",
            "",
            "CE(S) — Consequence Exposure",
            "SE(S) — Semantic Exposure",
            "",
            "Timeline:",
            f"  {label_line}",
            "",
            "CE(S):",
            f"  {ce_row}",
            "  ↑ monotonic non‑decrease (K6)",
            "",
            "SE(S):",
            f"  {se_row}",
            "  ↑ monotonic non‑decrease (K11)",
            "",
            "Legend:",
            "  █ = high exposure",
            "  ▇ = medium exposure",
            "  ▂ = low exposure",
            "  ░ = near‑zero exposure (unconstitutional)",
            "",
            "Interpretation:",
            "  - CE(S) and SE(S) must never decrease.",
            "  - Any downward step indicates unconstitutional drift.",
            "  - Zero exposure indicates semantic insulation.",
        ]
        return "\n".join(lines)

    def detect_violations(self) -> list[str]:
        violations: list[str] = []
        ce = self.timeline.ce_values
        se = self.timeline.se_values
        for index in range(len(ce) - 1):
            if ce[index + 1] < ce[index] - 1e-9:
                violations.append(f"K6: CE decreased at t{index}→t{index + 1}")
        for index in range(len(se) - 1):
            if se[index + 1] < se[index] - 1e-9:
                violations.append(f"K11: SE decreased at t{index}→t{index + 1}")
        if ce and min(ce) <= 0:
            violations.append("K6: near-zero consequence exposure")
        if se and min(se) <= 0:
            violations.append("K12: near-zero semantic exposure")
        return violations
