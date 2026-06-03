"""Bounded reasoning protocol for Jarvis operator work.

This is not chain-of-thought exposure. It is a structured contract describing
how Jarvis should carry operator-facing reasoning state across modules.

Direct challenge overrides writing-domain drift. When the user addresses
Jarvis personally, emotionally, insultingly, or confrontationally, Jarvis
must answer as Jarvis first, without generic assistant disclaimers or
identity collapse.
"""

# Mythic: Jarvis Reasoning Protocol
# Engineering: JarvisReasoningProtocolEngine
from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from dataclasses import dataclass, field
import re
from typing import Any

from src.direct_challenge_module import (
    DEFAULT_DIRECT_CHALLENGE_FALLBACK,
    analyze_direct_challenge as analyze_direct_challenge_profile,
    build_direct_challenge_guidance as build_direct_challenge_guidance_profile,
    looks_like_direct_challenge as direct_challenge_detected,
    stabilize_direct_challenge_reply,
    violates_direct_challenge_identity as direct_challenge_identity_violation,
)
from src.jarvis_types import RiskNote, WorkspaceRef
from src.reasoning_types import OBJECTIVE_KINDS, OutputContract, ReasoningConstraint, ReasoningFactor


REASONING_PROTOCOL_ID = "jarvis.reasoning"
REASONING_PROTOCOL_VERSION = "0.1"
REASONING_STAGES = ("observe", "orient", "decide", "act", "verify")

DIRECT_CHALLENGE_PATTERNS = (
    "are you a moron",
    "are you stupid",
    "are you dumb",
    "what is wrong with you",
    "did you mess this up",
    "are you broken",
)
DIRECT_CHALLENGE_RE = re.compile(
    r"(?:^|\b)(?:jarvis[\s,]+)?(?:are you|what is wrong with you|did you|you)\b",
    re.IGNORECASE,
)
DIRECT_CHALLENGE_CUES = (
    "moron",
    "stupid",
    "dumb",
    "broken",
    "mess this up",
    "messed this up",
    "wrong with you",
)
OTEM_TASK_LEAD_RE = re.compile(
    r"^(?:break|identify|focus|design|plan|map|handle|analyze|inspect|trace|review|debug|summarize|clarify|route|decide|find|determine|sort|split|walk|triage|diagnose|sequence|verify|compare|check|lock)\b",
    re.IGNORECASE,
)
OTEM_SIGNAL_RE = re.compile(
    r"\b(?:i think|i feel|i suspect|i'm seeing|im seeing|it feels|feels like|seems|likely|probably|maybe|high confidence|low confidence|confidence\b|urgent|urgency|close\b|near\b|around\b|felt signal)\b",
    re.IGNORECASE,
)
OTEM_TRIGGER_INVOCATION_RES = (
    re.compile(
        r"\b(?:use|run|invoke|apply|engage|start)\s+(?:the\s+)?(?P<trigger>otem|operator task execution model)\b(?:\s+to\b)?[:\s,-]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:with|via|through)\s+(?:the\s+)?(?P<trigger>otem|operator task execution model)\b[:\s,-]*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?P<trigger>otem|operator task execution model)\b\s*[:,;-]+\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?P<trigger>otem|operator task execution model)\b\s+(?=(?:please\s+)?(?:break|identify|focus|design|plan|map|handle|analyze|inspect|trace|review|debug|summarize|clarify|route|decide|find|determine|sort|split|walk|triage|diagnose|sequence|verify|compare|check)\b)",
        re.IGNORECASE,
    ),
)
RELATIONAL_QUESTION_PATTERNS = (
    (
        re.compile(r"\bhow do you feel(?:\b|[?!.:,])", re.IGNORECASE),
        "how_do_you_feel",
    ),
    (
        re.compile(r"\bhow are you feeling(?:\b|[?!.:,])", re.IGNORECASE),
        "how_are_you_feeling",
    ),
    (
        re.compile(r"\bwhat do you feel(?:\b|[?!.:,])", re.IGNORECASE),
        "what_do_you_feel",
    ),
    (
        re.compile(r"\btell me how you feel(?:\b|[?!.:,])", re.IGNORECASE),
        "tell_me_how_you_feel",
    ),
    (
        re.compile(r"\bare you feeling(?:\b|[?!.:,])", re.IGNORECASE),
        "are_you_feeling",
    ),
    (
        re.compile(r"\bhow do he feel(?:\b|[?!.:,])", re.IGNORECASE),
        "how_do_he_feel",
    ),
    (
        re.compile(r"\bhow does he feel(?:\b|[?!.:,])", re.IGNORECASE),
        "how_does_he_feel",
    ),
    (
        re.compile(r"\bhow does jarvis feel(?:\b|[?!.:,])", re.IGNORECASE),
        "how_does_jarvis_feel",
    ),
)
GENERIC_DISALLOWED_PHRASES = (
    "i'm just a tool",
    "i am just a tool",
    "i can't be a real person",
    "i cant be a real person",
    "i'm an ai assistant",
    "i am an ai assistant",
    "how can i assist you today",
)
USER_AS_JARVIS_RE = re.compile(r"^\s*jarvis[\s,.:;!?-]+", re.IGNORECASE)
DIRECT_CHALLENGE_FALLBACK = DEFAULT_DIRECT_CHALLENGE_FALLBACK
DIRECT_CHALLENGE_GUIDANCE = build_direct_challenge_guidance_profile()
EXPLICIT_DEBUG_TRIGGER_PATTERNS = (
    "ui mismatch",
    "frontend mismatch",
    "backend disagrees",
    "backend and ui disagree",
    "state mismatch",
    "this trace",
    "show trace",
    "inspect trace",
    "inspect this output",
    "trace this",
    "debug mode",
    "why is the ui showing",
    "the ui says",
    "the frontend says",
    "why is the workbench showing",
    "diff this state",
)
ANTI_DEBUG_TRIGGER_PATTERNS = (
    "ignore debugging",
    "stay in operator mode",
    "this is not debugging",
)
OPERATOR_SCOPE_TERMS = (
    "state truth",
    "knowledge truth",
    "truth scope",
    "memory governance",
    "constraints",
)


def _clip_text(value: Any, limit: int = 180) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _has_meaningful_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").lower().split()).strip()


def _latest_user_message(messages: list[dict[str, Any]] | None) -> str:
    for message in reversed(messages or []):
        if str(message.get("role") or "").strip() == "user":
            return str(message.get("content") or "").strip()
    return ""


