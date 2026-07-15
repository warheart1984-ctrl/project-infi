"""Nova cognitive router, session, and speaking adapter."""

# Mythic: Nova
# Engineering: NovaEngine
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid

from src.cog_runtime.attention import ATTENTION_RUNTIME_ID, run_attention_turn
from src.cog_runtime.deliberation import (
    DELIBERATION_RUNTIME_ID,
    run_deliberation_turn,
    should_activate_deliberation,
)
from src.cog_runtime.memory import (
    MEMORY_RUNTIME_ID,
    normalize_cortex_memory_cues,
    run_memory_turn,
)
from src.cog_runtime.arcs import (
    append_arc_turn,
    arc_context_for_turn,
    load_cortex_arc,
    persist_cortex_arc,
    start_or_continue_arc,
)
from src.cog_runtime.execution import (
    EXECUTION_RUNTIME_ID,
    merge_post_reply_execution,
    run_execution_turn,
    should_activate_execution,
)
from src.cog_runtime.planning import PLANNING_RUNTIME_ID, run_planning_turn, should_activate_planning
from src.cog_runtime.reflection import (
    REFLECTION_RUNTIME_ID,
    merge_post_reply_reflection,
    run_reflection_turn,
    should_handoff_to_planning,
)
from src.speaking_runtime import (
    SPEAKING_RUNTIME_ID,
    SpeakingRuntimeSession,
    build_check_utterance,
    build_frame_utterance,
    build_listen_utterance,
    build_plan_utterance,
    build_update_utterance,
    compose_reply,
    infer_frame_kind,
    validate_reply,
    verify_reply,
)
from src.cog_runtime.formal.intent_narrative_reconcile import reconcile_intent_narrative
from src.cog_runtime.tuning import load_tuned_thresholds, run_self_tune_invariants
from src.cog_runtime.narrative import load_nova_narrative, persist_nova_narrative, run_narrative_turn
from src.cog_runtime.intent_core import (
    intent_context_for_lobes,
    load_nova_intent,
    persist_nova_intent,
    run_intent_turn,
)
from src.cog_runtime.intent_store import (
    flush_nova_intent_store,
    rehydrate_nova_intent,
    resolve_intent_store_root,
)
from src.cog_runtime.narrative_store import (
    flush_nova_narrative_store,
    rehydrate_nova_narrative,
    resolve_narrative_store_root,
)
from src.jarvis_reasoning_protocol import REASONING_PROTOCOL_ID

TUNING_ARTIFACT_KEY = "invariant_tuning_artifact"

NOVA_CORTEX_ID = "nova.cortex"
# Back-compat alias for earlier family id string.
NOVA_COGNITIVE_FAMILY_ID = NOVA_CORTEX_ID
REASONING_RUNTIME_ID = REASONING_PROTOCOL_ID


def _json_safe(value: Any) -> Any:
    if callable(value):
        return getattr(value, "__name__", "callable")
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


@dataclass
class NovaCognitiveSession:
    """Shared turn session aggregating runtime ledgers and artifacts."""

    user_message: str
    context: dict[str, Any] = field(default_factory=dict)
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    active_runtimes: list[str] = field(default_factory=list)
    frame_kind: str = "general"
    ledger: list[dict[str, Any]] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)

    def append_ledger_entry(self, entry: dict[str, Any]) -> None:
        self.ledger.append(dict(entry))

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "family_id": NOVA_COGNITIVE_FAMILY_ID,
            "user_message": self.user_message,
            "frame_kind": self.frame_kind,
            "active_runtimes": list(self.active_runtimes),
            "ledger": _json_safe(list(self.ledger)),
            "artifacts": _json_safe(dict(self.artifacts)),
            "context": _json_safe(dict(self.context or {})),
        }


