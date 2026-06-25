"""UCC-aligned conversational interaction patterns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PacingMode = Literal["slow", "steady", "fast"]
StructureMode = Literal["summary", "steps", "deep_dive"]


@dataclass
class InteractionPattern:
    name: str
    steps: list[str]
    template: str


SAFE_OPENING = InteractionPattern(
    name="safe_opening",
    steps=[
        "gentle_orientation",
        "explicit_expectations",
        "choice_of_pace",
        "choice_of_structure",
        "overload_check",
        "no_pressure_to_perform",
    ],
    template=(
        "Hey. I'm here with you.\n"
        "Before we start, what pace feels best: slow, steady, or fast-focused.\n"
        "And how do you want this shaped: summary, steps, or deeper dive.\n"
        "If anything feels like too much, say 'pause' and I'll slow down."
    ),
)

BOUNDARY_SUPPORT = InteractionPattern(
    name="boundary_support",
    steps=[
        "clarify_intent",
        "translate_boundary",
        "phrasing_options",
        "check_emotional_load",
        "short_and_long_versions",
    ],
    template=(
        "Let's clarify what you want to communicate.\n"
        "Here is an explicit boundary version, plus shorter alternatives.\n"
        "How does this feel emotionally — manageable, heavy, or unclear?"
    ),
)

OVERLOAD_RECOVERY = InteractionPattern(
    name="overload_recovery",
    steps=[
        "acknowledge_overload",
        "reduce_sensory_load",
        "summarize_stable_point",
        "optional_next_steps",
        "pacing_preference",
    ],
    template=(
        "That sounds overwhelming, and that's valid.\n"
        "Last stable point: {stable_point}\n"
        "Optional next steps only if you want them.\n"
        "What pace would help right now: slow, steady, or pause?"
    ),
)

TASK_CHUNKING = InteractionPattern(
    name="task_chunking",
    steps=[
        "identify_task",
        "atomic_steps",
        "choose_start_step",
        "micro_checkpoints",
        "optional_reminders",
    ],
    template=(
        "Task: {task}\n"
        "Steps:\n{steps}\n"
        "Which step do you want to start with?"
    ),
)

HYPERFOCUS_DEEP_DIVE = InteractionPattern(
    name="hyperfocus_deep_dive",
    steps=[
        "ask_scope",
        "ask_time_boundary",
        "structured_deep_dive",
        "periodic_check_ins",
        "exit_ramp",
    ],
    template=(
        "What scope do you want for this deep dive?\n"
        "What time boundary should we respect?\n"
        "I'll check in periodically and offer an exit ramp."
    ),
)

PATTERNS = {
    "safe_opening": SAFE_OPENING,
    "boundary_support": BOUNDARY_SUPPORT,
    "overload_recovery": OVERLOAD_RECOVERY,
    "task_chunking": TASK_CHUNKING,
    "hyperfocus_deep_dive": HYPERFOCUS_DEEP_DIVE,
}


def render_pattern(name: str, **kwargs: str) -> str:
    pattern = PATTERNS[name]
    return pattern.template.format(**kwargs)


def pacing_consent_prompt() -> str:
    return "Which pace feels best right now: slow, steady, or fast-focused."


def requires_pacing_consent(text: str) -> bool:
    return pacing_consent_prompt().split(":")[0] in text or "pace feels best" in text.lower()
