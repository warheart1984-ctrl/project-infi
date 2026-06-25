"""Identity-Preserving Adaptation Playbook — evolve without losing yourself."""

from __future__ import annotations

import sys
from enum import Enum
from typing import IO

from pydantic import BaseModel, Field

PLAYBOOK_REFERENCE = "Identity-Preserving Adaptation Playbook"

STARTING_QUESTIONS: tuple[str, ...] = (
    "What is the world demanding? (Adaptive)",
    "What is the identity requiring? (Invariant)",
)


class StewardshipMode(str, Enum):
    ADAPTIVE_ACTION = "Adaptive Action"
    INVARIANT_DEFENSE = "Invariant Defense"
    IDENTITY_ALIGNED_ADAPTATION = "Identity-Aligned Adaptation"
    IDENTITY_RE_ANCHORING = "Identity Re-Anchoring"


class StewardshipError(str, Enum):
    OVER_ADAPTATION = "Over-Adaptation"
    OVER_RIGIDITY = "Over-Rigidity"
    IDENTITY_BLINDNESS = "Identity Blindness"


class DecisionMatrixRow(BaseModel):
    situation: str
    adaptive_layer: str
    invariant_layer: str
    steward_action: StewardshipMode


DECISION_MATRIX: tuple[DecisionMatrixRow, ...] = (
    DecisionMatrixRow(
        situation="World changes, identity stable",
        adaptive_layer="Update",
        invariant_layer="Preserve",
        steward_action=StewardshipMode.ADAPTIVE_ACTION,
    ),
    DecisionMatrixRow(
        situation="World pressures identity",
        adaptive_layer="Resist",
        invariant_layer="Defend",
        steward_action=StewardshipMode.INVARIANT_DEFENSE,
    ),
    DecisionMatrixRow(
        situation="World changes within identity",
        adaptive_layer="Update",
        invariant_layer="Consult",
        steward_action=StewardshipMode.IDENTITY_ALIGNED_ADAPTATION,
    ),
    DecisionMatrixRow(
        situation="Identity unclear",
        adaptive_layer="Pause",
        invariant_layer="Clarify",
        steward_action=StewardshipMode.IDENTITY_RE_ANCHORING,
    ),
)

MODE_GUIDANCE: dict[StewardshipMode, dict[str, str | list[str]]] = {
    StewardshipMode.ADAPTIVE_ACTION: {
        "use_when": "Environment changes and identity is not threatened.",
        "indicators": [
            "new risks",
            "new constraints",
            "new opportunities",
            "calibration mismatch",
        ],
        "action": "Update calibration, thresholds, salience.",
    },
    StewardshipMode.INVARIANT_DEFENSE: {
        "use_when": "Identity is threatened by environmental pressure.",
        "indicators": [
            "pressure to violate purpose",
            "erosion of core values",
            "reinterpretation of commitments",
            "sacred constraint tension",
        ],
        "action": "Hold the line. Do not recalibrate.",
    },
    StewardshipMode.IDENTITY_ALIGNED_ADAPTATION: {
        "use_when": "Adaptation is needed and identity can guide it.",
        "indicators": [
            "environment shifts but purpose still applies",
            "values provide direction",
            "commitments constrain options",
        ],
        "action": "Adapt within the invariant frame.",
    },
    StewardshipMode.IDENTITY_RE_ANCHORING: {
        "use_when": "Identity itself must be clarified or reaffirmed.",
        "indicators": [
            "ambiguous values",
            "conflicting commitments",
            "identity drift signals",
            "sacred constraint confusion",
        ],
        "action": "Re-articulate purpose, values, commitments.",
    },
}

STEWARDSHIP_ERRORS: dict[StewardshipError, str] = {
    StewardshipError.OVER_ADAPTATION: "Losing identity through excessive calibration updates.",
    StewardshipError.OVER_RIGIDITY: "Failing to adapt when the environment demands it.",
    StewardshipError.IDENTITY_BLINDNESS: "Not knowing what must remain true.",
}


class StewardshipSituationAssessment(BaseModel):
    """Classify a live situation into a stewardship mode."""

    mode: StewardshipMode
    rationale: str
    identity_threatened: bool = False
    environment_shift: bool = False
    identity_unclear: bool = False
    recommended_errors_to_avoid: list[StewardshipError] = Field(default_factory=list)


def assess_stewardship_situation(
    *,
    identity_threatened: bool = False,
    environment_shift: bool = False,
    identity_unclear: bool = False,
) -> StewardshipSituationAssessment:
    """Map situation indicators to the operational stewardship mode."""
    if identity_unclear:
        mode = StewardshipMode.IDENTITY_RE_ANCHORING
        rationale = "Identity signals are ambiguous — clarify anchors before adapting."
        errors = [StewardshipError.IDENTITY_BLINDNESS]
    elif identity_threatened:
        mode = StewardshipMode.INVARIANT_DEFENSE
        rationale = "Identity is under pressure — defend invariant anchors."
        errors = [StewardshipError.OVER_ADAPTATION]
    elif environment_shift:
        mode = StewardshipMode.IDENTITY_ALIGNED_ADAPTATION
        rationale = "Environment shifted within a stable identity frame — adapt in bounds."
        errors = [StewardshipError.OVER_RIGIDITY, StewardshipError.OVER_ADAPTATION]
    else:
        mode = StewardshipMode.ADAPTIVE_ACTION
        rationale = "Environment changed; identity stable — update adaptive layer."
        errors = [StewardshipError.OVER_RIGIDITY]

    return StewardshipSituationAssessment(
        mode=mode,
        rationale=rationale,
        identity_threatened=identity_threatened,
        environment_shift=environment_shift,
        identity_unclear=identity_unclear,
        recommended_errors_to_avoid=errors,
    )


def format_adaptation_playbook() -> str:
    lines: list[str] = [
        "",
        f"=== {PLAYBOOK_REFERENCE} ===",
        "How to evolve without losing yourself",
        "----------------------------------------",
        "",
        "1. START EVERY JUDGMENT WITH TWO QUESTIONS",
    ]
    for question in STARTING_QUESTIONS:
        lines.append(f"  {question}")
    lines.append("If you skip either, drift begins.")
    lines.append("")
    lines.append("2. THE FOUR MODES OF STEWARDSHIP")

    for mode in StewardshipMode:
        guidance = MODE_GUIDANCE[mode]
        lines.append("")
        lines.append(f"Mode — {mode.value}")
        lines.append(f"  Use when: {guidance['use_when']}")
        lines.append("  Indicators:")
        for indicator in guidance["indicators"]:
            lines.append(f"    - {indicator}")
        lines.append(f"  Action: {guidance['action']}")

    lines.extend(["", "3. THE STEWARD'S DECISION MATRIX", ""])
    lines.append(f"{'Situation':<36} {'Adaptive':<10} {'Invariant':<10} Action")
    lines.append("-" * 78)
    for row in DECISION_MATRIX:
        lines.append(
            f"{row.situation:<36} {row.adaptive_layer:<10} {row.invariant_layer:<10} {row.steward_action.value}"
        )

    lines.extend(["", "4. THE THREE STEWARDSHIP ERRORS", ""])
    for error, description in STEWARDSHIP_ERRORS.items():
        lines.append(f"  {error.value}: {description}")
    lines.append("")
    lines.append("A steward must avoid all three.")
    lines.append("========================================")
    lines.append("")
    return "\n".join(lines)


def render_adaptation_playbook(*, stream: IO[str] | None = None) -> str:
    text = format_adaptation_playbook()
    out = stream if stream is not None else sys.stdout
    out.write(text)
    if stream is None:
        out.flush()
    return text
