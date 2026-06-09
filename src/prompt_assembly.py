"""Deterministic prompt assembly helpers for Jarvis runtime paths."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


SECTION_MARKERS = (
    "response trace",
    "think contract",
    "god brain",
    "plan pass",
    "memory cues",
    "council deliberation",
    "model route",
    "specialists",
    "jarvis internal guidance for this turn",
)
PLAN_MARKERS = (
    "mode:",
    "focus:",
    "specialists:",
    "god brain:",
    "model route:",
    "evidence:",
    "answer shape:",
)
INLINE_MARKERS = (
    "workspace:",
    "memory:",
    "research:",
    "answer shape:",
)
ALLOWED_SCAFFOLD_IDENTITIES = {
    "plan_guidance",
    "direct_challenge_guidance",
    "local_fallback_guardrail",
}
IDENTITY_ALIASES = {
    "instruction": "system_seed",
    "runtime": "runtime_directive",
    "archive": "loaded_session_archive",
    "workspace": "workspace_context",
    "urg_library": "urg_library_context",
    "research": "live_research",
    "orchestration": "mission_board",
    "corrigibility": "corrigibility_guidance",
    "continuity": "continuity_profile",
    "turn_system": "system_seed",
    "seed": "system_seed",
}
SINGLETON_BLOCKS = {
    "system_seed",
    "runtime_directive",
    "loaded_session_archive",
    "workspace_context",
    "urg_library_context",
    "live_research",
    "mission_board",
    "corrigibility_guidance",
    "continuity_profile",
    "plan_guidance",
    "direct_challenge_guidance",
    "local_fallback_guardrail",
}
DEFAULT_PRIORITIES = {
    "system_seed": 0,
    "runtime_directive": 10,
    "local_fallback_guardrail": 15,
    "direct_challenge_guidance": 20,
    "plan_guidance": 25,
    "corrigibility_guidance": 30,
    "continuity_profile": 35,
    "mission_board": 40,
    "loaded_session_archive": 45,
    "live_research": 50,
    "urg_library_context": 52,
    "workspace_context": 55,
}
REQUIRED_IDENTITIES = {
    "system_seed",
    "runtime_directive",
    "local_fallback_guardrail",
    "direct_challenge_guidance",
    "plan_guidance",
}
SECTION_HEADER_RE = re.compile(r"^(?:response trace|think contract|god brain|plan pass|memory cues|council deliberation|model route|specialists)\b", re.IGNORECASE)
PLAN_HEADER_RE = re.compile(r"^(?:mode|focus|specialists|god brain|model route|evidence|answer shape)\s*:", re.IGNORECASE)
GENERIC_SYSTEM_IDENTITIES = {"system_context"}


class PromptAssemblyIdentityError(ValueError):
    """Raised when a system prompt block omits a semantic identity."""


def normalize_prompt_text(text: str | None) -> str:
    """Return a compact normalized representation for semantic comparison."""
    return " ".join(str(text or "").split()).strip().lower()


def estimate_text_tokens(text: str | None) -> int:
    """Estimate tokens conservatively from character count."""
    return max(1, (len(str(text or "").strip()) + 3) // 4)


def char_budget_from_tokens(token_budget: int | None) -> int | None:
    """Convert a token budget into the rough character budget used in session history."""
    if token_budget is None:
        return None
    return max(0, int(token_budget) * 4)


def scrub_assistant_guidance_echo(raw_response: str | None) -> str:
    """Remove scaffold-heavy assistant echoes before they re-enter prompt assembly."""
    text = str(raw_response or "").strip()
    if not text:
        return ""

    clean_lines: list[str] = []
    in_scaffolding = False
    for line in text.splitlines():
        stripped = line.strip()
        normalized = stripped.lower()
        if _looks_like_scaffold_heading(normalized) or _looks_like_inline_scaffold(normalized):
            in_scaffolding = True
            continue
        if in_scaffolding:
            if not stripped:
                in_scaffolding = False
            continue
        clean_lines.append(line)

    cleaned = "\n".join(clean_lines).strip()
    if _looks_like_malformed_fragment(cleaned, "assistant_context"):
        return ""
    return cleaned


@dataclass(slots=True)
class PromptBlock:
    """One semantic block that may enter prompt assembly."""

    identity: str
    content: str
    role: str = "system"
    channel: str = "instruction"
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    priority: int = 50
    required: bool = False
    singleton: bool = True


@dataclass(slots=True)
class PromptAssemblyReport:
    """Traceable report for one prompt assembly pass."""

    raw_chars: int = 0
    raw_tokens_estimate: int = 0
    chars_after_cleanup: int = 0
    tokens_after_cleanup_estimate: int = 0
    duplicates_removed: int = 0
    malformed_fragments_removed: int = 0
    budget_dropped: int = 0
    assistant_echoes_scrubbed: int = 0
    reserved_response_budget: int = 0
    prompt_token_budget: int = 0
    chars_by_identity: dict[str, int] = field(default_factory=dict)
    identity_counts: dict[str, int] = field(default_factory=dict)
    included_block_identities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_chars": self.raw_chars,
            "raw_tokens_estimate": self.raw_tokens_estimate,
            "chars_after_cleanup": self.chars_after_cleanup,
            "tokens_after_cleanup_estimate": self.tokens_after_cleanup_estimate,
            "duplicates_removed": self.duplicates_removed,
            "malformed_fragments_removed": self.malformed_fragments_removed,
            "budget_dropped": self.budget_dropped,
            "assistant_echoes_scrubbed": self.assistant_echoes_scrubbed,
            "reserved_response_budget": self.reserved_response_budget,
            "prompt_token_budget": self.prompt_token_budget,
            "chars_by_identity": dict(self.chars_by_identity),
            "identity_counts": dict(self.identity_counts),
            "included_block_identities": list(self.included_block_identities),
        }


def coerce_prompt_block(
    block: PromptBlock | dict[str, Any] | None,
    *,
    default_channel: str = "instruction",
    default_source: str = "",
) -> PromptBlock | None:
    """Convert loose prompt block payloads into typed prompt blocks."""
    if block is None:
        return None
    if isinstance(block, PromptBlock):
        _require_explicit_system_identity(
            block.identity,
            role=block.role,
            source=block.source,
            channel=block.channel,
        )
        return PromptBlock(
            identity=_canonical_identity(block.identity, block.content, channel=block.channel, source=block.source),
            content=str(block.content or "").strip(),
            role=str(block.role or "system"),
            channel=str(block.channel or default_channel),
            source=str(block.source or default_source),
            metadata=dict(block.metadata or {}),
            priority=int(block.priority),
            required=bool(block.required),
            singleton=bool(block.singleton),
        )
    if not isinstance(block, dict):
        return None

    content = str(block.get("content") or "").strip()
    role = str(block.get("role") or "system")
    channel = str(block.get("channel") or default_channel)
    source = str(block.get("source") or block.get("identity") or default_source)
    _require_explicit_system_identity(
        block.get("identity"),
        role=role,
        source=source,
        channel=channel,
    )
    identity = _canonical_identity(
        str(block.get("identity") or source or channel or "system_context"),
        content,
        channel=channel,
        source=source,
    )
    return PromptBlock(
        identity=identity,
        content=content,
        role=role,
        channel=channel,
        source=source,
        metadata=dict(block.get("metadata") or {}),
        priority=int(block.get("priority") if block.get("priority") is not None else DEFAULT_PRIORITIES.get(identity, 50)),
        required=bool(block.get("required") if block.get("required") is not None else identity in REQUIRED_IDENTITIES),
        singleton=bool(block.get("singleton") if block.get("singleton") is not None else identity in SINGLETON_BLOCKS),
    )


def assemble_prompt_blocks(
    blocks: list[PromptBlock | dict[str, Any] | None] | None,
    *,
    prompt_token_budget: int | None = None,
    reserved_response_budget: int = 0,
    assistant_echoes_scrubbed: int = 0,
) -> tuple[list[PromptBlock], PromptAssemblyReport]:
    """Canonicalize, dedupe, validate, and budget prompt blocks."""
    report = PromptAssemblyReport(
        reserved_response_budget=max(0, int(reserved_response_budget or 0)),
        prompt_token_budget=max(0, int(prompt_token_budget or 0)),
        assistant_echoes_scrubbed=max(0, int(assistant_echoes_scrubbed or 0)),
    )

    ordered_blocks: list[PromptBlock] = []
    deduped_by_identity: dict[str, PromptBlock] = {}
    order_index: dict[str, int] = {}

    for raw_block in list(blocks or []):
        block = coerce_prompt_block(raw_block)
        if block is None or block.role != "system":
            continue
        report.raw_chars += len(block.content)
        report.raw_tokens_estimate += estimate_text_tokens(block.content)
        if not block.content:
            report.malformed_fragments_removed += 1
            continue
        if _looks_like_malformed_fragment(block.content, block.identity):
            report.malformed_fragments_removed += 1
            continue

        if block.identity in deduped_by_identity and block.singleton:
            report.duplicates_removed += 1
            candidate = _select_better_block(deduped_by_identity[block.identity], block)
            deduped_by_identity[block.identity] = candidate
            continue

        deduped_by_identity[block.identity] = block
        order_index[block.identity] = len(order_index)

    ordered_blocks = sorted(
        deduped_by_identity.values(),
        key=lambda item: (item.priority, order_index.get(item.identity, 0)),
    )
    char_budget = char_budget_from_tokens(prompt_token_budget)
    if char_budget is None or char_budget <= 0:
        final_blocks = ordered_blocks
    else:
        final_blocks = []
        used_chars = 0
        for block in ordered_blocks:
            block_chars = len(block.content)
            if used_chars + block_chars <= char_budget or block.required:
                final_blocks.append(block)
                used_chars += block_chars
                continue
            report.budget_dropped += 1

    report.chars_after_cleanup = sum(len(block.content) for block in final_blocks)
    report.tokens_after_cleanup_estimate = sum(estimate_text_tokens(block.content) for block in final_blocks)
    for block in final_blocks:
        report.identity_counts[block.identity] = report.identity_counts.get(block.identity, 0) + 1
        report.chars_by_identity[block.identity] = report.chars_by_identity.get(block.identity, 0) + len(block.content)
        report.included_block_identities.append(block.identity)

    return final_blocks, report


def combine_system_prompt(blocks: list[PromptBlock]) -> str:
    """Render the final combined system prompt content."""
    return "\n\n".join(block.content.strip() for block in blocks if block.content.strip())


def merge_prompt_assembly_trace(
    response_trace: dict[str, Any] | None,
    report: PromptAssemblyReport,
) -> dict[str, Any]:
    """Attach prompt assembly trace data onto the active response trace."""
    if not isinstance(response_trace, dict):
        return {}
    response_trace["prompt_assembly"] = report.to_dict()
    return response_trace["prompt_assembly"]


def _canonical_identity(identity: str, content: str, *, channel: str = "", source: str = "") -> str:
    cleaned = normalize_prompt_text(identity)
    if cleaned in IDENTITY_ALIASES:
        return IDENTITY_ALIASES[cleaned]

    normalized = normalize_prompt_text(content)
    if "jarvis internal guidance for this turn" in normalized:
        return "plan_guidance"
    if "loaded session archive (external context, not memory)" in normalized:
        return "loaded_session_archive"
    if "runtime state:" in normalized and (
        "jarvis runtime state" in normalized
        or "tiny nova runtime state" in normalized
        or "small nova runtime state" in normalized
    ):
        return "runtime_directive"
    if "answer as jarvis in one concise, operator-safe voice" in normalized:
        return "local_fallback_guardrail"
    if channel == "continuity" or source == "continuity_prompt_block":
        return "continuity_profile"
    if channel == "corrigibility" or source == "corrigibility_prompt_block":
        return "corrigibility_guidance"
    if channel == "workspace" or source == "workspace_context":
        return "workspace_context"
    if channel == "research" or source == "live_research":
        return "live_research"
    if channel == "urg_library" or source == "urg_library_context":
        return "urg_library_context"
    if channel == "orchestration" or source == "mission_board":
        return "mission_board"
    if channel == "archive" or source == "loaded_session_archive":
        return "loaded_session_archive"
    if source == "direct_challenge_guidance":
        return "direct_challenge_guidance"
    if source == "plan_guidance":
        return "plan_guidance"
    if cleaned:
        return cleaned.replace(" ", "_")
    return "system_context"


def _require_explicit_system_identity(
    identity: Any,
    *,
    role: str,
    source: str = "",
    channel: str = "",
) -> None:
    """Reject unlabeled or generic system blocks before they enter assembly."""
    if str(role or "system") != "system":
        return
    cleaned = normalize_prompt_text(str(identity or ""))
    if cleaned and cleaned not in GENERIC_SYSTEM_IDENTITIES:
        return

    source_class = normalize_prompt_text(source or channel or "unspecified")
    if not cleaned:
        raise PromptAssemblyIdentityError(
            "Prompt assembly rejected a system guidance block because it did not declare "
            f"a semantic identity (source_class={source_class}). "
            "Every system guidance block must carry an explicit semantic identity such as "
            "runtime_directive or plan_guidance before assembly. "
            "This is a prompt-assembly seam violation, so the block was rejected."
        )

    if cleaned in GENERIC_SYSTEM_IDENTITIES:
        raise PromptAssemblyIdentityError(
            "Prompt assembly rejected a system guidance block because it used a generic "
            f"semantic identity (source_class={source_class}). "
            "Every system guidance block must carry an explicit non-generic semantic identity "
            "such as runtime_directive or plan_guidance before assembly. "
            "This is a prompt-assembly seam violation, so the block was rejected."
        )


def _select_better_block(current: PromptBlock, candidate: PromptBlock) -> PromptBlock:
    current_score = _block_score(current)
    candidate_score = _block_score(candidate)
    if candidate_score > current_score:
        return candidate
    return current


def _block_score(block: PromptBlock) -> tuple[int, int]:
    malformed = _looks_like_malformed_fragment(block.content, block.identity)
    return (
        0 if malformed else 1,
        len(block.content.strip()),
    )


def _looks_like_scaffold_heading(normalized_line: str) -> bool:
    if not normalized_line:
        return False
    return bool(SECTION_HEADER_RE.match(normalized_line) or PLAN_HEADER_RE.match(normalized_line))


def _looks_like_inline_scaffold(normalized_line: str) -> bool:
    return any(token in normalized_line for token in INLINE_MARKERS)


def _looks_like_malformed_fragment(content: str | None, identity: str) -> bool:
    text = str(content or "").strip()
    if not text:
        return True

    normalized = normalize_prompt_text(text)
    if not normalized:
        return True

    if text.endswith((":","-","*","•")):
        return True
    if normalized.endswith(("mode:", "focus:", "specialists:", "god brain:", "model route:", "evidence:", "answer shape:", "jarvis internal guidance for this turn:")):
        return True

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return True

    heading_lines = [line for line in lines if _looks_like_scaffold_heading(line.lower())]
    if heading_lines and identity not in ALLOWED_SCAFFOLD_IDENTITIES:
        return True
    if len(heading_lines) >= len(lines):
        return True

    if identity == "plan_guidance":
        if "jarvis internal guidance for this turn" not in normalized:
            return True
        if len(lines) < 2:
            return True

    if identity in {"assistant_context", "system_seed"} and (
        any(token in normalized for token in SECTION_MARKERS)
        or any(token in normalized for token in PLAN_MARKERS)
    ):
        return True

    if len(lines) <= 2 and all(line.endswith(":") or _looks_like_scaffold_heading(line.lower()) for line in lines):
        return True

    return False