def nova_cognitive_router(turn_context: dict[str, Any]) -> list[str]:
    """Select which runtime IDs activate for this turn."""
    user_message = str(turn_context.get("user_message") or "")
    frame_kind = str(turn_context.get("frame_kind") or infer_frame_kind(user_message))
    response_mode = str(turn_context.get("response_mode") or "")
    companion_turn = bool(turn_context.get("companion_turn"))
    cognitive_enabled = bool(turn_context.get("cognitive_runtime_enabled", True))
    speaking_enabled = bool(turn_context.get("speaking_runtime_enabled"))

    if not cognitive_enabled:
        return [REASONING_RUNTIME_ID] if not companion_turn else []

    if turn_context.get("cortex_fast_path"):
        return _dedupe([REASONING_RUNTIME_ID, ATTENTION_RUNTIME_ID])

    active = [REASONING_RUNTIME_ID, ATTENTION_RUNTIME_ID]

    if should_activate_deliberation(user_message, frame_kind=frame_kind):
        active.append(DELIBERATION_RUNTIME_ID)
    elif response_mode in {"think", "research"} and frame_kind == "decision":
        active.append(DELIBERATION_RUNTIME_ID)

    memory_cues = turn_context.get("memory_cues")
    has_cues = isinstance(memory_cues, list) and bool(memory_cues)
    if companion_turn or has_cues:
        active.append(MEMORY_RUNTIME_ID)

    if speaking_enabled or turn_context.get("require_speaking"):
        active.append(SPEAKING_RUNTIME_ID)

    if companion_turn and SPEAKING_RUNTIME_ID not in active:
        active.append(SPEAKING_RUNTIME_ID)

    return _dedupe(active)


def nova_cognitive_session(
    user_message: str,
    *,
    context: dict[str, Any] | None = None,
) -> NovaCognitiveSession:
    """Create a shared Nova cognitive session for the turn."""
    ctx = dict(context or {})
    frame_kind = str(ctx.get("frame_kind") or infer_frame_kind(user_message))
    return NovaCognitiveSession(
        user_message=user_message,
        context=ctx,
        frame_kind=frame_kind,
    )


