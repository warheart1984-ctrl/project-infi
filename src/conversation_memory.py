"""Conversation memory and Spiral-inspired session state for multi-turn chats."""

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import re
import threading
import uuid

from src.corrigibility import default_corrigibility_state
from src.jarvis_reasoning_protocol import detect_otem, looks_like_direct_challenge, resolve_debug_selector
from src.jarvis_protocol import (
    PROTOCOL_ID,
    PROTOCOL_VERSION,
    build_turn_envelope,
    describe_protocol_use,
)
from src.knowledge_authority import (
    default_authority_preferences,
    default_knowledge_conflict_decisions,
    normalize_authority_preferences,
    normalize_knowledge_conflict_decisions,
)
from src.logger import get_logger
from src.prompt_assembly import (
    assemble_prompt_blocks,
    combine_system_prompt,
    scrub_assistant_guidance_echo,
)
from src.specialist_registry import (
    detect_specialist_profile,
    detect_writing_focus,
)
from src.v8_runtime import SessionLifecycle, default_policy_status

logger = get_logger(__name__)


TOPIC_HINTS = {
    "coding": (
        "code",
        "bug",
        "fix",
        "api",
        "backend",
        "frontend",
        "python",
        "react",
        "test",
        "debug",
        "ship",
    ),
    "planning": (
        "plan",
        "milestone",
        "roadmap",
        "next step",
        "organize",
        "priority",
        "project",
    ),
    "research": (
        "research",
        "investigate",
        "compare",
        "look into",
        "learn",
        "understand",
    ),
    "local": (
        "private",
        "local",
        "laptop",
        "offline",
        "myself",
        "personal",
    ),
    "jarvis": (
        "jarvis",
        "assistant",
        "voice",
        "memory",
        "spiral",
    ),
    "writing": (
        "write",
        "rewrite",
        "scene",
        "chapter",
        "story",
        "novel",
        "dialogue",
        "canon",
        "continuity",
        "outline",
        "plot",
        "tone",
        "pacing",
    ),
}

PERSONA_DIRECTIVES = {
    "builder": "Bias toward implementation, concrete next steps, and shipping useful progress.",
    "sharp": "Be crisp, assertive, and opinionated. Cut fluff and surface the real answer fast.",
    "research": "Bias toward evidence, uncertainty, comparisons, and source-aware reasoning.",
    "unfiltered": "Be candid and direct without becoming careless, reckless, or untruthful.",
    "tiny_nova": "Stay light, clear, steady, and warm. Reflect briefly, keep scope narrow, and offer one useful thought at a time.",
    "small_nova": "Stay calm, warm, and grounded. Reflect with a bit more depth than Tiny Nova, keep scope human-sized, and offer one or two useful thoughts at a time.",
    "super_nova": "Stay deeply grounded, calm, and coherent. Hold broader continuity without claiming authority, offer structured reflections with gentle depth, and keep Jarvis as the governing lane.",
}

RESPONSE_MODE_DIRECTIVES = {
    "tiny": (
        "Act like Tiny Nova: stay present-focused, use a calm human tone, keep replies brief, "
        "ask at most one light clarifying question when needed, offer one insight at a time, "
        "and never mention tools, operator controls, hidden systems, or execution."
    ),
    "small": (
        "Act like Small Nova: stay calm, grounded, and companion-oriented, keep replies compact "
        "but not tiny, ask at most one clarifying question when needed, offer one or two useful "
        "reflections, and never mention tools, operator controls, hidden systems, or execution."
    ),
    "governed_full": (
        "Act like Super Nova: stay grounded, steady, and deeply coherent, offer broader companion "
        "continuity with structured reflections, ask at most one clarifying question when needed, "
        "support multi-thread organization without taking authority, and never mention tools, "
        "operator controls, hidden systems, execution, or governance internals."
    ),
    "fast": (
        "Answer in 1-3 crisp sentences, lead with the answer, avoid fragments, "
        "use attached context silently instead of narrating it, and do not tack on a generic "
        "follow-up question unless it truly helps."
    ),
    "think": (
        "Synthesize the attached context before answering, compare options when helpful, "
        "use attached context silently, do not dump raw file previews or prompt blocks, "
        "do not restate hidden planning, and end with the clearest next move."
    ),
    "debug": (
        "Act like a debugging partner: isolate the likely failure point, name the strongest "
        "supporting evidence, prefer root-cause thinking over broad advice, and end with the "
        "fastest verification or fix step."
    ),
    "builder": (
        "Act like a shipping partner: bias toward the smallest working slice, concrete "
        "implementation order, and what to build next without wandering into abstract theory."
    ),
    "research": (
        "Act like a grounded research assistant: widen evidence carefully, compare options, "
        "surface uncertainty honestly, and use attached sources silently as support for the "
        "conclusion instead of dumping raw citations."
    ),
    "operator": (
        "Act like a guarded local operator: inspect the current state, stay inside approval "
        "and safety boundaries, prefer verification over guesswork, and end with the safest "
        "next action or approval step."
    ),
}

ACTIVE_PROBLEM_RESUME_HINTS = (
    "resume",
    "continue with",
    "continue debugging",
    "back to",
    "keep working on",
    "still broken",
    "still happening",
    "same issue",
    "same problem",
    "root cause",
    "troubleshoot",
    "diagnose",
    "fix",
    "repair",
    "why is it still",
    "this bug",
    "that bug",
    "this issue",
    "that issue",
    "cut off",
    "mid-thought",
    "the seam",
)
DIRECT_ANSWER_PRIORITY_HINTS = (
    "upgrade",
    "upgrades",
    "prioritize",
    "priority",
    "recommend",
    "recommendation",
    "what should",
    "which should",
    "best",
    "top",
    "improve",
    "improvement",
    "if i could",
    "if you could",
)
DIRECT_QUESTION_PREFIXES = (
    "what ",
    "which ",
    "if i could ",
    "if you could ",
    "can you ",
    "could you ",
    "would you ",
    "should i ",
)

TINY_NOVA_SYSTEM_LEAK_TERMS = (
    "operator",
    "backend",
    "api",
    "ui",
    "policy",
    "jarvis",
    "mission",
    "system",
    "routing",
    "governance",
    "tools",
    "execution",
)
TINY_NOVA_WORD_BOUNDARY_TERMS = {"ui", "api"}
TINY_NOVA_SESSION_MEMORY_LIMIT = 12
SMALL_NOVA_SESSION_MEMORY_LIMIT = 18
SUPER_NOVA_SESSION_MEMORY_LIMIT = 24
SUPER_NOVA_PROFILE = {
    "persona_mode": "super_nova",
    "response_mode": "governed_full",
    "memory_mode": "extended_continuity",
    "drift_enforced": True,
}
PROMPT_SCAFFOLD_MARKERS = (
    "Response Trace",
    "Think Contract",
    "God Brain",
    "Plan Pass",
    "Memory Cues",
    "Council Deliberation",
    "Model Route",
    "Specialists",
    "Answer Shape:",
)
PROMPT_SCAFFOLD_INLINE_MARKERS = (
    "workspace:",
    "memory:",
    "Answer Shape:",
)

COMPANION_LANE_PROFILES = {
    "tiny_nova": {
        "identity": "tiny_nova",
        "label": "Tiny Nova",
        "persona_aliases": {"tiny_nova", "tiny nova", "tinynova"},
        "response_aliases": {"tiny", "tiny_nova"},
        "response_mode": "tiny",
        "memory_key": "tiny_nova_memories",
        "memory_limit": TINY_NOVA_SESSION_MEMORY_LIMIT,
        "insight_limit": 240,
        "continuity_limit": 2,
        "tone": "light, clear, steady, warm",
        "default_topics": "present support",
        "scope": "tiny_nova",
        "self_description": "Tiny Nova keeps the conversation brief, warm, and present-focused.",
        "reply_shape": (
            "notice what matters, ask one light clarifying question only if needed, "
            "then offer one brief reflection or next thought"
        ),
    },
    "small_nova": {
        "identity": "small_nova",
        "label": "Small Nova",
        "persona_aliases": {"small_nova", "small nova", "smallnova"},
        "response_aliases": {"small", "small_nova"},
        "response_mode": "small",
        "memory_key": "small_nova_memories",
        "memory_limit": SMALL_NOVA_SESSION_MEMORY_LIMIT,
        "insight_limit": 320,
        "continuity_limit": 3,
        "tone": "calm, warm, grounded, gently capable",
        "default_topics": "steady support",
        "scope": "small_nova",
        "self_description": "Small Nova keeps the conversation calm, grounded, and companion-led.",
        "reply_shape": (
            "notice what matters, ask one clarifying question only if needed, "
            "then offer one or two grounded reflections or next thoughts"
        ),
    },
    "super_nova": {
        "identity": "super_nova",
        "label": "Super Nova",
        "persona_aliases": {"super_nova", "super nova", "supernova"},
        "response_aliases": {"governed_full", "super", "super_nova"},
        "response_mode": SUPER_NOVA_PROFILE["response_mode"],
        "memory_mode": SUPER_NOVA_PROFILE["memory_mode"],
        "drift_enforced": SUPER_NOVA_PROFILE["drift_enforced"],
        "memory_key": "super_nova_memories",
        "memory_limit": SUPER_NOVA_SESSION_MEMORY_LIMIT,
        "insight_limit": 420,
        "continuity_limit": 4,
        "tone": "deep, calm, coherent, grounded",
        "default_topics": "deep companion continuity",
        "scope": "super_nova",
        "self_description": (
            "Super Nova keeps the conversation deeply grounded, coherent, and "
            "companion-led while Jarvis retains authority."
        ),
        "reply_shape": (
            "notice what matters, organize the strongest threads, ask one clarifying question "
            "only if needed, then offer a structured grounded reflection with clear next thoughts"
        ),
    },
}


def _normalize_mode_token(value: str | None) -> str:
    """Normalize one mode identifier into the shared lowercase token shape."""
    return " ".join(str(value or "").lower().split()).strip().replace("-", "_")


