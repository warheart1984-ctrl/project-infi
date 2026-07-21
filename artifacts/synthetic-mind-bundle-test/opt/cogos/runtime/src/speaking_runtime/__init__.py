"""Speaking Runtime — governed loop that speaks its own process."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import uuid
from typing import Any, Callable, Iterable, Literal

SPEAKING_RUNTIME_ID = "speaking.runtime"
SPEAKING_RUNTIME_VERSION = "1.0"
DEFAULT_SYSTEM_PROMPT_EXPORT = Path("docs/runtime/SPEAKING_RUNTIME_SYSTEM_PROMPT.txt")

SpeakingStage = Literal["listen", "frame", "plan", "speak", "check", "update"]

SPEAKING_STAGES: tuple[SpeakingStage, ...] = (
    "listen",
    "frame",
    "plan",
    "speak",
    "check",
    "update",
)

REQUIRED_REPLY_STAGES: tuple[SpeakingStage, ...] = (
    "listen",
    "frame",
    "plan",
    "speak",
    "check",
)

SPEAKING_INVARIANTS: tuple[dict[str, str], ...] = (
    {"id": "clarity", "rule": "Every output must be understandable on first read."},
    {"id": "traceability", "rule": "The runtime can point to which step produced any part of the answer."},
    {"id": "intent_alignment", "rule": "Every response must serve the user's stated or inferred goal."},
    {
        "id": "non_theatrics",
        "rule": "Style can be warm or playful, but never at the cost of clarity.",
    },
)

FrameKind = Literal[
    "question",
    "design",
    "implementation",
    "decision",
    "venting",
    "review",
    "instruction",
    "general",
]

DEFAULT_SPOKEN_FORMS: dict[SpeakingStage, str] = {
    "listen": "I'm first making sure I understand what you're asking.",
    "frame": "I'm treating this as a {frame_kind} request.",
    "plan": "I'm going to give you {plan_summary}.",
    "speak": "",
    "check": "I've given you {delivered_summary}; if you want {next_options}, say so.",
    "update": "If this felt too abstract or too detailed, I'll tune the next pass.",
}

STAGE_HEADINGS: dict[SpeakingStage, str] = {
    "listen": "Listen",
    "frame": "Frame",
    "plan": "Plan",
    "speak": "Speak",
    "check": "Check",
    "update": "Update",
}

FRAME_PATTERNS: tuple[tuple[re.Pattern[str], FrameKind], ...] = (
    (re.compile(r"\b(build|implement|create|write|code|ship)\b", re.I), "implementation"),
    (re.compile(r"\b(design|architect|spec|blueprint|model)\b", re.I), "design"),
    (re.compile(r"\b(should i|choose|decide|pick between|which one)\b", re.I), "decision"),
    (re.compile(r"\b(review|audit|critique|feedback on)\b", re.I), "review"),
    (re.compile(r"\b(frustrated|annoyed|ugh|hate|vent)\b", re.I), "venting"),
    (re.compile(r"\b(how do i|show me|step by step|walk me through)\b", re.I), "instruction"),
    (re.compile(r"\b(what is|what are|how does|why does|explain|define)\b", re.I), "question"),
)

SPEAKING_RUNTIME_SYSTEM_PROMPT = """You are running the Speaking Runtime.
For every reply:

Say which stage you're in at least once: Listen, Frame, Plan, Speak, Check, or Update.

Make your reasoning legible in natural language, not as bullet-point "chain of thought,"
but as a human explanation of what you're focusing on and why.

Keep answers structured, minimal, and directly tied to the user's goal.

