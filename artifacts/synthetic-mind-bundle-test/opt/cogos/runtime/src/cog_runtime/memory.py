"""Memory Runtime — Encode → Index → Retrieve → Forget."""

from __future__ import annotations

import re
import uuid
from typing import Any

from src.cog_runtime.base import CogRuntimeSession, runtime_spec_template
from src.cog_runtime.capability_governance import lobe_capability_contract

MEMORY_RUNTIME_ID = "cognitive.memory"
MEMORY_RUNTIME_VERSION = "1.2"
MEMORY_STAGES = ("encode", "index", "retrieve", "forget")
REQUIRED_TURN_STAGES = ("encode", "retrieve")
MAX_RETRIEVED_CUES = 5
MAX_INDEX_KEYS = 8
WORD_RE = re.compile(r"[A-Za-z0-9']{3,}")
EPISODIC_KIND = "episodic"
SEMANTIC_KIND = "semantic"

MEMORY_INVARIANTS: tuple[dict[str, str], ...] = (
    {"id": "bounded_recall", "rule": "Retrieve bounded cues only; no ungoverned writes."},
    {"id": "forget_safe", "rule": "Forget stage is advisory in v1; no destructive deletes."},
    {"id": "kind_separation", "rule": "Episodic turn records and semantic continuity cues are indexed separately."},
    {"id": "compression", "rule": "Episodic records compress into bounded summaries; semantic cues abstract to stable facts."},
)


def _memory_cue_text(cue: Any) -> str:
    if isinstance(cue, dict):
        for key in ("text", "content", "insight", "excerpt", "summary"):
            value = str(cue.get(key) or "").strip()
            if value:
                return value
        return str(cue).strip()
    return str(cue or "").strip()


def _memory_cue_id(cue: Any, *, fallback_text: str = "") -> str:
    if isinstance(cue, dict):
        cue_id = str(cue.get("id") or "").strip()
        if cue_id:
            return cue_id
    text = fallback_text or _memory_cue_text(cue)
    if text:
        return text[:48].lower().replace(" ", "_")
    return uuid.uuid4().hex[:12]


def classify_memory_kind(cue: Any, *, default: str = SEMANTIC_KIND) -> str:
    if isinstance(cue, dict):
        explicit = str(cue.get("memory_kind") or cue.get("kind") or "").strip().lower()
        if explicit in {EPISODIC_KIND, SEMANTIC_KIND}:
            return explicit
        if cue.get("episodic") is True:
            return EPISODIC_KIND
        if cue.get("semantic") is True:
            return SEMANTIC_KIND
        if cue.get("source") in {"turn_message", "turn_event", "episode"}:
            return EPISODIC_KIND
    return default


def summarize_memory_board_slot(slot: dict[str, Any]) -> dict[str, Any] | None:
    """Summarize one active memory-board slot into a bounded cortex cue."""
    if not isinstance(slot, dict) or not slot.get("active"):
        return None
    module = slot.get("module")
    if not isinstance(module, dict):
        return None
    summary = str(module.get("summary") or module.get("display_name") or "").strip()
    if not summary:
        return None
    return {
        "id": f"memory_board_{module.get('module_id') or slot.get('slot_id')}",
        "text": summary,
        "source": "memory_board",
        "semantic": True,
        "memory_kind": SEMANTIC_KIND,
        "slot_id": str(slot.get("slot_id") or ""),
    }