def run_nova_cognitive_turn(
    user_message: str,
    *,
    context: dict[str, Any] | None = None,
) -> NovaCognitiveSession:
    """Execute activated runtimes and populate shared ledger."""
    ctx = dict(context or {})
    arc_payload = dict(ctx.get("cognitive_arc") or {})
    tuned_thresholds = dict(ctx.get("tuned_thresholds") or load_tuned_thresholds(ctx))
    session = nova_cognitive_session(user_message, context=ctx)
    turn_context = {
        "user_message": user_message,
        "frame_kind": session.frame_kind,
        "response_mode": ctx.get("response_mode"),
        "companion_turn": ctx.get("companion_turn"),
        "cognitive_runtime_enabled": ctx.get("cognitive_runtime_enabled", True),
        "speaking_runtime_enabled": ctx.get("speaking_runtime_enabled"),
        "memory_cues": ctx.get("memory_cues"),
        "require_speaking": ctx.get("require_speaking"),
        "cortex_fast_path": bool(ctx.get("cortex_fast_path")),
    }
    session.active_runtimes = nova_cognitive_router(turn_context)

    if ATTENTION_RUNTIME_ID in session.active_runtimes:
        focus_artifact, attention_session = run_attention_turn(user_message, context=ctx)
        session.artifacts["focus_artifact"] = focus_artifact
        session.artifacts["focus_signals"] = list(focus_artifact.get("focus_signals") or [])
        session.ledger.extend(attention_session.export_ledger())

    if MEMORY_RUNTIME_ID in session.active_runtimes:
        nova_face = dict(ctx.get("nova_face") or {})
        cues, memory_artifact, memory_session = run_memory_turn(
            user_message,
            memory_cues=list(ctx.get("memory_cues") or []),
            focus_artifact=session.artifacts.get("focus_artifact"),
            frame_kind=session.frame_kind,
            face_scope=str(nova_face.get("scope") or nova_face.get("face_id") or ""),
            companion_turn=bool(ctx.get("companion_turn")),
            cognitive_arc=arc_payload,
        )
        session.artifacts["retrieved_cues"] = cues
        session.artifacts["memory_artifact"] = memory_artifact
        session.ledger.extend(memory_session.export_ledger())

    if DELIBERATION_RUNTIME_ID in session.active_runtimes:
        decision, deliberation_session = run_deliberation_turn(
            user_message,
            context=ctx,
            frame_kind=session.frame_kind,
            focus_artifact=session.artifacts.get("focus_artifact"),
            deliberate_fn=ctx.get("deliberate_fn"),
            use_llm=bool(ctx.get("deliberation_llm")),
            revisit_note=str(ctx.get("revisit_note") or ""),
        )
        session.artifacts["decision_object"] = decision
        session.ledger.extend(deliberation_session.export_ledger())

    if not ctx.get("cortex_fast_path") and _should_run_reflection(ctx, session):
        reflection_artifact, reflection_session = run_reflection_turn(
            focus_artifact=session.artifacts.get("focus_artifact"),
            decision_object=session.artifacts.get("decision_object"),
            memory_artifact=session.artifacts.get("memory_artifact"),
            frame_kind=session.frame_kind,
            user_message=user_message,
        )
        session.artifacts["reflection_artifact"] = reflection_artifact
        session.ledger.extend(reflection_session.export_ledger())
        if REFLECTION_RUNTIME_ID not in session.active_runtimes:
            session.active_runtimes.append(REFLECTION_RUNTIME_ID)

        if should_activate_planning(
            reflection_artifact,
            companion_turn=bool(ctx.get("companion_turn")),
        ) or should_handoff_to_planning(reflection_artifact):
            planning_artifact, planning_session = run_planning_turn(
                reflection_artifact=reflection_artifact,
                focus_artifact=session.artifacts.get("focus_artifact"),
                decision_object=session.artifacts.get("decision_object"),
                cognitive_arc=arc_payload,
                frame_kind=session.frame_kind,
                user_message=user_message,
                tuned_thresholds=tuned_thresholds,
                context=ctx,
            )
            session.artifacts["planning_artifact"] = planning_artifact
            session.ledger.extend(planning_session.export_ledger())
            if PLANNING_RUNTIME_ID not in session.active_runtimes:
                session.active_runtimes.append(PLANNING_RUNTIME_ID)

            if should_activate_execution(
                planning_artifact,
                companion_turn=bool(ctx.get("companion_turn")),
            ):
                execution_artifact, execution_session = run_execution_turn(
                    planning_artifact=planning_artifact,
                    focus_artifact=session.artifacts.get("focus_artifact"),
                    decision_object=session.artifacts.get("decision_object"),
                    reflection_artifact=reflection_artifact,
                    cognitive_arc=arc_payload,
                    frame_kind=session.frame_kind,
                    user_message=user_message,
                    tuned_thresholds=tuned_thresholds,
                )
                session.artifacts["execution_artifact"] = execution_artifact
                session.ledger.extend(execution_session.export_ledger())
                if EXECUTION_RUNTIME_ID not in session.active_runtimes:
                    session.active_runtimes.append(EXECUTION_RUNTIME_ID)
                tuning_artifact = run_self_tune_invariants(
                    session.artifacts,
                    prior_tuning=ctx.get("cortex_invariant_tuning"),
                    tuned_thresholds=tuned_thresholds,
                )
                session.artifacts[TUNING_ARTIFACT_KEY] = tuning_artifact

    if arc_payload:
        session.artifacts["cognitive_arc"] = arc_payload

    return session


