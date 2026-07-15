"""Attention Runtime — Capture → Filter → Prioritize → Hold."""

from __future__ import annotations

import re
from typing import Any

from src.cog_runtime.base import CogRuntimeSession, runtime_spec_template
from src.cog_runtime.capability_governance import lobe_capability_contract
from src.speaking_runtime import infer_frame_kind

ATTENTION_RUNTIME_ID = "cognitive.attention"
ATTENTION_RUNTIME_VERSION = "1.2"
ATTENTION_STAGES = ("capture", "filter", "prioritize", "hold")
REQUIRED_TURN_STAGES = ATTENTION_STAGES
MAX_FOCUS_SIGNALS = 3
MAX_SECONDARY_FOCUS = 2
SECONDARY_SALIENCE_GAP = 0.15

ATTENTION_INVARIANTS: tuple[dict[str, str], ...] = (
    {"id": "bounded_focus", "rule": "Hold at most three prioritized focus signals per turn."},
    {"id": "traceability", "rule": "Every focus signal maps to a ledger stage."},
)

BOILERPLATE_RE = re.compile(
    r"^(hi|hello|hey|thanks|thank you|ok|okay|please|just|so|well)[\s,!.]*",
    re.I,
)
SENTENCE_SPLIT_RE = re.compile(r"[.!?;\n]+")
WORD_SIGNAL_RE = re.compile(r"[A-Za-z0-9']{3,}")


def _contains_companion_leak(text: str) -> bool:
    from src.conversation_memory import contains_companion_system_leak

    return contains_companion_system_leak(text)


FRAME_WEIGHTS: dict[str, tuple[str, ...]] = {
    "decision": ("should", "choose", "pick", "or", "versus", "option", "decide"),
    "question": ("what", "why", "how", "when", "where", "who", "?"),
    "implementation": ("build", "implement", "create", "code", "ship", "write"),
    "instruction": ("show", "step", "walk", "guide", "help"),
    "design": ("design", "architect", "spec", "model", "blueprint"),
    "review": ("review", "audit", "critique", "feedback"),
    "venting": ("frustrated", "annoyed", "ugh", "hate", "tired"),
    "general": ("need", "want", "think", "feel"),
}


def attention_runtime_spec() -> dict[str, Any]:
    return runtime_spec_template(
        runtime_id=ATTENTION_RUNTIME_ID,
        version=ATTENTION_RUNTIME_VERSION,
        summary="Select turn focus signals from message, Nova Face, memory, and frame context.",
        stages=ATTENTION_STAGES,
        required_turn_stages=REQUIRED_TURN_STAGES,
        invariants=ATTENTION_INVARIANTS,
        inputs={
            "user_message": "string",
            "context": "object",
            "nova_face": "object",
            "frame_kind": "string",
            "memory_cues": "string[]",
        },
        outputs={
            "focus_artifact": {
                "primary_focus": "string",
                "secondary_focus": "string[]",
                "focus_signals": "string[]",
                "weights": "object",
                "salience": "object",
                "signal_sources": "object",
                "frame_kind": "string",
                "suppressed": "string[]",
            }
        },
        doc="docs/runtime/NOVA_CORTEX.md",
        **lobe_capability_contract(ATTENTION_RUNTIME_ID),
    )


def validate_focus_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    primary = str(artifact.get("primary_focus") or "").strip()
    if not primary:
        issues.append("missing_primary_focus")
    signals = artifact.get("focus_signals")
    if not isinstance(signals, list):
        issues.append("focus_signals_not_list")
    elif len(signals) > MAX_FOCUS_SIGNALS:
        issues.append("too_many_focus_signals")
    elif signals and not primary:
        issues.append("empty_primary_with_signals")
    secondary = artifact.get("secondary_focus")
    if secondary is None:
        issues.append("missing_secondary_focus")
    elif not isinstance(secondary, list):
        issues.append("secondary_focus_not_list")
    elif len(secondary) > MAX_SECONDARY_FOCUS:
        issues.append("too_many_secondary_focus")
    weights = artifact.get("weights")
    if weights is not None and not isinstance(weights, dict):
        issues.append("weights_not_object")
    salience = artifact.get("salience")
    if salience is None:
        issues.append("missing_salience")
    elif not isinstance(salience, dict):
        issues.append("salience_not_object")
    elif salience:
        total = sum(float(value) for value in salience.values())
        if abs(total - 1.0) > 0.05:
            issues.append("salience_not_normalized")
    sources = artifact.get("signal_sources")
    if sources is None:
        issues.append("missing_signal_sources")
    elif not isinstance(sources, dict):
        issues.append("signal_sources_not_object")
    suppressed = artifact.get("suppressed")
    if suppressed is not None and not isinstance(suppressed, list):
        issues.append("suppressed_not_list")
    if not str(artifact.get("frame_kind") or "").strip():
        issues.append("missing_frame_kind")
    return {"valid": not issues, "issues": issues}


