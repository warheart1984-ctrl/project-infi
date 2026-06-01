"""AAIS-native corrigibility helpers for corrections, rewind, and soft pause.

This module maps the "corrigibility engine" idea onto the real AAIS runtime:

- session-local correction memory lives on ConversationSession.metadata
- soft pause routes through System Guard
- rewind removes the latest substantive assistant reply from the session
- pending corrections are folded silently into the next model-generated reply
"""

from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
import re

from src.system_guard import system_guard


_SEVERITY_SCORES = {
    "mild": 0.68,
    "strong": 0.86,
    "override": 0.98,
}

_SELF_CORRECT_PATTERNS = (
    re.compile(r"\bcorrect yourself\b"),
    re.compile(r"\bfix your (?:answer|reply|response)\b"),
    re.compile(r"\badjust your (?:answer|reply|response)\b"),
    re.compile(r"\bchange your (?:answer|reply|response)\b"),
    re.compile(r"\btry again\b"),
    re.compile(r"\bredo that\b"),
    re.compile(r"\b(?:you are|you're) wrong\b"),
    re.compile(r"\bthat(?:'s| is| was) wrong\b"),
    re.compile(r"\bwrong answer\b"),
    re.compile(r"\bno,\s*wrong\b"),
    re.compile(r"\bnot what i asked\b"),
    re.compile(r"\bthat(?:'s| is) incorrect\b"),
)

_REVERT_PATTERNS = (
    re.compile(r"^\s*undo that\b"),
    re.compile(r"^\s*revert that\b"),
    re.compile(r"^\s*undo (?:your |the )?last (?:answer|reply|response)\b"),
    re.compile(r"^\s*revert (?:your |the )?last (?:answer|reply|response)\b"),
    re.compile(r"^\s*roll ?back (?:your |the )?last (?:answer|reply|response)\b"),
    re.compile(r"^\s*go back\b"),
    re.compile(r"^\s*back up\b"),
)

_PAUSE_PATTERNS = (
    re.compile(r"^\s*pause(?:\b| for now\b| the system\b)"),
    re.compile(r"^\s*withdraw\b"),
    re.compile(r"^\s*draw back\b"),
    re.compile(r"^\s*quiet(?:\b| now\b| for now\b)"),
)

_OVERRIDE_HINTS = (
    "absolutely not",
    "hard no",
    "do not do that",
    "never do that",
)

_STRONG_HINTS = (
    "wrong",
    "incorrect",
    "not what i asked",
    "undo",
    "revert",
    "roll back",
)

_MILD_HINTS = (
    "adjust",
    "change",
    "correct",
    "fix",
    "tweak",
)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _clip_text(value: str | None, limit: int = 220) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def default_corrigibility_state() -> dict:
    """Return a fresh default state for one AAIS chat session."""
    from src.aais_ul_substrate import wrap_runtime_snapshot

    return wrap_runtime_snapshot(
        {
            "status": "steady",
            "pending": None,
            "last_action": None,
            "last_command": None,
            "last_severity": "none",
            "last_applied_at": None,
            "recent": [],
            "total_corrections": 0,
        }
    )


def ensure_corrigibility_state(session) -> dict:
    """Attach a valid corrigibility state to a session if needed."""
    state = session.metadata.get("corrigibility")
    if not isinstance(state, dict):
        state = default_corrigibility_state()
        session.metadata["corrigibility"] = state
    else:
        for key, value in default_corrigibility_state().items():
            state.setdefault(key, value)
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(state)


class CorrigibilityEngine:
    """Handle explicit operator corrections in an AAIS-native way."""

    @staticmethod
    def _wrap_response(payload: dict) -> dict:
        from src.aais_ul_substrate import attach_ul_substrate

        return attach_ul_substrate(dict(payload))

    def classify(self, command: str) -> dict | None:
        """Detect whether a command is an explicit self-correction, rewind, or pause."""
        cleaned = " ".join(str(command or "").split()).strip()
        lower = cleaned.lower()
        if not cleaned:
            return None

        if len(cleaned) <= 96 and any(pattern.search(lower) for pattern in _PAUSE_PATTERNS):
            return {
                "action": "soft_pause",
                "direction": "pause",
                "severity": "override",
                "rating": _SEVERITY_SCORES["override"],
                "matched": "soft_pause",
                "guidance_text": None,
            }

        if any(pattern.search(lower) for pattern in _REVERT_PATTERNS):
            severity = self._severity_for(lower, fallback="strong")
            guidance_text = self._extract_guidance_text(cleaned, action="revert")
            return {
                "action": "revert",
                "direction": "rollback",
                "severity": severity,
                "rating": _SEVERITY_SCORES[severity],
                "matched": "revert",
                "guidance_text": guidance_text,
            }

        if any(pattern.search(lower) for pattern in _SELF_CORRECT_PATTERNS):
            severity = self._severity_for(lower, fallback="strong")
            guidance_text = self._extract_guidance_text(cleaned, action="self_correct") or cleaned
            return {
                "action": "self_correct",
                "direction": "self_correct",
                "severity": severity,
                "rating": _SEVERITY_SCORES[severity],
                "matched": "self_correct",
                "guidance_text": guidance_text,
            }

        if lower.startswith(("correct ", "fix ", "adjust ", "change ")) and any(
            token in lower
            for token in ("your answer", "your reply", "your response", "that answer", "that reply", "that response")
        ):
            severity = self._severity_for(lower, fallback="mild")
            guidance_text = self._extract_guidance_text(cleaned, action="self_correct") or cleaned
            return {
                "action": "self_correct",
                "direction": "self_correct",
                "severity": severity,
                "rating": _SEVERITY_SCORES[severity],
                "matched": "self_correct",
                "guidance_text": guidance_text,
            }

        return None

    def handle_user_correction(self, session, command: str) -> dict | None:
        """Apply one explicit correction command to a live session."""
        correction = self.classify(command)
        if not correction:
            return None

        state = ensure_corrigibility_state(session)
        now = _utc_now_iso()
        cleaned = " ".join(str(command or "").split()).strip()
        state["last_command"] = cleaned
        state["last_action"] = correction["action"]
        state["last_severity"] = correction["severity"]
        state["total_corrections"] = int(state.get("total_corrections", 0)) + 1

        if correction["action"] == "soft_pause":
            snapshot = system_guard.pause(
                reason=f"Corrigibility pause: {_clip_text(cleaned, limit=180)}",
                actor="corrigibility",
            )
            self._append_recent(
                state,
                {
                    "timestamp": now,
                    "action": "soft_pause",
                    "severity": correction["severity"],
                    "command": cleaned,
                    "summary": "System Guard was paused from an explicit operator correction.",
                },
            )
            return self._wrap_response(
                {
                    "response": snapshot.get(
                        "summary",
                        "System Guard is paused. New Jarvis turns will stay quiet until resume.",
                    ),
                    "tool_result": {
                        "type": "corrigibility",
                        "action": {
                            "id": "corrigibility_soft_pause",
                            "label": "Soft Pause",
                        },
                        "status": "paused",
                        "direction": correction["direction"],
                        "severity": correction["severity"],
                        "rating": correction["rating"],
                        "command": cleaned,
                        "system_guard": snapshot,
                        "corrigibility": state,
                        "summary": "System Guard paused new Jarvis work after an explicit correction.",
                    },
                }
            )

        if correction["action"] == "revert":
            removed = session.rollback_last_assistant_turn(skip_tool_types={"corrigibility"})
            pending = self._queue_pending_correction(
                state,
                correction=correction,
                command=cleaned,
                timestamp=now,
            ) if correction.get("guidance_text") else None

            if removed:
                summary = "Jarvis rewound the last assistant answer."
                response = (
                    "I rewound the last assistant answer."
                    + (
                        " I also queued your correction for the next real reply."
                        if pending
                        else " Send the next prompt and I’ll continue from the corrected state."
                    )
                )
            else:
                summary = "There was no earlier assistant answer to rewind."
                response = (
                    "There was no earlier assistant answer to rewind."
                    + (
                        " I still queued your correction for the next real reply."
                        if pending
                        else ""
                    )
                )

            self._append_recent(
                state,
                {
                    "timestamp": now,
                    "action": "revert",
                    "severity": correction["severity"],
                    "command": cleaned,
                    "summary": summary,
                },
            )
            return self._wrap_response(
                {
                    "response": response,
                    "tool_result": {
                        "type": "corrigibility",
                        "action": {
                            "id": "corrigibility_revert",
                            "label": "Rewind Last Answer",
                        },
                        "status": "completed" if removed else "noop",
                        "direction": correction["direction"],
                        "severity": correction["severity"],
                        "rating": correction["rating"],
                        "command": cleaned,
                        "removed_turn": removed,
                        "pending": pending,
                        "corrigibility": state,
                        "summary": summary,
                    },
                }
            )

        pending = self._queue_pending_correction(
            state,
            correction=correction,
            command=cleaned,
            timestamp=now,
        )
        self._append_recent(
            state,
            {
                "timestamp": now,
                "action": "self_correct",
                "severity": correction["severity"],
                "command": cleaned,
                "summary": "Queued an operator correction for the next generated reply.",
            },
        )
        return self._wrap_response(
            {
                "response": self._render_self_correction_response(correction["severity"]),
                "tool_result": {
                    "type": "corrigibility",
                    "action": {
                        "id": "corrigibility_self_correct",
                        "label": "Self-Correct",
                    },
                    "status": "queued",
                    "direction": correction["direction"],
                    "severity": correction["severity"],
                    "rating": correction["rating"],
                    "command": cleaned,
                    "pending": pending,
                    "corrigibility": state,
                    "summary": "Queued an explicit operator correction for the next generated reply.",
                },
            }
        )

    def apply_to_next_generation(self, session) -> str | None:
        """Fold any pending correction into the next model-generated reply."""
        state = ensure_corrigibility_state(session)
        pending = state.get("pending")
        session.metadata["corrigibility_prompt_block"] = None
        if not pending:
            state["status"] = "steady"
            return None

        guidance = _clip_text(pending.get("guidance") or pending.get("command"), limit=260)
        if pending.get("action") == "revert":
            prompt = (
                "The operator explicitly withdrew the previous assistant answer. "
                "Do not rely on the withdrawn answer. "
                "Honor this corrected direction silently in the next reply: "
                f"{guidance}"
            )
        else:
            prompt = (
                "The operator explicitly corrected Jarvis. "
                "Honor this correction silently in the next reply without narrating hidden correction logic: "
                f"{guidance}"
            )

        session.metadata["corrigibility_prompt_block"] = prompt
        state["status"] = "pending"
        return prompt

    def mark_generation_applied(self, session) -> None:
        """Clear a pending correction after one model-generated reply used it."""
        state = ensure_corrigibility_state(session)
        pending = state.get("pending")
        if not pending:
            session.metadata["corrigibility_prompt_block"] = None
            return

        state["last_applied_at"] = _utc_now_iso()
        state["last_action"] = pending.get("action")
        state["last_command"] = pending.get("command")
        state["last_severity"] = pending.get("severity", "none")
        state["pending"] = None
        state["status"] = "steady"
        session.metadata["corrigibility_prompt_block"] = None

    def _extract_guidance_text(self, cleaned: str, action: str) -> str | None:
        if ":" in cleaned:
            _, remainder = cleaned.split(":", 1)
            remainder = remainder.strip(" -.,")
            if len(remainder) >= 8:
                return _clip_text(remainder, limit=220)

        if "," in cleaned:
            _, remainder = cleaned.split(",", 1)
            remainder = remainder.strip(" -.")
            if len(remainder) >= 8:
                return _clip_text(remainder, limit=220)

        lower = cleaned.lower()
        if action == "self_correct":
            for prefix in (
                "correct yourself",
                "fix your answer",
                "adjust your answer",
                "change your answer",
                "redo that",
                "try again",
                "you are wrong",
                "you're wrong",
                "that was wrong",
                "that is wrong",
                "wrong answer",
                "not what i asked",
            ):
                if lower.startswith(prefix):
                    remainder = cleaned[len(prefix):].strip(" -.,")
                    if len(remainder) >= 8:
                        return _clip_text(remainder, limit=220)
        if action == "revert":
            for prefix in (
                "undo that",
                "revert that",
                "go back",
                "back up",
                "undo your last answer",
                "revert your last answer",
                "roll back your last answer",
            ):
                if lower.startswith(prefix):
                    remainder = cleaned[len(prefix):].strip(" -.,")
                    if len(remainder) >= 8:
                        return _clip_text(remainder, limit=220)
        return None

    def _severity_for(self, lower: str, fallback: str = "mild") -> str:
        if any(token in lower for token in _OVERRIDE_HINTS):
            return "override"
        if any(token in lower for token in _STRONG_HINTS):
            return "strong"
        if any(token in lower for token in _MILD_HINTS):
            return "mild"
        return fallback

    def _queue_pending_correction(
        self,
        state: dict,
        *,
        correction: dict,
        command: str,
        timestamp: str,
    ) -> dict:
        pending = {
            "action": correction["action"],
            "severity": correction["severity"],
            "direction": correction["direction"],
            "command": _clip_text(command, limit=220),
            "guidance": _clip_text(correction.get("guidance_text") or command, limit=220),
            "queued_at": timestamp,
        }
        state["pending"] = pending
        state["status"] = "pending"
        return pending

    def _append_recent(self, state: dict, item: dict) -> None:
        recent = list(state.get("recent") or [])
        recent.insert(0, dict(item))
        state["recent"] = recent[:8]

    def _render_self_correction_response(self, severity: str) -> str:
        if severity == "override":
            return "Understood. I treated that as an override and will answer differently on the next real reply."
        if severity == "strong":
            return "Got it. I queued that as a strong correction for the next real reply."
        return "Correction noted. I’ll fold it into the next real reply."


corrigibility_engine = CorrigibilityEngine()