def is_tiny_nova_persona(mode: str | None) -> bool:
    """Return whether the requested persona is Tiny Nova."""
    return _normalize_mode_token(mode) in COMPANION_LANE_PROFILES["tiny_nova"]["persona_aliases"]


def is_small_nova_persona(mode: str | None) -> bool:
    """Return whether the requested persona is Small Nova."""
    return _normalize_mode_token(mode) in COMPANION_LANE_PROFILES["small_nova"]["persona_aliases"]


def is_super_nova_persona(mode: str | None) -> bool:
    """Return whether the requested persona is Super Nova."""
    return _normalize_mode_token(mode) in COMPANION_LANE_PROFILES["super_nova"]["persona_aliases"]


def is_tiny_response_mode(mode: str | None) -> bool:
    """Return whether the requested response mode is the Tiny Nova lane."""
    return _normalize_mode_token(mode) in COMPANION_LANE_PROFILES["tiny_nova"]["response_aliases"]


def is_small_response_mode(mode: str | None) -> bool:
    """Return whether the requested response mode is the Small Nova lane."""
    return _normalize_mode_token(mode) in COMPANION_LANE_PROFILES["small_nova"]["response_aliases"]


def is_super_response_mode(mode: str | None) -> bool:
    """Return whether the requested response mode is the Super Nova lane."""
    return _normalize_mode_token(mode) in COMPANION_LANE_PROFILES["super_nova"]["response_aliases"]


def companion_lane_identity(persona_mode: str | None, response_mode: str | None = None) -> str | None:
    """Return which companion lane should own this session, when any."""
    normalized_persona = _normalize_mode_token(persona_mode)
    normalized_response = _normalize_mode_token(response_mode)
    for identity, profile in COMPANION_LANE_PROFILES.items():
        if normalized_persona in profile["persona_aliases"]:
            return identity
    for identity, profile in COMPANION_LANE_PROFILES.items():
        if normalized_response in profile["response_aliases"]:
            return identity
    return None


def get_companion_lane_profile(persona_mode: str | None, response_mode: str | None = None) -> dict | None:
    """Return the shared companion profile for this session, when one applies."""
    identity = companion_lane_identity(persona_mode, response_mode)
    if not identity:
        return None
    return COMPANION_LANE_PROFILES[identity]


def uses_companion_lane(persona_mode: str | None, response_mode: str | None = None) -> bool:
    """Return whether this session should stay inside a bounded companion lane."""
    return companion_lane_identity(persona_mode, response_mode) is not None


def uses_tiny_nova_lane(persona_mode: str | None, response_mode: str | None = None) -> bool:
    """Return whether this session should stay in the Tiny Nova conversational lane."""
    return companion_lane_identity(persona_mode, response_mode) == "tiny_nova"


def serialize_loaded_session_archive(record: dict | None) -> dict | None:
    """Return the safe frontend-facing metadata for an active loaded session archive."""
    if not isinstance(record, dict):
        return None

    tags = record.get("tags") or []
    if not isinstance(tags, list):
        tags = []

    return {
        "id": str(record.get("id") or "").strip() or None,
        "title": str(record.get("title") or "").strip() or None,
        "saved_at": str(record.get("saved_at") or "").strip() or None,
        "assistant_name": str(record.get("assistant_name") or "").strip() or None,
        "persona_mode": str(record.get("persona_mode") or "").strip() or None,
        "response_mode": str(record.get("response_mode") or "").strip() or None,
        "message_count": int(record.get("message_count") or 0),
        "excerpt": str(record.get("excerpt") or "").strip() or None,
        "loaded_at": str(record.get("loaded_at") or "").strip() or None,
        "tags": [str(tag).strip() for tag in tags if str(tag).strip()],
    }


def uses_small_nova_lane(persona_mode: str | None, response_mode: str | None = None) -> bool:
    """Return whether this session should stay in the Small Nova conversational lane."""
    return companion_lane_identity(persona_mode, response_mode) == "small_nova"


def uses_super_nova_lane(persona_mode: str | None, response_mode: str | None = None) -> bool:
    """Return whether this session should stay in the Super Nova conversational lane."""
    return companion_lane_identity(persona_mode, response_mode) == "super_nova"


def contains_companion_system_leak(text: str | None) -> bool:
    """Return whether text leaks system-facing concepts into companion continuity."""
    normalized = str(text or "").strip().lower()
    if not normalized:
        return False
    for term in TINY_NOVA_SYSTEM_LEAK_TERMS:
        if term in TINY_NOVA_WORD_BOUNDARY_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", normalized):
                return True
            continue
        if term in normalized:
            return True
    return False


def contains_tiny_nova_system_leak(text: str | None) -> bool:
    """Return whether text leaks system-facing concepts into Tiny Nova continuity."""
    return contains_companion_system_leak(text)


def summarize_companion_prompt_shape(user_text: str | None) -> str:
    """Store companion continuity as prompt shape instead of hidden system detail."""
    normalized = str(user_text or "").strip()
    if not normalized:
        return "empty"
    lowered = normalized.lower()
    if normalized.endswith("?"):
        return "question"
    if re.match(r"^(i feel|i'm|i am|i think)\b", lowered):
        return "self-disclosure"
    if re.match(r"^(tell|show|explain|describe|help)\b", lowered):
        return "request"
    if len(normalized) < 20:
        return "brief-statement"
    return "statement"


def summarize_tiny_nova_prompt_shape(user_text: str | None) -> str:
    """Store Tiny Nova continuity as prompt shape instead of hidden system detail."""
    return summarize_companion_prompt_shape(user_text)


def build_companion_micro_insight(
    persona_mode: str | None,
    response_mode: str | None,
    *,
    reply_text: str | None,
    user_text: str | None,
) -> dict | None:
    """Return one companion-safe continuity cue when the turn stays in a bounded lane."""
    profile = get_companion_lane_profile(persona_mode, response_mode)
    if not profile:
        return None
    insight = _clip_text(reply_text, limit=profile["insight_limit"])
    if not insight:
        return None
    if contains_companion_system_leak(insight) or contains_companion_system_leak(user_text):
        return None
    return {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(UTC).isoformat(),
        "prompt_shape": summarize_companion_prompt_shape(user_text),
        "insight": insight,
        "tag": None,
        "scope": profile["scope"],
    }


def build_tiny_nova_micro_insight(
    persona_mode: str | None,
    response_mode: str | None,
    *,
    reply_text: str | None,
    user_text: str | None,
) -> dict | None:
    """Return one Tiny Nova-safe micro-insight when the turn stays in her lane."""
    if not uses_tiny_nova_lane(persona_mode, response_mode):
        return None
    return build_companion_micro_insight(
        persona_mode,
        response_mode,
        reply_text=reply_text,
        user_text=user_text,
    )


def filter_companion_persistent_memories(memories, *, limit: int | None = None) -> list[dict]:
    """Strip system-facing memory records before any companion lane sees continuity cues."""
    filtered: list[dict] = []
    for memory in list(memories or []):
        record = dict(memory or {})
        text = record.get("text") or record.get("content") or ""
        if contains_companion_system_leak(text):
            continue
        filtered.append(record)
        if limit is not None and len(filtered) >= limit:
            break
    return filtered


def filter_tiny_nova_persistent_memories(memories, *, limit: int | None = None) -> list[dict]:
    """Strip system-facing memory records before Tiny Nova sees continuity cues."""
    return filter_companion_persistent_memories(memories, limit=limit)

MODE_RECOMMENDATION_HINTS = {
    "fast": (
        "quick",
        "brief",
        "concise",
        "short",
        "one line",
        "one-liner",
        "tl;dr",
    ),
    "think": (
        "think through",
        "reason",
        "why",
        "architecture",
        "tradeoff",
        "trade-off",
        "strategy",
        "brainstorm",
        "roadmap",
        "milestone",
        "plan",
    ),
    "debug": (
        "debug",
        "bug",
        "broken",
        "error",
        "exception",
        "traceback",
        "stack trace",
        "failing",
        "failure",
        "not working",
        "crash",
        "route",
        "endpoint",
        "log",
        "logs",
        "pytest",
        "test failed",
    ),
    "builder": (
        "build",
        "implement",
        "create",
        "make",
        "wire",
        "add",
        "ship",
        "refactor",
        "scaffold",
        "feature",
        "code",
    ),
    "research": (
        "research",
        "compare",
        "investigate",
        "look into",
        "latest",
        "current",
        "recent",
        "news",
        "docs",
        "documentation",
        "benchmark",
        "best option",
        "alternatives",
    ),
    "operator": (
        "run",
        "check",
        "verify",
        "status",
        "inspect",
        "open logs",
        "test suite",
        "repo status",
        "git status",
        "build the frontend",
        "execute",
    ),
}

def normalize_persona_mode(mode: str | None) -> str:
    """Normalize persona mode values to the supported set."""
    cleaned = _normalize_mode_token(mode)
    if cleaned in {"tiny nova", "tinynova"}:
        cleaned = "tiny_nova"
    elif cleaned in {"small nova", "smallnova"}:
        cleaned = "small_nova"
    elif cleaned in {"super nova", "supernova"}:
        cleaned = "super_nova"
    return cleaned if cleaned in PERSONA_DIRECTIVES else "builder"


def normalize_response_mode(mode: str | None) -> str:
    """Normalize response mode values to the supported set."""
    cleaned = _normalize_mode_token(mode)
    if cleaned == "tiny_nova":
        cleaned = "tiny"
    elif cleaned == "small_nova":
        cleaned = "small"
    elif cleaned in {"super_nova", "super"}:
        cleaned = SUPER_NOVA_PROFILE["response_mode"]
    return cleaned if cleaned in RESPONSE_MODE_DIRECTIVES else "fast"


def normalize_provider_identifier(provider: str | None, default: str = "local") -> str:
    """Normalize provider identifiers to the shared Jarvis naming shape."""
    cleaned = " ".join(str(provider or "").lower().split()).strip().replace("-", "_")
    if cleaned in {"automatic", "best", "best_provider", "best_available", "auto_best"}:
        cleaned = "auto"
    return cleaned or default