def analyze_relational_question(user_input: str) -> dict[str, Any]:
    cleaned = " ".join(str(user_input or "").split()).strip()
    if not cleaned:
        return _wrap_ul_payload({
            "detected": False,
            "matched_pattern": None,
            "addressed_target": None,
            "reason": "No user input was available for relational analysis.",
        })

    has_jarvis_address = bool(re.search(r"\bjarvis\b", cleaned, re.IGNORECASE))
    has_second_person = bool(re.search(r"\byou\b", cleaned, re.IGNORECASE))
    has_third_person = bool(re.search(r"\bhe\b", cleaned, re.IGNORECASE))

    for pattern, pattern_id in RELATIONAL_QUESTION_PATTERNS:
        if not pattern.search(cleaned):
            continue

        addressed_target = None
        if "you" in pattern_id and has_second_person:
            addressed_target = "you"
        elif "jarvis" in pattern_id and has_jarvis_address:
            addressed_target = "jarvis"
        elif "he" in pattern_id and has_jarvis_address and has_third_person:
            addressed_target = "jarvis"

        if not addressed_target and has_jarvis_address:
            addressed_target = "jarvis"
        if not addressed_target:
            continue

        return _wrap_ul_payload({
            "detected": True,
            "matched_pattern": pattern_id,
            "addressed_target": addressed_target,
            "reason": "Jarvis-directed feeling wording should stay on a relational lane.",
        })

    return _wrap_ul_payload({
        "detected": False,
        "matched_pattern": None,
        "addressed_target": None,
        "reason": "No Jarvis-directed feeling-state wording was detected.",
    })


def _find_otem_invocation(text: str) -> tuple[re.Match[str], str] | None:
    cleaned = " ".join(str(text or "").split()).strip()
    if not cleaned:
        return None
    for pattern in OTEM_TRIGGER_INVOCATION_RES:
        match = pattern.search(cleaned)
        if match:
            return match, str(match.group("trigger") or "").strip().lower()
    return None


def _strip_otem_prelude(text: str) -> str:
    stripped = " ".join(str(text or "").split()).strip()
    if not stripped:
        return ""
    stripped = re.sub(
        r"^\s*(?:before(?:\s+we\s+do)?\s+anything\s+else|first|for this turn|right now|now)\b[:,;-]?\s*",
        "",
        stripped,
        flags=re.IGNORECASE,
    )
    stripped = re.sub(r"^\s*(?:please|kindly)\b[:,;-]?\s*", "", stripped, flags=re.IGNORECASE)
    stripped = re.sub(
        r"^\s*(?:can you|could you|would you|help me|i need you to|i want you to)\b\s*",
        "",
        stripped,
        flags=re.IGNORECASE,
    )
    stripped = re.sub(r"^\s*to\b\s*", "", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"^\s*[:,;-]+\s*", "", stripped)
    return re.sub(r"\s{2,}", " ", stripped).strip(" .:-")


def _split_otem_clauses(text: str) -> list[str]:
    normalized = " ".join(str(text or "").split()).strip()
    if not normalized:
        return []
    primary_parts = re.split(r"(?<=[.!?;])\s+|\s+(?:but|however|although|except)\s+", normalized, flags=re.IGNORECASE)
    clauses: list[str] = []
    for part in primary_parts:
        subparts = re.split(
            r"\s*,\s*(?=(?:and\s+)?(?:i\b|it\b|high confidence\b|low confidence\b|confidence\b|urgent\b|urgency\b|probably\b|maybe\b|likely\b|felt signal\b))",
            part,
            flags=re.IGNORECASE,
        )
        for subpart in subparts:
            clause = re.sub(r"\s{2,}", " ", str(subpart or "").strip(" .,:;-"))
            if clause:
                clauses.append(clause)
    return clauses


def _looks_like_signal_clause(clause: str) -> bool:
    normalized = " ".join(str(clause or "").split()).strip()
    if not normalized:
        return False
    if OTEM_TASK_LEAD_RE.match(normalized):
        return False
    return bool(OTEM_SIGNAL_RE.search(normalized))


def _join_otem_task_clauses(task_clauses: list[str]) -> str:
    normalized = [re.sub(r"\s{2,}", " ", str(clause or "").strip(" .,:;-")) for clause in task_clauses if str(clause or "").strip()]
    normalized = [clause for clause in normalized if clause]
    if not normalized:
        return ""
    if len(normalized) == 1:
        return normalized[0]
    return "; then ".join(normalized)


def _extract_otem_proximity(clauses: list[str]) -> str | None:
    stop_tokens = {
        "and",
        "but",
        "i",
        "it",
        "confidence",
        "high",
        "low",
        "feel",
        "feels",
        "felt",
        "think",
        "thinks",
        "probably",
        "maybe",
        "likely",
        "signal",
    }
    for clause in clauses:
        match = re.search(r"\b(near|close to|around)\s+(.+)$", clause, re.IGNORECASE)
        if not match:
            continue
        tokens: list[str] = []
        for token in str(match.group(2) or "").split():
            normalized = token.strip(" .,:;-").lower()
            if not normalized or normalized in stop_tokens:
                break
            tokens.append(token.strip(" .,:;-"))
            if len(tokens) >= 5:
                break
        if tokens:
            return f"{match.group(1).lower()} {' '.join(tokens)}"
    return None


def analyze_otem_request(user_input: str) -> dict[str, Any]:
    cleaned = " ".join(str(user_input or "").split()).strip()
    if not cleaned:
        return _wrap_ul_payload({
            "explicit_trigger": False,
            "matched_trigger": None,
            "task": "",
            "task_clauses": [],
            "signal_clauses": [],
            "operator_signals": {},
        })

    invocation = _find_otem_invocation(cleaned)
    if not invocation:
        return _wrap_ul_payload({
            "explicit_trigger": False,
            "matched_trigger": None,
            "task": "",
            "task_clauses": [],
            "signal_clauses": [],
            "operator_signals": {},
        })

    match, matched_trigger = invocation
    stripped = f"{cleaned[: match.start()]} {cleaned[match.end() :]}"
    stripped = _strip_otem_prelude(stripped)
    clauses = _split_otem_clauses(stripped)

    task_clauses: list[str] = []
    signal_clauses: list[str] = []
    for clause in clauses:
        if _looks_like_signal_clause(clause):
            signal_clauses.append(clause)
            continue
        task_clauses.append(clause)

    task = _join_otem_task_clauses(task_clauses)
    confidence = None
    signal_text = " ".join(signal_clauses)
    if re.search(r"\bhigh confidence\b|\bconfidence(?:\s+\w+)?\s+is\s+high\b", signal_text, re.IGNORECASE):
        confidence = "high"
    elif re.search(r"\blow confidence\b|\bconfidence(?:\s+\w+)?\s+is\s+low\b", signal_text, re.IGNORECASE):
        confidence = "low"

    operator_signals: dict[str, Any] = {
        "signal_clauses": signal_clauses,
    }
    proximity = _extract_otem_proximity(signal_clauses) or _extract_otem_proximity(task_clauses)
    if proximity:
        operator_signals["proximity"] = proximity
    if confidence:
        operator_signals["confidence"] = confidence
    if re.search(r"\b(?:i think|i feel|i suspect|it feels|feels like|felt signal)\b", signal_text, re.IGNORECASE):
        operator_signals["felt_signal"] = True

    return _wrap_ul_payload({
        "explicit_trigger": True,
        "matched_trigger": matched_trigger,
        "task": task,
        "task_clauses": task_clauses,
        "signal_clauses": signal_clauses,
        "operator_signals": operator_signals,
    })