def nova_speaking_adapter(
    session: NovaCognitiveSession,
    speak_body: str,
    *,
    include_update: bool = False,
) -> str:
    """Wrap Speaking Runtime around speak body, ingesting deliberation artifacts."""
    runtime_session = SpeakingRuntimeSession(
        user_message=session.user_message,
        context=dict(session.context or {}),
    )
    runtime_session.frame_kind = session.frame_kind  # type: ignore[assignment]

    build_listen_utterance(runtime_session)
    build_frame_utterance(runtime_session)

    plan_sections = ["direct answer", "alignment check"]
    focus_artifact = session.artifacts.get("focus_artifact")
    if isinstance(focus_artifact, dict) and focus_artifact.get("primary_focus"):
        plan_sections = ["focus summary", "direct answer", "alignment check"]
    decision = session.artifacts.get("decision_object")
    if isinstance(decision, dict):
        plan_sections = ["focus summary", "decision summary", "rationale", "alternatives considered"]
    planning = session.artifacts.get("planning_artifact")
    if isinstance(planning, dict) and planning.get("steps"):
        plan_sections = ["arc plan", "focus summary", "direct answer", "alignment check"]
    build_plan_utterance(runtime_session, sections=plan_sections)

    body = str(speak_body or "").strip()
    if isinstance(focus_artifact, dict) and focus_artifact.get("primary_focus"):
        focus_block = f"Focus: {focus_artifact['primary_focus']}"
        body = f"{focus_block}\n\n{body}".strip() if body else focus_block
    if isinstance(decision, dict):
        chosen = decision.get("chosen_option")
        rationale = decision.get("rationale")
        alts = decision.get("alternatives") or []
        winning = decision.get("winning_criteria") or []
        decision_block = (
            f"Decision: {chosen}\n"
            f"Rationale: {rationale}\n"
            f"Alternatives considered: {', '.join(str(a) for a in alts)}"
        )
        if winning:
            decision_block += f"\nTop criteria: {', '.join(str(item) for item in winning)}"
        body = f"{decision_block}\n\n{body}".strip()

    delivered = "a decision-aware answer" if decision else "a direct answer"
    build_check_utterance(runtime_session, delivered_summary=delivered)

    reflection = session.artifacts.get("reflection_artifact")
    planning = session.artifacts.get("planning_artifact")
    tuning_note = ""
    if isinstance(planning, dict) and planning.get("next_action"):
        tuning_note = str(planning["next_action"])
    elif isinstance(reflection, dict):
        adjustments = reflection.get("adjustments") or []
        if adjustments:
            tuning_note = str(adjustments[0])
    if include_update and tuning_note:
        build_update_utterance(runtime_session, tuning_note=tuning_note)

    return compose_reply(
        runtime_session,
        body,
        include_update=include_update,
        delivered_summary=delivered,
    )