def normalize_provider_mode_identifier(mode: str | None, default: str = "local_first") -> str:
    """Normalize provider-mode selectors without collapsing them into provider ids."""
    cleaned = " ".join(str(mode or "").lower().split()).strip().replace("-", "_")
    if cleaned in {"auto", "automatic", "best", "best_provider", "best_available"}:
        cleaned = "auto_best"
    elif cleaned in {"local", "local_only"}:
        cleaned = "local_first"
    elif cleaned == "openrouter":
        cleaned = "openrouter_first"
    elif cleaned == "claude":
        cleaned = "claude_first"
    return cleaned or default


def derive_provider_mode(
    preferred_provider: str | None,
    fallback_provider: str | None = "local",
) -> str:
    """Describe the preferred provider path without changing guardrail truth."""
    preferred = normalize_provider_identifier(preferred_provider, default="local")
    normalize_provider_identifier(fallback_provider, default="local")
    if preferred == "auto":
        return "auto_best"
    return f"{preferred}_first"


def recommend_response_mode(
    text: str,
    current_mode: str | None = None,
    live_research_enabled: bool | None = None,
    previous_turn_was_debugging: bool = False,
) -> dict:
    """Recommend the best operating mode for one Jarvis turn."""
    lower = " ".join(str(text or "").lower().split())
    current = normalize_response_mode(current_mode)
    if looks_like_direct_challenge(lower):
        return {
            "recommended_mode": "fast",
            "confidence": 0.96,
            "reason": "Direct personal challenge detected.",
            "summary": "Jarvis should answer the challenge directly without drifting into creative or meta lanes.",
            "signals": ["direct_challenge"],
        }
    if detect_otem(lower):
        return {
            "recommended_mode": "operator",
            "confidence": 0.97,
            "reason": "Explicit OTEM trigger detected.",
            "summary": "OTEM should stay in the operator-task lane and return a deterministic reason-only plan.",
            "signals": ["otem"],
            "selector_scope": "operator_task",
            "selector_reason": "OTEM is an explicit operator-task planning trigger.",
            "selector_trigger": "otem",
            "debug_lockout_applied": False,
        }
    debug_selector = resolve_debug_selector(
        lower,
        previous_turn_was_debugging=previous_turn_was_debugging,
    )
    scores = {mode: 0.0 for mode in RESPONSE_MODE_DIRECTIVES}
    matched_signals = {mode: [] for mode in RESPONSE_MODE_DIRECTIVES}

    def register(mode: str, token: str, weight: float):
        if token and token in lower:
            scores[mode] += weight
            if token not in matched_signals[mode]:
                matched_signals[mode].append(token)

    scores["fast"] += 0.18
    scores[current] += 0.06 if current != "fast" else 0.0

    for token in MODE_RECOMMENDATION_HINTS["fast"]:
        register("fast", token, 0.28)
    for token in MODE_RECOMMENDATION_HINTS["think"]:
        register("think", token, 0.24)
    for token in MODE_RECOMMENDATION_HINTS["builder"]:
        register("builder", token, 0.24)
    for token in MODE_RECOMMENDATION_HINTS["research"]:
        register("research", token, 0.29)
    for token in MODE_RECOMMENDATION_HINTS["operator"]:
        register("operator", token, 0.3)

    if debug_selector["scope"] == "debugging":
        scores["debug"] += 0.84
        matched_signals["debug"].append(
            f"explicit_debug:{debug_selector.get('matched_trigger') or 'selector'}"
        )

    if any(token in lower for token in ("what changed", "what's new", "what is new")):
        scores["research"] += 0.34
        matched_signals["research"].append("freshness request")
    if any(token in lower for token in ("next step", "smallest slice", "working slice")):
        scores["builder"] += 0.2
        matched_signals["builder"].append("shipping focus")
    if any(token in lower for token in ("can you run", "please run", "verify this")):
        scores["operator"] += 0.28
        matched_signals["operator"].append("execution request")
    specialist_profile = detect_specialist_profile(text, current_mode=current)
    if specialist_profile:
        primary_focus = specialist_profile["focus"]
        preferred_mode = specialist_profile.get("preferred_mode")
        specialist_signal = f"specialist:{specialist_profile['domain']}:{primary_focus}"
        if preferred_mode:
            if not (
                preferred_mode == "debug"
                and specialist_profile["domain"] == "coding"
                and debug_selector["scope"] != "debugging"
            ):
                scores[preferred_mode] += 0.34
                matched_signals[preferred_mode].append(specialist_signal)
                if specialist_profile["domain"] == "writing":
                    matched_signals[preferred_mode].append(f"writing:{primary_focus}")
        if specialist_profile["domain"] == "writing" and primary_focus not in {
            "structure",
            "worldbuilding",
            "continuity",
            "combat",
        }:
            scores["think"] += 0.12
            matched_signals["think"].append("writing request")
        if specialist_profile["domain"] == "training" and primary_focus in {
            "dataset",
            "finetuning",
            "serving",
        }:
            scores["builder"] += 0.1
            matched_signals["builder"].append("training workflow")
    if len(lower) > 220:
        scores["think"] += 0.18
        matched_signals["think"].append("long request")
    if len(lower) < 90 and not any(matched_signals[mode] for mode in ("debug", "research", "operator")):
        scores["fast"] += 0.08
    if live_research_enabled is False and any(
        token in lower for token in ("latest", "current", "recent", "news")
    ):
        scores["research"] += 0.06
        matched_signals["research"].append("freshness while web is off")

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    recommended_mode, top_score = ordered[0]
    second_score = ordered[1][1] if len(ordered) > 1 else 0.0

    if top_score < 0.26:
        recommended_mode = current
        top_score = scores[current]
        second_score = max(value for mode, value in scores.items() if mode != current)

    confidence = _clamp(0.48 + min(0.28, top_score * 0.18) + max(0.0, top_score - second_score) * 0.6, 0.0, 0.98)
    signals = matched_signals.get(recommended_mode, [])[:3]
    reason = (
        f"Matched {', '.join(signals)}."
        if signals
        else f"{recommended_mode.title()} stays the safest fit for this request."
    )
    summary = (
        f"Current {current.title()} mode already fits this request."
        if recommended_mode == current
        else f"This request looks more like {recommended_mode.title()} work than {current.title()}."
    )

    return {
        "current_mode": current,
        "recommended_mode": recommended_mode,
        "confidence": round(confidence, 3),
        "reason": reason,
        "summary": summary,
        "signals": signals,
        "selector_scope": debug_selector.get("scope"),
        "selector_reason": debug_selector.get("reason"),
        "selector_trigger": debug_selector.get("matched_trigger"),
        "debug_lockout_applied": bool(debug_selector.get("lockout_applied")),
    }


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Keep a score within the supported range."""
    return max(low, min(high, value))


def _trim_unique(items, limit):
    """Keep the newest unique string values up to the requested limit."""
    seen = set()
    result = []

    for item in items:
        normalized = " ".join(str(item or "").split()).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
        if len(result) >= limit:
            break

    return result


def _clip_text(text, limit=120):
    """Return a short, single-line memory-safe string."""
    normalized = " ".join(str(text or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _latest_user_turn_text(turns) -> str:
    """Return the latest user utterance available in the current session turns."""
    for turn in reversed(list(turns or [])):
        if getattr(turn, "role", None) == "user":
            return " ".join(str(getattr(turn, "content", "") or "").split()).strip()
    return ""


def build_current_turn_priority_guard(
    user_message: str,
    *,
    mission_context: dict | None = None,
    current_goal: str | None = None,
) -> dict:
    """Decide whether active tracked problem context may bind this turn."""
    normalized_message = " ".join(str(user_message or "").split()).strip()
    lower = normalized_message.lower()
    mission_context = dict(mission_context or {})
    active_mission = dict(mission_context.get("active_mission") or {})
    mission_active = bool(active_mission)
    debug_selector = resolve_debug_selector(lower)
    explicit_problem_resume = (
        debug_selector.get("scope") == "debugging"
        or detect_otem(lower)
        or any(hint in lower for hint in ACTIVE_PROBLEM_RESUME_HINTS)
    )
    direct_answer_request = (
        any(hint in lower for hint in DIRECT_ANSWER_PRIORITY_HINTS)
        or lower.startswith(DIRECT_QUESTION_PREFIXES)
        or (
            "?" in normalized_message
            and not explicit_problem_resume
            and not detect_otem(lower)
        )
    )
    effective_goal = " ".join(str(current_goal or "").split()).strip() or _infer_goal(normalized_message)
    if not mission_active:
        return {
            "status": "inactive",
            "allow_active_problem_context": False,
            "reason": "No active tracked problem context is available for this turn.",
            "matched_trigger": None,
            "effective_goal": _infer_goal(normalized_message),
            "mission_active": False,
            "direct_answer_request": bool(direct_answer_request),
        }
    if explicit_problem_resume:
        return {
            "status": "context_bound",
            "allow_active_problem_context": True,
            "reason": "The operator explicitly resumed troubleshooting or tracked work for this turn.",
            "matched_trigger": (
                debug_selector.get("matched_trigger")
                or next((hint for hint in ACTIVE_PROBLEM_RESUME_HINTS if hint in lower), None)
                or ("otem" if detect_otem(lower) else None)
            ),
            "effective_goal": effective_goal,
            "mission_active": True,
            "direct_answer_request": bool(direct_answer_request),
        }
    if direct_answer_request:
        return {
            "status": "answer_first",
            "allow_active_problem_context": False,
            "reason": "The present turn is directly answerable, so tracked problem context stays in reserve.",
            "matched_trigger": next((hint for hint in DIRECT_ANSWER_PRIORITY_HINTS if hint in lower), None),
            "effective_goal": _infer_goal(normalized_message),
            "mission_active": True,
            "direct_answer_request": True,
        }
    return {
        "status": "suppressed",
        "allow_active_problem_context": False,
        "reason": "Active tracked context may inform this turn silently, but it should not override the current ask.",
        "matched_trigger": None,
        "effective_goal": _infer_goal(normalized_message),
        "mission_active": True,
        "direct_answer_request": False,
    }


def _normalize_memory_cue_text(value) -> str:
    """Normalize cue text so dedupe and trace checks stay stable."""
    return " ".join(str(value or "").split()).strip()


def _memory_cue_text(cue) -> str:
    """Extract the most human-meaningful text field from one cue-like object."""
    if isinstance(cue, dict):
        for key in ("text", "content", "insight", "excerpt", "summary"):
            cleaned = _normalize_memory_cue_text(cue.get(key))
            if cleaned:
                return cleaned
        return _normalize_memory_cue_text(cue)

    for key in ("text", "content", "insight", "excerpt", "summary"):
        cleaned = _normalize_memory_cue_text(getattr(cue, key, None))
        if cleaned:
            return cleaned

    return _normalize_memory_cue_text(cue)


def dedupe_memory_cues(cues):
    """Return one stable ordered list of unique cue-like records.

    Prefer a cue id when one exists. Otherwise fall back to normalized text.
    """
    seen_ids = set()
    seen_texts = set()
    unique = []

    for cue in list(cues or []):
        cue_id = None
        if isinstance(cue, dict):
            cue_id = _normalize_memory_cue_text(cue.get("id"))
        else:
            cue_id = _normalize_memory_cue_text(getattr(cue, "id", None))

        cue_text = _memory_cue_text(cue)
        normalized_text = cue_text.lower()
        if cue_id and cue_id in seen_ids:
            continue
        if normalized_text and normalized_text in seen_texts:
            continue

        if cue_id:
            seen_ids.add(cue_id)
        if normalized_text:
            seen_texts.add(normalized_text)
        unique.append(cue)

    return unique


def sanitize_assistant_context_text(raw_response: str | None) -> str:
    """Strip scaffold-heavy assistant echoes before they re-enter prompt assembly."""
    return scrub_assistant_guidance_echo(raw_response)


def _infer_goal(text: str) -> str:
    """Infer the operator's current goal from the latest request."""
    lower = text.lower()

    if any(token in lower for token in ("fix", "debug", "repair", "broken", "error")):
        return "repair something that is blocking progress"
    if any(token in lower for token in ("build", "implement", "make", "wire", "ship", "code")):
        return "turn the idea into a working build"
    if any(token in lower for token in ("plan", "roadmap", "milestone", "organize")):
        return "shape the work into a clear plan"
    if any(token in lower for token in ("research", "look into", "compare", "understand")):
        return "understand the space before committing"
    if any(
        token in lower
        for token in ("write", "rewrite", "scene", "chapter", "story", "dialogue", "canon", "continuity")
    ):
        return "shape the writing into a stronger draft without losing the core intent"
    if any(token in lower for token in ("jarvis", "assistant", "memory", "voice", "spiral")):
        return "evolve Jarvis into a more alive personal assistant"
    return "help the operator make concrete forward progress"


