"""Mission-aware critic heuristics for Jarvis.

The critic does not replace the main answer path. It reviews whether a turn,
browser verification, or safe local action actually advanced the active mission
and returns a compact judgment that the Mission Board can store and surface.
"""

# Mythic: Critic
# Engineering: CriticEngine
from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
import re

from src.logger import get_logger
from src.performance import timed

logger = get_logger(__name__)

SCORE_THRESHOLD = 0.72
BLOCK_THRESHOLD = 0.52
DONE_THRESHOLD = 0.9

_TOKEN_RE = re.compile(r"[a-z0-9_./-]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "help",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "please",
    "so",
    "that",
    "the",
    "their",
    "them",
    "this",
    "to",
    "use",
    "we",
    "what",
    "when",
    "why",
    "with",
    "you",
    "your",
}
_ACTIONABLE_HINTS = (
    "next step",
    "run ",
    "open ",
    "check ",
    "verify ",
    "build ",
    "update ",
    "start ",
    "measure ",
    "inspect ",
    "approve ",
    "focus on",
    "ship ",
)
_UNCERTAINTY_HINTS = ("maybe", "possibly", "not sure", "unclear", "might")
_BLOCKER_HINTS = (
    "blocked",
    "can't",
    "cannot",
    "failed",
    "failure",
    "missing",
    "needs attention",
    "mismatch",
    "not available",
    "not enough",
)
_SUCCESS_HINTS = (
    "aligned",
    "clear",
    "completed",
    "done",
    "healthy",
    "passed",
    "ready",
    "resolved",
    "success",
    "working",
)
_COMPLETION_HINTS = ("done", "completed", "resolved", "fixed", "shipped", "green")


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _clip_text(value: str | None, limit: int = 220) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _tokenize(value: str | None) -> list[str]:
    tokens: list[str] = []
    for token in _TOKEN_RE.findall(str(value or "").lower()):
        if token in _STOPWORDS or len(token) <= 1:
            continue
        tokens.append(token)
        if "." in token:
            stem = token.rsplit("/", 1)[-1].split(".", 1)[0]
            if stem and stem not in _STOPWORDS and stem not in tokens:
                tokens.append(stem)
    return tokens


def _token_overlap(text: str | None, *references: str | None) -> tuple[float, list[str]]:
    text_tokens = set(_tokenize(text))
    reference_tokens: set[str] = set()
    for reference in references:
        reference_tokens.update(_tokenize(reference))
    if not text_tokens or not reference_tokens:
        return 0.0, []
    overlap = sorted(text_tokens & reference_tokens)
    coverage = len(overlap) / max(1, min(8, len(reference_tokens)))
    return min(1.0, coverage), overlap[:6]


def _contains_any(text: str | None, phrases) -> bool:
    lower = str(text or "").lower()
    return any(phrase in lower for phrase in phrases)


def _normalize_status(value: str | None) -> str | None:
    lowered = " ".join(str(value or "").lower().split()).strip().replace("-", "_")
    if lowered in {"active", "blocked", "done", "queued"}:
        return lowered
    return None