def memory_board_active_slots(board: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(board, dict):
        return []
    return [
        slot
        for slot in board.get("slots") or []
        if isinstance(slot, dict) and slot.get("active") and isinstance(slot.get("module"), dict)
    ]


def _resolve_memory_board(source: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(source, dict):
        return None
    slots = source.get("slots")
    if isinstance(slots, list) and slots and any(isinstance(item, dict) and "slot_id" in item for item in slots):
        return source
    board = source.get("memory_board_snapshot") or source.get("memory_board")
    return board if isinstance(board, dict) else None


def normalize_cortex_memory_cues(
    board_or_metadata: dict[str, Any] | None,
    *,
    companion_turn: bool = False,
    limit: int = MAX_RETRIEVED_CUES,
    metadata: dict[str, Any] | None = None,
) -> list[Any]:
    """Derive bounded cortex cues from the memory board snapshot (primary source)."""
    from src.conversation_memory import (
        dedupe_memory_cues,
        filter_companion_persistent_memories,
    )

    board = _resolve_memory_board(board_or_metadata)
    meta = dict(metadata or (board_or_metadata if board is None else {}) or {})
    raw: list[Any] = []

    if isinstance(board, dict):
        for slot in memory_board_active_slots(board):
            cue = summarize_memory_board_slot(slot)
            if cue:
                raw.append(cue)

    episodic = list(meta.get("cortex_episodic_memory") or [])
    raw.extend(episodic)

    if not raw and meta:
        legacy = meta.get("memory_cues")
        if isinstance(legacy, list):
            raw.extend(legacy)
        elif isinstance(legacy, dict):
            for key in ("items", "cues", "retrieved"):
                items = legacy.get(key)
                if isinstance(items, list):
                    raw.extend(items)

    unique = dedupe_memory_cues(raw)
    if companion_turn:
        unique = filter_companion_persistent_memories(unique, limit=limit)
    return unique[:limit]


def _keyword_keys(text: str, *, frame_kind: str = "", face_scope: str = "") -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for token in WORD_RE.findall(text.lower()):
        if len(token) < 4 or token in seen:
            continue
        seen.add(token)
        keys.append(token)
    if frame_kind and frame_kind not in seen:
        keys.append(frame_kind)
    if face_scope:
        scope_key = face_scope.replace("-", "_").lower()
        if scope_key not in seen:
            keys.append(scope_key)
    return keys[:MAX_INDEX_KEYS]


def _cue_overlap_score(
    cue_text: str,
    *,
    user_message: str,
    focus_primary: str,
    index_keys: list[str],
    memory_kind: str = SEMANTIC_KIND,
) -> float:
    lowered = cue_text.lower()
    score = 0.0
    message_tokens = set(WORD_RE.findall(user_message.lower()))
    cue_tokens = set(WORD_RE.findall(lowered))
    overlap = message_tokens & cue_tokens
    if overlap:
        score += min(0.45, 0.08 * len(overlap))
    if focus_primary and focus_primary.lower() in lowered:
        score += 0.35
    for key in index_keys:
        if key in lowered:
            score += 0.1
    if len(cue_text) > 20:
        score += 0.05
    if memory_kind == EPISODIC_KIND:
        score += 0.08
    return round(min(score, 1.0), 3)


def memory_runtime_spec() -> dict[str, Any]:
    return runtime_spec_template(
        runtime_id=MEMORY_RUNTIME_ID,
        version=MEMORY_RUNTIME_VERSION,
        summary="Episodic compression and semantic abstraction within bounded memory law.",
        stages=MEMORY_STAGES,
        required_turn_stages=REQUIRED_TURN_STAGES,
        invariants=MEMORY_INVARIANTS,
        inputs={
            "user_message": "string",
            "memory_cues": "object[]",
            "focus_artifact": "object",
            "frame_kind": "string",
            "face_scope": "string",
            "cognitive_arc": "object",
        },
        outputs={
            "memory_artifact": {
                "encoded": "object",
                "episodic_records": "object[]",
                "semantic_records": "object[]",
                "index_keys": "string[]",
                "retrieved_episodic": "string[]",
                "retrieved_semantic": "string[]",
                "retrieved_cues": "string[]",
                "compressed_episodic": "object[]",
                "semantic_abstractions": "object[]",
                "forgotten_advisory": "string[]",
            }
        },
        doc="docs/runtime/NOVA_CORTEX.md",
        **lobe_capability_contract(MEMORY_RUNTIME_ID),
    )


def validate_memory_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    encoded = artifact.get("encoded")
    if not isinstance(encoded, dict):
        issues.append("encoded_not_object")
    for field in ("episodic_records", "semantic_records", "retrieved_episodic", "retrieved_semantic"):
        value = artifact.get(field)
        if not isinstance(value, list):
            issues.append(f"{field}_not_list")
    index_keys = artifact.get("index_keys")
    if not isinstance(index_keys, list):
        issues.append("index_keys_not_list")
    retrieved = artifact.get("retrieved_cues")
    if not isinstance(retrieved, list):
        issues.append("retrieved_cues_not_list")
    forgotten = artifact.get("forgotten_advisory")
    if forgotten is not None and not isinstance(forgotten, list):
        issues.append("forgotten_advisory_not_list")
    compressed = artifact.get("compressed_episodic")
    if not isinstance(compressed, list):
        issues.append("compressed_episodic_not_list")
    abstractions = artifact.get("semantic_abstractions")
    if not isinstance(abstractions, list):
        issues.append("semantic_abstractions_not_list")
    return {"valid": not issues, "issues": issues}


def _compress_episodic_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not records:
        return []
    texts = [str(item.get("text") or "").strip() for item in records if str(item.get("text") or "").strip()]
    if not texts:
        return []
    if len(texts) == 1 and len(texts[0]) <= 96:
        return [{"summary": texts[0], "source_ids": [records[0].get("id")], "record_count": 1}]

    primary = texts[0][:72]
    overlap_tokens: set[str] = set()
    for text in texts[1:]:
        overlap_tokens.update(WORD_RE.findall(text.lower())[:4])
    tail = " ".join(sorted(overlap_tokens)[:4])
    summary = primary if not tail else f"{primary} (+ {tail})"
    summary = summary[:120]
    return [
        {
            "summary": summary,
            "source_ids": [str(item.get("id") or "") for item in records if item.get("id")],
            "record_count": len(records),
        }
    ]


def _abstract_semantic_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    abstractions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        text = str(record.get("text") or "").strip()
        if not text:
            continue
        tokens = [token for token in WORD_RE.findall(text.lower()) if len(token) >= 4]
        if tokens:
            abstract = f"Preference/theme: {', '.join(list(dict.fromkeys(tokens))[:4])}"
        else:
            abstract = text[:80]
        normalized = abstract.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        abstractions.append(
            {
                "abstract": abstract[:120],
                "source_id": str(record.get("id") or ""),
                "memory_kind": SEMANTIC_KIND,
            }
        )
    return abstractions[:MAX_RETRIEVED_CUES]


def _build_episodic_record(
    *,
    user_message: str,
    primary_focus: str,
    frame_kind: str,
    face_scope: str,
    salience: float,
    arc_context: dict[str, Any],
) -> dict[str, Any]:
    encoded_text = " ".join((user_message or "").split()).strip()[:160]
    if primary_focus and primary_focus.lower() not in encoded_text.lower():
        encoded_text = f"{primary_focus} | {encoded_text}"[:160]
    return {
        "id": uuid.uuid4().hex[:12],
        "text": encoded_text,
        "memory_kind": EPISODIC_KIND,
        "frame_kind": frame_kind,
        "face_scope": face_scope,
        "salience": salience,
        "source": "turn_message",
        "arc_id": arc_context.get("arc_id"),
        "arc_step": arc_context.get("arc_turn_count"),
    }


def _normalize_semantic_record(cue: Any) -> dict[str, Any]:
    text = _memory_cue_text(cue)
    return {
        "id": _memory_cue_id(cue, fallback_text=text),
        "text": text,
        "memory_kind": classify_memory_kind(cue, default=SEMANTIC_KIND),
        "source": "continuity_cue",
    }


def run_memory_turn(
    user_message: str,
    *,
    memory_cues: list[Any] | None = None,
    focus_artifact: dict[str, Any] | None = None,
    frame_kind: str = "general",
    face_scope: str = "",
    companion_turn: bool = False,
    cognitive_arc: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, Any], CogRuntimeSession]:
    session = CogRuntimeSession(
        runtime_id=MEMORY_RUNTIME_ID,
        user_message=user_message,
        context={
            "memory_cues": list(memory_cues or []),
            "focus_artifact": dict(focus_artifact or {}),
            "cognitive_arc": dict(cognitive_arc or {}),
        },
        required_stages=REQUIRED_TURN_STAGES,
        stage_order=MEMORY_STAGES,
    )

    focus = dict(focus_artifact or {})
    arc = dict(cognitive_arc or {})
    primary_focus = str(focus.get("primary_focus") or "").strip()
    salience = float((focus.get("salience") or {}).get(primary_focus, 0.5) or 0.5)

    episodic_record = _build_episodic_record(
        user_message=user_message,
        primary_focus=primary_focus,
        frame_kind=frame_kind,
        face_scope=face_scope,
        salience=salience,
        arc_context=arc,
    )

    semantic_records: list[dict[str, Any]] = []
    episodic_records: list[dict[str, Any]] = [episodic_record]
    for cue in list(memory_cues or []):
        record = _normalize_semantic_record(cue)
        kind = classify_memory_kind(cue, default=SEMANTIC_KIND)
        record["memory_kind"] = kind
        if kind == EPISODIC_KIND:
            episodic_records.append(record)
        else:
            semantic_records.append(record)

    session.start_stage("encode", {"message": user_message, "focus": primary_focus})
    session.end_stage(
        "encode",
        {
            "encoded": episodic_record,
            "episodic_count": len(episodic_records),
            "semantic_count": len(semantic_records),
        },
    )

    index_keys = _keyword_keys(
        f"{user_message} {primary_focus}",
        frame_kind=frame_kind,
        face_scope=face_scope,
    )
    for record in semantic_records + episodic_records:
        index_keys.extend(_keyword_keys(str(record.get("text") or ""))[:3])
    index_keys = list(dict.fromkeys(index_keys))[:MAX_INDEX_KEYS]

    session.start_stage("index", {"encoded": episodic_record})
    session.end_stage(
        "index",
        {
            "index_keys": index_keys,
            "episodic_indexed": len(episodic_records),
            "semantic_indexed": len(semantic_records),
        },
    )

    ranked_episodic: list[tuple[float, str, str]] = []
    ranked_semantic: list[tuple[float, str, str]] = []
    for record in episodic_records:
        text = str(record.get("text") or "")
        if not text:
            continue
        score = _cue_overlap_score(
            text,
            user_message=user_message,
            focus_primary=primary_focus,
            index_keys=index_keys,
            memory_kind=EPISODIC_KIND,
        )
        ranked_episodic.append((score, str(record.get("id") or ""), text))
    for record in semantic_records:
        text = str(record.get("text") or "")
        if not text:
            continue
        score = _cue_overlap_score(
            text,
            user_message=user_message,
            focus_primary=primary_focus,
            index_keys=index_keys,
            memory_kind=SEMANTIC_KIND,
        )
        ranked_semantic.append((score, str(record.get("id") or ""), text))

    ranked_episodic.sort(key=lambda item: (-item[0], item[1]))
    ranked_semantic.sort(key=lambda item: (-item[0], item[1]))
    retrieved_episodic = [text for _, _, text in ranked_episodic[:3]]
    retrieved_semantic = [text for _, _, text in ranked_semantic[:MAX_RETRIEVED_CUES]]
    retrieved_cues = list(dict.fromkeys(retrieved_semantic + retrieved_episodic))[:MAX_RETRIEVED_CUES]
    if not retrieved_cues and episodic_record.get("text"):
        retrieved_cues = [str(episodic_record["text"])[:120]]
        retrieved_episodic = retrieved_cues[:1]

    session.start_stage("retrieve", {"index_keys": index_keys})
    session.end_stage(
        "retrieve",
        {
            "retrieved_episodic": retrieved_episodic,
            "retrieved_semantic": retrieved_semantic,
            "retrieved_cues": retrieved_cues,
        },
    )

    forgotten_advisory: list[str] = []
    combined = ranked_semantic + ranked_episodic
    if combined:
        threshold = max(0.08, combined[0][0] * 0.35)
        for score, cue_id, cue_text in combined[MAX_RETRIEVED_CUES:]:
            if score <= threshold:
                forgotten_advisory.append(cue_id or cue_text[:48])
    if companion_turn and len(memory_cues or []) > MAX_RETRIEVED_CUES:
        forgotten_advisory.append("overflow_companion_recall")

    session.start_stage("forget", {"policy": "advisory_only"})
    compressed_episodic = _compress_episodic_records(episodic_records)
    semantic_abstractions = _abstract_semantic_records(semantic_records)
    session.end_stage(
        "forget",
        {
            "forgotten_advisory": forgotten_advisory,
            "compressed_episodic": compressed_episodic,
            "semantic_abstractions": semantic_abstractions,
        },
    )

    memory_artifact = {
        "encoded": episodic_record,
        "episodic_records": episodic_records,
        "semantic_records": semantic_records,
        "index_keys": index_keys,
        "retrieved_episodic": retrieved_episodic,
        "retrieved_semantic": retrieved_semantic,
        "retrieved_cues": retrieved_cues,
        "compressed_episodic": compressed_episodic,
        "semantic_abstractions": semantic_abstractions,
        "forgotten_advisory": forgotten_advisory,
    }

    validation = validate_memory_artifact(memory_artifact)
    if not validation["valid"]:
        raise ValueError(f"memory turn invalid: {validation['issues']}")
    turn_validation = session.validate_turn()
    if not turn_validation["valid"]:
        raise ValueError(f"memory ledger invalid: {turn_validation['issues']}")

    return retrieved_cues, memory_artifact, session