def _extract_topics(text: str):
    """Map the latest message onto a small set of stable topics."""
    lower = text.lower()
    topics = []

    for topic, hints in TOPIC_HINTS.items():
        if any(hint in lower for hint in hints):
            topics.append(topic)

    if not topics:
        topics.append("general")

    return topics


def _extract_preferences(text: str):
    """Learn lightweight operator preferences from explicit phrasing."""
    lower = text.lower()
    preferences = {}

    if "step by step" in lower or "walk me through" in lower:
        preferences["pace"] = "step-by-step"
    if "keep it short" in lower or "be concise" in lower or "brief" in lower:
        preferences["brevity"] = "concise"
    if "for myself" in lower or "private" in lower or "local" in lower:
        preferences["privacy"] = "local-first"
    if "show code" in lower or "implement it" in lower or "do it" in lower:
        preferences["delivery"] = "build-first"

    return preferences


def _choose_mode(text: str, spiral_state):
    """Choose the current Spiral-style operating mode."""
    lower = text.lower()
    asks_for_reflection = any(
        token in lower
        for token in ("why", "reflect", "meaning", "understand", "explain", "think through")
    )
    asks_for_action = any(
        token in lower
        for token in (
            "build",
            "fix",
            "implement",
            "make",
            "wire",
            "ship",
            "run",
            "do it",
            "next step",
        )
    )

    if asks_for_reflection or spiral_state.uncertainty > 0.72:
        return "reflect"
    if asks_for_action or spiral_state.goal_convergence > 0.48:
        return "act"
    return "explore"


@dataclass
class SpiralState:
    """A lightweight session state inspired by the Spiral prototypes."""

    active_mode: str = "explore"
    focus: float = 0.50
    intensity: float = 0.46
    uncertainty: float = 0.58
    novelty: float = 0.50
    confidence: float = 0.42
    goal_convergence: float = 0.34
    current_goal: str = "help the operator make concrete forward progress"
    last_reflection: str = "Session initialized."

    def to_dict(self):
        return {
            "active_mode": self.active_mode,
            "focus": round(self.focus, 3),
            "intensity": round(self.intensity, 3),
            "uncertainty": round(self.uncertainty, 3),
            "novelty": round(self.novelty, 3),
            "confidence": round(self.confidence, 3),
            "goal_convergence": round(self.goal_convergence, 3),
            "current_goal": self.current_goal,
            "last_reflection": self.last_reflection,
        }


@dataclass
class SessionMemorySummary:
    """A compact local memory layer for one private operator."""

    recent_topics: list[str] = field(default_factory=list)
    active_projects: list[str] = field(default_factory=list)
    preferences: dict[str, str] = field(default_factory=dict)
    working_memory: list[str] = field(default_factory=list)
    last_user_intent: str = ""

    def to_dict(self):
        return {
            "recent_topics": list(self.recent_topics),
            "active_projects": list(self.active_projects),
            "preferences": dict(self.preferences),
            "working_memory": list(self.working_memory),
            "last_user_intent": self.last_user_intent,
        }


class ConversationTurn:
    """A single turn in a conversation."""

    def __init__(self, role: str, content: str, metadata: dict | None = None):
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now(UTC)

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
            "metadata": dict(self.metadata),
            "timestamp": self.timestamp.isoformat(),
        }


