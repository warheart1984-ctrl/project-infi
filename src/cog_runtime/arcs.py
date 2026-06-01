"""Cortex cognitive arcs — multi-turn continuity across Nova lobes."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

ARC_RUNTIME_VERSION = "1.3"
MAX_ARC_TURNS = 12
MAX_OPEN_THREADS = 5
MAX_SUBGOALS = 4
GOAL_TYPES = ("decision", "continuity", "exploration", "repair", "general")
GOAL_CLOSURE_STATUSES = ("open", "subgoals_closed", "parent_closed")


@dataclass
class CognitiveArc:
    """Bounded multi-turn cognitive arc spanning several cortex turns."""

    arc_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    goal: str = ""
    root_goal: str = ""
    goal_type: str = "general"
    subgoals: list[str] = field(default_factory=list)
    current_subgoal: str = ""
    goal_hierarchy: list[dict[str, Any]] = field(default_factory=list)
    closed_subgoals: list[str] = field(default_factory=list)
    goal_closure_status: str = "open"
    status: str = "active"
    turn_count: int = 0
    turns: list[dict[str, Any]] = field(default_factory=list)
    open_threads: list[str] = field(default_factory=list)
    closed_threads: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "arc_id": self.arc_id,
            "goal": self.goal,
            "root_goal": self.root_goal,
            "goal_type": self.goal_type,
            "subgoals": list(self.subgoals),
            "current_subgoal": self.current_subgoal,
            "goal_hierarchy": list(self.goal_hierarchy),
            "closed_subgoals": list(self.closed_subgoals),
            "goal_closure_status": self.goal_closure_status,
            "arc_version": ARC_RUNTIME_VERSION,
            "status": self.status,
            "turn_count": self.turn_count,
            "turns": list(self.turns),
            "open_threads": list(self.open_threads),
            "closed_threads": list(self.closed_threads),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> CognitiveArc | None:
        if not isinstance(payload, dict) or not payload.get("arc_id"):
            return None
        goal_type = str(payload.get("goal_type") or "general")
        if goal_type not in GOAL_TYPES:
            goal_type = "general"
        closure_status = str(payload.get("goal_closure_status") or "open")
        if closure_status not in GOAL_CLOSURE_STATUSES:
            closure_status = "open"
        return cls(
            arc_id=str(payload.get("arc_id") or ""),
            goal=str(payload.get("goal") or ""),
            root_goal=str(payload.get("root_goal") or payload.get("goal") or ""),
            goal_type=goal_type,
            subgoals=list(payload.get("subgoals") or []),
            current_subgoal=str(payload.get("current_subgoal") or ""),
            goal_hierarchy=list(payload.get("goal_hierarchy") or []),
            closed_subgoals=list(payload.get("closed_subgoals") or []),
            goal_closure_status=closure_status,
            status=str(payload.get("status") or "active"),
            turn_count=int(payload.get("turn_count") or 0),
            turns=list(payload.get("turns") or []),
            open_threads=list(payload.get("open_threads") or []),
            closed_threads=list(payload.get("closed_threads") or []),
        )


def infer_arc_goal_type(
    user_message: str,
    *,
    frame_kind: str = "general",
    focus_artifact: dict[str, Any] | None = None,
    decision_object: dict[str, Any] | None = None,
) -> str:
    lowered = (user_message or "").lower()
    if frame_kind == "decision" or decision_object:
        return "decision"
    if any(token in lowered for token in ("fix", "debug", "repair", "broken", "error")):
        return "repair"
    if any(token in lowered for token in ("research", "explore", "compare", "learn about")):
        return "exploration"
    if any(token in lowered for token in ("remember", "continuity", "last time", "earlier")):
        return "continuity"
    if focus_artifact and focus_artifact.get("primary_focus"):
        if frame_kind in {"instruction", "implementation", "design"}:
            return "exploration"
    return "general"


def infer_arc_goal(
    user_message: str,
    *,
    focus_artifact: dict[str, Any] | None = None,
    frame_kind: str = "general",
    goal_type: str = "general",
) -> str:
    primary = str((focus_artifact or {}).get("primary_focus") or "").strip()
    if primary:
        return primary[:160]
    clipped = " ".join((user_message or "").split()).strip()[:120]
    if clipped:
        return clipped
    return f"Continue {goal_type} {frame_kind} thread"


def build_goal_hierarchy(
    *,
    root_goal: str,
    goal_type: str,
    focus_artifact: dict[str, Any] | None = None,
    planning_artifact: dict[str, Any] | None = None,
    closed_subgoals: list[str] | None = None,
) -> tuple[list[str], list[dict[str, Any]], str]:
    focus = dict(focus_artifact or {})
    planning = dict(planning_artifact or {})
    closed_ids = set(closed_subgoals or [])

    subgoals: list[str] = []
    secondary = [str(item).strip() for item in (focus.get("secondary_focus") or []) if str(item).strip()]
    subgoals.extend(secondary[:2])

    for chain in list(planning.get("step_chains") or [])[:2]:
        label = str(chain.get("label") or chain.get("chain_id") or "chain")
        steps = list(chain.get("steps") or [])
        if steps:
            subgoals.append(f"{label}: {steps[0][:80]}")

    if goal_type == "decision" and focus.get("primary_focus"):
        subgoals.insert(0, f"Decide: {focus['primary_focus'][:80]}")

    subgoals = list(dict.fromkeys(subgoals))[:MAX_SUBGOALS]
    hierarchy = [
        {
            "level": 0,
            "goal": root_goal,
            "kind": "root",
            "goal_id": "root",
            "parent_id": None,
            "status": "open",
        }
    ]
    for index, subgoal in enumerate(subgoals, start=1):
        goal_id = f"subgoal-{index}"
        hierarchy.append(
            {
                "level": index,
                "goal": subgoal,
                "kind": "subgoal",
                "goal_id": goal_id,
                "parent_id": "root",
                "status": "closed" if goal_id in closed_ids else "open",
            }
        )

    open_subgoals = [node for node in hierarchy if node.get("kind") == "subgoal" and node.get("status") == "open"]
    current = open_subgoals[0]["goal"] if open_subgoals else root_goal
    return subgoals, hierarchy, current


def apply_goal_closure(
    arc: CognitiveArc,
    *,
    execution: dict[str, Any] | None,
    planning: dict[str, Any] | None,
) -> None:
    """Close child subgoals on successful execution; bubble closure to parent root."""
    execution = dict(execution or {})
    planning = dict(planning or {})
    if not execution.get("execution_complete"):
        return

    next_action = str(planning.get("next_action") or "").strip()
    closed_ids = list(arc.closed_subgoals)

    for node in arc.goal_hierarchy:
        if node.get("kind") != "subgoal" or node.get("status") != "open":
            continue
        goal_text = str(node.get("goal") or "")
        goal_id = str(node.get("goal_id") or "")
        if next_action and (goal_text in next_action or next_action in goal_text):
            node["status"] = "closed"
            if goal_id and goal_id not in closed_ids:
                closed_ids.append(goal_id)

    arc.closed_subgoals = list(dict.fromkeys(closed_ids))[:MAX_SUBGOALS]

    open_children = [
        node
        for node in arc.goal_hierarchy
        if node.get("kind") == "subgoal" and node.get("status") == "open"
    ]
    if not open_children and arc.goal_hierarchy:
        arc.goal_closure_status = "subgoals_closed"
        for node in arc.goal_hierarchy:
            if node.get("kind") == "root" and node.get("status") == "open":
                node["status"] = "closed"
                arc.goal_closure_status = "parent_closed"
                break
    else:
        arc.goal_closure_status = "open"


def should_continue_arc(
    arc: CognitiveArc | None,
    *,
    user_message: str,
    companion_turn: bool = False,
    goal_type: str | None = None,
) -> bool:
    if arc is None or arc.status != "active":
        return False
    if goal_type and arc.goal_type not in {goal_type, "general"}:
        return False
    if companion_turn and arc.turn_count > 0:
        return True
    if not arc.open_threads:
        return companion_turn
    lowered = user_message.lower()
    return any(thread.lower() in lowered for thread in arc.open_threads[:3])


def load_cortex_arc(metadata: dict[str, Any] | None) -> CognitiveArc | None:
    payload = dict(metadata or {}).get("cortex_arc")
    return CognitiveArc.from_dict(payload)


def start_or_continue_arc(
    metadata: dict[str, Any] | None,
    *,
    user_message: str,
    focus_artifact: dict[str, Any] | None = None,
    frame_kind: str = "general",
    companion_turn: bool = False,
    decision_object: dict[str, Any] | None = None,
    force_new: bool = False,
) -> CognitiveArc:
    goal_type = infer_arc_goal_type(
        user_message,
        frame_kind=frame_kind,
        focus_artifact=focus_artifact,
        decision_object=decision_object,
    )
    existing = None if force_new else load_cortex_arc(metadata)
    if existing and should_continue_arc(
        existing,
        user_message=user_message,
        companion_turn=companion_turn,
        goal_type=goal_type,
    ):
        if existing.goal_type == "general" and goal_type != "general":
            existing.goal_type = goal_type
        return existing

    goal = infer_arc_goal(
        user_message,
        focus_artifact=focus_artifact,
        frame_kind=frame_kind,
        goal_type=goal_type,
    )
    subgoals, hierarchy, current = build_goal_hierarchy(
        root_goal=goal,
        goal_type=goal_type,
        focus_artifact=focus_artifact,
    )
    return CognitiveArc(
        goal=goal,
        root_goal=goal,
        goal_type=goal_type,
        subgoals=subgoals,
        current_subgoal=current,
        goal_hierarchy=hierarchy,
    )


def arc_context_for_turn(arc: CognitiveArc | None) -> dict[str, Any]:
    if arc is None:
        return {}
    prior = arc.turns[-1] if arc.turns else {}
    return {
        "arc_id": arc.arc_id,
        "arc_goal": arc.goal,
        "arc_root_goal": arc.root_goal,
        "arc_goal_type": arc.goal_type,
        "arc_subgoals": list(arc.subgoals),
        "arc_current_subgoal": arc.current_subgoal,
        "arc_goal_hierarchy": list(arc.goal_hierarchy),
        "arc_goal_closure_status": arc.goal_closure_status,
        "arc_closed_subgoals": list(arc.closed_subgoals),
        "arc_turn_count": arc.turn_count,
        "arc_status": arc.status,
        "arc_open_threads": list(arc.open_threads),
        "prior_primary_focus": prior.get("primary_focus"),
        "prior_next_action": prior.get("next_action"),
        "prior_execution_status": prior.get("execution_status"),
        "prior_active_chain_id": prior.get("active_chain_id"),
        "prior_chain_step_index": prior.get("chain_step_index"),
        "prior_rollback_applied": prior.get("rollback_applied"),
    }


def append_arc_turn(
    arc: CognitiveArc,
    *,
    user_message: str,
    cog_session: Any,
) -> CognitiveArc:
    artifacts = dict(getattr(cog_session, "artifacts", {}) or {})
    focus = dict(artifacts.get("focus_artifact") or {})
    reflection = dict(artifacts.get("reflection_artifact") or {})
    planning = dict(artifacts.get("planning_artifact") or {})
    execution = dict(artifacts.get("execution_artifact") or {})

    if arc.turn_count == 0 and not arc.goal:
        arc.goal = infer_arc_goal(
            user_message,
            focus_artifact=focus,
            frame_kind=str(getattr(cog_session, "frame_kind", "") or "general"),
            goal_type=arc.goal_type,
        )
        arc.root_goal = arc.goal

    subgoals, hierarchy, current = build_goal_hierarchy(
        root_goal=arc.root_goal or arc.goal,
        goal_type=arc.goal_type,
        focus_artifact=focus,
        planning_artifact=planning,
        closed_subgoals=arc.closed_subgoals,
    )
    arc.subgoals = subgoals
    arc.goal_hierarchy = hierarchy
    arc.current_subgoal = current
    apply_goal_closure(arc, execution=execution, planning=planning)

    turn_record = {
        "turn_index": arc.turn_count + 1,
        "user_message": user_message[:160],
        "frame_kind": getattr(cog_session, "frame_kind", "general"),
        "goal_type": arc.goal_type,
        "root_goal": arc.root_goal,
        "current_subgoal": arc.current_subgoal,
        "goal_closure_status": arc.goal_closure_status,
        "primary_focus": focus.get("primary_focus"),
        "alignment": reflection.get("alignment"),
        "next_action": planning.get("next_action") or (reflection.get("adjustments") or [None])[0],
        "execution_status": execution.get("verification_status"),
        "active_chain_id": planning.get("active_chain_id"),
        "chain_step_index": planning.get("chain_step_index"),
        "rollback_applied": execution.get("rollback_applied"),
        "rollback_policy": execution.get("rollback_policy"),
        "session_id": getattr(cog_session, "session_id", ""),
    }
    arc.turns.append(turn_record)
    arc.turn_count += 1

    open_threads = list(arc.open_threads)
    for hint in reflection.get("next_turn_hints") or []:
        hint_text = str(hint).strip()
        if hint_text and hint_text not in open_threads:
            open_threads.append(hint_text)
    for step in planning.get("steps") or []:
        step_text = str(step).strip()
        if step_text and step_text not in open_threads:
            open_threads.append(step_text)
    for subgoal in arc.subgoals[:2]:
        if subgoal not in open_threads:
            open_threads.append(subgoal)
    arc.open_threads = open_threads[:MAX_OPEN_THREADS]

    if execution.get("execution_complete") and planning.get("next_action"):
        closed = str(planning.get("next_action"))
        if closed in arc.open_threads:
            arc.open_threads = [item for item in arc.open_threads if item != closed]
            arc.closed_threads = list(dict.fromkeys(list(arc.closed_threads) + [closed]))[:MAX_OPEN_THREADS]
    elif execution.get("rollback_applied") and execution.get("rollback_target"):
        closed = str(execution.get("bound_action") or "")
        if closed and closed in arc.open_threads:
            arc.open_threads = [item for item in arc.open_threads if item != closed]

    if arc.turn_count >= MAX_ARC_TURNS:
        arc.status = "closed"
    return arc


def persist_cortex_arc(session, arc: CognitiveArc | None) -> None:
    if session is None or arc is None:
        return
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return
    metadata["cortex_arc"] = arc.to_dict()


def validate_cognitive_arc(arc: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if not str(arc.get("arc_id") or "").strip():
        issues.append("missing_arc_id")
    if arc.get("status") not in {"active", "closed"}:
        issues.append("invalid_status")
    goal_type = str(arc.get("goal_type") or "")
    if goal_type not in GOAL_TYPES:
        issues.append("invalid_goal_type")
    if not str(arc.get("root_goal") or arc.get("goal") or "").strip():
        issues.append("missing_root_goal")
    hierarchy = arc.get("goal_hierarchy")
    if not isinstance(hierarchy, list):
        issues.append("goal_hierarchy_not_list")
    subgoals = arc.get("subgoals")
    if subgoals is not None and not isinstance(subgoals, list):
        issues.append("subgoals_not_list")
    closed_subgoals = arc.get("closed_subgoals")
    if closed_subgoals is not None and not isinstance(closed_subgoals, list):
        issues.append("closed_subgoals_not_list")
    closure_status = str(arc.get("goal_closure_status") or "open")
    if closure_status not in GOAL_CLOSURE_STATUSES:
        issues.append("invalid_goal_closure_status")
    turns = arc.get("turns")
    if not isinstance(turns, list):
        issues.append("turns_not_list")
    elif len(turns) > MAX_ARC_TURNS:
        issues.append("too_many_turns")
    return {"valid": not issues, "issues": issues}