def configure_nova_cognitive_turn(
    session,
    request_payload: dict[str, Any] | None,
    user_message: str,
    *,
    companion_turn: bool = False,
) -> NovaCognitiveSession | None:
    """Configure and run Nova cognitive runtimes for a Jarvis session turn."""
    payload = dict(request_payload or {})
    if "cognitive_runtime" in payload and not payload.get("cognitive_runtime"):
        session.metadata["cognitive_runtime_enabled"] = False
        return None

    enabled = bool(payload.get("cognitive_runtime", companion_turn))
    session.metadata["cognitive_runtime_enabled"] = bool(enabled)
    if not enabled:
        return None

    board = session.metadata.get("memory_board_snapshot") or session.metadata.get("memory_board")
    memory_cues = normalize_cortex_memory_cues(
        board if isinstance(board, dict) else session.metadata,
        companion_turn=companion_turn,
        metadata=session.metadata,
    )
    session.metadata["cortex_memory_cues"] = memory_cues
    ctx = {
        "response_mode": (session.metadata.get("turn_contract") or {}).get("resolved_mode"),
        "companion_turn": companion_turn,
        "cognitive_runtime_enabled": True,
        "speaking_runtime_enabled": bool(session.metadata.get("speaking_runtime_enabled")),
        "memory_cues": memory_cues,
        "require_speaking": bool(session.metadata.get("speaking_runtime_enabled")),
        "nova_face": dict(session.metadata.get("nova_face") or {}),
        "deliberation_llm": bool(session.metadata.get("deliberation_llm_enabled")),
        "deliberate_fn": session.metadata.get("deliberate_fn"),
        "policy_status": dict(session.metadata.get("policy_status") or {}),
        "policy_posture": (session.metadata.get("policy_status") or {}).get("posture"),
        "cortex_fast_path": bool(
            payload.get("cortex_fast_path") or session.metadata.get("cortex_fast_path")
        ),
    }
    arc = start_or_continue_arc(
        session.metadata,
        user_message=user_message,
        companion_turn=companion_turn,
    )
    ctx.update(arc_context_for_turn(arc))
    ctx["cognitive_arc"] = arc.to_dict()
    ctx["tuned_thresholds"] = load_tuned_thresholds(session.metadata)
    ctx["cortex_invariant_tuning"] = dict(session.metadata.get("cortex_invariant_tuning") or {})
    store_root = resolve_narrative_store_root(payload.get("nova_narrative_store"))
    intent_store_root = resolve_intent_store_root(payload.get("nova_intent_store"))
    if _should_persist_narrative(session, payload, companion_turn=companion_turn):
        rehydrate_nova_narrative(session, store_root=store_root, nova_face=ctx.get("nova_face"))
    if _should_persist_intent(session, payload, companion_turn=companion_turn):
        rehydrate_nova_intent(session, store_root=intent_store_root, nova_face=ctx.get("nova_face"))
    prior_intent = load_nova_intent(session.metadata)
    ctx.update(intent_context_for_lobes(prior_intent))
    cog_session = run_nova_cognitive_turn(user_message, context=ctx)
    _persist_memory_compression(session, cog_session)
    _persist_invariant_tuning(session, cog_session)
    arc = append_arc_turn(arc, user_message=user_message, cog_session=cog_session)
    persist_cortex_arc(session, arc)
    session.metadata["cortex_arc"] = arc.to_dict()
    if _should_run_intent(session, companion_turn=companion_turn, payload=payload):
        intent = run_intent_turn(
            cog_session=cog_session,
            prior_intent=prior_intent,
            prior_narrative=load_nova_narrative(session.metadata),
        )
        persist_nova_intent(session, intent)
        cog_session.artifacts["intent_artifact"] = intent
        if _should_persist_intent(session, payload, companion_turn=companion_turn):
            flush_nova_intent_store(
                session,
                intent,
                store_root=intent_store_root,
                nova_face=ctx.get("nova_face"),
            )
    if _should_run_narrative(session, companion_turn=companion_turn, payload=payload):
        cog_session.artifacts["cognitive_arc"] = arc.to_dict()
        narrative = run_narrative_turn(
            user_message,
            cog_session=cog_session,
            prior_narrative=load_nova_narrative(session.metadata),
            nova_face=ctx.get("nova_face"),
        )
        persist_nova_narrative(session, narrative)
        cog_session.artifacts["narrative_artifact"] = narrative
        if _should_persist_narrative(session, payload, companion_turn=companion_turn):
            flush_nova_narrative_store(
                session,
                narrative,
                store_root=store_root,
                nova_face=ctx.get("nova_face"),
            )
    intent_artifact = cog_session.artifacts.get("intent_artifact")
    narrative_artifact = cog_session.artifacts.get("narrative_artifact")
    if isinstance(intent_artifact, dict) or isinstance(narrative_artifact, dict):
        reconciliation = reconcile_intent_narrative(
            intent_artifact if isinstance(intent_artifact, dict) else None,
            narrative_artifact if isinstance(narrative_artifact, dict) else None,
            prior_intent=prior_intent if isinstance(prior_intent, dict) else None,
        )
        cog_session.artifacts["reconciliation_artifact"] = reconciliation
        session.metadata["intent_narrative_reconciliation"] = reconciliation
    session.metadata["nova_cognitive_session"] = cog_session.to_dict()
    session.metadata["cognitive_runtime_ledger"] = list(cog_session.ledger)
    session.metadata["cognitive_runtime_artifacts"] = dict(cog_session.artifacts)
    turn_contract = dict(session.metadata.get("turn_contract") or {})
    turn_contract["cognitive_runtime_enabled"] = True
    turn_contract["active_cognitive_runtimes"] = list(cog_session.active_runtimes)
    session.metadata["turn_contract"] = turn_contract
    return cog_session