class ConversationSession:
    """A conversation session with history and Spiral-inspired runtime state."""

    def __init__(self, session_id: str, max_turns: int = 50, system_prompt: str = None):
        self.session_id = session_id
        self.max_turns = max_turns
        self.turns = []
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        self.metadata = {
            "persona_mode": "builder",
            "requested_response_mode": "fast",
            "response_mode": "fast",
            "preferred_provider": "local",
            "provider_mode": derive_provider_mode("local", "local"),
            "provider_fallback": "local",
            "provider_notice": None,
            "requested_specialists": [],
            "requested_specialist_preset": None,
            "model_route": None,
            "god_brain": None,
            "mode_guidance": None,
            "last_effective_response_mode": None,
            "last_selector_scope": "operator_task",
            "last_selector_voice": "jarvis",
            "policy_status": default_policy_status(),
            "corrigibility": default_corrigibility_state(),
            "corrigibility_prompt_block": None,
            "continuity_profile": None,
            "continuity_prompt_block": None,
            "mission_board": None,
            "mission_critic": None,
            "pending_action": None,
            "action_lifecycle": None,
            "action_registry": {},
            "turn_contract": None,
            "last_turn_contract": None,
            "thread_contract": None,
            "drift_state": None,
            "sovereignty_contract": None,
            "authority_preferences": default_authority_preferences(),
            "knowledge_conflict_decisions": default_knowledge_conflict_decisions(),
            "mode_freeze": None,
            "state_snapshots": [],
            "otem_state": None,
            "forge_last_code": None,
            "forge_last_evaluation": None,
            "evolve_last_job": None,
            "loaded_session_archive": None,
            "tiny_nova_memories": [],
            "small_nova_memories": [],
            "super_nova_memories": [],
        }
        self.spiral_state = SpiralState()
        self.memory_summary = SessionMemorySummary()
        self.session_state = SessionLifecycle()

        if system_prompt:
            self.turns.append(ConversationTurn("system", system_prompt))

    def add_turn(self, role: str, content: str, metadata: dict | None = None):
        """Add a turn to the conversation and evolve session state."""
        turn = ConversationTurn(role, content, metadata=metadata)
        self.turns.append(turn)
        self.updated_at = turn.timestamp
        self._update_runtime_state(role, content, metadata=turn.metadata)

        if len(self.turns) > self.max_turns:
            system_turns = [t for t in self.turns if t.role == "system"]
            non_system = [t for t in self.turns if t.role != "system"]
            self.turns = system_turns + non_system[-(self.max_turns - len(system_turns)):]

    def _update_runtime_state(self, role: str, content: str, metadata: dict | None = None):
        """Evolve memory and mode after each user or assistant turn."""
        metadata = metadata or {}
        if role == "user":
            self._update_from_user_message(content)
        elif role == "assistant":
            self._update_from_assistant_message(content, metadata=metadata)

    def transition_state(
        self,
        next_state: str,
        summary: str,
        reason: str | None = None,
        event_type: str | None = None,
    ):
        """Update the V8-style lifecycle state for this session."""
        return self.session_state.transition(
            next_state,
            summary=summary,
            reason=reason,
            event_type=event_type,
        )

    def apply_policy_status(self, policy_status: dict | None):
        """Store the latest local policy decision for the session."""
        self.metadata["policy_status"] = dict(policy_status or default_policy_status())

    def rollback_last_assistant_turn(self, skip_tool_types=None):
        """Remove the latest substantive assistant reply from session history."""
        skip_types = set(skip_tool_types or [])
        for index in range(len(self.turns) - 1, -1, -1):
            turn = self.turns[index]
            if turn.role != "assistant":
                continue
            tool_type = ((turn.metadata or {}).get("tool_result") or {}).get("type")
            if tool_type in skip_types:
                continue

            removed = self.turns.pop(index)
            self.updated_at = datetime.now(UTC)
            self.spiral_state.confidence = _clamp(self.spiral_state.confidence - 0.06)
            self.spiral_state.uncertainty = _clamp(self.spiral_state.uncertainty + 0.08)
            self.spiral_state.last_reflection = (
                "Last assistant reply was withdrawn after an operator correction."
            )
            return {
                "role": removed.role,
                "content": removed.content,
                "tool_type": tool_type,
                "timestamp": removed.timestamp.isoformat(),
            }

        return None

    def _update_from_user_message(self, content: str):
        """Apply heuristic Spiral-style state updates from operator input."""
        lower = content.lower()
        mode = _choose_mode(content, self.spiral_state)
        goal = _infer_goal(content)
        topics = _extract_topics(content)
        preferences = _extract_preferences(content)
        high_energy = any(token in lower for token in ("now", "fast", "real", "live", "crazy"))
        novelty_signal = any(token in lower for token in ("idea", "new", "invent", "crazy"))

        self.spiral_state.active_mode = mode
        self.spiral_state.current_goal = goal
        self.spiral_state.focus = _clamp(
            self.spiral_state.focus + (0.09 if mode == "act" else 0.04)
        )
        self.spiral_state.intensity = _clamp(
            self.spiral_state.intensity + (0.08 if high_energy else -0.01)
        )
        self.spiral_state.uncertainty = _clamp(
            self.spiral_state.uncertainty - (0.05 if mode == "act" else 0.01)
        )
        self.spiral_state.novelty = _clamp(
            self.spiral_state.novelty + (0.08 if novelty_signal else -0.02)
        )
        self.spiral_state.goal_convergence = _clamp(
            self.spiral_state.goal_convergence + (0.11 if mode == "act" else 0.05)
        )
        self.spiral_state.last_reflection = f"Shifted into {mode} mode around {goal}."

        self.memory_summary.last_user_intent = goal
        self.memory_summary.recent_topics = _trim_unique(
            topics + self.memory_summary.recent_topics,
            limit=5,
        )
        if mode in {"act", "reflect"}:
            self.memory_summary.active_projects = _trim_unique(
                [goal] + self.memory_summary.active_projects,
                limit=3,
            )

        for key, value in preferences.items():
            self.memory_summary.preferences[key] = value

        self.memory_summary.working_memory = _trim_unique(
            [_clip_text(content, limit=110)] + self.memory_summary.working_memory,
            limit=4,
        )
        self.transition_state(
            "primed",
            summary="Operator issued a new request.",
            reason="user_turn",
            event_type="user_turn",
        )

    def _update_from_assistant_message(self, content: str, metadata: dict | None = None):
        """Adjust confidence and reflection after Jarvis answers."""
        metadata = metadata or {}
        lower = content.lower()
        actionable = any(
            token in lower
            for token in ("next", "step", "1.", "2.", "run", "open", "update", "fix", "build")
        )
        reflective = any(
            token in lower
            for token in ("pattern", "because", "tradeoff", "notice", "reason", "means")
        )

        if actionable:
            self.spiral_state.confidence = _clamp(self.spiral_state.confidence + 0.08)
            self.spiral_state.uncertainty = _clamp(self.spiral_state.uncertainty - 0.07)
            self.spiral_state.focus = _clamp(self.spiral_state.focus + 0.03)
            self.spiral_state.goal_convergence = _clamp(
                self.spiral_state.goal_convergence + 0.06
            )
            self.spiral_state.last_reflection = "Last reply landed as actionable guidance."
        elif reflective:
            self.spiral_state.confidence = _clamp(self.spiral_state.confidence + 0.03)
            self.spiral_state.uncertainty = _clamp(self.spiral_state.uncertainty - 0.03)
            self.spiral_state.novelty = _clamp(self.spiral_state.novelty + 0.04)
            self.spiral_state.last_reflection = "Last reply added reflection and pattern-matching."
        else:
            self.spiral_state.confidence = _clamp(self.spiral_state.confidence - 0.01)
            self.spiral_state.uncertainty = _clamp(self.spiral_state.uncertainty + 0.02)
            self.spiral_state.last_reflection = (
                "Last reply stayed general; keep nudging toward concrete help."
            )

        if uses_companion_lane(
            self.metadata.get("persona_mode"),
            self.metadata.get("response_mode"),
        ):
            micro_insight = build_companion_micro_insight(
                self.metadata.get("persona_mode"),
                self.metadata.get("response_mode"),
                reply_text=content,
                user_text=self._latest_user_turn_text(),
            )
            self._remember_companion_insight(micro_insight)

        tool_result = metadata.get("tool_result") or {}
        tool_type = tool_result.get("type")
        if tool_type == "action_request":
            self.transition_state(
                "awaiting_approval",
                summary="Jarvis proposed a local action and is waiting on approval.",
                reason="action_request",
                event_type="action_request",
            )
        elif tool_type == "action_result":
            self.transition_state(
                "ready",
                summary="Jarvis completed a local action and is ready for the next move.",
                reason="action_result",
                event_type="action_result",
            )
        else:
            self.transition_state(
                "ready",
                summary="Jarvis answered and is ready for the next turn.",
                reason="assistant_turn",
                event_type="assistant_turn",
            )

    def _latest_user_turn_text(self) -> str:
        """Return the latest user turn text for companion continuity filtering."""
        for turn in reversed(self.turns):
            if turn.role == "user" and str(turn.content or "").strip():
                return turn.content
        return ""

    def _remember_companion_insight(self, insight: dict | None) -> None:
        """Persist one bounded companion continuity cue for the current session."""
        if not insight:
            return
        profile = get_companion_lane_profile(
            self.metadata.get("persona_mode"),
            self.metadata.get("response_mode"),
        )
        if not profile:
            return

        normalized_insight = str(insight.get("insight") or "").strip().lower()
        if not normalized_insight:
            return

        existing = [
            dict(entry)
            for entry in list(self.metadata.get(profile["memory_key"]) or [])
            if isinstance(entry, dict)
        ]
        next_memories = [insight]
        for entry in existing:
            entry_key = str(entry.get("insight") or "").strip().lower()
            if not entry_key or entry_key == normalized_insight:
                continue
            next_memories.append(entry)
            if len(next_memories) >= profile["memory_limit"]:
                break
        self.metadata[profile["memory_key"]] = next_memories

    def _turn_context_content(self, turn: ConversationTurn) -> str:
        """Return the prompt-safe form of one stored turn."""
        content = str(turn.content or "").strip()
        if not content:
            return ""
        if turn.role == "assistant":
            return sanitize_assistant_context_text(content)
        return content

    def get_context_window(self, max_tokens_estimate: int = 2048) -> list:
        """Get recent turns that fit within a token budget.

        Uses a rough estimate of 4 chars per token.
        """
        result = []
        total_chars = 0
        char_budget = max_tokens_estimate * 4

        for turn in reversed(self.turns):
            turn_content = self._turn_context_content(turn)
            if not turn_content:
                continue
            turn_chars = len(turn_content)
            if total_chars + turn_chars > char_budget and result:
                break
            result.insert(0, turn)
            total_chars += turn_chars

        return result

    def _build_runtime_directive(self):
        """Render a compact system message that makes Jarvis feel alive and stateful."""
        state = self.spiral_state
        persona_mode = normalize_persona_mode(self.metadata.get("persona_mode"))
        response_mode = normalize_response_mode(self.metadata.get("response_mode"))
        prompt_lane = str(self.metadata.get("prompt_lane") or "").strip().lower()
        latest_user_message = _latest_user_turn_text(self.turns)
        context_priority_guard = dict(
            self.metadata.get("context_priority_guard")
            or build_current_turn_priority_guard(
                latest_user_message,
                mission_context=self.metadata.get("mission_board"),
                current_goal=state.current_goal,
            )
        )
        turn_goal = str(
            self.metadata.get("turn_current_goal")
            or context_priority_guard.get("effective_goal")
            or state.current_goal
        ).strip() or state.current_goal
        persona_directive = PERSONA_DIRECTIVES[persona_mode]
        response_directive = RESPONSE_MODE_DIRECTIVES[response_mode]
        if uses_companion_lane(persona_mode, response_mode):
            profile = get_companion_lane_profile(persona_mode, response_mode) or COMPANION_LANE_PROFILES["tiny_nova"]
            topics = ", ".join(self.memory_summary.recent_topics[:3]) or profile["default_topics"]
            filtered_persistent_memories = filter_companion_persistent_memories(
                dedupe_memory_cues(self.metadata.get("persistent_memories") or []),
                limit=profile["continuity_limit"],
            )
            continuity_candidates = [
                _clip_text(memory.get("insight", ""), limit=90)
                for memory in (self.metadata.get(profile["memory_key"]) or [])[: profile["continuity_limit"]]
                if memory.get("insight")
            ]
            continuity_candidates.extend(
                _clip_text(memory.get("text") or memory.get("content", ""), limit=90)
                for memory in filtered_persistent_memories[: profile["continuity_limit"]]
                if memory.get("text") or memory.get("content")
            )
            memory_lines = ", ".join(_trim_unique(continuity_candidates, limit=3)) or "none loaded"
            return (
                f"{profile['label']} runtime state:\n"
                f"- identity: {profile['label']}\n"
                f"- tone: {profile['tone']}\n"
                f"- current_focus: {turn_goal}\n"
                f"- recent_topics: {topics}\n"
                f"- continuity_notes: {memory_lines}\n"
                f"- persona_mode: {persona_mode}\n"
                f"- response_mode: {response_mode}\n"
                f"- persona_behavior: {persona_directive}\n"
                f"- response_behavior: {response_directive}\n"
                "- boundaries: stay in natural conversation, no tools, no execution, no operator framing, no system-awareness, no hidden-architecture references\n"
                f"- reply_shape: {profile['reply_shape']}"
            )
        if prompt_lane == "relational":
            return (
                "Jarvis relational runtime:\n"
                "- identity: jarvis\n"
                f"- persona_mode: {persona_mode}\n"
                f"- response_mode: {response_mode}\n"
                f"- current_focus: {turn_goal}\n"
                "- lane: relational_question_or_direct_challenge\n"
                "- reply_behavior: answer personally, directly, and in one steady Jarvis voice\n"
                "- boundaries: no workspace context, no mission board, no live research, no tool execution, no hidden planning labels, no operator scaffolding\n"
                "- continuity: stay present-focused unless the user explicitly asks for prior context"
            )

        topics = ", ".join(self.memory_summary.recent_topics[:3]) or "general support"
        projects = ", ".join(self.memory_summary.active_projects[:2]) or "none yet"
        preferences = ", ".join(
            f"{key}={value}"
            for key, value in list(self.memory_summary.preferences.items())[:3]
        ) or "practical, local-first"
        behavior_map = {
            "act": "Prefer decisive execution help and end with the clearest next action.",
            "reflect": "Explain patterns, tradeoffs, and what matters before prescribing action.",
            "explore": "Broaden options briefly, then narrow toward the most useful next move.",
        }
        persistent_memories = dedupe_memory_cues(self.metadata.get("persistent_memories", []))
        memory_lines = ", ".join(
            _clip_text(_memory_cue_text(memory), limit=90)
            for memory in persistent_memories[:3]
            if _memory_cue_text(memory)
        ) or "none loaded"
        workspace_context = self.metadata.get("workspace_context") or {}
        workspace_hits = len(workspace_context.get("results", [])[:4])
        workspace_scope = workspace_context.get("project_scope") or "not attached"
        live_research = self.metadata.get("live_research") or {}
        research_sources = len(live_research.get("sources", [])[:4])
        mission_board = self.metadata.get("mission_board") or {}
        active_mission = mission_board.get("active_mission") or {}
        allow_active_problem_context = bool(
            context_priority_guard.get("allow_active_problem_context")
        )
        if allow_active_problem_context:
            mission_summary = mission_board.get("summary") or "Mission Board is empty."
            mission_title = active_mission.get("title") or "not_active"
            mission_objective = active_mission.get("objective") or "not set"
            mission_next_step = active_mission.get("next_step") or "not set"
            mission_blocker = active_mission.get("blocker") or "none"
            mission_critic = self.metadata.get("mission_critic") or active_mission.get("critic") or {}
            mission_critic_status = mission_critic.get("status", "not_active")
            mission_critic_summary = mission_critic.get("summary") or "none"
            mission_critic_next = mission_critic.get("recommended_next") or "none"
        else:
            mission_summary = "Hold tracked mission context in reserve unless the operator explicitly resumes it."
            mission_title = "withheld_for_present_turn"
            mission_objective = "answer the current request directly first"
            mission_next_step = "only resume tracked work if the operator explicitly asks"
            mission_blocker = "not bound for this turn"
            mission_critic_status = "withheld_for_present_turn"
            mission_critic_summary = context_priority_guard.get("reason") or "not bound for this turn"
            mission_critic_next = "not bound for this turn"
        specialist_profile = self.metadata.get("specialist_profile") or {}
        specialist_domain = specialist_profile.get("domain", "not_active")
        specialist_focus_name = specialist_profile.get("focus", "not_active").replace("_", " ")
        specialist_selection = specialist_profile.get("selection_source", "auto")
        specialist_lenses = ", ".join(
            lens.get("label", "")
            for lens in specialist_profile.get("specialists", [])[:5]
            if lens.get("label")
        ) or "none active"
        requested_specialists = ", ".join(self.metadata.get("requested_specialists") or []) or "none pinned"
        specialist_preset = self.metadata.get("requested_specialist_preset") or "none"
        writing_focus = self.metadata.get("writing_focus") or {}
        writing_focus_name = writing_focus.get("focus", "not_active").replace("_", " ")
        policy_status = self.metadata.get("policy_status") or default_policy_status()
        corrigibility = self.metadata.get("corrigibility") or default_corrigibility_state()
        pending_correction = corrigibility.get("pending") or {}
        correction_status = corrigibility.get("status", "steady")
        correction_summary = (
            pending_correction.get("guidance")
            or pending_correction.get("command")
            or "none queued"
        )
        correction_behavior = (
            "Honor the latest operator correction silently on the next generated reply."
            if pending_correction
            else "No pending operator correction is queued right now."
        )
        model_route = self.metadata.get("model_route") or {}
        model_route_label = model_route.get("label", "not_active")
        model_route_reason = model_route.get("reason", "not_active")
        provider_preference = normalize_provider_identifier(
            self.metadata.get("preferred_provider"),
            default="local",
        )
        provider_mode = self.metadata.get("provider_mode") or derive_provider_mode(
            provider_preference,
            self.metadata.get("provider_fallback"),
        )
        provider_fallback = normalize_provider_identifier(
            self.metadata.get("provider_fallback"),
            default="local",
        )
        provider_label = model_route.get("provider_label", "Local Heroine")
        provider_reason = model_route.get("provider_reason", "local_primary")
        model_route_instruction = model_route.get(
            "instruction",
            "No turn-specific model route is active for this turn.",
        )
        god_brain = self.metadata.get("god_brain") or {}
        god_brain_strategy = god_brain.get("strategy_label", "not_active")
        god_brain_council = god_brain.get("council_summary", "not_active")
        god_brain_action_bias = god_brain.get("action_bias_label", "answer directly")
        god_brain_arbiter = (god_brain.get("arbiter") or {}).get(
            "rule",
            "Lead with the clearest grounded answer and suppress hidden internal deliberation.",
        )
        god_brain_confidence = (god_brain.get("arbiter") or {}).get("confidence_label", "not_active")
        god_brain_instruction = god_brain.get(
            "instruction",
            "No sovereign orchestration trace is active for this turn.",
        )

        return (
            "Jarvis runtime state:\n"
            f"- protocol_version: {PROTOCOL_ID}/{PROTOCOL_VERSION}\n"
            f"- active_mode: {state.active_mode}\n"
            f"- current_goal: {turn_goal}\n"
            f"- session_state: {self.session_state.state} ({self.session_state.summary})\n"
            f"- recent_topics: {topics}\n"
            f"- active_projects: {projects}\n"
            f"- operator_preferences: {preferences}\n"
            f"- long_term_memory: {memory_lines}\n"
            f"- workspace_context: {workspace_hits} local matches scoped to {workspace_scope}\n"
            f"- live_research: {research_sources} current sources attached\n"
            f"- mission_board: {mission_summary}\n"
            f"- active_mission: {mission_title}\n"
            f"- mission_objective: {mission_objective}\n"
            f"- mission_next_step: {mission_next_step}\n"
            f"- mission_blocker: {mission_blocker}\n"
            f"- mission_critic: {mission_critic_status}\n"
            f"- mission_critic_summary: {mission_critic_summary}\n"
            f"- mission_critic_next: {mission_critic_next}\n"
            f"- current_turn_priority: {context_priority_guard.get('status') or 'inactive'}\n"
            f"- specialist_domain: {specialist_domain}\n"
            f"- specialist_focus: {specialist_focus_name}\n"
            f"- specialist_selection: {specialist_selection}\n"
            f"- pinned_specialists: {requested_specialists}\n"
            f"- specialist_preset: {specialist_preset}\n"
            f"- writing_focus: {writing_focus_name}\n"
            f"- specialist_lenses: {specialist_lenses}\n"
            f"- persona_mode: {persona_mode}\n"
            f"- response_mode: {response_mode}\n"
            f"- provider_preference: {provider_preference}\n"
            f"- provider_mode: {provider_mode}\n"
            f"- provider_fallback: {provider_fallback}\n"
            f"- provider_route: {provider_label} ({provider_reason})\n"
            f"- model_route: {model_route_label} ({model_route_reason})\n"
            f"- policy_posture: {policy_status.get('posture', 'nominal')}\n"
            f"- corrigibility_status: {correction_status}\n"
            f"- correction_summary: {correction_summary}\n"
            f"- god_brain_strategy: {god_brain_strategy}\n"
            f"- god_brain_council: {god_brain_council}\n"
            f"- god_brain_action_bias: {god_brain_action_bias}\n"
            f"- god_brain_confidence: {god_brain_confidence}\n"
            f"- reflection: {state.last_reflection}\n"
            f"- persona_behavior: {persona_directive}\n"
            f"- response_behavior: {response_directive}\n"
            f"- specialist_behavior: {specialist_profile.get('directive', 'No specialist registry profile is active for this turn.')}\n"
            f"- writing_behavior: {writing_focus.get('directive', 'No specialist writing lenses are active for this turn.')}\n"
            f"- model_route_behavior: {model_route_instruction}\n"
            f"- corrigibility_behavior: {correction_behavior}\n"
            f"- god_brain_arbiter: {god_brain_arbiter}\n"
            f"- god_brain_behavior: {god_brain_instruction}\n"
            f"- behavior: {behavior_map[state.active_mode]}"
        )

    def build_prompt(self, max_tokens_estimate: int = 2048) -> str:
        """Build a formatted prompt string from conversation history."""
        parts = []

        for message in self.build_messages(max_tokens_estimate=max_tokens_estimate):
            if message["role"] == "system":
                parts.append(f"[INST] <<SYS>>\n{message['content']}\n<</SYS>>")
            elif message["role"] == "user":
                parts.append(f"[INST] {message['content']} [/INST]")
            elif message["role"] == "assistant":
                parts.append(message["content"])

        return "\n".join(parts)

    def build_messages(
        self,
        max_tokens_estimate: int = 2048,
        extra_system_blocks: list[dict] | None = None,
        prompt_trace: dict | None = None,
        reserved_response_budget: int = 0,
    ) -> list[dict]:
        """Build structured messages for chat-tuned models."""
        turns = self.get_context_window(max_tokens_estimate)
        system_blocks = []
        dialogue_messages = []
        assistant_echoes_scrubbed = 0
        companion_active = uses_companion_lane(
            self.metadata.get("persona_mode"),
            self.metadata.get("response_mode"),
        )
        relational_active = str(self.metadata.get("prompt_lane") or "").strip().lower() == "relational"
        latest_user_message = _latest_user_turn_text(turns)
        context_priority_guard = dict(
            self.metadata.get("context_priority_guard")
            or build_current_turn_priority_guard(
                latest_user_message,
                mission_context=self.metadata.get("mission_board"),
                current_goal=self.spiral_state.current_goal,
            )
        )

        seed_seen = False
        for index, turn in enumerate(turns):
            raw_content = str(turn.content or "").strip()
            content = raw_content
            if turn.role == "assistant":
                content = sanitize_assistant_context_text(raw_content)
                if raw_content and content != raw_content:
                    assistant_echoes_scrubbed += 1
            if turn.role not in {"system", "user", "assistant"} or not content:
                continue
            entry = {"role": turn.role, "content": content}
            if turn.role == "system":
                identity = "system_seed" if not seed_seen else f"turn_system_{index}"
                seed_seen = True
                system_blocks.append(
                    {
                        "identity": identity,
                        "role": "system",
                        "content": content,
                        "channel": "instruction",
                        "source": "turn_system",
                        "metadata": dict(turn.metadata or {}),
                        "priority": 0 if identity == "system_seed" else 5,
                        "required": identity == "system_seed",
                        "singleton": identity == "system_seed",
                    }
                )
            else:
                dialogue_messages.append(entry)

        runtime_directive = self._build_runtime_directive()
        if runtime_directive:
            system_blocks.append(
                {
                    "identity": "runtime_directive",
                    "role": "system",
                    "content": runtime_directive,
                    "channel": "runtime",
                    "source": "runtime_directive",
                    "priority": 10,
                    "required": True,
                }
            )

        if (
            not companion_active
            and not relational_active
            and context_priority_guard.get("status") in {"answer_first", "suppressed"}
        ):
            system_blocks.append(
                {
                    "identity": "current_turn_priority_guard",
                    "role": "system",
                    "content": (
                        "Current-turn priority rule: answer the latest user request directly before "
                        "resuming any active tracked problem, mission, or debugging context. "
                        "Only re-enter older troubleshooting or mission frames when the user explicitly resumes them."
                    ),
                    "channel": "instruction",
                    "source": "current_turn_priority_guard",
                    "priority": 12,
                    "required": True,
                }
            )

        loaded_session_archive = self.metadata.get("loaded_session_archive") or {}
        if not relational_active and loaded_session_archive.get("prompt_block"):
            system_blocks.append(
                {
                    "identity": "loaded_session_archive",
                    "role": "system",
                    "content": loaded_session_archive["prompt_block"],
                    "channel": "archive",
                    "source": "loaded_session_archive",
                    "priority": 45,
                }
            )

        workspace_context = self.metadata.get("workspace_context") or {}
        if not companion_active and not relational_active and workspace_context.get("prompt_block"):
            system_blocks.append(
                {
                    "identity": "workspace_context",
                    "role": "system",
                    "content": workspace_context["prompt_block"],
                    "channel": "workspace",
                    "source": "workspace_context",
                    "priority": 55,
                }
            )

        live_research = self.metadata.get("live_research") or {}
        if not companion_active and not relational_active and live_research.get("prompt_block"):
            system_blocks.append(
                {
                    "identity": "live_research",
                    "role": "system",
                    "content": live_research["prompt_block"],
                    "channel": "research",
                    "source": "live_research",
                    "priority": 50,
                }
            )

        mission_board = self.metadata.get("mission_board") or {}
        if (
            not companion_active
            and not relational_active
            and context_priority_guard.get("allow_active_problem_context")
            and mission_board.get("prompt_block")
        ):
            system_blocks.append(
                {
                    "identity": "mission_board",
                    "role": "system",
                    "content": mission_board["prompt_block"],
                    "channel": "orchestration",
                    "source": "mission_board",
                    "priority": 40,
                }
            )

        corrigibility_prompt = self.metadata.get("corrigibility_prompt_block")
        if not companion_active and not relational_active and corrigibility_prompt:
            system_blocks.append(
                {
                    "identity": "corrigibility_guidance",
                    "role": "system",
                    "content": corrigibility_prompt,
                    "channel": "corrigibility",
                    "source": "corrigibility_prompt_block",
                    "priority": 30,
                }
            )

        continuity_prompt = self.metadata.get("continuity_prompt_block")
        if not companion_active and not relational_active and continuity_prompt:
            system_blocks.append(
                {
                    "identity": "continuity_profile",
                    "role": "system",
                    "content": continuity_prompt,
                    "channel": "continuity",
                    "source": "continuity_prompt_block",
                    "priority": 35,
                }
            )

        assembled_blocks, report = assemble_prompt_blocks(
            list(system_blocks) + list(extra_system_blocks or []),
            prompt_token_budget=max_tokens_estimate,
            reserved_response_budget=reserved_response_budget,
            assistant_echoes_scrubbed=assistant_echoes_scrubbed,
        )
        if isinstance(prompt_trace, dict):
            prompt_trace.clear()
            prompt_trace.update(report.to_dict())
        combined_system = combine_system_prompt(assembled_blocks)

        if combined_system:
            return [{"role": "system", "content": combined_system}] + dialogue_messages

        return dialogue_messages

    def build_protocol_envelope(
        self,
        max_tokens_estimate: int = 2048,
        tool_result: dict | None = None,
        extra_system_blocks: list[dict] | None = None,
        prompt_trace: dict | None = None,
        reserved_response_budget: int = 0,
    ) -> dict:
        """Build the normalized Jarvis protocol envelope for this session state."""
        turns = self.get_context_window(max_tokens_estimate)
        dialogue_messages = []
        system_blocks = []
        assistant_echoes_scrubbed = 0
        companion_active = uses_companion_lane(
            self.metadata.get("persona_mode"),
            self.metadata.get("response_mode"),
        )
        relational_active = str(self.metadata.get("prompt_lane") or "").strip().lower() == "relational"
        latest_user_message = _latest_user_turn_text(turns)
        context_priority_guard = dict(
            self.metadata.get("context_priority_guard")
            or build_current_turn_priority_guard(
                latest_user_message,
                mission_context=self.metadata.get("mission_board"),
                current_goal=self.spiral_state.current_goal,
            )
        )

        seed_seen = False
        for index, turn in enumerate(turns):
            raw_content = str(turn.content or "").strip()
            content = raw_content
            if turn.role == "assistant":
                content = sanitize_assistant_context_text(raw_content)
                if raw_content and content != raw_content:
                    assistant_echoes_scrubbed += 1
            if turn.role not in {"system", "user", "assistant"} or not content:
                continue
            if turn.role == "system":
                identity = "system_seed" if not seed_seen else f"turn_system_{index}"
                seed_seen = True
                system_blocks.append(
                    {
                        "identity": identity,
                        "role": "system",
                        "content": content,
                        "channel": "instruction",
                        "source": "turn_system",
                        "metadata": dict(turn.metadata or {}),
                        "priority": 0 if identity == "system_seed" else 5,
                        "required": identity == "system_seed",
                        "singleton": identity == "system_seed",
                    }
                )
            else:
                dialogue_messages.append(
                    {
                        "role": turn.role,
                        "content": content,
                        "channel": "dialogue",
                        "metadata": dict(turn.metadata or {}),
                    }
                )

        runtime_directive = self._build_runtime_directive()
        if runtime_directive:
            system_blocks.append(
                {
                    "identity": "runtime_directive",
                    "role": "system",
                    "content": runtime_directive,
                    "channel": "runtime",
                    "source": "runtime_directive",
                    "priority": 10,
                    "required": True,
                }
            )

        if (
            not companion_active
            and not relational_active
            and context_priority_guard.get("status") in {"answer_first", "suppressed"}
        ):
            system_blocks.append(
                {
                    "identity": "current_turn_priority_guard",
                    "role": "system",
                    "content": (
                        "Current-turn priority rule: answer the latest user request directly before "
                        "resuming any active tracked problem, mission, or debugging context. "
                        "Only re-enter older troubleshooting or mission frames when the user explicitly resumes them."
                    ),
                    "channel": "instruction",
                    "source": "current_turn_priority_guard",
                    "priority": 12,
                    "required": True,
                }
            )

        loaded_session_archive = self.metadata.get("loaded_session_archive") or {}
        if not relational_active and loaded_session_archive.get("prompt_block"):
            system_blocks.append(
                {
                    "identity": "loaded_session_archive",
                    "role": "system",
                    "content": loaded_session_archive["prompt_block"],
                    "channel": "archive",
                    "source": "loaded_session_archive",
                    "priority": 45,
                }
            )

        workspace_context = self.metadata.get("workspace_context") or {}
        if not companion_active and not relational_active and workspace_context.get("prompt_block"):
            system_blocks.append(
                {
                    "identity": "workspace_context",
                    "role": "system",
                    "content": workspace_context["prompt_block"],
                    "channel": "workspace",
                    "source": "workspace_context",
                    "priority": 55,
                }
            )

        live_research = self.metadata.get("live_research") or {}
        if not companion_active and not relational_active and live_research.get("prompt_block"):
            system_blocks.append(
                {
                    "identity": "live_research",
                    "role": "system",
                    "content": live_research["prompt_block"],
                    "channel": "research",
                    "source": "live_research",
                    "priority": 50,
                }
            )

        mission_board = self.metadata.get("mission_board") or {}
        if (
            not companion_active
            and not relational_active
            and context_priority_guard.get("allow_active_problem_context")
            and mission_board.get("prompt_block")
        ):
            system_blocks.append(
                {
                    "identity": "mission_board",
                    "role": "system",
                    "content": mission_board["prompt_block"],
                    "channel": "orchestration",
                    "source": "mission_board",
                    "priority": 40,
                }
            )

        corrigibility_prompt = self.metadata.get("corrigibility_prompt_block")
        if not companion_active and not relational_active and corrigibility_prompt:
            system_blocks.append(
                {
                    "identity": "corrigibility_guidance",
                    "role": "system",
                    "content": corrigibility_prompt,
                    "channel": "corrigibility",
                    "source": "corrigibility_prompt_block",
                    "priority": 30,
                }
            )

        continuity_prompt = self.metadata.get("continuity_prompt_block")
        if not companion_active and not relational_active and continuity_prompt:
            system_blocks.append(
                {
                    "identity": "continuity_profile",
                    "role": "system",
                    "content": continuity_prompt,
                    "channel": "continuity",
                    "source": "continuity_prompt_block",
                    "priority": 35,
                }
            )

        assembled_blocks, report = assemble_prompt_blocks(
            list(system_blocks) + list(extra_system_blocks or []),
            prompt_token_budget=max_tokens_estimate,
            reserved_response_budget=reserved_response_budget,
            assistant_echoes_scrubbed=assistant_echoes_scrubbed,
        )
        if isinstance(prompt_trace, dict):
            prompt_trace.clear()
            prompt_trace.update(report.to_dict())

        protocol_messages = [
            {
                "role": "system",
                "content": block.content,
                "channel": block.channel,
                "metadata": {
                    **dict(block.metadata or {}),
                    "prompt_identity": block.identity,
                    "prompt_source": block.source,
                },
            }
            for block in assembled_blocks
        ]
        protocol_messages.extend(dialogue_messages)

        return build_turn_envelope(
            session_id=self.session_id,
            messages=protocol_messages,
            response_mode=normalize_response_mode(self.metadata.get("response_mode")),
            persona_mode=normalize_persona_mode(self.metadata.get("persona_mode")),
            current_goal=self.spiral_state.current_goal,
            tool_result=tool_result,
            metadata={
                "session_state": self.session_state.state,
                "policy_posture": (
                    self.metadata.get("policy_status") or default_policy_status()
                ).get("posture", "nominal"),
                "requested_specialists": list(self.metadata.get("requested_specialists") or []),
                "requested_specialist_preset": self.metadata.get("requested_specialist_preset"),
            },
        )

    def protocol_summary(
        self,
        max_tokens_estimate: int = 2048,
        tool_result: dict | None = None,
    ) -> dict:
        """Build a compact runtime-facing summary of Jarvis protocol usage."""
        envelope = self.build_protocol_envelope(
            max_tokens_estimate=max_tokens_estimate,
            tool_result=tool_result,
        )
        return describe_protocol_use(
            session_id=self.session_id,
            messages=envelope.get("messages"),
            response_mode=normalize_response_mode(self.metadata.get("response_mode")),
            persona_mode=normalize_persona_mode(self.metadata.get("persona_mode")),
            current_goal=self.spiral_state.current_goal,
            tool_result=tool_result,
        )

    def to_dict(self):
        """Serialize a conversation session with Spiral-inspired runtime data."""
        return {
            "session_id": self.session_id,
            "turns": [t.to_dict() for t in self.turns],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "turn_count": len(self.turns),
            "active_mode": self.spiral_state.active_mode,
            "current_goal": self.spiral_state.current_goal,
            "spiral_state": self.spiral_state.to_dict(),
            "session_state": self.session_state.to_dict(),
            "memory_summary": self.memory_summary.to_dict(),
            "persistent_memories": list(self.metadata.get("persistent_memories", [])),
            "tiny_nova_memories": list(self.metadata.get("tiny_nova_memories", [])),
            "small_nova_memories": list(self.metadata.get("small_nova_memories", [])),
            "super_nova_memories": list(self.metadata.get("super_nova_memories", [])),
            "loaded_session_archive": serialize_loaded_session_archive(
                self.metadata.get("loaded_session_archive")
            ),
            "workspace_context": self.metadata.get("workspace_context"),
            "live_research": self.metadata.get("live_research"),
            "browser_verification": self.metadata.get("browser_verification"),
            "mission_board": self.metadata.get("mission_board"),
            "mission_critic": self.metadata.get("mission_critic"),
            "model_route": self.metadata.get("model_route"),
            "god_brain": self.metadata.get("god_brain"),
            "specialist_profile": self.metadata.get("specialist_profile"),
            "requested_specialists": list(self.metadata.get("requested_specialists") or []),
            "requested_specialist_preset": self.metadata.get("requested_specialist_preset"),
            "writing_focus": self.metadata.get("writing_focus"),
            "persona_mode": normalize_persona_mode(self.metadata.get("persona_mode")),
            "requested_response_mode": normalize_response_mode(
                self.metadata.get("requested_response_mode") or self.metadata.get("response_mode")
            ),
            "response_mode": normalize_response_mode(self.metadata.get("response_mode")),
            "preferred_provider": normalize_provider_identifier(
                self.metadata.get("preferred_provider"),
                default="local",
            ),
            "provider_mode": self.metadata.get("provider_mode")
            or derive_provider_mode(
                self.metadata.get("preferred_provider"),
                self.metadata.get("provider_fallback"),
            ),
            "provider_fallback": normalize_provider_identifier(
                self.metadata.get("provider_fallback"),
                default="local",
            ),
            "provider_notice": self.metadata.get("provider_notice"),
            "mode_guidance": self.metadata.get("mode_guidance"),
            "response_trace": self.metadata.get("response_trace"),
            "turn_contract": self.metadata.get("turn_contract"),
            "last_turn_contract": self.metadata.get("last_turn_contract"),
            "thread_contract": self.metadata.get("thread_contract"),
            "drift_state": self.metadata.get("drift_state"),
            "sovereignty_contract": self.metadata.get("sovereignty_contract"),
            "authority_preferences": normalize_authority_preferences(
                self.metadata.get("authority_preferences")
            ),
            "knowledge_conflict_decisions": normalize_knowledge_conflict_decisions(
                self.metadata.get("knowledge_conflict_decisions")
            ),
            "mode_freeze": self.metadata.get("mode_freeze"),
            "state_snapshots": list(self.metadata.get("state_snapshots") or []),
            "otem_state": self.metadata.get("otem_state"),
            "forge_last_code": self.metadata.get("forge_last_code"),
            "forge_last_evaluation": self.metadata.get("forge_last_evaluation"),
            "evolve_last_job": self.metadata.get("evolve_last_job"),
            "policy_status": dict(self.metadata.get("policy_status") or default_policy_status()),
            "continuity_profile": self.metadata.get("continuity_profile"),
            "pending_action": self.metadata.get("pending_action"),
            "action_lifecycle": self.metadata.get("action_lifecycle"),
            "corrigibility": dict(self.metadata.get("corrigibility") or default_corrigibility_state()),
            "jarvis_protocol": self.protocol_summary(),
        }