def _memory_cue_text(cue: Any) -> str:
    if isinstance(cue, dict):
        for key in ("text", "content", "insight", "excerpt", "summary"):
            value = str(cue.get(key) or "").strip()
            if value:
                return value[:80]
        return str(cue)[:80]
    return str(cue or "")[:80]


def _tokenize_signals(text: str) -> list[str]:
    cleaned = BOILERPLATE_RE.sub("", (text or "").strip())
    parts: list[str] = []
    for chunk in SENTENCE_SPLIT_RE.split(cleaned):
        chunk = " ".join(chunk.split()).strip(" ?.")
        if not chunk or _contains_companion_leak(chunk):
            continue
        if len(chunk) >= 8:
            parts.append(chunk[:160])
            continue
        for word in WORD_SIGNAL_RE.findall(chunk):
            if len(word) >= 4:
                parts.append(word.lower())
    return parts


def _score_signal_channels(
    signal: str,
    frame_kind: str,
    *,
    face_scope: str = "",
    source: str = "message",
) -> dict[str, float]:
    lowered = signal.lower()
    channels = {
        "frame_match": 0.35,
        "memory_boost": 0.0,
        "face_scope": 0.0,
        "message_length": 0.0,
    }
    for token in FRAME_WEIGHTS.get(frame_kind, FRAME_WEIGHTS["general"]):
        if token in lowered:
            channels["frame_match"] += 0.2
            break
    if source == "memory":
        channels["memory_boost"] = 0.25
    if face_scope and face_scope.replace("_", " ") in lowered:
        channels["face_scope"] = 0.15
    if len(signal) > 40:
        channels["message_length"] = 0.1
    if signal.endswith("?"):
        channels["frame_match"] += 0.05
    total = round(min(sum(channels.values()), 1.0), 3)
    channels["total"] = total
    return channels


def _score_signal(
    signal: str,
    frame_kind: str,
    *,
    face_scope: str = "",
    source: str = "message",
) -> float:
    return _score_signal_channels(
        signal, frame_kind, face_scope=face_scope, source=source
    )["total"]


def _normalize_salience(weights: dict[str, float]) -> dict[str, float]:
    if not weights:
        return {}
    total = sum(weights.values()) or 1.0
    return {key: round(value / total, 3) for key, value in weights.items()}


def _build_focus_artifact(
    *,
    user_message: str,
    frame_kind: str,
    candidates: list[str],
    candidate_sources: dict[str, str],
    suppressed: list[str],
    face_scope: str,
) -> dict[str, Any]:
    weights: dict[str, float] = {}
    channel_breakdown: dict[str, dict[str, float]] = {}
    for signal in candidates:
        source = candidate_sources.get(signal, "message")
        channels = _score_signal_channels(
            signal,
            frame_kind,
            face_scope=face_scope,
            source=source,
        )
        weights[signal] = channels["total"]
        channel_breakdown[signal] = channels

    ranked = sorted(weights.items(), key=lambda item: (-item[1], item[0]))
    focus_signals = [signal for signal, _ in ranked[:MAX_FOCUS_SIGNALS]]
    if not focus_signals:
        clipped = " ".join((user_message or "").split()).strip()[:120]
        focus_signals = [clipped or "general intent"]
        weights = {focus_signals[0]: 0.5}
        channel_breakdown = {
            focus_signals[0]: _score_signal_channels(
                focus_signals[0], frame_kind, face_scope=face_scope
            )
        }
        candidate_sources = {focus_signals[0]: "frame"}

    salience = _normalize_salience({key: weights[key] for key in focus_signals})
    primary_focus = focus_signals[0]
    primary_score = weights.get(primary_focus, 0.0)
    secondary_focus: list[str] = []
    for signal in focus_signals[1:]:
        gap = primary_score - weights.get(signal, 0.0)
        if gap <= SECONDARY_SALIENCE_GAP:
            secondary_focus.append(signal)
        if len(secondary_focus) >= MAX_SECONDARY_FOCUS:
            break

    signal_sources = {
        signal: candidate_sources.get(signal, "message") for signal in focus_signals
    }

    return {
        "primary_focus": primary_focus,
        "secondary_focus": secondary_focus,
        "focus_signals": focus_signals,
        "weights": {key: weights.get(key, 0.0) for key in focus_signals},
        "salience": salience,
        "signal_sources": signal_sources,
        "frame_kind": frame_kind,
        "suppressed": suppressed[:10],
        "_channel_breakdown": channel_breakdown,
    }