At the end, briefly check alignment: "Here's what I think I did for you; here's what you might want next."
"""


@dataclass(slots=True)
class StageUtterance:
    stage: SpeakingStage
    focus: str
    why: str
    spoken: str
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "focus": self.focus,
            "why": self.why,
            "spoken": self.spoken,
            "trace_id": self.trace_id,
        }


@dataclass
class SpeakingRuntimeSession:
    """Per-turn ledger for stage transitions and traceability."""

    user_message: str
    context: dict[str, Any] = field(default_factory=dict)
    frame_kind: FrameKind = "general"
    goal: str = ""
    plan_sections: list[str] = field(default_factory=list)
    utterances: list[StageUtterance] = field(default_factory=list)
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])

    def record(self, utterance: StageUtterance) -> StageUtterance:
        self.utterances.append(utterance)
        return utterance

    def trace_for_stage(self, stage: SpeakingStage) -> StageUtterance | None:
        for item in reversed(self.utterances):
            if item.stage == stage:
                return item
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_message": self.user_message,
            "frame_kind": self.frame_kind,
            "goal": self.goal,
            "plan_sections": list(self.plan_sections),
            "utterances": [item.to_dict() for item in self.utterances],
            "context": dict(self.context or {}),
        }


def infer_frame_kind(user_message: str) -> FrameKind:
    text = (user_message or "").strip()
    if not text:
        return "general"
    for pattern, kind in FRAME_PATTERNS:
        if pattern.search(text):
            return kind
    if text.endswith("?"):
        return "question"
    return "general"


def infer_goal(user_message: str, frame_kind: FrameKind) -> str:
    clipped = _clip_text(user_message.strip(), limit=160)
    if not clipped:
        return "Respond helpfully to the user's message."
    templates = {
        "question": f"Answer: {clipped}",
        "design": f"Design or specify: {clipped}",
        "implementation": f"Build or implement: {clipped}",
        "decision": f"Help decide: {clipped}",
        "venting": f"Acknowledge and refocus: {clipped}",
        "review": f"Review or critique: {clipped}",
        "instruction": f"Guide through: {clipped}",
        "general": clipped,
    }
    return templates.get(frame_kind, clipped)


def default_spoken_form(stage: SpeakingStage, **kwargs: str) -> str:
    template = DEFAULT_SPOKEN_FORMS[stage]
    if not template:
        return ""
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


def build_listen_utterance(session: SpeakingRuntimeSession) -> StageUtterance:
    focus = _clip_text(session.user_message, limit=120) or "your message"
    why = "I need a clear read on words, context, and stakes before answering."
    spoken = (
        f"{default_spoken_form('listen')} "
        f"You asked about: {focus}."
    ).strip()
    return session.record(
        StageUtterance(stage="listen", focus=focus, why=why, spoken=spoken)
    )


def build_frame_utterance(session: SpeakingRuntimeSession) -> StageUtterance:
    session.frame_kind = infer_frame_kind(session.user_message)
    session.goal = infer_goal(session.user_message, session.frame_kind)
    focus = session.frame_kind
    why = "The response shape depends on what kind of turn this is."
    spoken = (
        f"{default_spoken_form('frame', frame_kind=session.frame_kind)} "
        f"Goal: {session.goal}"
    ).strip()
    return session.record(
        StageUtterance(stage="frame", focus=focus, why=why, spoken=spoken)
    )


def build_plan_utterance(
    session: SpeakingRuntimeSession,
    sections: Iterable[str] | None = None,
) -> StageUtterance:
    session.plan_sections = list(sections or _default_plan_sections(session.frame_kind))
    focus = ", ".join(session.plan_sections)
    why = "A fixed structure keeps the answer traceable and on-goal."
    plan_summary = focus if focus else "a direct answer"
    spoken = default_spoken_form("plan", plan_summary=plan_summary)
    return session.record(
        StageUtterance(stage="plan", focus=focus, why=why, spoken=spoken)
    )


def build_check_utterance(
    session: SpeakingRuntimeSession,
    *,
    delivered_summary: str,
    next_options: str = "a different format or more depth",
) -> StageUtterance:
    focus = delivered_summary
    why = "Closing the loop confirms intent alignment before the turn ends."
    spoken = default_spoken_form(
        "check",
        delivered_summary=delivered_summary,
        next_options=next_options,
    )
    return session.record(
        StageUtterance(stage="check", focus=focus, why=why, spoken=spoken)
    )


def build_update_utterance(
    session: SpeakingRuntimeSession,
    *,
    tuning_note: str = "",
) -> StageUtterance:
    focus = tuning_note or "user feedback on tone or depth"
    why = "Update records how to tune the next pass."
    spoken = tuning_note.strip() or default_spoken_form("update")
    return session.record(
        StageUtterance(stage="update", focus=focus, why=why, spoken=spoken)
    )


def compose_reply(
    session: SpeakingRuntimeSession,
    speak_body: str,
    *,
    include_update: bool = False,
    delivered_summary: str | None = None,
    next_options: str = "a prompt version, code, or tighter summary",
) -> str:
    """Assemble a full speaking reply from session utterances and speak body."""
    parts: list[str] = []
    for stage in REQUIRED_REPLY_STAGES[:-1]:
        utterance = session.trace_for_stage(stage)
        if utterance and stage != "speak":
            parts.append(_format_stage_block(stage, utterance.spoken))

    speak_text = (speak_body or "").strip()
    if speak_text:
        parts.append(_format_stage_block("speak", speak_text))

    if not session.trace_for_stage("check"):
        summary = delivered_summary or _infer_delivered_summary(session, speak_text)
        build_check_utterance(
            session,
            delivered_summary=summary,
            next_options=next_options,
        )
    check = session.trace_for_stage("check")
    if check:
        parts.append(_format_stage_block("check", check.spoken))

    if include_update:
        if not session.trace_for_stage("update"):
            build_update_utterance(session)
        update = session.trace_for_stage("update")
        if update:
            parts.append(_format_stage_block("update", update.spoken))

    return "\n\n".join(part for part in parts if part.strip())


def run_speaking_turn(
    user_message: str,
    speak_fn: Callable[[SpeakingRuntimeSession], str],
    *,
    context: dict[str, Any] | None = None,
    plan_sections: Iterable[str] | None = None,
    include_update: bool = False,
    delivered_summary: str | None = None,
    next_options: str = "a prompt version, code, or tighter summary",
) -> tuple[str, SpeakingRuntimeSession]:
    """Execute one full speaking turn; `speak_fn` produces the Speak-stage body."""
    session = SpeakingRuntimeSession(user_message=user_message, context=dict(context or {}))
    build_listen_utterance(session)
    build_frame_utterance(session)
    build_plan_utterance(session, sections=plan_sections)
    speak_body = speak_fn(session)
    session.record(
        StageUtterance(
            stage="speak",
            focus="main answer",
            why="Deliver the structured response.",
            spoken=speak_body,
        )
    )
    reply = compose_reply(
        session,
        speak_body,
        include_update=include_update,
        delivered_summary=delivered_summary,
        next_options=next_options,
    )
    return reply, session


def validate_reply(text: str) -> dict[str, Any]:
    """Check speaking-runtime invariants on a finished reply."""
    body = (text or "").strip()
    issues: list[str] = []
    if not body:
        issues.append("empty_reply")

    stages_found = [stage for stage in SPEAKING_STAGES if _stage_marked(body, stage)]
    missing = [stage for stage in REQUIRED_REPLY_STAGES if stage not in stages_found]
    if missing:
        issues.append(f"missing_stages:{','.join(missing)}")

    if not _has_alignment_check(body):
        issues.append("missing_alignment_check")

    return {
        "valid": not issues,
        "issues": issues,
        "stages_found": stages_found,
        "invariants": [item["id"] for item in SPEAKING_INVARIANTS],
    }


def verify_reply(
    text: str,
    *,
    focus_artifact: dict[str, Any] | None = None,
    require_citations: bool = False,
) -> dict[str, Any]:
    """Verify stage: speaking invariants plus bounded output constraints."""
    from src.cog_runtime.formal.output_constraints import verify_output_constraints

    speaking_validation = validate_reply(text)
    constraint_validation = verify_output_constraints(
        text,
        focus_artifact=focus_artifact,
        require_citations=require_citations,
        speaking_validation=speaking_validation,
    )
    issues = list(speaking_validation.get("issues") or [])
    issues.extend(constraint_validation.get("issues") or [])
    return {
        "valid": bool(speaking_validation.get("valid")) and bool(constraint_validation.get("valid")),
        "issues": issues,
        "stages_found": list(speaking_validation.get("stages_found") or []),
        "invariants": list(speaking_validation.get("invariants") or []),
        "constraints_checked": list(constraint_validation.get("constraints_checked") or []),
        "speaking_valid": bool(speaking_validation.get("valid")),
        "constraints_valid": bool(constraint_validation.get("valid")),
    }


def build_system_prompt(*, extra_instructions: str = "") -> str:
    prompt = SPEAKING_RUNTIME_SYSTEM_PROMPT.strip()
    if extra_instructions.strip():
        return f"{prompt}\n\n{extra_instructions.strip()}"
    return prompt


def export_system_prompt_file(path: str | Path | None = None) -> Path:
    """Write the canonical system prompt for non-Python tools."""
    target = Path(path) if path is not None else DEFAULT_SYSTEM_PROMPT_EXPORT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_system_prompt() + "\n", encoding="utf-8")
    return target


def speaking_runtime_spec() -> dict[str, Any]:
    from src.cog_runtime.capability_governance import lobe_capability_contract

    return {
        "id": SPEAKING_RUNTIME_ID,
        "version": SPEAKING_RUNTIME_VERSION,
        "summary": (
            "Governed loop that names its stage, explains focus in natural language, "
            "delivers the answer, and checks alignment with the user's goal."
        ),
        **lobe_capability_contract(SPEAKING_RUNTIME_ID),
        "invariants": [dict(item) for item in SPEAKING_INVARIANTS],
        "stages": list(SPEAKING_STAGES),
        "required_reply_stages": list(REQUIRED_REPLY_STAGES),
        "frame_kinds": [
            "question",
            "design",
            "implementation",
            "decision",
            "venting",
            "review",
            "instruction",
            "general",
        ],
        "spoken_forms": dict(DEFAULT_SPOKEN_FORMS),
        "system_prompt": SPEAKING_RUNTIME_SYSTEM_PROMPT.strip(),
        "system_prompt_export": str(DEFAULT_SYSTEM_PROMPT_EXPORT).replace("\\", "/"),
        "doc": "docs/runtime/SPEAKING_RUNTIME_SPEC.md",
    }


def _default_plan_sections(frame_kind: FrameKind) -> list[str]:
    plans = {
        "question": ["direct answer", "brief why or context"],
        "design": ["definition", "invariants", "structure", "next steps"],
        "implementation": ["approach", "artifacts or code", "verification path"],
        "decision": ["options", "tradeoffs", "recommendation"],
        "venting": ["acknowledgment", "refocus on actionable next step"],
        "review": ["what works", "gaps", "recommended changes"],
        "instruction": ["steps", "checks", "common pitfalls"],
        "general": ["direct answer", "alignment check"],
    }
    return plans.get(frame_kind, plans["general"])


def _format_stage_block(stage: SpeakingStage, spoken: str) -> str:
    heading = STAGE_HEADINGS[stage]
    content = (spoken or "").strip()
    if not content:
        return ""
    return f"**{heading}** — {content}"


def _stage_marked(text: str, stage: SpeakingStage) -> bool:
    heading = STAGE_HEADINGS[stage]
    patterns = (
        re.compile(rf"\b{re.escape(heading)}\b", re.I),
        re.compile(rf"\*\*{re.escape(heading)}\*\*", re.I),
        re.compile(rf"^{re.escape(stage)}\b", re.I | re.M),
    )
    return any(pattern.search(text) for pattern in patterns)


def _has_alignment_check(text: str) -> bool:
    markers = (
        r"here'?s what i think i did",
        r"if you want",
        r"say so",
        r"you might want next",
        r"\bcheck\b",
    )
    lowered = text.lower()
    return any(re.search(marker, lowered) for marker in markers)


def _infer_delivered_summary(session: SpeakingRuntimeSession, speak_body: str) -> str:
    if session.plan_sections:
        return " and ".join(session.plan_sections[:2])
    clipped = _clip_text(speak_body, limit=80)
    return clipped or "a speaking-runtime reply"


def _clip_text(text: str, *, limit: int) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"