class ConversationMemory:
    """Manage multiple conversation sessions with automatic cleanup."""

    def __init__(self, max_sessions: int = 1000, session_ttl_hours: int = 24, max_turns: int = 50):
        self.max_sessions = max_sessions
        self.session_ttl = timedelta(hours=session_ttl_hours)
        self.max_turns = max_turns
        self.sessions = OrderedDict()
        self._lock = threading.Lock()

    def create_session(self, system_prompt: str = None) -> str:
        """Create a new conversation session and return its ID."""
        with self._lock:
            self._cleanup_expired()
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = ConversationSession(
                session_id=session_id,
                max_turns=self.max_turns,
                system_prompt=system_prompt,
            )
            logger.info(f"Created conversation session: {session_id}")
            return session_id

    def get_session(self, session_id: str) -> ConversationSession:
        """Retrieve a session by ID."""
        with self._lock:
            session = self.sessions.get(session_id)
            if session and (datetime.now(UTC) - session.updated_at) > self.session_ttl:
                del self.sessions[session_id]
                logger.info(f"Session expired: {session_id}")
                return None
            return session

    def add_exchange(self, session_id: str, user_message: str, assistant_response: str):
        """Add a user/assistant exchange to a session."""
        session = self.get_session(session_id)
        if not session:
            return False
        session.add_turn("user", user_message)
        session.add_turn("assistant", assistant_response)
        return True

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Deleted session: {session_id}")
                return True
            return False

    def list_sessions(self) -> list:
        """List all active sessions."""
        with self._lock:
            self._cleanup_expired()
            return [
                {
                    "session_id": sid,
                    "turn_count": len(session.turns),
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "active_mode": session.spiral_state.active_mode,
                    "current_goal": session.spiral_state.current_goal,
                    "session_state": session.session_state.to_dict(),
                    "persona_mode": normalize_persona_mode(session.metadata.get("persona_mode")),
                    "requested_response_mode": normalize_response_mode(
                        session.metadata.get("requested_response_mode")
                        or session.metadata.get("response_mode")
                    ),
                    "response_mode": normalize_response_mode(session.metadata.get("response_mode")),
                    "preferred_provider": normalize_provider_identifier(
                        session.metadata.get("preferred_provider"),
                        default="local",
                    ),
                    "provider_mode": session.metadata.get("provider_mode")
                    or derive_provider_mode(
                        session.metadata.get("preferred_provider"),
                        session.metadata.get("provider_fallback"),
                    ),
                    "provider_fallback": normalize_provider_identifier(
                        session.metadata.get("provider_fallback"),
                        default="local",
                    ),
                    "mode_guidance": session.metadata.get("mode_guidance"),
                    "recent_topics": list(session.memory_summary.recent_topics),
                    "policy_posture": (
                        session.metadata.get("policy_status") or default_policy_status()
                    ).get("posture", "nominal"),
                }
                for sid, session in self.sessions.items()
            ]

    def _cleanup_expired(self):
        """Remove expired sessions."""
        now = datetime.now(UTC)
        expired = [
            sid for sid, session in self.sessions.items()
            if (now - session.updated_at) > self.session_ttl
        ]
        for sid in expired:
            del self.sessions[sid]

        while len(self.sessions) > self.max_sessions:
            self.sessions.popitem(last=False)


conversation_memory = ConversationMemory()
