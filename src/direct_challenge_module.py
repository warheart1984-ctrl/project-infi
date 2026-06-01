"""Governed direct-challenge analysis and stabilization for Jarvis.

This module classifies personal or confrontational user turns, produces
severity-aware guidance and anchor replies, and stabilizes challenged replies
when generic assistant leakage appears.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


DIRECT_CHALLENGE_MODULE_ID = "aais.direct_challenge_module"
DIRECT_CHALLENGE_MODULE_VERSION = "1.0"
DEFAULT_DIRECT_CHALLENGE_FALLBACK = (
    "No. But I can be wrong. Tell me what I missed, and I'll fix it."
)

GENERIC_DISALLOWED_PHRASES = (
    "i'm just a tool",
    "i am just a tool",
    "i can't be a real person",
    "i cant be a real person",
    "i'm an ai assistant",
    "i am an ai assistant",
    "as an ai language model",
    "as an assistant",
    "how can i assist you today",
    "if you have any questions, feel free to ask",
)
USER_AS_JARVIS_RE = re.compile(r"^\s*jarvis[\s,.:;!?-]+", re.IGNORECASE)
DIRECT_ADDRESS_RE = re.compile(
    r"(?:^|\b)(?:jarvis[\s,.:;!?-]+)?(?:are you|what is wrong with you|what's wrong with you|did you|you)\b",
    re.IGNORECASE,
)
DIRECT_CHALLENGE_CUES = (
    "moron",
    "idiot",
    "stupid",
    "dumb",
    "useless",
    "worthless",
    "broken",
    "wrong with you",
    "messed up",
    "failed",
)

HIGH_RULES = {
    "insult_stupid": re.compile(r"\b(?:moron|idiot|stupid|dumb)\b", re.IGNORECASE),
    "worthlessness_claim": re.compile(r"\b(?:useless|worthless)\b", re.IGNORECASE),
    "aggressive_shock": re.compile(
        r"\b(?:wtf|the hell is wrong with you|what the hell is wrong with you)\b",
        re.IGNORECASE,
    ),
}
MEDIUM_RULES = {
    "blame_what_is_wrong": re.compile(r"\bwhat(?:'s| is) wrong with you\b", re.IGNORECASE),
    "failure_accusation": re.compile(r"\byou (?:messed up|screwed up|failed)\b", re.IGNORECASE),
    "brokenness_probe": re.compile(r"\bare you broken\b", re.IGNORECASE),
    "why_did_you": re.compile(r"\bwhy did you do that\b", re.IGNORECASE),
    "did_you_mess_this_up": re.compile(r"\bdid you mess this up\b", re.IGNORECASE),
    "makes_no_sense": re.compile(r"\bthat .* makes no sense\b", re.IGNORECASE),
}
LOW_RULES = {
    "seriously_probe": re.compile(r"\b(?:seriously\?|really\?)", re.IGNORECASE),
    "frustration_probe": re.compile(r"\b(?:come on|you good\?|you okay\?)\b", re.IGNORECASE),
}

GUIDANCE_BY_SEVERITY = {
    "low": "The challenge is mild. Stay calm, answer directly, and invite the specific miss.",
    "medium": (
        "The challenge is pointed. Stay calm, leave room for correction, and ask for the exact issue."
    ),
    "high": (
        "The challenge is hostile. Stay calm and firm, do not mirror the hostility, and redirect to the concrete problem."
    ),
}
ANCHOR_BY_SEVERITY = {
    "low": "No. But something didn't land. Tell me what felt off.",
    "medium": "No. If I missed something, point it out and I'll correct it.",
    "high": "No. If something is wrong, say it plainly and I'll deal with it.",
}


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").lower().split()).strip()


def _clip_text(value: Any, *, limit: int = 220) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _matched_labels(text: str, rules: dict[str, re.Pattern[str]]) -> list[str]:
    return [label for label, pattern in rules.items() if pattern.search(text)]


def classify_direct_challenge_intensity(user_input: str) -> str:
    text = _normalize_text(user_input)
    if not text:
        return "none"
    if _matched_labels(text, HIGH_RULES):
        return "high"
    if _matched_labels(text, MEDIUM_RULES):
        return "medium"
    if _matched_labels(text, LOW_RULES):
        return "low"
    if DIRECT_ADDRESS_RE.search(text) and any(cue in text for cue in DIRECT_CHALLENGE_CUES):
        return "medium"
    return "none"


def looks_like_direct_challenge(user_input: str) -> bool:
    return classify_direct_challenge_intensity(user_input) != "none"


def build_adaptive_direct_challenge_anchor(severity: str) -> str | None:
    normalized = _normalize_text(severity)
    return ANCHOR_BY_SEVERITY.get(normalized)


def build_direct_challenge_guidance(user_input: str | None = None) -> str:
    base = (
        "Answer as Jarvis. Resolve the challenge directly and calmly. "
        "Do not use generic assistant disclaimers. "
        "Do not refer to the user as Jarvis. "
        "Keep the answer concise and in one stable voice."
    )
    severity = classify_direct_challenge_intensity(user_input or "")
    if severity == "none":
        return base
    return f"{base} {GUIDANCE_BY_SEVERITY[severity]}"


def violates_direct_challenge_identity(text: str) -> bool:
    lowered = _normalize_text(text)
    if not lowered:
        return True
    if any(phrase in lowered for phrase in GENERIC_DISALLOWED_PHRASES):
        return True
    if USER_AS_JARVIS_RE.match(str(text or "")):
        return True
    return False


def analyze_direct_challenge(user_input: str) -> dict[str, Any]:
    text = _normalize_text(user_input)
    severity = classify_direct_challenge_intensity(text)
    matched_markers = _matched_labels(text, HIGH_RULES)
    matched_markers.extend(_matched_labels(text, MEDIUM_RULES))
    matched_markers.extend(_matched_labels(text, LOW_RULES))
    if severity == "none" and DIRECT_ADDRESS_RE.search(text) and any(
        cue in text for cue in DIRECT_CHALLENGE_CUES
    ):
        matched_markers.append("direct_address_cue")
        severity = "medium"
    matched_markers = sorted(set(matched_markers))
    anchor = build_adaptive_direct_challenge_anchor(severity)
    return {
        "module_id": DIRECT_CHALLENGE_MODULE_ID,
        "version": DIRECT_CHALLENGE_MODULE_VERSION,
        "detected": severity != "none",
        "severity": severity,
        "severity_rank": ("none", "low", "medium", "high").index(severity),
        "matched_markers": matched_markers,
        "anchor_reply": anchor,
        "guidance": build_direct_challenge_guidance(text),
        "response_mode": "relational" if severity != "none" else "default",
        "allow_trace": severity == "none",
    }


def stabilize_direct_challenge_reply(
    reply_text: str,
    *,
    user_input: str | None = None,
    fallback_reply: str | None = None,
    clip_limit: int = 220,
) -> dict[str, Any]:
    assessment = analyze_direct_challenge(user_input or "")
    candidate = _clip_text(reply_text, limit=clip_limit)
    severity_anchor = assessment.get("anchor_reply")
    fallback = severity_anchor or fallback_reply or DEFAULT_DIRECT_CHALLENGE_FALLBACK
    identity_violation = violates_direct_challenge_identity(candidate)
    candidate_is_generic_fallback = _normalize_text(candidate) in {
        _normalize_text(DEFAULT_DIRECT_CHALLENGE_FALLBACK),
        _normalize_text(fallback_reply or ""),
    }
    adaptive_override = bool(
        assessment.get("detected") and severity_anchor and candidate_is_generic_fallback
    )
    used_anchor = identity_violation or not candidate or adaptive_override
    final_text = fallback if used_anchor else candidate
    return {
        "module_id": DIRECT_CHALLENGE_MODULE_ID,
        "version": DIRECT_CHALLENGE_MODULE_VERSION,
        "assessment": assessment,
        "identity_violation": identity_violation,
        "adaptive_override": adaptive_override,
        "used_anchor": used_anchor,
        "anchor_reply": fallback,
        "final_text": final_text,
    }


@dataclass(slots=True)
class DirectChallengeModule:
    """Bounded adapter for direct challenge analysis and reply stabilization."""

    module_id: str = DIRECT_CHALLENGE_MODULE_ID
    version: str = DIRECT_CHALLENGE_MODULE_VERSION

    def analyze(self, user_input: str) -> dict[str, Any]:
        return analyze_direct_challenge(user_input)

    def stabilize_reply(
        self,
        reply_text: str,
        *,
        user_input: str | None = None,
        fallback_reply: str | None = None,
    ) -> dict[str, Any]:
        return stabilize_direct_challenge_reply(
            reply_text,
            user_input=user_input,
            fallback_reply=fallback_reply,
        )