def apply_nova_cognitive_finalization(
    session,
    user_message: str,
    response_text: str,
    *,
    response_trace: dict[str, Any] | None = None,
) -> str:
    """Apply speaking adapter when cognitive runtime is active."""
    if not session.metadata.get("cognitive_runtime_enabled"):
        return response_text

    stored = dict(session.metadata.get("nova_cognitive_session") or {})
    if not stored:
        return response_text

    cog_session = NovaCognitiveSession(
        user_message=user_message,
        context=dict(stored.get("context") or {}),
        session_id=str(stored.get("session_id") or ""),
        active_runtimes=list(stored.get("active_runtimes") or []),
        frame_kind=str(stored.get("frame_kind") or infer_frame_kind(user_message)),
        ledger=list(stored.get("ledger") or []),
        artifacts=dict(stored.get("artifacts") or {}),
    )

    speaking_required = SPEAKING_RUNTIME_ID in cog_session.active_runtimes
    if not speaking_required:
        return response_text

    companion_turn = bool((cog_session.context or {}).get("companion_turn"))
    reflection = cog_session.artifacts.get("reflection_artifact")
    if isinstance(reflection, dict):
        merged = merge_post_reply_reflection(
            reflection,
            speak_body=response_text,
            focus_artifact=cog_session.artifacts.get("focus_artifact"),
            decision_object=cog_session.artifacts.get("decision_object"),
        )
        cog_session.artifacts["reflection_artifact"] = merged
        session.metadata["cortex_reflection"] = merged

    planning = cog_session.artifacts.get("planning_artifact")
    execution = cog_session.artifacts.get("execution_artifact")
    tuned_thresholds = load_tuned_thresholds(session.metadata)
    if isinstance(execution, dict) and isinstance(planning, dict):
        merged_exec = merge_post_reply_execution(
            execution,
            speak_body=response_text,
            planning_artifact=planning,
            focus_artifact=cog_session.artifacts.get("focus_artifact"),
            cognitive_arc=dict(session.metadata.get("cortex_arc") or cog_session.artifacts.get("cognitive_arc") or {}),
            tuned_thresholds=tuned_thresholds,
        )
        cog_session.artifacts["execution_artifact"] = merged_exec
        session.metadata["cortex_execution"] = merged_exec
        tuning_artifact = run_self_tune_invariants(
            cog_session.artifacts,
            prior_tuning=session.metadata.get("cortex_invariant_tuning"),
            tuned_thresholds=tuned_thresholds,
        )
        cog_session.artifacts[TUNING_ARTIFACT_KEY] = tuning_artifact
        session.metadata["cortex_invariant_tuning"] = tuning_artifact
        session.metadata["nova_cognitive_session"] = cog_session.to_dict()

    wrapped = nova_speaking_adapter(
        cog_session,
        response_text,
        include_update=companion_turn and isinstance(reflection, dict),
    )
    focus_artifact = cog_session.artifacts.get("focus_artifact")
    validation = verify_reply(
        wrapped,
        focus_artifact=focus_artifact if isinstance(focus_artifact, dict) else None,
    )
    trace_payload = {
        "family_id": NOVA_COGNITIVE_FAMILY_ID,
        "wrapped": True,
        "valid": validation.get("valid"),
        "issues": list(validation.get("issues") or []),
        "constraints_checked": list(validation.get("constraints_checked") or []),
        "active_runtimes": list(cog_session.active_runtimes),
        "artifacts": dict(cog_session.artifacts),
        "ledger_count": len(cog_session.ledger),
    }
    session.metadata["nova_cognitive_summary"] = trace_payload
    if isinstance(response_trace, dict):
        response_trace["nova_cognitive"] = trace_payload
    return wrapped