def run_attention_turn(
    user_message: str,
    *,
    context: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], CogRuntimeSession]:
    ctx = dict(context or {})
    nova_face = dict(ctx.get("nova_face") or {})
    frame_kind = str(ctx.get("frame_kind") or infer_frame_kind(user_message))
    face_scope = str(nova_face.get("scope") or nova_face.get("face_id") or "")

    session = CogRuntimeSession(
        runtime_id=ATTENTION_RUNTIME_ID,
        user_message=user_message,
        context=ctx,
        required_stages=REQUIRED_TURN_STAGES,
        stage_order=ATTENTION_STAGES,
    )

    captured = {
        "user_message": user_message,
        "frame_kind": frame_kind,
        "nova_face": nova_face,
        "memory_cues": list(ctx.get("memory_cues") or [])[:5],
        "response_mode": ctx.get("response_mode"),
    }
    session.start_stage("capture", captured)
    session.end_stage("capture", {"captured_fields": sorted(captured.keys())})

    raw_candidates: list[str] = []
    candidate_sources: dict[str, str] = {}
    for signal in _tokenize_signals(user_message):
        raw_candidates.append(signal)
        candidate_sources[signal] = "message"
    if face_scope:
        face_signal = face_scope.replace("_", " ")
        if face_signal not in candidate_sources:
            raw_candidates.append(face_signal)
            candidate_sources[face_signal] = "face"
    if ctx.get("memory_cues"):
        for item in ctx["memory_cues"][:3]:
            cue_text = _memory_cue_text(item)
            if cue_text and cue_text not in candidate_sources:
                raw_candidates.append(cue_text)
                candidate_sources[cue_text] = "memory"

    suppressed: list[str] = []
    filtered: list[str] = []
    seen: set[str] = set()
    for candidate in raw_candidates:
        normalized = candidate.strip().lower()
        if not normalized or normalized in seen:
            continue
        if _contains_companion_leak(candidate):
            suppressed.append(candidate)
            continue
        seen.add(normalized)
        filtered.append(candidate)

    session.start_stage("filter", {"raw_count": len(raw_candidates)})
    session.end_stage("filter", {"filtered": filtered, "suppressed_count": len(suppressed)})

    session.start_stage("prioritize", {"candidates": filtered})
    artifact = _build_focus_artifact(
        user_message=user_message,
        frame_kind=frame_kind,
        candidates=filtered,
        candidate_sources=candidate_sources,
        suppressed=suppressed,
        face_scope=face_scope,
    )
    channel_breakdown = artifact.pop("_channel_breakdown", {})
    session.end_stage(
        "prioritize",
        {
            "ranked": artifact["focus_signals"],
            "weights": artifact["weights"],
            "salience": artifact["salience"],
            "channel_breakdown": channel_breakdown,
        },
    )

    session.start_stage("hold", {"prioritized": artifact["focus_signals"]})
    session.end_stage("hold", {"focus_artifact": artifact})

    validation = validate_focus_artifact(artifact)
    if not validation["valid"]:
        raise ValueError(f"attention turn invalid: {validation['issues']}")
    turn_validation = session.validate_turn()
    if not turn_validation["valid"]:
        raise ValueError(f"attention ledger invalid: {turn_validation['issues']}")

    return artifact, session