class MissionCriticEngine:
    """Review whether the latest output actually moved the active mission."""

    def _build_review(
        self,
        *,
        source: str,
        score: float,
        confidence: float,
        summary: str,
        wins=None,
        issues=None,
        recommended_next: str | None = None,
        suggested_mission_status: str | None = None,
    ) -> dict:
        normalized_score = round(_clamp(score), 2)
        normalized_confidence = round(_clamp(confidence), 2)
        wins = [_clip_text(item, limit=110) for item in wins or [] if str(item or "").strip()][:4]
        issues = [_clip_text(item, limit=110) for item in issues or [] if str(item or "").strip()][:4]

        if normalized_score >= DONE_THRESHOLD and _normalize_status(suggested_mission_status) == "done":
            status = "done"
        elif normalized_score < BLOCK_THRESHOLD or _normalize_status(suggested_mission_status) == "blocked":
            status = "blocked"
        elif normalized_score < SCORE_THRESHOLD or issues:
            status = "mixed"
        else:
            status = "advancing"

        review = {
            "source": source,
            "status": status,
            "score": normalized_score,
            "confidence": normalized_confidence,
            "summary": _clip_text(summary, limit=240),
            "wins": wins,
            "issues": issues,
            "recommended_next": _clip_text(recommended_next, limit=240) or None,
            "suggested_mission_status": _normalize_status(suggested_mission_status),
            "reviewed_at": _utc_now_iso(),
        }
        logger.info(
            "[MissionCritic] %s score=%.2f status=%s suggested=%s issues=%s",
            source,
            review["score"],
            review["status"],
            review["suggested_mission_status"],
            review["issues"],
        )
        return review

    @timed
    def review_reply(
        self,
        *,
        answer: str,
        user_message: str | None = None,
        mission_context: dict | None = None,
        response_trace: dict | None = None,
        tool_result: dict | None = None,
    ) -> dict | None:
        mission = ((mission_context or {}).get("active_mission") or {})
        if not mission:
            return None

        objective = mission.get("objective") or ""
        next_step = mission.get("next_step") or ""
        blocker = mission.get("blocker") or ""
        answer_text = str(answer or "")
        lower = answer_text.lower()
        wins: list[str] = []
        issues: list[str] = []
        score = 0.58

        mission_overlap, mission_terms = _token_overlap(answer_text, objective, next_step)
        if mission_overlap >= 0.18:
            score += 0.18
            wins.append(
                "Stayed aligned to the active mission"
                + (f" through {', '.join(mission_terms[:3])}" if mission_terms else ".")
            )
        else:
            score -= 0.12
            issues.append("Light alignment to the mission objective")

        request_overlap, request_terms = _token_overlap(answer_text, user_message)
        if user_message and request_overlap >= 0.16:
            score += 0.14
            wins.append(
                "Carried through the operator request"
                + (f" with {', '.join(request_terms[:3])}" if request_terms else ".")
            )
        elif user_message:
            score -= 0.08
            issues.append("Weak carry-through from the latest user request")

        actionable = _contains_any(lower, _ACTIONABLE_HINTS) or (
            bool(response_trace and response_trace.get("plan_summary"))
        )
        if actionable:
            score += 0.12
            wins.append("Ended with a concrete next move")
        else:
            issues.append("Did not land on a concrete next move")

        if len(answer_text.strip()) < 90 and len(" ".join([objective, next_step, user_message or ""])) > 180:
            score -= 0.1
            issues.append("Answer stayed thin relative to mission complexity")

        unresolved_uncertainty = _contains_any(lower, _UNCERTAINTY_HINTS) and not actionable
        if unresolved_uncertainty:
            score -= 0.12
            issues.append("Left uncertainty unresolved")

        blocker_signal = _contains_any(lower, _BLOCKER_HINTS)
        if blocker_signal:
            score -= 0.1
            issues.append("Signals a blocker or missing prerequisite")

        contract = (response_trace or {}).get("contract")
        if contract in {"trace_isolate_verify", "scope_build_ship", "gather_plan_answer"}:
            score += 0.06
            wins.append("Used a richer operating contract for the turn")

        action = (tool_result or {}).get("action") or {}
        tool_type = (tool_result or {}).get("type")
        recommended_next = None
        if tool_type == "action_request" and action.get("label"):
            score += 0.08
            wins.append("Proposed a direct safe action for the mission")
            recommended_next = f"Approve {action['label']} if you want Jarvis to push the mission forward directly."
        elif next_step:
            recommended_next = next_step
        elif actionable:
            recommended_next = "Use the latest answer as the next concrete move."

        suggested_mission_status = None
        if blocker_signal and not blocker:
            suggested_mission_status = "blocked"
        elif (
            _contains_any(lower, _COMPLETION_HINTS)
            and not issues
            and mission_overlap >= 0.24
        ):
            score += 0.06
            suggested_mission_status = "done"

        summary = (
            "Mission Critic sees this reply as moving the mission forward."
            if score >= SCORE_THRESHOLD and not issues
            else "Mission Critic sees this reply as only partially moving the mission forward."
        )
        if suggested_mission_status == "blocked":
            summary = "Mission Critic sees a blocker or prerequisite that should be handled before the mission can move."
        elif suggested_mission_status == "done":
            summary = "Mission Critic sees this turn as strong evidence that the mission may be complete."

        confidence = 0.62 + min(0.22, mission_overlap * 0.22) + min(0.12, request_overlap * 0.2)
        if tool_type:
            confidence += 0.04
        if issues:
            confidence -= 0.06

        return self._build_review(
            source="reply",
            score=score,
            confidence=confidence,
            summary=summary,
            wins=wins,
            issues=issues,
            recommended_next=recommended_next,
            suggested_mission_status=suggested_mission_status,
        )

    @timed
    def review_browser_verification(
        self,
        *,
        verification: dict | None,
        mission_context: dict | None = None,
    ) -> dict | None:
        mission = ((mission_context or {}).get("active_mission") or {})
        if not mission or not isinstance(verification, dict):
            return None

        status = str(verification.get("status") or "warning").strip().lower()
        fit = (((verification.get("route_expectation") or {}).get("fit") or {}).get("status") or "").strip().lower()
        suggested_action = verification.get("suggested_action") or {}
        target_path = verification.get("target_path") or "route"

        wins: list[str] = []
        issues: list[str] = []
        score_map = {"healthy": 0.86, "warning": 0.58, "fail": 0.32}
        score = score_map.get(status, 0.55)

        if fit == "aligned":
            score += 0.08
            wins.append("The live route matched the expected UI signature")
        elif fit == "partial":
            issues.append("The live route only partially matched the expected UI signature")
        elif fit == "mismatch":
            score -= 0.12
            issues.append("The live route did not match the expected UI signature")

        if suggested_action.get("label"):
            wins.append(f"Named a concrete next action: {suggested_action['label']}")

        recommended_next = None
        suggested_mission_status = None
        if status in {"fail", "warning"}:
            recommended_next = (
                verification.get("next_steps") or [None]
            )[0] or f"Review {target_path} and the strongest matched file."
            if status == "fail":
                suggested_mission_status = "blocked"
        else:
            recommended_next = (
                verification.get("next_steps") or [None]
            )[0] or f"Use the grounded route check for {target_path} as the next verification anchor."
            if fit == "aligned" and any(
                token in " ".join(
                    [
                        str(mission.get("title") or ""),
                        str(mission.get("objective") or ""),
                        ",".join(mission.get("tags") or []),
                    ]
                ).lower()
                for token in ("fix", "verify", "route", "page")
            ):
                suggested_mission_status = "done"

        summary = (
            f"Mission Critic sees the browser check for {target_path} as healthy and mission-aligned."
            if status == "healthy"
            else f"Mission Critic sees the browser check for {target_path} as needing more work."
        )
        if suggested_mission_status == "blocked":
            summary = f"Mission Critic sees the browser check for {target_path} as blocked until the flagged route issue is resolved."
        elif suggested_mission_status == "done":
            summary = f"Mission Critic sees the browser check for {target_path} as strong evidence that the route mission may be complete."

        confidence = 0.7 if fit else 0.62
        if status == "fail":
            confidence += 0.08

        return self._build_review(
            source="browser_verification",
            score=score,
            confidence=confidence,
            summary=summary,
            wins=wins,
            issues=issues,
            recommended_next=recommended_next,
            suggested_mission_status=suggested_mission_status,
        )

    @timed
    def review_action_result(
        self,
        *,
        tool_result: dict | None,
        mission_context: dict | None = None,
    ) -> dict | None:
        mission = ((mission_context or {}).get("active_mission") or {})
        if not mission or not isinstance(tool_result, dict):
            return None

        action = tool_result.get("action") or {}
        action_label = action.get("label") or action.get("id") or "local action"
        status = str(tool_result.get("status") or "completed").strip().lower()
        summary_text = str(tool_result.get("summary") or "")
        wins: list[str] = []
        issues: list[str] = []

        score = 0.84 if status in {"completed", "success"} else 0.34
        if status in {"completed", "success"}:
            wins.append(f"{action_label} finished cleanly")
        else:
            issues.append(f"{action_label} did not finish cleanly")

        relevance, overlap = _token_overlap(
            " ".join(
                [
                    action_label,
                    action.get("description") or "",
                    action.get("command_preview") or "",
                    summary_text,
                ]
            ),
            mission.get("objective"),
            mission.get("next_step"),
            ",".join(mission.get("tags") or []),
        )
        if relevance >= 0.16:
            score += 0.08
            wins.append(
                "The action matched the active mission"
                + (f" through {', '.join(overlap[:3])}" if overlap else ".")
            )
        else:
            issues.append("The action result was only loosely tied to the active mission")

        suggested_mission_status = None
        recommended_next = mission.get("next_step") or None
        if status not in {"completed", "success"}:
            suggested_mission_status = "blocked"
            recommended_next = summary_text or f"Review why {action_label} failed and clear the blocker."
        elif not recommended_next:
            recommended_next = f"Use {action_label} as fresh evidence and decide the next smallest mission step."

        summary = (
            f"Mission Critic sees {action_label} as moving the mission forward."
            if status in {"completed", "success"}
            else f"Mission Critic sees {action_label} as a blocker for the active mission."
        )

        confidence = 0.74 + min(0.14, relevance * 0.22)
        if status not in {"completed", "success"}:
            confidence += 0.06

        return self._build_review(
            source="action_result",
            score=score,
            confidence=confidence,
            summary=summary,
            wins=wins,
            issues=issues,
            recommended_next=recommended_next,
            suggested_mission_status=suggested_mission_status,
        )


mission_critic = MissionCriticEngine()


def judge_pass(answer: str, context: str, intent: str) -> dict:
    """Compatibility wrapper for older answer-scoring call sites."""
    review = mission_critic.review_reply(
        answer=answer,
        user_message=intent,
        mission_context={"active_mission": {"objective": context}},
        response_trace=None,
        tool_result=None,
    ) or {
        "score": 0.5,
        "confidence": 0.5,
        "issues": ["No mission context was available for the critic."],
        "summary": "Mission Critic could not evaluate this answer.",
    }
    return {
        "score": review["score"],
        "boost_needed": review["score"] < SCORE_THRESHOLD,
        "issues": review.get("issues", []),
        "confidence": review.get("confidence"),
        "summary": review.get("summary"),
    }