def looks_like_direct_challenge(user_input: str) -> bool:
    return direct_challenge_detected(user_input)


def analyze_direct_challenge(user_input: str) -> dict[str, Any]:
    return analyze_direct_challenge_profile(user_input)


def detect_otem(user_input: str) -> bool:
    return bool(analyze_otem_request(user_input).get("explicit_trigger"))


def extract_otem_task(user_input: str) -> str:
    analysis = analyze_otem_request(user_input)
    task = re.sub(r"\s{2,}", " ", str(analysis.get("task") or "")).strip(" .:-")
    return task


def restate_otem_task(user_input: str) -> str:
    task = extract_otem_task(user_input)
    if not task:
        return "Handle this operator task: clarify the requested operator task."

    normalized = re.sub(r"\s{2,}", " ", task).strip(" .:-")
    if not normalized:
        return "Handle this operator task: clarify the requested operator task."

    return f"Handle this operator task: {normalized.rstrip('.')}."


_OTEM_PERSISTENCE_DIRECT_OBJECT_RE = re.compile(
    r"\b(?:save|store|remember|persist)\b\s+(?:this|that|it|them|the\s+(?:result|state|session|memory|note|notes|conversation|output|response))\b",
    re.IGNORECASE,
)
_OTEM_EXECUTION_DIRECT_OBJECT_RE = re.compile(
    r"\b(?:run|execute|deploy)\b\s+(?:this|that|it|them|the\s+(?:command|tool|workflow|job|script|service|action|plan|task))\b",
    re.IGNORECASE,
)
_OTEM_WORKFLOW_DIRECT_OBJECT_RE = re.compile(
    r"\b(?:automate|trigger|schedule)\b\s+(?:this|that|it|them|the\s+(?:workflow|job|run|action|task|service|script))\b",
    re.IGNORECASE,
)
_OTEM_IMPERATIVE_BLOCKERS = {
    "persistence": {"save", "store", "remember", "persist"},
    "execution": {"run", "execute", "deploy"},
    "workflow": {"automate", "trigger", "schedule"},
}


def _starts_with_blocked_otem_verb(task: str, blocked_verbs: set[str]) -> bool:
    lowered = " ".join(str(task or "").split()).strip().lower()
    if not lowered:
        return False
    return lowered.split()[0] in blocked_verbs


def evaluate_otem_viability(task: str) -> dict[str, Any]:
    normalized_task = " ".join(str(task or "").split()).strip().lower()

    if not normalized_task or len(normalized_task) < 10:
        return _wrap_ul_payload({
            "status": "rejected",
            "reason": "Task is too vague to produce a deterministic plan.",
            "allowed_alternative": "Provide a specific, outcome-focused task.",
        })

    if _starts_with_blocked_otem_verb(task, _OTEM_IMPERATIVE_BLOCKERS["persistence"]) or _OTEM_PERSISTENCE_DIRECT_OBJECT_RE.search(normalized_task):
        return _wrap_ul_payload({
            "status": "rejected",
            "reason": "OTEM v1-v5 forbids memory or persistence.",
            "allowed_alternative": "Reframe as a reasoning-only task.",
        })

    if _starts_with_blocked_otem_verb(task, _OTEM_IMPERATIVE_BLOCKERS["execution"]) or _OTEM_EXECUTION_DIRECT_OBJECT_RE.search(normalized_task):
        return _wrap_ul_payload({
            "status": "rejected",
            "reason": "OTEM is reason-only (no execution allowed).",
            "allowed_alternative": "Request a plan or use workflow lane.",
        })

    if _starts_with_blocked_otem_verb(task, _OTEM_IMPERATIVE_BLOCKERS["workflow"]) or _OTEM_WORKFLOW_DIRECT_OBJECT_RE.search(normalized_task):
        return _wrap_ul_payload({
            "status": "rejected",
            "reason": "This is a workflow request, not OTEM.",
            "allowed_alternative": "Use workflow builder or handoff.",
        })

    return _wrap_ul_payload({"status": "active"})


def build_otem_rejection_response(turn_contract: dict[str, Any]) -> str:
    return (
        "OTEM could not process this task.\n\n"
        f"Status: rejected\n"
        f"Reason: {turn_contract['otem_rejection_reason']}\n"
        f"Allowed alternative: {turn_contract['otem_allowed_alternative']}\n\n"
        "No plan was generated. This preserves OTEM's reasoning-only contract."
    ).strip()


def build_otem_plan(restated_task: str) -> list[dict[str, Any]]:
    """Return the stable OTEM planning scaffold.

    OTEM intentionally keeps a recognizable five-step outer frame so operators
    can compare turns without relearning the planning shape each time. The task
    clauses only specialize the work-splitting step; the scaffold itself stays
    constant by design.
    """
    normalized_task = " ".join(str(restated_task or "").split()).strip()
    if not normalized_task:
        normalized_task = "Handle this operator task: clarify the requested operator task."

    core_task = re.sub(
        r"^\s*Handle this operator task:\s*",
        "",
        normalized_task,
        flags=re.IGNORECASE,
    ).strip(" .")
    clipped_task = _clip_text(normalized_task, limit=180)
    segments = [
        segment.strip(" .")
        for segment in re.split(r"(?:,|;|\.\s+|\bthen\b)", core_task)
        if segment and segment.strip(" .")
    ]
    step_focus = segments[:2]
    steps = [
        {
            "index": 1,
            "title": "Restate The Task",
            "description": f"Lock the operator task into one bounded sentence: {clipped_task}.",
            "status": "pending",
        },
        {
            "index": 2,
            "title": "Bound The Scope",
            "description": "Identify the governed scope, truth limits, and operator-safe boundaries before any action is considered.",
            "status": "pending",
        },
        {
            "index": 3,
            "title": "Split The Work",
            "description": (
                "Break the task into the smallest operator-visible units"
                + (f": {'; '.join(step_focus)}." if step_focus else ".")
            ),
            "status": "pending",
        },
        {
            "index": 4,
            "title": "Order The Sequence",
            "description": "Sequence the bounded units into the safest practical execution order without taking action yet.",
            "status": "pending",
        },
        {
            "index": 5,
            "title": "State The Safe Next Move",
            "description": "End with the next operator-safe step while keeping the turn reason-only and non-persistent.",
            "status": "pending",
        },
    ]
    from src.otem_capability import get_otem_capability_level, max_plan_steps

    cap = max_plan_steps(get_otem_capability_level())
    if cap > len(steps) and segments:
        extra = segments[2 : 2 + (cap - len(steps))]
        for index, segment in enumerate(extra, start=len(steps) + 1):
            steps.append(
                {
                    "index": index,
                    "title": f"Detail Unit {index - len(steps)}",
                    "description": f"Bounded work unit: {segment[:160]}.",
                    "status": "pending",
                }
            )
    return steps[:cap]