def summarize_cognitive_runtime_state(session) -> dict[str, Any] | None:
    """Project cognitive runtime state for API payloads."""
    stored = session.metadata.get("nova_cognitive_session")
    summary = session.metadata.get("nova_cognitive_summary")
    if not stored and not summary:
        return None
    payload = {
        "enabled": bool(session.metadata.get("cognitive_runtime_enabled")),
        "family_id": NOVA_COGNITIVE_FAMILY_ID,
    }
    if isinstance(stored, dict):
        payload.update(
            {
                "session_id": stored.get("session_id"),
                "frame_kind": stored.get("frame_kind"),
                "active_runtimes": stored.get("active_runtimes"),
                "ledger_count": len(stored.get("ledger") or []),
            }
        )
    arc = session.metadata.get("cortex_arc")
    if isinstance(arc, dict):
        payload["cortex_arc_id"] = arc.get("arc_id")
        payload["cortex_arc_turn_count"] = arc.get("turn_count")
        payload["cortex_arc_status"] = arc.get("status")
        payload["cortex_arc_goal_type"] = arc.get("goal_type")
    if isinstance(summary, dict):
        payload["speaking_valid"] = summary.get("valid")
        payload["speaking_issues"] = summary.get("issues")
    narrative = session.metadata.get("nova_narrative")
    if isinstance(narrative, dict):
        payload["nova_narrative_story"] = narrative.get("active_story")
        payload["nova_narrative_chapter"] = narrative.get("current_chapter")
        store = session.metadata.get("nova_narrative_store")
        if isinstance(store, dict):
            payload["nova_narrative_id"] = store.get("narrative_id")
            payload["nova_narrative_turn_count"] = store.get("turn_count")
    intent = session.metadata.get("nova_intent")
    if isinstance(intent, dict):
        payload["nova_intent_agency_note"] = intent.get("agency_note")
        payload["nova_intent_commitment_count"] = len(
            [c for c in intent.get("active_commitments") or [] if c.get("status") == "active"]
        )
        store = session.metadata.get("nova_intent_store")
        if isinstance(store, dict):
            payload["nova_intent_id"] = store.get("intent_id")
            payload["nova_intent_turn_count"] = store.get("turn_count")
    return payload


def _should_run_intent(session, *, companion_turn: bool, payload: dict[str, Any]) -> bool:
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return False
    if payload.get("nova_intent") is False:
        metadata["nova_intent_enabled"] = False
        return False
    enabled = payload.get("nova_intent", companion_turn or metadata.get("cognitive_runtime_enabled"))
    metadata["nova_intent_enabled"] = bool(enabled)
    return bool(enabled)


def _should_persist_intent(session, payload: dict[str, Any], *, companion_turn: bool) -> bool:
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return False
    if payload.get("nova_intent_persist") is False:
        metadata["nova_intent_persist"] = False
        return False
    default = companion_turn or bool(metadata.get("nova_intent_persist", True))
    enabled = bool(payload.get("nova_intent_persist", default))
    metadata["nova_intent_persist"] = enabled
    return enabled


def _should_run_narrative(session, *, companion_turn: bool, payload: dict[str, Any]) -> bool:
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return False
    if payload.get("nova_narrative") is False:
        metadata["nova_narrative_enabled"] = False
        return False
    enabled = payload.get("nova_narrative", companion_turn or metadata.get("cognitive_runtime_enabled"))
    metadata["nova_narrative_enabled"] = bool(enabled)
    return bool(enabled)


def _should_persist_narrative(session, payload: dict[str, Any], *, companion_turn: bool) -> bool:
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return False
    if payload.get("nova_narrative_persist") is False:
        metadata["nova_narrative_persist"] = False
        return False
    default = companion_turn or bool(metadata.get("nova_narrative_persist", True))
    enabled = bool(payload.get("nova_narrative_persist", default))
    metadata["nova_narrative_persist"] = enabled
    return enabled


def _persist_invariant_tuning(session, cog_session: NovaCognitiveSession) -> None:
    tuning = cog_session.artifacts.get(TUNING_ARTIFACT_KEY)
    if not isinstance(tuning, dict):
        return
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return
    metadata["cortex_invariant_tuning"] = tuning


def _persist_memory_compression(session, cog_session: NovaCognitiveSession) -> None:
    memory_artifact = dict(cog_session.artifacts.get("memory_artifact") or {})
    compressed = list(memory_artifact.get("compressed_episodic") or [])
    if not compressed:
        return
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return
    metadata["cortex_episodic_memory"] = [
        {
            "id": f"compressed-{index}",
            "text": str(item.get("summary") or ""),
            "memory_kind": "episodic",
            "source": "compressed_episode",
        }
        for index, item in enumerate(compressed)
        if isinstance(item, dict) and item.get("summary")
    ]


def _should_run_reflection(ctx: dict[str, Any], session: NovaCognitiveSession) -> bool:
    if bool(ctx.get("companion_turn")):
        return True
    return bool(session.artifacts)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered
