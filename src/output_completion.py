"""Output completion integrity guards for visible Jarvis replies."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import re


TRUNCATION_NOTICE = "Response truncated due to output budget."
REPETITION_NOTICE = "Response truncated due to repetition loop."
_STRONG_INCOMPLETE_STOP_REASONS = {
    "budget_exhausted",
    "length",
    "max_new_tokens",
    "max_output_tokens",
    "max_tokens",
    "token_limit",
}
_NATURAL_COMPLETE_REASONS = {
    "cache_hit",
    "direct_tool",
    "eos_token",
    "mock_complete",
    "stop",
}
_DANGLING_TERMINAL_CHARS = tuple(":;,/-([{")
_DANGLING_TERMINAL_WORDS = {
    "about",
    "across",
    "after",
    "against",
    "along",
    "amid",
    "among",
    "and",
    "as",
    "at",
    "because",
    "before",
    "between",
    "but",
    "by",
    "during",
    "for",
    "from",
    "if",
    "in",
    "inside",
    "into",
    "near",
    "of",
    "on",
    "onto",
    "or",
    "over",
    "since",
    "so",
    "than",
    "that",
    "through",
    "to",
    "under",
    "until",
    "via",
    "when",
    "where",
    "while",
    "with",
    "without",
}
_COMPLETE_TERMINAL_RE = re.compile(r'[.!?](?:["\')\]]|\s|$)')
_TRAILING_WORD_RE = re.compile(r"\s*\S+\s*$")
_LAST_WORD_RE = re.compile(r"([A-Za-z']+)[^A-Za-z']*$")
_LIST_MARKER_RE = re.compile(r"(?m)^\s*(?:[-*+]|\d+\.)\s*$")
_TOKEN_RE = re.compile(r"[A-Za-z0-9']+")


@dataclass(slots=True)
class RepetitionRisk:
    """Structured repetition-loop detection state."""

    reasons: list[str] = field(default_factory=list)
    cut_char: int | None = None
    repeated_phrase: str | None = None
    loop_start_token: int | None = None


@dataclass(slots=True)
class OutputCompletionReport:
    """Structured report describing output-completion enforcement."""

    stop_reason: str | None = None
    finish_reason: str | None = None
    output_token_budget: int = 0
    output_tokens_used: int = 0
    output_tokens_estimated: bool = False
    budget_pressure: bool = False
    completion_guard_applied: bool = False
    truncation_detected: bool = False
    repetition_detected: bool = False
    structural_completion_status: str = "complete"
    visible_truncation_notice: bool = False
    reasons: list[str] = field(default_factory=list)
    original_chars: int = 0
    final_chars: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "stop_reason": self.stop_reason,
            "finish_reason": self.finish_reason,
            "output_token_budget": int(self.output_token_budget or 0),
            "output_tokens_used": int(self.output_tokens_used or 0),
            "output_tokens_estimated": bool(self.output_tokens_estimated),
            "budget_pressure": bool(self.budget_pressure),
            "completion_guard_applied": bool(self.completion_guard_applied),
            "truncation_detected": bool(self.truncation_detected),
            "repetition_detected": bool(self.repetition_detected),
            "structural_completion_status": self.structural_completion_status,
            "visible_truncation_notice": bool(self.visible_truncation_notice),
            "reasons": list(self.reasons),
            "original_chars": int(self.original_chars or 0),
            "final_chars": int(self.final_chars or 0),
        }


def _normalize_reason(value: object) -> str | None:
    cleaned = str(value or "").strip().lower()
    return cleaned or None


def _estimate_output_tokens(text: str) -> int:
    normalized = str(text or "").strip()
    if not normalized:
        return 0
    return max(1, len(normalized) // 4)


def _last_word(text: str) -> str:
    match = _LAST_WORD_RE.search(text or "")
    return str(match.group(1) if match else "").strip().lower()


def _token_spans(text: str) -> list[tuple[str, int, int]]:
    return [
        (match.group(0).lower(), match.start(), match.end())
        for match in _TOKEN_RE.finditer(text or "")
    ]


def _ends_with_complete_boundary(text: str) -> bool:
    normalized = str(text or "").rstrip()
    if not normalized:
        return False
    return bool(_COMPLETE_TERMINAL_RE.search(normalized[-16:]))


def _analyze_completion_risk(text: str, *, budget_pressure: bool) -> list[str]:
    normalized = str(text or "").rstrip()
    if not normalized:
        return ["empty_output"]

    reasons: list[str] = []
    ends_with_complete_boundary = _ends_with_complete_boundary(normalized)
    if normalized.count("```") % 2 == 1:
        reasons.append("unclosed_code_fence")

    lines = normalized.splitlines()
    if lines and _LIST_MARKER_RE.search(lines[-1]):
        reasons.append("dangling_list_marker")

    if normalized.endswith(_DANGLING_TERMINAL_CHARS):
        reasons.append("dangling_terminal_char")

    trailing_word = _last_word(normalized)
    if not ends_with_complete_boundary and trailing_word in _DANGLING_TERMINAL_WORDS:
        reasons.append("dangling_terminal_word")

    if budget_pressure and not ends_with_complete_boundary:
        if len(trailing_word) >= 2 or len(normalized.split()) >= 6:
            reasons.append("unfinished_sentence")

    return reasons


def _detect_repetition_risk(text: str) -> RepetitionRisk:
    normalized = str(text or "").rstrip()
    spans = _token_spans(normalized)
    if len(spans) < 12:
        return RepetitionRisk()

    tokens = [token for token, _start, _end in spans]
    tail_start = max(0, len(tokens) - 36)
    tail_tokens = tokens[tail_start:]
    reasons: list[str] = []
    cut_char: int | None = None
    repeated_phrase: str | None = None
    loop_start_token: int | None = None

    search_start = max(0, tail_start - 10)
    for ngram_size in range(5, 2, -1):
        for start in range(search_start, len(tokens) - (2 * ngram_size) + 1):
            phrase = tokens[start : start + ngram_size]
            if tokens[start + ngram_size : start + (2 * ngram_size)] != phrase:
                continue
            repeats = 2
            while start + ((repeats + 1) * ngram_size) <= len(tokens):
                next_slice = tokens[
                    start + (repeats * ngram_size) : start + ((repeats + 1) * ngram_size)
                ]
                if next_slice != phrase:
                    break
                repeats += 1
            if repeats >= 2 and (start + (repeats * ngram_size)) >= max(tail_start, len(tokens) - 4):
                reasons.append("repeated_token_sequence")
                repeated_phrase = " ".join(phrase)
                loop_start_token = start
                second_pass_token = start + ngram_size
                cut_char = spans[second_pass_token][1] if second_pass_token < len(spans) else None
                break
        if cut_char is not None:
            break

    for ngram_size in range(5, 2, -1):
        if len(tail_tokens) < ngram_size * 3:
            continue
        counts = Counter(
            tuple(tail_tokens[index : index + ngram_size])
            for index in range(len(tail_tokens) - ngram_size + 1)
        )
        if not counts:
            continue
        phrase, count = counts.most_common(1)[0]
        coverage = (count * ngram_size) / max(1, len(tail_tokens))
        if count >= 3 and coverage >= 0.45:
            if "phrase_frequency_spike" not in reasons:
                reasons.append("phrase_frequency_spike")
            if repeated_phrase is None:
                repeated_phrase = " ".join(phrase)
            if cut_char is None:
                occurrences = [
                    tail_start + index
                    for index in range(len(tail_tokens) - ngram_size + 1)
                    if tuple(tail_tokens[index : index + ngram_size]) == phrase
                ]
                if len(occurrences) >= 2:
                    loop_start_token = occurrences[0]
                    cut_char = spans[occurrences[1]][1]
            break

    unique_ratio = len(set(tail_tokens)) / max(1, len(tail_tokens))
    highest_token_density = max(Counter(tail_tokens).values()) / max(1, len(tail_tokens))
    if len(tail_tokens) >= 18 and unique_ratio <= 0.42 and highest_token_density >= 0.22:
        if "low_entropy_tail" not in reasons:
            reasons.append("low_entropy_tail")
        if cut_char is None and tail_start < len(spans):
            loop_start_token = tail_start
            cut_char = spans[tail_start][1]

    return RepetitionRisk(
        reasons=reasons,
        cut_char=cut_char,
        repeated_phrase=repeated_phrase,
        loop_start_token=loop_start_token,
    )


def _strip_unclosed_code_fence(text: str) -> tuple[str, bool]:
    normalized = str(text or "").rstrip()
    if normalized.count("```") % 2 == 0:
        return normalized, False
    cut = normalized.rfind("```")
    if cut <= 0:
        return normalized, False
    return normalized[:cut].rstrip(), True


def _trim_to_last_complete_boundary(text: str) -> tuple[str | None, bool]:
    normalized, changed = _strip_unclosed_code_fence(text)
    matches = list(re.finditer(r'[.!?](?=(?:["\')\]]|\s|$))', normalized))
    if matches:
        candidate = normalized[: matches[-1].end()].rstrip()
        if candidate:
            return candidate, candidate != str(text or "").rstrip() or changed

    paragraphs = re.split(r"\n{2,}", normalized)
    if len(paragraphs) > 1:
        candidate = "\n\n".join(paragraphs[:-1]).rstrip()
        if candidate:
            return candidate, True

    lines = normalized.splitlines()
    if len(lines) > 1:
        candidate = "\n".join(lines[:-1]).rstrip()
        if candidate:
            return candidate, True

    return None, changed


def _trim_incomplete_tail(text: str) -> tuple[str | None, bool]:
    working, changed = _strip_unclosed_code_fence(text)
    original = working

    while working and working[-1] in _DANGLING_TERMINAL_CHARS:
        working = working[:-1].rstrip()
        changed = True

    while True:
        trailing_word = _last_word(working)
        if trailing_word not in _DANGLING_TERMINAL_WORDS:
            break
        updated = _TRAILING_WORD_RE.sub("", working).rstrip()
        if updated == working:
            break
        working = updated
        changed = True

    if not working:
        return None, changed

    if not _COMPLETE_TERMINAL_RE.search(working[-4:]):
        working = f"{working}."
        changed = True

    if len(working) < 8 and original != working:
        return None, changed
    return working, changed


def _close_fragment(text: str) -> str | None:
    normalized = str(text or "").rstrip()
    if not normalized:
        return None
    candidate, _changed = _trim_to_last_complete_boundary(normalized)
    if candidate:
        return candidate
    candidate, _changed = _trim_incomplete_tail(normalized)
    if candidate:
        return candidate
    return None


def _trim_repetition_loop(text: str, risk: RepetitionRisk) -> tuple[str | None, bool]:
    if not risk.cut_char:
        return None, False
    prefix = str(text or "")[: risk.cut_char].rstrip()
    candidate = _close_fragment(prefix)
    if candidate:
        return candidate, candidate != str(text or "").rstrip()
    return None, False


def guard_output_completion(
    text: str,
    *,
    stop_reason: object = None,
    finish_reason: object = None,
    output_token_budget: int | None = None,
    output_tokens_used: int | None = None,
) -> tuple[str, OutputCompletionReport]:
    """Guarantee a structurally complete visible reply or fail visibly."""

    normalized_text = str(text or "").strip()
    normalized_stop_reason = _normalize_reason(stop_reason)
    normalized_finish_reason = _normalize_reason(finish_reason)
    used_tokens = int(output_tokens_used or 0)
    estimated_tokens = used_tokens <= 0
    if estimated_tokens:
        used_tokens = _estimate_output_tokens(normalized_text)

    budget = max(0, int(output_token_budget or 0))
    explicit_budget_stop = (
        normalized_stop_reason in _STRONG_INCOMPLETE_STOP_REASONS
        or normalized_finish_reason in _STRONG_INCOMPLETE_STOP_REASONS
    )
    natural_completion = (
        normalized_stop_reason in _NATURAL_COMPLETE_REASONS
        or normalized_finish_reason in _NATURAL_COMPLETE_REASONS
    )
    budget_pressure = explicit_budget_stop or (
        budget > 0
        and used_tokens >= max(1, budget - 8)
        and not estimated_tokens
        and not natural_completion
    )
    ends_with_complete_boundary = _ends_with_complete_boundary(normalized_text)
    repetition_risk = _detect_repetition_risk(normalized_text)
    reasons = _analyze_completion_risk(normalized_text, budget_pressure=budget_pressure)
    for repetition_reason in repetition_risk.reasons:
        if repetition_reason not in reasons:
            reasons.append(repetition_reason)
    report = OutputCompletionReport(
        stop_reason=normalized_stop_reason,
        finish_reason=normalized_finish_reason,
        output_token_budget=budget,
        output_tokens_used=used_tokens,
        output_tokens_estimated=estimated_tokens,
        budget_pressure=budget_pressure,
        truncation_detected=bool(reasons or repetition_risk.reasons),
        repetition_detected=bool(repetition_risk.reasons),
        reasons=reasons,
        original_chars=len(normalized_text),
        final_chars=len(normalized_text),
    )

    if repetition_risk.reasons:
        candidate, changed = _trim_repetition_loop(normalized_text, repetition_risk)
        if candidate:
            final_text = f"{candidate}\n\n{REPETITION_NOTICE}"
            report.completion_guard_applied = True
            report.visible_truncation_notice = True
            report.structural_completion_status = "repetition_loop_trimmed"
            report.final_chars = len(final_text)
            return final_text, report

    should_guard = bool(reasons) and (
        budget_pressure
        or "unclosed_code_fence" in reasons
        or "dangling_terminal_char" in reasons
        or "dangling_terminal_word" in reasons
    )
    if not should_guard:
        if reasons:
            report.structural_completion_status = "low_risk_unmodified"
        elif budget_pressure:
            report.structural_completion_status = "complete_under_budget_pressure"
        return normalized_text, report

    candidate, boundary_changed = _trim_to_last_complete_boundary(normalized_text)
    if candidate:
        if candidate == normalized_text and ends_with_complete_boundary:
            report.structural_completion_status = "complete_under_budget_pressure"
            report.truncation_detected = False
            return normalized_text, report
        final_text = f"{candidate}\n\n{TRUNCATION_NOTICE}"
        report.completion_guard_applied = True
        report.visible_truncation_notice = True
        report.structural_completion_status = "trimmed_to_boundary"
        report.final_chars = len(final_text)
        return final_text, report

    candidate, tail_changed = _trim_incomplete_tail(normalized_text)
    if candidate:
        if candidate == normalized_text and ends_with_complete_boundary:
            report.structural_completion_status = "complete_under_budget_pressure"
            report.truncation_detected = False
            return normalized_text, report
        final_text = f"{candidate}\n\n{TRUNCATION_NOTICE}"
        report.completion_guard_applied = bool(boundary_changed or tail_changed)
        report.visible_truncation_notice = True
        report.structural_completion_status = "tail_trimmed_with_notice"
        report.final_chars = len(final_text)
        return final_text, report

    final_text = TRUNCATION_NOTICE
    report.completion_guard_applied = True
    report.visible_truncation_notice = True
    report.structural_completion_status = "visible_truncation_notice"
    report.final_chars = len(final_text)
    return final_text, report