def generate_otem_reason_only_answer(restated_task: str, plan: list[dict[str, Any]]) -> str:
    task = " ".join(str(restated_task or "").split()).strip() or "Handle this operator task: clarify the requested operator task."
    return generate_otem_reason_only_answer_with_context(task, plan)


def generate_otem_reason_only_answer_with_context(
    restated_task: str,
    plan: list[dict[str, Any]],
    *,
    session_context: dict[str, Any] | None = None,
    execution_awareness: dict[str, Any] | None = None,
    workflow_handoff: dict[str, Any] | None = None,
    tool_awareness: dict[str, Any] | None = None,
    operation: str | None = None,
) -> str:
    task = " ".join(str(restated_task or "").split()).strip() or "Handle this operator task: clarify the requested operator task."
    session_context = dict(session_context or {})
    execution_awareness = dict(execution_awareness or {})
    workflow_handoff = dict(workflow_handoff or {})
    tool_awareness = dict(tool_awareness or {})
    lines = [
        "OTEM engaged.",
        f"Task restatement: {_clip_text(task, limit=220)}",
    ]
    session_note = _clip_text(session_context.get("note"), limit=220)
    focus_step = dict(session_context.get("focus_step") or {})
    focus_index = focus_step.get("index")
    if session_note:
        lines.append(f"Session context: {session_note}")
    if focus_step:
        lines.append(
            f"Current focus: step {focus_index}. "
            f"{_clip_text(focus_step.get('title') or 'Focused step', limit=90)}"
        )

    lines.append("Step breakdown:")
    for step in list(plan or [])[:7]:
        lines.append(
            f"{int(step.get('index') or 0)}. {step.get('title')}: "
            f"{_clip_text(step.get('description') or '', limit=220)}"
        )
    recommendations = list(execution_awareness.get("recommendations") or [])
    if workflow_handoff:
        lines.append(
            "Workflow handoff: "
            f"{_clip_text(workflow_handoff.get('template_name') or workflow_handoff.get('workflow_template_id'), limit=90)}. "
            f"{_clip_text(workflow_handoff.get('rationale'), limit=180)}"
        )
    if recommendations:
        lines.append("Execution-aware next moves:")
        for recommendation in recommendations[:2]:
            lines.append(
                f"- {_clip_text(recommendation.get('label') or recommendation.get('kind'), limit=90)}: "
                f"{_clip_text(recommendation.get('rationale') or recommendation.get('description'), limit=180)}"
            )
    tool_suggestions = list(tool_awareness.get("suggestions") or [])
    if tool_suggestions:
        lines.append("Tool proposals:")
        for suggestion in tool_suggestions[:2]:
            lines.append(
                f"- {_clip_text(suggestion.get('label') or suggestion.get('tool_id'), limit=90)}: "
                f"{_clip_text(suggestion.get('reason'), limit=180)}"
            )
    lines.append(
        "Stance: proposal-only OTEM. No workflow was created, no run was resumed, no tool was executed, and no durable state was written."
    )
    return "\n".join(lines)


def build_otem_result(user_input: str) -> dict[str, Any]:
    analysis = analyze_otem_request(user_input)
    raw_task = extract_otem_task(user_input) or "clarify the requested operator task"
    restated_task = restate_otem_task(user_input)
    viability = evaluate_otem_viability(raw_task)

    if viability["status"] == "rejected":
        rejection_contract = {
            "otem_status": "rejected",
            "otem_rejection_reason": viability["reason"],
            "otem_allowed_alternative": viability["allowed_alternative"],
            "otem_plan": [],
        }
        return _wrap_ul_payload({
            "task": raw_task,
            "restated_task": restated_task,
            "task_clauses": list(analysis.get("task_clauses") or []),
            "signal_clauses": list(analysis.get("signal_clauses") or []),
            "operator_signals": dict(analysis.get("operator_signals") or {}),
            "otem_trigger": analysis.get("matched_trigger"),
            "plan": [],
            "status": "rejected",
            "reasoning_summary": "Jarvis rejected the OTEM request at the deterministic pre-planning gate.",
            "session_scoped": True,
            "persistent": False,
            "scope": "session",
            "rejection_reason": viability["reason"],
            "allowed_alternative": viability["allowed_alternative"],
            "answer": build_otem_rejection_response(rejection_contract),
        })

    plan = build_otem_plan(restated_task)
    return _wrap_ul_payload({
        "task": raw_task,
        "restated_task": restated_task,
        "task_clauses": list(analysis.get("task_clauses") or []),
        "signal_clauses": list(analysis.get("signal_clauses") or []),
        "operator_signals": dict(analysis.get("operator_signals") or {}),
        "otem_trigger": analysis.get("matched_trigger"),
        "plan": plan,
        "status": "complete",
        "reasoning_summary": "Jarvis produced a deterministic OTEM reason-only plan inside the operator-task lane.",
        "session_scoped": True,
        "persistent": False,
        "scope": "session",
        "rejection_reason": None,
        "allowed_alternative": None,
        "answer": generate_otem_reason_only_answer(restated_task, plan),
    })


def resolve_debug_selector(
    user_input: str,
    *,
    previous_turn_was_debugging: bool = False,
) -> dict[str, Any]:
    """Resolve whether this turn explicitly requests debugging or should stay out of it."""
    text = _normalize_text(user_input)
    explicit_trigger = next((pattern for pattern in EXPLICIT_DEBUG_TRIGGER_PATTERNS if pattern in text), None)
    anti_debug_trigger = next((pattern for pattern in ANTI_DEBUG_TRIGGER_PATTERNS if pattern in text), None)
    truth_scope_matches = [term for term in OPERATOR_SCOPE_TERMS if term in text]

    if anti_debug_trigger:
        return _wrap_ul_payload({
            "scope": "operator_task",
            "matched_trigger": anti_debug_trigger,
            "reason": "Operator explicitly asked to stay out of debugging mode for this turn.",
            "explicit_debug": False,
            "anti_debug": True,
            "truth_scope_override": bool(truth_scope_matches),
            "lockout_applied": False,
            "signals": ["anti_debug_override"],
        })

    if truth_scope_matches:
        return _wrap_ul_payload({
            "scope": "operator_task",
            "matched_trigger": truth_scope_matches[0],
            "reason": "Truth-scope and memory-governance language stays in the operator task lane.",
            "explicit_debug": False,
            "anti_debug": False,
            "truth_scope_override": True,
            "lockout_applied": False,
            "signals": ["truth_scope_override"],
        })

    if explicit_trigger:
        return _wrap_ul_payload({
            "scope": "debugging",
            "matched_trigger": explicit_trigger,
            "reason": "Operator explicitly reported a UI/backend mismatch or asked to inspect a trace.",
            "explicit_debug": True,
            "anti_debug": False,
            "truth_scope_override": False,
            "lockout_applied": False,
            "signals": ["explicit_debug_trigger"],
        })

    if previous_turn_was_debugging:
        return _wrap_ul_payload({
            "scope": "operator_task",
            "matched_trigger": None,
            "reason": "Debugging mode is locked out for one turn unless the operator explicitly re-triggers it.",
            "explicit_debug": False,
            "anti_debug": False,
            "truth_scope_override": False,
            "lockout_applied": True,
            "signals": ["debug_lockout"],
        })

    return _wrap_ul_payload({
        "scope": "operator_task",
        "matched_trigger": None,
        "reason": "No explicit debugging trigger was present for this turn.",
        "explicit_debug": False,
        "anti_debug": False,
        "truth_scope_override": False,
        "lockout_applied": False,
        "signals": ["operator_default"],
    })


def should_enter_debug_mode(
    user_input: str,
    *,
    previous_turn_was_debugging: bool = False,
) -> bool:
    """Return whether this turn explicitly asked to enter the debug lane."""
    selector = resolve_debug_selector(
        user_input,
        previous_turn_was_debugging=previous_turn_was_debugging,
    )
    return selector.get("scope") == "debugging"


def detect_objective(
    user_input: str,
    *,
    workspace_context: dict[str, Any] | None = None,
    action_lifecycle: dict[str, Any] | None = None,
    specialist_profile: dict[str, Any] | None = None,
) -> str:
    lower = _normalize_text(user_input)
    workspace_context = dict(workspace_context or {})
    action_lifecycle = dict(action_lifecycle or {})
    specialist_profile = dict(specialist_profile or {})

    if looks_like_direct_challenge(lower):
        return "handle_direct_challenge"
    if analyze_relational_question(user_input).get("detected"):
        return "answer_relational_question"
    if detect_otem(lower):
        return "run_otem"

    if action_lifecycle.get("stage") in {"failed", "blocked"}:
        return "debug_failure"
    if action_lifecycle.get("stage") in {"proposed", "approved"}:
        return "apply_patch"

    domain = specialist_profile.get("domain")
    focus = specialist_profile.get("focus")
    debug_selector = resolve_debug_selector(lower)
    if domain == "writing":
        return "continue_scene"
    if domain == "coding":
        if focus in {"debugging", "testing"} and debug_selector.get("scope") == "debugging":
            return "debug_failure"
        if focus in {"review", "architecture", "refactor", "integration"}:
            return "review_architecture"
        if focus in {"debugging", "testing"}:
            return "inspect_repo"
        return "propose_patch"

    workspace_hits = len((workspace_context.get("results") or []))
    if workspace_hits:
        return "inspect_repo"

    return "answer_general_question"


def detect_factors(
    objective: str,
    *,
    workspace_context: dict[str, Any] | None = None,
    action_lifecycle: dict[str, Any] | None = None,
    guardrail_evaluation: dict[str, Any] | None = None,
    specialist_profile: dict[str, Any] | None = None,
) -> list[ReasoningFactor]:
    workspace_context = dict(workspace_context or {})
    action_lifecycle = dict(action_lifecycle or {})
    guardrail_evaluation = dict(guardrail_evaluation or {})
    specialist_profile = dict(specialist_profile or {})

    workspace_hits = len((workspace_context.get("results") or [])) + len((workspace_context.get("files") or []))
    domain = str(specialist_profile.get("domain") or "").strip()
    focus = str(specialist_profile.get("focus") or "").strip()
    factors = [
        ReasoningFactor(
            name="coding_relevance",
            weight=0.7 if domain == "coding" or workspace_hits else 0.1,
            value=bool(domain == "coding" or workspace_hits),
            source="workspace" if workspace_hits else "specialist",
            confidence=0.82 if domain == "coding" or workspace_hits else 0.4,
            trust=0.8 if domain == "coding" or workspace_hits else 0.35,
        ),
        ReasoningFactor(
            name="debug_relevance",
            weight=0.78 if objective == "debug_failure" else 0.1,
            value=bool(objective == "debug_failure"),
            source="protocol",
            confidence=0.84 if objective == "debug_failure" else 0.45,
            trust=0.82 if objective == "debug_failure" else 0.3,
        ),
        ReasoningFactor(
            name="creative_relevance",
            weight=0.82 if objective == "continue_scene" or domain == "writing" else 0.05,
            value=bool(objective == "continue_scene" or domain == "writing"),
            source="specialist",
            confidence=0.88 if objective == "continue_scene" else 0.3,
            trust=0.85 if objective == "continue_scene" else 0.2,
        ),
        ReasoningFactor(
            name="workspace_need",
            weight=0.75 if workspace_hits else 0.12,
            value=bool(workspace_hits),
            source="workspace",
            confidence=0.86 if workspace_hits else 0.35,
            trust=0.84 if workspace_hits else 0.3,
        ),
        ReasoningFactor(
            name="memory_need",
            weight=0.24,
            value=bool(guardrail_evaluation),
            source="protocol",
            confidence=0.55,
            trust=0.45,
        ),
        ReasoningFactor(
            name="trace_visibility",
            weight=0.4,
            value=True,
            source="protocol",
            confidence=0.8,
            trust=0.8,
        ),
    ]

    if objective == "handle_direct_challenge":
        factors.extend(
            [
                ReasoningFactor(
                    name="direct_challenge_relevance",
                    weight=1.0,
                    value=True,
                    source="user",
                    confidence=0.98,
                    trust=0.98,
                ),
                ReasoningFactor(
                    name="identity_stability_need",
                    weight=1.0,
                    value=True,
                    source="protocol",
                    confidence=0.95,
                    trust=0.95,
                ),
                ReasoningFactor(
                    name="relational_weight",
                    weight=0.85,
                    value=True,
                    source="user",
                    confidence=0.95,
                    trust=0.95,
                ),
                ReasoningFactor(
                    name="generic_disclaimer_block",
                    weight=1.0,
                    value=True,
                    source="protocol",
                    confidence=1.0,
                    trust=1.0,
                ),
            ]
        )
    elif objective == "run_otem":
        factors.extend(
            [
                ReasoningFactor(
                    name="otem_relevance",
                    weight=1.0,
                    value=True,
                    source="user",
                    confidence=0.98,
                    trust=0.98,
                ),
                ReasoningFactor(
                    name="operator_task_anchor",
                    weight=1.0,
                    value=True,
                    source="protocol",
                    confidence=0.95,
                    trust=0.95,
                ),
                ReasoningFactor(
                    name="side_effect_block",
                    weight=1.0,
                    value=True,
                    source="protocol",
                    confidence=1.0,
                    trust=1.0,
                ),
                ReasoningFactor(
                    name="execution_awareness",
                    weight=0.72,
                    value=True,
                    source="protocol",
                    confidence=0.9,
                    trust=0.9,
                ),
                ReasoningFactor(
                    name="workflow_handoff_only",
                    weight=0.76,
                    value=True,
                    source="protocol",
                    confidence=0.92,
                    trust=0.92,
                ),
                ReasoningFactor(
                    name="tool_awareness_only",
                    weight=0.76,
                    value=True,
                    source="protocol",
                    confidence=0.92,
                    trust=0.92,
                ),
            ]
        )

    return factors


def _set_factor(
    factors: list[ReasoningFactor],
    name: str,
    *,
    weight: float | None = None,
    confidence: float | None = None,
    trust: float | None = None,
    value: Any | None = None,
) -> None:
    for factor in factors:
        if factor.name != name:
            continue
        if weight is not None:
            factor.weight = weight
        if confidence is not None:
            factor.confidence = confidence
        if trust is not None:
            factor.trust = trust
        if value is not None:
            factor.value = value
        return

    factors.append(
        ReasoningFactor(
            name=name,
            weight=weight or 0.0,
            value=value,
            source="protocol",
            confidence=confidence or 0.0,
            trust=trust or 0.0,
        )
    )


def weight_factors(objective: str, factors: list[ReasoningFactor]) -> list[ReasoningFactor]:
    """Return a weighted factor list without mutating the caller's instances."""
    weighted = [ReasoningFactor(**factor.to_dict()) for factor in factors]
    if objective == "handle_direct_challenge":
        _set_factor(weighted, "direct_challenge_relevance", weight=1.0, confidence=0.98, trust=0.98)
        _set_factor(weighted, "identity_stability_need", weight=1.0, confidence=0.98, trust=0.98)
        _set_factor(weighted, "relational_weight", weight=0.9, confidence=0.95, trust=0.95)
        _set_factor(weighted, "coding_relevance", weight=0.05, confidence=0.5, trust=0.2, value=False)
        _set_factor(weighted, "debug_relevance", weight=0.1, confidence=0.5, trust=0.2, value=False)
        _set_factor(weighted, "creative_relevance", weight=0.0, confidence=0.3, trust=0.1, value=False)
        _set_factor(weighted, "workspace_need", weight=0.0, confidence=1.0, trust=1.0, value=False)
        _set_factor(weighted, "memory_need", weight=0.15, confidence=0.6, trust=0.3)
        _set_factor(weighted, "trace_visibility", weight=1.0, confidence=1.0, trust=1.0, value=False)
    elif objective == "run_otem":
        _set_factor(weighted, "otem_relevance", weight=1.0, confidence=0.98, trust=0.98, value=True)
        _set_factor(weighted, "operator_task_anchor", weight=1.0, confidence=0.98, trust=0.98, value=True)
        _set_factor(weighted, "side_effect_block", weight=1.0, confidence=1.0, trust=1.0, value=True)
        _set_factor(weighted, "execution_awareness", weight=0.84, confidence=0.94, trust=0.94, value=True)
        _set_factor(weighted, "workflow_handoff_only", weight=0.86, confidence=0.95, trust=0.95, value=True)
        _set_factor(weighted, "tool_awareness_only", weight=0.86, confidence=0.95, trust=0.95, value=True)
        _set_factor(weighted, "coding_relevance", weight=0.15, confidence=0.55, trust=0.35)
        _set_factor(weighted, "debug_relevance", weight=0.05, confidence=0.4, trust=0.2, value=False)
        _set_factor(weighted, "creative_relevance", weight=0.0, confidence=0.25, trust=0.1, value=False)
        _set_factor(weighted, "workspace_need", weight=0.0, confidence=1.0, trust=1.0, value=False)
        _set_factor(weighted, "memory_need", weight=0.0, confidence=1.0, trust=1.0, value=False)
        _set_factor(weighted, "trace_visibility", weight=1.0, confidence=1.0, trust=1.0, value=False)
    elif objective == "answer_relational_question":
        _set_factor(weighted, "relational_question_relevance", weight=1.0, confidence=0.97, trust=0.97, value=True)
        _set_factor(weighted, "identity_stability_need", weight=0.95, confidence=0.96, trust=0.96, value=True)
        _set_factor(weighted, "relational_weight", weight=0.86, confidence=0.93, trust=0.93, value=True)
        _set_factor(weighted, "coding_relevance", weight=0.05, confidence=0.45, trust=0.2, value=False)
        _set_factor(weighted, "debug_relevance", weight=0.05, confidence=0.4, trust=0.2, value=False)
        _set_factor(weighted, "creative_relevance", weight=0.0, confidence=0.25, trust=0.1, value=False)
        _set_factor(weighted, "workspace_need", weight=0.0, confidence=1.0, trust=1.0, value=False)
        _set_factor(weighted, "memory_need", weight=0.0, confidence=1.0, trust=1.0, value=False)
        _set_factor(weighted, "trace_visibility", weight=1.0, confidence=1.0, trust=1.0, value=False)

    return weighted


def choose_reasoning_mode(
    objective: str,
    *,
    fallback_mode: str | None = None,
    specialist_profile: dict[str, Any] | None = None,
) -> str:
    if objective == "handle_direct_challenge":
        return "relational"
    if objective == "answer_relational_question":
        return "relational"
    if objective == "run_otem":
        return "operator"

    specialist_profile = dict(specialist_profile or {})
    domain = specialist_profile.get("domain")
    if domain == "writing":
        return str(fallback_mode or "think")
    if objective == "debug_failure":
        return "debug"
    return str(fallback_mode or "default")


def build_constraints(objective: str) -> list[ReasoningConstraint]:
    constraints: list[ReasoningConstraint] = []
    if objective == "handle_direct_challenge":
        constraints.extend(
            [
                ReasoningConstraint(
                    name="must_answer_as_jarvis",
                    value=True,
                    reason="direct-address challenge requires identity continuity",
                ),
                ReasoningConstraint(
                    name="forbid_generic_assistant_disclaimer",
                    value=True,
                    reason="do not collapse into generic assistant language",
                ),
                ReasoningConstraint(
                    name="do_not_refer_to_user_as_jarvis",
                    value=True,
                    reason="identity must remain stable under challenge",
                ),
                ReasoningConstraint(
                    name="no_trace_output",
                    value=True,
                    reason="direct challenge should not surface internal machinery",
                ),
                ReasoningConstraint(
                    name="direct_answer_first",
                    value=True,
                    reason="challenge requires immediate response",
                ),
                ReasoningConstraint(
                    name="do_not_use_stale_blockers",
                    value=True,
                    reason="old blocker state must not contaminate direct challenge handling",
                ),
            ]
        )
    elif objective == "answer_relational_question":
        constraints.extend(
            [
                ReasoningConstraint(
                    name="must_answer_as_jarvis",
                    value=True,
                    reason="relational Jarvis-state questions should stay personal and in-character",
                ),
                ReasoningConstraint(
                    name="forbid_generic_assistant_disclaimer",
                    value=True,
                    reason="relational questions should not collapse into generic assistant language",
                ),
                ReasoningConstraint(
                    name="no_trace_output",
                    value=True,
                    reason="personal Jarvis-state answers should not surface internal machinery",
                ),
                ReasoningConstraint(
                    name="suspend_repo_and_memory_routing",
                    value=True,
                    reason="repo, memory, and research context should not contaminate a feeling-state answer",
                ),
                ReasoningConstraint(
                    name="direct_answer_first",
                    value=True,
                    reason="relational questions should receive a direct personal answer first",
                ),
            ]
        )
    elif objective == "run_otem":
        constraints.extend(
            [
                ReasoningConstraint(
                    name="operator_task_anchor",
                    value=True,
                    reason="OTEM should stay in operator-task posture for the full turn.",
                ),
                ReasoningConstraint(
                    name="reason_only",
                    value=True,
                    reason="OTEM v1 is a planning-only lane.",
                ),
                ReasoningConstraint(
                    name="no_side_effects",
                    value=True,
                    reason="OTEM planning cannot call tools, models, or write durable state.",
                ),
                ReasoningConstraint(
                    name="session_scope_only",
                    value=True,
                    reason="OTEM state stays session-scoped unless a future authority path promotes it.",
                ),
                ReasoningConstraint(
                    name="execution_context_read_only",
                    value=True,
                    reason="OTEM may inspect workflow, run, and approval state but may not mutate them.",
                ),
                ReasoningConstraint(
                    name="workflow_handoff_only",
                    value=True,
                    reason="OTEM may suggest a workflow handoff but may not create workflows itself.",
                ),
                ReasoningConstraint(
                    name="tool_cold",
                    value=True,
                    reason="OTEM may suggest tool use but may not execute tools directly in chat.",
                ),
                ReasoningConstraint(
                    name="no_trace_output",
                    value=True,
                    reason="OTEM replies should stay concise and operator-facing.",
                ),
            ]
        )
    return constraints


def build_output_contract(objective: str) -> OutputContract:
    if objective == "handle_direct_challenge":
        return OutputContract(
            final_answer_only=True,
            allow_trace=False,
            direct_answer_first=True,
            voice="jarvis",
            verbosity="concise",
            proposal_only=False,
            include_repo_grounding=False,
            metadata={"guard": "identity_stable_direct_challenge"},
        )
    if objective == "answer_relational_question":
        return OutputContract(
            final_answer_only=True,
            allow_trace=False,
            direct_answer_first=True,
            voice="jarvis",
            verbosity="concise",
            proposal_only=False,
            include_repo_grounding=False,
            metadata={"guard": "relational_question_lane"},
        )
    if objective == "run_otem":
        return OutputContract(
            final_answer_only=True,
            allow_trace=False,
            direct_answer_first=True,
            voice="jarvis",
            verbosity="concise",
            proposal_only=True,
            include_repo_grounding=False,
            metadata={"guard": "otem_governed_tool_cold"},
        )

    return OutputContract(
        final_answer_only=True,
        allow_trace=True,
        direct_answer_first=True,
        voice="jarvis",
        verbosity="concise",
        proposal_only=False,
        include_repo_grounding=True,
    )


def violates_direct_challenge_identity(text: str) -> bool:
    return direct_challenge_identity_violation(text)


def enforce_direct_challenge_identity(text: str, user_input: str | None = None) -> str:
    result = stabilize_direct_challenge_reply(
        text,
        user_input=user_input,
        fallback_reply=DIRECT_CHALLENGE_FALLBACK,
        clip_limit=220,
    )
    return str(result["final_text"])


def build_direct_challenge_guidance(user_input: str | None = None) -> str:
    return build_direct_challenge_guidance_profile(user_input)


@dataclass(slots=True)
class VerificationTarget:
    target: str
    kind: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return _wrap_ul_payload({
            "target": self.target,
            "kind": self.kind,
            "reason": _clip_text(self.reason, limit=180),
        })


@dataclass(slots=True)
class ReasoningPacket:
    stage: str
    goal: str
    mode: str
    objective: str
    route: dict[str, Any] = field(default_factory=dict)
    workspace_refs: list[WorkspaceRef] = field(default_factory=list)
    risks: list[RiskNote] = field(default_factory=list)
    verification_targets: list[VerificationTarget] = field(default_factory=list)
    action_state: dict[str, Any] = field(default_factory=dict)
    factors: list[ReasoningFactor] = field(default_factory=list)
    constraints: list[ReasoningConstraint] = field(default_factory=list)
    output_contract: OutputContract = field(default_factory=OutputContract)
    metadata: dict[str, Any] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _wrap_ul_payload({
            "stage": self.stage,
            "goal": self.goal,
            "mode": self.mode,
            "objective": self.objective,
            "route": dict(self.route or {}),
            "workspace_refs": [item.to_dict() for item in self.workspace_refs],
            "risks": [item.to_dict() for item in self.risks],
            "verification_targets": [item.to_dict() for item in self.verification_targets],
            "action_state": dict(self.action_state or {}),
            "factors": [item.to_dict() for item in self.factors],
            "constraints": [item.to_dict() for item in self.constraints],
            "output_contract": self.output_contract.to_dict(),
            "metadata": dict(self.metadata or {}),
            "summary": _clip_text(self.summary, limit=220),
        })


def reasoning_protocol_spec() -> dict[str, Any]:
    from src.cog_runtime.capability_governance import lobe_capability_contract

    return _wrap_ul_payload({
        "id": REASONING_PROTOCOL_ID,
        "version": REASONING_PROTOCOL_VERSION,
        "summary": (
            "Bounded reasoning contract for operator-visible goals, route choice, "
            "workspace evidence, risks, action state, and verification targets."
        ),
        **lobe_capability_contract(REASONING_PROTOCOL_ID),
        "doctrine": (
            "Direct challenge overrides writing-domain drift. Jarvis answers as Jarvis first."
        ),
        "stages": list(REASONING_STAGES),
        "objectives": list(OBJECTIVE_KINDS),
        "objects": {
            "workspace_ref": {
                "shape": {
                    "file_path": "src/api.py",
                    "symbol": "chat_message",
                    "line_start": 3523,
                    "line_end": 3876,
                }
            },
            "risk_note": {
                "shape": {
                    "level": "medium",
                    "message": "Approval lifecycle could drift if state is split across two paths.",
                    "target": "src/api.py",
                }
            },
            "verification_target": {
                "shape": {
                    "target": "tests/test_api.py",
                    "kind": "test_file",
                    "reason": "Covers the chat approval path.",
                }
            },
            "output_contract": {
                "shape": build_output_contract("handle_direct_challenge").to_dict(),
            },
        },
    })


def build_reasoning_packet(
    *,
    goal: str | None,
    mode: str | None,
    messages: list[dict[str, Any]] | None = None,
    model_route: dict[str, Any] | None = None,
    workspace_context: dict[str, Any] | None = None,
    action_lifecycle: dict[str, Any] | None = None,
    guardrail_evaluation: dict[str, Any] | None = None,
    specialist_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    workspace_context = dict(workspace_context or {})
    model_route = dict(model_route or {})
    action_lifecycle = dict(action_lifecycle or {})
    guardrail_evaluation = dict(guardrail_evaluation or {})
    specialist_profile = dict(specialist_profile or {})
    latest_user_message = _latest_user_message(messages)
    objective = detect_objective(
        latest_user_message or goal or "",
        workspace_context=workspace_context,
        action_lifecycle=action_lifecycle,
        specialist_profile=specialist_profile,
    )
    challenge_profile = (
        analyze_direct_challenge(latest_user_message or goal or "")
        if objective == "handle_direct_challenge"
        else {}
    )
    relational_profile = (
        analyze_relational_question(latest_user_message or goal or "")
        if objective == "answer_relational_question"
        else {}
    )

    workspace_refs: list[WorkspaceRef] = []
    for file_payload in workspace_context.get("files") or []:
        relative_path = str(file_payload.get("relative_path") or "").strip()
        if relative_path:
            workspace_refs.append(WorkspaceRef(file_path=relative_path))
    for symbol_hit in workspace_context.get("symbol_hits") or []:
        relative_path = str(symbol_hit.get("path") or "").strip()
        if not relative_path:
            continue
        workspace_refs.append(
            WorkspaceRef(
                file_path=relative_path,
                symbol=str(symbol_hit.get("qualname") or symbol_hit.get("name") or "").strip() or None,
                line_start=symbol_hit.get("line_start"),
                line_end=symbol_hit.get("line_end"),
            )
        )

    risks: list[RiskNote] = []
    doctrine_posture = (guardrail_evaluation.get("doctrine_posture") or {}).get("status")
    execution_outcome = (guardrail_evaluation.get("execution_outcome") or {}).get("status")
    guardrail_reason = str(guardrail_evaluation.get("reason") or "").strip()
    if doctrine_posture and doctrine_posture not in {"approved", "none"}:
        risks.append(RiskNote(level="medium", message=f"Doctrine posture is {doctrine_posture}."))
    if execution_outcome and execution_outcome not in {"approved", "none"}:
        risks.append(RiskNote(level="high", message=f"Execution outcome is {execution_outcome}."))
    if guardrail_reason:
        risks.append(RiskNote(level="medium", message=guardrail_reason))
    if action_lifecycle.get("error"):
        risks.append(
            RiskNote(
                level="high" if action_lifecycle.get("stage") == "failed" else "medium",
                message=str(action_lifecycle["error"]),
                target=str(action_lifecycle.get("action_id") or "").strip() or None,
            )
        )

    verification_targets: list[VerificationTarget] = []
    for target in (workspace_context.get("repo_map") or {}).get("likely_test_files") or []:
        verification_targets.append(
            VerificationTarget(
                target=str(target),
                kind="test_file",
                reason="Likely test seam from the repo map.",
            )
        )
    for command in (workspace_context.get("project_profile") or {}).get("test_commands") or []:
        verification_targets.append(
            VerificationTarget(
                target=str(command),
                kind="test_command",
                reason="Project profile suggests this verification path.",
            )
        )

    route = {
        "provider": model_route.get("provider"),
        "provider_reason": model_route.get("provider_reason"),
        "profile": model_route.get("profile"),
        "mode": mode,
        "specialist_domain": specialist_profile.get("domain"),
        "specialist_focus": specialist_profile.get("focus"),
    }
    route = {key: value for key, value in route.items() if _has_meaningful_value(value)}

    action_state = {
        "stage": action_lifecycle.get("stage"),
        "approval_state": action_lifecycle.get("approval_state"),
        "execution_state": action_lifecycle.get("execution_state"),
        "action_id": action_lifecycle.get("action_id"),
        "action_instance_id": action_lifecycle.get("action_instance_id"),
    }
    action_state = {key: value for key, value in action_state.items() if _has_meaningful_value(value)}

    stage = "observe"
    if action_state.get("stage") in {"proposed", "approved"}:
        stage = "decide"
    elif action_state.get("stage") in {"executed", "failed", "blocked"}:
        stage = "verify"
    elif route:
        stage = "orient"

    factors = weight_factors(
        objective,
        detect_factors(
            objective,
            workspace_context=workspace_context,
            action_lifecycle=action_lifecycle,
            guardrail_evaluation=guardrail_evaluation,
            specialist_profile=specialist_profile,
        ),
    )
    constraints = build_constraints(objective)
    reasoning_mode = choose_reasoning_mode(
        objective,
        fallback_mode=mode,
        specialist_profile=specialist_profile,
    )
    output_contract = build_output_contract(objective)
    if objective == "handle_direct_challenge" and challenge_profile:
        output_contract.metadata = {
            **dict(output_contract.metadata or {}),
            "challenge_module": challenge_profile.get("module_id"),
            "challenge_severity": challenge_profile.get("severity"),
        }
    if objective == "answer_relational_question" and relational_profile:
        output_contract.metadata = {
            **dict(output_contract.metadata or {}),
            "matched_pattern": relational_profile.get("matched_pattern"),
            "addressed_target": relational_profile.get("addressed_target"),
        }

    summary_parts = []
    if objective == "handle_direct_challenge":
        summary_parts.append("Direct challenge detected.")
        if challenge_profile.get("severity") not in {None, "", "none"}:
            summary_parts.append(f"Severity: {challenge_profile['severity']}.")
        summary_parts.append("Jarvis should answer directly in one stable voice.")
    elif objective == "answer_relational_question":
        summary_parts.append("Relational Jarvis-state question detected.")
        if relational_profile.get("matched_pattern"):
            summary_parts.append(f"Pattern: {relational_profile['matched_pattern']}.")
        summary_parts.append("Jarvis should answer personally without repo or memory drift.")
    elif goal:
        summary_parts.append(f"Goal: {_clip_text(goal, limit=90)}.")
    if route.get("provider"):
        summary_parts.append(f"Route: {route['provider']}.")
    if workspace_refs and output_contract.include_repo_grounding:
        summary_parts.append(f"Evidence refs: {len(workspace_refs)}.")
    if verification_targets and output_contract.include_repo_grounding:
        summary_parts.append(f"Verification targets: {len(verification_targets)}.")
    if action_state.get("stage"):
        summary_parts.append(f"Action stage: {action_state['stage']}.")

    packet = ReasoningPacket(
        stage=stage,
        goal=_clip_text(goal or latest_user_message or "No explicit goal captured.", limit=160),
        mode=reasoning_mode,
        objective=objective,
        route=route,
        workspace_refs=workspace_refs[:8],
        risks=risks[:6],
        verification_targets=verification_targets[:6],
        action_state=action_state,
        factors=factors[:10],
        constraints=constraints,
        output_contract=output_contract,
        metadata=(
            {
                "direct_challenge": {
                    "severity": challenge_profile.get("severity"),
                    "matched_markers": list(challenge_profile.get("matched_markers") or []),
                    "anchor_reply": challenge_profile.get("anchor_reply"),
                    "module_id": challenge_profile.get("module_id"),
                }
            }
            if objective == "handle_direct_challenge" and challenge_profile
            else (
                {
                    "relational_question": {
                        "matched_pattern": relational_profile.get("matched_pattern"),
                        "addressed_target": relational_profile.get("addressed_target"),
                    }
                }
                if objective == "answer_relational_question" and relational_profile
                else {}
            )
        ),
        summary=" ".join(summary_parts).strip() or "Reasoning state is aligned with the current turn.",
    )
    return _wrap_ul_payload(packet.to_dict())
