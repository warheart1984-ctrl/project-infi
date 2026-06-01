"""Persistent mission board for AAIS.

Mission Board gives Jarvis a durable objective layer that lives above any
single turn. Missions can be focused, blocked, queued, or completed and can be
linked back to an active chat session.
"""

from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
import json
import os
from pathlib import Path
import shutil
import threading
import uuid

from src.cisiv import CISIV_STAGE_SEQUENCE, normalize_cisiv_stage
from src.verification_gate import (
    GateDecision,
    evaluate_verification_gate,
    normalize_verification_results,
)


MISSION_STATUSES = {"active", "eligible", "queued", "blocked", "done"}
MISSION_CRITIC_STATUSES = {"advancing", "mixed", "blocked", "done"}
STATUS_SORT_ORDER = {"active": 0, "eligible": 1, "blocked": 2, "queued": 3, "done": 4}
MISSION_PRESETS = {
    "fix_broken_route": {
        "id": "fix_broken_route",
        "label": "Fix Broken Route",
        "summary": "Ground a failing page against the running app, local files, and the safest verification loop.",
        "title": "Fix broken route",
        "objective": "Find why a route is broken, ground it against the running UI and local files, and ship the safest fix.",
        "next_step": "Run Browser Verify on the failing route and inspect the strongest matched file.",
        "tags": ["browser", "debug", "ui"],
    },
    "ship_feature": {
        "id": "ship_feature",
        "label": "Ship Feature",
        "summary": "Turn a rough feature request into the smallest working slice and verify it end to end.",
        "title": "Ship feature",
        "objective": "Break the feature into the smallest working slice, implement it, and verify the flow before moving on.",
        "next_step": "Define the smallest shippable slice and the first file or route to touch.",
        "tags": ["builder", "feature", "ship"],
    },
    "train_small_llm": {
        "id": "train_small_llm",
        "label": "Train Small LLM",
        "summary": "Run a small-model training loop with dataset, fine-tune, and eval work connected to one mission.",
        "title": "Train small LLM",
        "objective": "Prepare the dataset, run a realistic small-model training pass, and evaluate whether the model actually improved.",
        "next_step": "Lock the dataset shape and decide the next fine-tune or eval pass.",
        "tags": ["training", "dataset", "evaluation"],
    },
    "research_stack_choice": {
        "id": "research_stack_choice",
        "label": "Research Stack Choice",
        "summary": "Compare stack options, keep uncertainty honest, and land on one recommendation.",
        "title": "Research stack choice",
        "objective": "Compare the strongest stack options with clear tradeoffs and choose one grounded recommendation.",
        "next_step": "Gather the top two or three options and compare them against the real constraints.",
        "tags": ["research", "comparison", "decision"],
    },
}


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def _clip_text(value: str | None, limit: int = 220) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _normalize_status(value: str | None) -> str:
    cleaned = " ".join(str(value or "active").lower().split()).strip().replace("-", "_")
    if cleaned == "completed":
        return "done"
    return cleaned if cleaned in MISSION_STATUSES else "active"


def _normalize_blocker(value: str | None, *, status: str | None) -> str | None:
    clipped = _clip_text(value, limit=240)
    return clipped if _normalize_status(status) == "blocked" and clipped else None


def _normalize_tags(values) -> list[str]:
    if isinstance(values, str):
        values = [tag.strip() for tag in values.split(",")]
    normalized: list[str] = []
    for value in values or []:
        tag = " ".join(str(value or "").split()).strip()
        if tag and tag not in normalized:
            normalized.append(tag)
    return normalized[:8]


def _normalize_links(values) -> list[dict]:
    normalized: list[dict] = []
    for value in values or []:
        if not isinstance(value, dict):
            continue
        link_value = str(value.get("value") or "").strip()
        if not link_value:
            continue
        normalized.append(
            {
                "kind": str(value.get("kind") or "context").strip().lower() or "context",
                "label": str(value.get("label") or link_value).strip() or link_value,
                "value": link_value,
            }
        )
    return normalized[:10]


def _normalize_activity(values, *, default_cisiv_stage: str = "implementation") -> list[dict]:
    normalized: list[dict] = []
    for value in values or []:
        if not isinstance(value, dict):
            continue
        summary = _clip_text(value.get("summary"), limit=220)
        if not summary:
            continue
        normalized.append(
            {
                "id": str(value.get("id") or uuid.uuid4().hex),
                "kind": str(value.get("kind") or "note").strip().lower() or "note",
                "summary": summary,
                "timestamp": value.get("timestamp") or _utc_now_iso(),
                "cisiv_stage": normalize_cisiv_stage(value.get("cisiv_stage"), default=default_cisiv_stage),
            }
        )
    return normalized[:12]


def _normalize_history(values, *, default_cisiv_stage: str = "concept") -> list[dict]:
    normalized: list[dict] = []
    for value in values or []:
        if not isinstance(value, dict):
            continue
        summary = _clip_text(value.get("summary"), limit=240)
        if not summary:
            continue
        normalized.append(
            {
                "id": str(value.get("id") or uuid.uuid4().hex),
                "kind": str(value.get("kind") or "note").strip().lower() or "note",
                "summary": summary,
                "timestamp": value.get("timestamp") or _utc_now_iso(),
                "status": str(value.get("status") or "").strip().lower() or None,
                "source": str(value.get("source") or "").strip().lower() or None,
                "label": _clip_text(value.get("label"), limit=110) or None,
                "cisiv_stage": normalize_cisiv_stage(value.get("cisiv_stage"), default=default_cisiv_stage),
            }
        )
    return normalized[:160]


def _normalize_critic(value) -> dict | None:
    if not isinstance(value, dict):
        return None
    status = str(value.get("status") or "mixed").strip().lower()
    if status not in MISSION_CRITIC_STATUSES:
        status = "mixed"
    try:
        score = round(max(0.0, min(1.0, float(value.get("score", 0.0)))), 2)
    except (TypeError, ValueError):
        score = 0.0
    try:
        confidence = round(max(0.0, min(1.0, float(value.get("confidence", 0.0)))), 2)
    except (TypeError, ValueError):
        confidence = 0.0
    suggested_status = _normalize_status(value.get("suggested_mission_status")) if value.get("suggested_mission_status") else None
    wins = [_clip_text(item, limit=110) for item in value.get("wins") or [] if str(item or "").strip()][:4]
    issues = [_clip_text(item, limit=110) for item in value.get("issues") or [] if str(item or "").strip()][:4]
    return {
        "source": str(value.get("source") or "reply").strip().lower() or "reply",
        "status": status,
        "score": score,
        "confidence": confidence,
        "cisiv_stage": normalize_cisiv_stage(value.get("cisiv_stage"), default="verification"),
        "summary": _clip_text(value.get("summary"), limit=240),
        "wins": wins,
        "issues": issues,
        "recommended_next": _clip_text(value.get("recommended_next"), limit=240),
        "suggested_mission_status": suggested_status,
        "reviewed_at": value.get("reviewed_at") or _utc_now_iso(),
    }


def _normalize_verification_gate(value) -> dict | None:
    if not isinstance(value, dict):
        return None
    decision = " ".join(str(value.get("decision") or "").split()).strip().upper()
    if decision not in {GateDecision.BLOCK.value, GateDecision.ELIGIBLE.value}:
        return None
    reasons = [_clip_text(item, limit=180) for item in value.get("reasons") or [] if str(item or "").strip()]
    failed_tests = [
        " ".join(str(item or "").split()).strip()
        for item in value.get("failed_tests") or []
        if " ".join(str(item or "").split()).strip()
    ]
    evaluated_at = str(value.get("evaluated_at") or _utc_now_iso())
    return {
        "decision": decision,
        "reasons": reasons[:24],
        "failed_tests": sorted(set(failed_tests)),
        "evaluated_at": evaluated_at,
    }


def _merge_links(existing, additions) -> list[dict]:
    merged = _normalize_links(existing)
    seen = {(item["kind"], item["value"]) for item in merged}
    for item in _normalize_links(additions):
        key = (item["kind"], item["value"])
        if key in seen:
            continue
        merged.append(item)
        seen.add(key)
    return merged[:10]


class MissionBoardController:
    """Persist and expose a lightweight mission/objective layer for Jarvis."""

    def __init__(self, runtime_dir: str | Path | None = None):
        self.runtime_dir = Path(runtime_dir or _default_runtime_dir())
        self._lock = threading.Lock()
        self._board = {
            "active_mission_id": None,
            "missions": [],
            "updated_at": _utc_now_iso(),
        }
        self._load_from_disk()

    @property
    def _state_path(self) -> Path:
        return self.runtime_dir / "mission-board.json"

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        with self._lock:
            self.runtime_dir = Path(runtime_dir)
            self._board = {
                "active_mission_id": None,
                "missions": [],
                "updated_at": _utc_now_iso(),
            }
            self._load_from_disk()

    def reset(self, persist: bool = True) -> dict:
        with self._lock:
            self._board = {
                "active_mission_id": None,
                "missions": [],
                "updated_at": _utc_now_iso(),
            }
            if persist:
                self._persist_locked()
            return self._snapshot_locked()

    def backup_state(self, destination: str | Path | None = None) -> Path:
        """Write a point-in-time backup of the current mission board state."""
        with self._lock:
            self.runtime_dir.mkdir(parents=True, exist_ok=True)
            backup_path = Path(destination) if destination else self.runtime_dir / "mission-board.backup.json"
            if self._state_path.exists():
                shutil.copy2(self._state_path, backup_path)
            else:
                backup_path.write_text(
                    json.dumps(self._board, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            return backup_path

    def snapshot(self, session_id: str | None = None, limit: int = 24) -> dict:
        with self._lock:
            from src.aais_ul_substrate import wrap_runtime_snapshot

            return wrap_runtime_snapshot(self._snapshot_locked(session_id=session_id, limit=limit))

    def list_presets(self) -> list[dict]:
        return [dict(preset) for preset in MISSION_PRESETS.values()]

    def create_mission(
        self,
        *,
        title: str | None,
        objective: str | None,
        next_step: str | None = None,
        blocker: str | None = None,
        status: str | None = "active",
        session_id: str | None = None,
        tags=None,
        links=None,
        focus: bool | None = None,
        cisiv_stage: str | None = None,
    ) -> dict:
        with self._lock:
            normalized_objective = _clip_text(objective, limit=1200)
            normalized_title = _clip_text(title, limit=110) or _clip_text(normalized_objective, limit=80)
            if not normalized_title and not normalized_objective:
                raise ValueError("Mission title or objective is required")

            normalized_status = _normalize_status(status)
            normalized_cisiv_stage = normalize_cisiv_stage(cisiv_stage, default="concept")
            mission_id = uuid.uuid4().hex
            now = _utc_now_iso()
            mission = {
                "id": mission_id,
                "title": normalized_title or "Untitled mission",
                "objective": normalized_objective,
                "status": normalized_status,
                "next_step": _clip_text(next_step, limit=240),
                "blocker": _normalize_blocker(blocker, status=normalized_status),
                "session_id": str(session_id or "").strip() or None,
                "tags": _normalize_tags(tags),
                "links": _normalize_links(links),
                "cisiv_stage": normalized_cisiv_stage,
                "activity": [],
                "history": [],
                "critic": None,
                "verification_gate": None,
                "created_at": now,
                "updated_at": now,
            }
            self._append_history_locked(
                mission,
                kind="mission_created",
                summary=f"Created mission '{mission['title']}'.",
                status=mission["status"],
                label=mission["title"],
                cisiv_stage=normalized_cisiv_stage,
            )
            self._board["missions"].append(mission)
            if focus or self._board.get("active_mission_id") is None or normalized_status == "active":
                self._board["active_mission_id"] = mission_id
            self._board["updated_at"] = now
            self._persist_locked()
            return self._snapshot_locked(session_id=session_id)

    def create_from_preset(
        self,
        preset_id: str,
        *,
        session_id: str | None = None,
        focus: bool = True,
        title: str | None = None,
        objective: str | None = None,
        next_step: str | None = None,
        cisiv_stage: str | None = None,
    ) -> dict:
        preset = MISSION_PRESETS.get(str(preset_id or "").strip().lower())
        if not preset:
            raise KeyError(preset_id)
        return self.create_mission(
            title=title or preset["title"],
            objective=objective or preset["objective"],
            next_step=next_step or preset["next_step"],
            session_id=session_id,
            tags=preset.get("tags"),
            focus=focus,
            status="active",
            cisiv_stage=cisiv_stage,
        )

    def update_mission(self, mission_id: str, **updates) -> dict:
        with self._lock:
            mission = self._find_mission_locked(mission_id)
            if not mission:
                raise KeyError(mission_id)
            touched_fields: list[str] = []

            if "title" in updates:
                title = _clip_text(updates.get("title"), limit=110)
                if title:
                    mission["title"] = title
                    touched_fields.append("title")
            if "objective" in updates:
                mission["objective"] = _clip_text(updates.get("objective"), limit=1200)
                touched_fields.append("objective")
            if "next_step" in updates:
                mission["next_step"] = _clip_text(updates.get("next_step"), limit=240)
                touched_fields.append("next_step")
            if "blocker" in updates:
                mission["blocker"] = _clip_text(updates.get("blocker"), limit=240)
                touched_fields.append("blocker")
            if "status" in updates:
                mission["status"] = _normalize_status(updates.get("status"))
                touched_fields.append("status")
            if "session_id" in updates:
                mission["session_id"] = str(updates.get("session_id") or "").strip() or None
                touched_fields.append("session")
            if "tags" in updates:
                mission["tags"] = _normalize_tags(updates.get("tags"))
                touched_fields.append("tags")
            if "links" in updates:
                mission["links"] = _merge_links([], updates.get("links"))
                touched_fields.append("links")
            if "cisiv_stage" in updates:
                mission["cisiv_stage"] = normalize_cisiv_stage(
                    updates.get("cisiv_stage"),
                    default=mission.get("cisiv_stage") or "concept",
                )
                touched_fields.append("cisiv_stage")
            if "activity" in updates:
                mission["activity"] = _normalize_activity(
                    updates.get("activity"),
                    default_cisiv_stage=mission.get("cisiv_stage") or "concept",
                )
                touched_fields.append("activity")
            if "critic" in updates:
                mission["critic"] = _normalize_critic(updates.get("critic"))
                touched_fields.append("critic")
            if "verification_gate" in updates:
                mission["verification_gate"] = _normalize_verification_gate(updates.get("verification_gate"))
                touched_fields.append("verification_gate")
            if "verification_results" in updates:
                verification_results = normalize_verification_results(updates.get("verification_results"))
                gate = evaluate_verification_gate(verification_results)
                mission["verification_gate"] = _normalize_verification_gate(
                    {
                        "decision": gate.decision.value,
                        "reasons": gate.reasons,
                        "failed_tests": gate.failed_tests,
                        "evaluated_at": _utc_now_iso(),
                    }
                )
                mission["status"] = (
                    "blocked" if gate.decision == GateDecision.BLOCK else "eligible"
                )
                mission["blocker"] = (
                    "; ".join(gate.reasons[:4]) if gate.decision == GateDecision.BLOCK else None
                )
                touched_fields.extend(["verification_results", "verification_gate", "status"])

            mission["blocker"] = _normalize_blocker(mission.get("blocker"), status=mission.get("status"))

            mission["updated_at"] = _utc_now_iso()
            if touched_fields:
                self._append_history_locked(
                    mission,
                    kind="mission_updated",
                    summary=f"Updated mission '{mission['title']}' ({', '.join(touched_fields[:5])}).",
                    status=mission.get("status"),
                    label=mission["title"],
                    cisiv_stage=mission.get("cisiv_stage"),
                )
            if mission["status"] == "done" and self._board.get("active_mission_id") == mission_id:
                self._board["active_mission_id"] = self._next_focus_candidate_locked()
            self._board["updated_at"] = mission["updated_at"]
            self._persist_locked()
            return self._snapshot_locked(session_id=mission.get("session_id"))

    def attach_browser_verification(self, session_id: str | None, verification: dict | None) -> dict:
        with self._lock:
            mission = self._resolve_auto_link_target_locked(session_id=session_id)
            if not mission or not isinstance(verification, dict):
                return self._snapshot_locked(session_id=session_id)

            cisiv_stage = normalize_cisiv_stage(verification.get("cisiv_stage"), default="verification")
            target_path = str(verification.get("target_path") or "").strip()
            status = str(verification.get("status") or "healthy").strip().lower()
            suggested_action = verification.get("suggested_action") or {}
            strongest_match = ((verification.get("workspace_context") or {}).get("results") or [None])[0] or {}
            additions = []
            if target_path:
                additions.append({
                    "kind": "route",
                    "label": verification.get("route_label") or target_path,
                    "value": target_path,
                })
            if strongest_match.get("relative_path"):
                additions.append({
                    "kind": "file",
                    "label": strongest_match.get("relative_path"),
                    "value": strongest_match.get("relative_path"),
                })
            if suggested_action.get("id"):
                additions.append({
                    "kind": "action",
                    "label": suggested_action.get("label") or suggested_action.get("id"),
                    "value": suggested_action.get("id"),
                })

            mission["links"] = _merge_links(mission.get("links"), additions)
            mission["tags"] = _normalize_tags([*(mission.get("tags") or []), "browser", "verification"])
            mission["cisiv_stage"] = cisiv_stage
            if session_id and not mission.get("session_id"):
                mission["session_id"] = session_id
            if status in {"warning", "fail"} and not mission.get("blocker"):
                mission["blocker"] = _clip_text(
                    verification.get("summary")
                    or f"Browser verification flagged {target_path or 'this route'} for review.",
                    limit=240,
                )
            if not mission.get("next_step") and suggested_action.get("label"):
                mission["next_step"] = _clip_text(
                    f"Run {suggested_action.get('label')} and review the matched file.",
                    limit=240,
                )
            mission["updated_at"] = _utc_now_iso()
            self._append_activity_locked(
                mission,
                kind="browser_verification",
                summary=(
                    f"Verified {target_path or 'route'} and got {status}. "
                    f"Suggested action: {suggested_action.get('label') or 'none'}."
                ),
                cisiv_stage=cisiv_stage,
            )
            self._append_history_locked(
                mission,
                kind="browser_verification",
                summary=(
                    f"Browser verification checked {target_path or 'route'} and returned {status}. "
                    f"Suggested action: {suggested_action.get('label') or 'none'}."
                ),
                status=status,
                source="browser_verification",
                label=target_path or verification.get("route_label"),
                cisiv_stage=cisiv_stage,
            )
            self._board["updated_at"] = mission["updated_at"]
            self._persist_locked()
            return self._snapshot_locked(session_id=session_id)

    def attach_critic_review(
        self,
        session_id: str | None,
        review: dict | None,
        *,
        mission_id: str | None = None,
    ) -> dict:
        with self._lock:
            mission = (
                self._find_mission_locked(mission_id)
                if mission_id
                else self._resolve_auto_link_target_locked(session_id=session_id)
            )
            normalized = _normalize_critic(review)
            if not mission or not normalized:
                return self._snapshot_locked(session_id=session_id)

            cisiv_stage = normalize_cisiv_stage((review or {}).get("cisiv_stage"), default="verification")
            verification_results = normalize_verification_results((review or {}).get("verification_results"))
            gate_payload = None
            if verification_results:
                gate = evaluate_verification_gate(verification_results)
                gate_payload = _normalize_verification_gate(
                    {
                        "decision": gate.decision.value,
                        "reasons": gate.reasons,
                        "failed_tests": gate.failed_tests,
                        "evaluated_at": _utc_now_iso(),
                    }
                )
                mission["verification_gate"] = gate_payload
                mission["status"] = (
                    "blocked" if gate.decision == GateDecision.BLOCK else "eligible"
                )
                if gate.decision == GateDecision.BLOCK:
                    mission["blocker"] = "; ".join(gate.reasons[:4]) or normalized.get("summary")
                else:
                    mission["blocker"] = None

            mission["critic"] = normalized
            mission["cisiv_stage"] = cisiv_stage
            if session_id and not mission.get("session_id"):
                mission["session_id"] = session_id
            if normalized.get("recommended_next") and not mission.get("next_step"):
                mission["next_step"] = normalized["recommended_next"]
            if (
                normalized.get("suggested_mission_status") == "blocked"
                and not mission.get("blocker")
                and (not gate_payload or gate_payload["decision"] == GateDecision.BLOCK.value)
            ):
                mission["blocker"] = normalized.get("summary")
            if normalized.get("source") in {"browser_verification", "action_result"}:
                mission["tags"] = _normalize_tags([*(mission.get("tags") or []), "critic"])

            should_append_activity = (
                normalized.get("source") != "reply"
                or normalized.get("status") != "advancing"
                or normalized.get("suggested_mission_status") in {"blocked", "done"}
            )
            if should_append_activity:
                self._append_activity_locked(
                    mission,
                    kind="critic_review",
                    summary=(
                        f"Mission Critic marked the latest {normalized.get('source', 'turn').replace('_', ' ')} "
                        f"as {normalized.get('status')} ({normalized.get('score')}). "
                        f"{normalized.get('summary') or ''}"
                    ).strip(),
                    cisiv_stage=cisiv_stage,
                )
            self._append_history_locked(
                mission,
                kind="critic_review",
                summary=(
                    f"Mission Critic reviewed the latest {normalized.get('source', 'turn').replace('_', ' ')} "
                    f"as {normalized.get('status')} ({normalized.get('score')}). "
                    f"{normalized.get('summary') or ''}"
                ).strip(),
                status=normalized.get("status"),
                source=normalized.get("source"),
                label=normalized.get("recommended_next"),
                cisiv_stage=cisiv_stage,
            )
            if gate_payload:
                self._append_activity_locked(
                    mission,
                    kind="verification_gate",
                    summary=(
                        f"Verification gate returned {gate_payload['decision']}. "
                        f"{'; '.join(gate_payload['reasons'][:2]) or 'No blocking reasons.'}"
                    ),
                    cisiv_stage=cisiv_stage,
                )
                self._append_history_locked(
                    mission,
                    kind="verification_gate",
                    summary=(
                        f"Verification gate returned {gate_payload['decision']}. "
                        f"{'; '.join(gate_payload['reasons'][:4]) or 'No blocking reasons.'}"
                    ),
                    status=mission.get("status"),
                    source="verification_gate",
                    label=", ".join(gate_payload["failed_tests"][:3]) or gate_payload["decision"],
                    cisiv_stage=cisiv_stage,
                )

            mission["blocker"] = _normalize_blocker(
                mission.get("blocker"),
                status=mission.get("status"),
            )
            mission["updated_at"] = _utc_now_iso()
            self._board["updated_at"] = mission["updated_at"]
            self._persist_locked()
            return self._snapshot_locked(session_id=session_id or mission.get("session_id"))

    def attach_action_result(self, session_id: str | None, tool_result: dict | None) -> dict:
        with self._lock:
            mission = self._resolve_auto_link_target_locked(session_id=session_id)
            if not mission or not isinstance(tool_result, dict):
                return self._snapshot_locked(session_id=session_id)

            action = tool_result.get("action") or {}
            action_id = str(action.get("id") or "").strip()
            action_label = action.get("label") or action_id or "action"
            status = str(tool_result.get("status") or "completed").strip().lower()
            cisiv_stage = normalize_cisiv_stage(
                tool_result.get("cisiv_stage") or action.get("cisiv_stage"),
                default="implementation",
            )
            additions = []
            if action_id:
                additions.append({
                    "kind": "action",
                    "label": action_label,
                    "value": action_id,
                })
            mission["links"] = _merge_links(mission.get("links"), additions)
            mission["tags"] = _normalize_tags([*(mission.get("tags") or []), "operator", "action"])
            mission["cisiv_stage"] = cisiv_stage
            if session_id and not mission.get("session_id"):
                mission["session_id"] = session_id
            if status not in {"completed", "success"}:
                mission["blocker"] = _clip_text(
                    tool_result.get("summary")
                    or f"{action_label} did not finish cleanly.",
                    limit=240,
                )
            mission["updated_at"] = _utc_now_iso()
            self._append_activity_locked(
                mission,
                kind="action_result",
                summary=(
                    f"Ran {action_label} and got {status}. "
                    f"{_clip_text(tool_result.get('summary'), limit=120) or ''}".strip()
                ),
                cisiv_stage=cisiv_stage,
            )
            self._append_history_locked(
                mission,
                kind="action_result",
                summary=(
                    f"Safe local action {action_label} finished with {status}. "
                    f"{_clip_text(tool_result.get('summary'), limit=140) or ''}".strip()
                ),
                status=status,
                source="action_result",
                label=action_label,
                cisiv_stage=cisiv_stage,
            )
            self._board["updated_at"] = mission["updated_at"]
            self._persist_locked()
            return self._snapshot_locked(session_id=session_id)

    def focus_mission(self, mission_id: str) -> dict:
        with self._lock:
            mission = self._find_mission_locked(mission_id)
            if not mission:
                raise KeyError(mission_id)
            self._board["active_mission_id"] = mission_id
            mission["updated_at"] = _utc_now_iso()
            self._append_history_locked(
                mission,
                kind="mission_focused",
                summary=f"Focused mission '{mission['title']}'.",
                status=mission.get("status"),
                label=mission["title"],
                cisiv_stage=mission.get("cisiv_stage"),
            )
            self._board["updated_at"] = mission["updated_at"]
            self._persist_locked()
            return self._snapshot_locked(session_id=mission.get("session_id"))

    def apply_critic_suggestion(
        self,
        mission_id: str,
        *,
        adopt_status: bool = True,
        adopt_next_step: bool = True,
    ) -> dict:
        with self._lock:
            mission = self._find_mission_locked(mission_id)
            if not mission:
                raise KeyError(mission_id)

            critic = mission.get("critic") or {}
            suggested_status = _normalize_status(critic.get("suggested_mission_status"))
            recommended_next = _clip_text(critic.get("recommended_next"), limit=240)
            if not suggested_status and not recommended_next:
                raise ValueError("Mission Critic has no actionable suggestion for this mission.")

            cisiv_stage = normalize_cisiv_stage(critic.get("cisiv_stage"), default="verification")
            if adopt_status and suggested_status:
                mission["status"] = suggested_status
                if suggested_status == "blocked" and critic.get("summary"):
                    mission["blocker"] = _clip_text(critic.get("summary"), limit=240)
                if suggested_status == "done" and self._board.get("active_mission_id") == mission_id:
                    self._board["active_mission_id"] = self._next_focus_candidate_locked()

            if adopt_next_step and recommended_next:
                mission["next_step"] = recommended_next

            mission["cisiv_stage"] = cisiv_stage
            mission["blocker"] = _normalize_blocker(mission.get("blocker"), status=mission.get("status"))

            mission["updated_at"] = _utc_now_iso()
            self._append_activity_locked(
                mission,
                kind="critic_apply",
                summary=(
                    f"Applied Mission Critic suggestion."
                    f" Status: {suggested_status or 'unchanged'}."
                    f" Next: {recommended_next or 'unchanged'}."
                ),
                cisiv_stage=cisiv_stage,
            )
            self._append_history_locked(
                mission,
                kind="critic_apply",
                summary=(
                    "Applied Mission Critic suggestion. "
                    f"Status: {suggested_status or 'unchanged'}. "
                    f"Next: {recommended_next or 'unchanged'}."
                ),
                status=mission.get("status"),
                source="critic_apply",
                label=critic.get("source"),
                cisiv_stage=cisiv_stage,
            )
            self._board["updated_at"] = mission["updated_at"]
            self._persist_locked()
            return self._snapshot_locked(session_id=mission.get("session_id"))

    def delete_mission(self, mission_id: str) -> dict:
        with self._lock:
            missions = self._board.get("missions", [])
            mission = self._find_mission_locked(mission_id)
            if not mission:
                raise KeyError(mission_id)
            self._board["missions"] = [item for item in missions if item.get("id") != mission_id]
            if self._board.get("active_mission_id") == mission_id:
                self._board["active_mission_id"] = self._next_focus_candidate_locked()
            self._board["updated_at"] = _utc_now_iso()
            self._persist_locked()
            return self._snapshot_locked(session_id=mission.get("session_id"))

    def build_session_context(self, session_id: str | None = None) -> dict:
        with self._lock:
            snapshot = self._snapshot_locked(session_id=session_id, limit=8)

        active_mission = snapshot.get("active_mission")
        related_missions = snapshot.get("session_missions") or []
        if not active_mission and not related_missions:
            return {
                "summary": snapshot["summary"],
                "active_mission": None,
                "related_missions": [],
                "prompt_block": "",
                "recommended_next": snapshot.get("recommended_next"),
            }

        lines = [
            "Mission Board:",
            f"- board_summary: {snapshot['summary']}",
        ]
        if active_mission:
            critic = active_mission.get("critic") or {}
            lines.extend(
                [
                    f"- active_mission: {active_mission['title']}",
                    f"- mission_status: {active_mission['status']}",
                    f"- mission_cisiv_stage: {active_mission.get('cisiv_stage') or 'concept'}",
                    f"- mission_objective: {active_mission.get('objective') or 'not set'}",
                    f"- mission_next_step: {active_mission.get('next_step') or 'not set'}",
                    f"- mission_blocker: {active_mission.get('blocker') or 'none'}",
                ]
            )
            if critic.get("summary"):
                lines.extend(
                    [
                        f"- mission_critic_status: {critic.get('status') or 'mixed'}",
                        f"- mission_critic_summary: {critic.get('summary')}",
                        f"- mission_critic_next: {critic.get('recommended_next') or 'none'}",
                    ]
                )
        if related_missions:
            related_line = "; ".join(
                f"{mission['title']} ({mission['status']})"
                for mission in related_missions[:3]
            )
            lines.append(f"- related_session_missions: {related_line}")

        return {
            "summary": snapshot["summary"],
            "active_mission": active_mission,
            "related_missions": related_missions[:3],
            "recommended_next": snapshot.get("recommended_next"),
            "prompt_block": "\n".join(lines),
        }

    def _load_from_disk(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        if not self._state_path.exists():
            self._persist_locked()
            return
        try:
            payload = json.loads(self._state_path.read_text(encoding="utf-8"))
        except Exception:
            self._persist_locked()
            return

        missions = payload.get("missions")
        if not isinstance(missions, list):
            missions = []
        self._board = {
            "active_mission_id": payload.get("active_mission_id"),
            "missions": [self._normalize_loaded_mission(item) for item in missions if isinstance(item, dict)],
            "updated_at": payload.get("updated_at") or _utc_now_iso(),
        }
        if self._board.get("active_mission_id") and not self._find_mission_locked(self._board["active_mission_id"]):
            self._board["active_mission_id"] = self._next_focus_candidate_locked()

    def _persist_locked(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(
            json.dumps(self._board, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _normalize_loaded_mission(self, mission: dict) -> dict:
        now = _utc_now_iso()
        status = _normalize_status(mission.get("status"))
        cisiv_stage = normalize_cisiv_stage(mission.get("cisiv_stage"), default="concept")
        return {
            "id": str(mission.get("id") or uuid.uuid4().hex),
            "title": _clip_text(mission.get("title"), limit=110) or "Untitled mission",
            "objective": _clip_text(mission.get("objective"), limit=1200),
            "status": status,
            "next_step": _clip_text(mission.get("next_step"), limit=240),
            "blocker": _normalize_blocker(mission.get("blocker"), status=status),
            "session_id": str(mission.get("session_id") or "").strip() or None,
            "tags": _normalize_tags(mission.get("tags")),
            "links": _normalize_links(mission.get("links")),
            "cisiv_stage": cisiv_stage,
            "activity": _normalize_activity(mission.get("activity"), default_cisiv_stage=cisiv_stage),
            "history": _normalize_history(mission.get("history"), default_cisiv_stage=cisiv_stage),
            "critic": _normalize_critic(mission.get("critic")),
            "verification_gate": _normalize_verification_gate(mission.get("verification_gate")),
            "created_at": mission.get("created_at") or now,
            "updated_at": mission.get("updated_at") or now,
        }

    def _find_mission_locked(self, mission_id: str | None) -> dict | None:
        if not mission_id:
            return None
        for mission in self._board.get("missions", []):
            if mission.get("id") == mission_id:
                return mission
        return None

    def _next_focus_candidate_locked(self) -> str | None:
        sorted_missions = self._sorted_missions_locked()
        for mission in sorted_missions:
            if mission.get("status") != "done":
                return mission.get("id")
        return sorted_missions[0].get("id") if sorted_missions else None

    def _resolve_auto_link_target_locked(self, session_id: str | None = None) -> dict | None:
        active = self._find_mission_locked(self._board.get("active_mission_id"))
        if active:
            if session_id and not active.get("session_id"):
                active["session_id"] = session_id
            return active

        if session_id:
            for mission in self._sorted_missions_locked():
                if mission.get("session_id") == session_id and mission.get("status") != "done":
                    return mission
        return None

    def _sorted_missions_locked(self) -> list[dict]:
        active_id = self._board.get("active_mission_id")
        return sorted(
            self._board.get("missions", []),
            key=lambda mission: (
                0 if mission.get("id") == active_id else 1,
                STATUS_SORT_ORDER.get(mission.get("status"), 9),
                mission.get("updated_at", ""),
            ),
            reverse=False,
        )

    def _mission_payload(self, mission: dict, *, session_id: str | None = None) -> dict:
        payload = dict(mission)
        payload["focused"] = payload.get("id") == self._board.get("active_mission_id")
        payload["linked_to_active_session"] = bool(
            session_id and payload.get("session_id") and payload.get("session_id") == session_id
        )
        payload["cisiv_stage"] = normalize_cisiv_stage(payload.get("cisiv_stage"), default="concept")
        payload["history"] = _normalize_history(
            payload.get("history"),
            default_cisiv_stage=payload["cisiv_stage"],
        )
        payload["history_count"] = len(payload["history"])
        payload["activity"] = _normalize_activity(
            payload.get("activity"),
            default_cisiv_stage=payload["cisiv_stage"],
        )
        payload["critic"] = _normalize_critic(payload.get("critic"))
        payload["verification_gate"] = _normalize_verification_gate(payload.get("verification_gate"))
        return payload

    def _append_activity_locked(self, mission: dict, *, kind: str, summary: str, cisiv_stage: str | None = None) -> None:
        stage = normalize_cisiv_stage(cisiv_stage, default=mission.get("cisiv_stage") or "implementation")
        activity = _normalize_activity(mission.get("activity"), default_cisiv_stage=stage)
        activity.insert(
            0,
            {
                "id": uuid.uuid4().hex,
                "kind": kind,
                "summary": summary,
                "timestamp": _utc_now_iso(),
                "cisiv_stage": stage,
            },
        )
        mission["activity"] = activity[:8]

    def _append_history_locked(
        self,
        mission: dict,
        *,
        kind: str,
        summary: str,
        status: str | None = None,
        source: str | None = None,
        label: str | None = None,
        cisiv_stage: str | None = None,
    ) -> None:
        stage = normalize_cisiv_stage(cisiv_stage, default=mission.get("cisiv_stage") or "concept")
        history = _normalize_history(mission.get("history"), default_cisiv_stage=stage)
        history.append(
            {
                "id": uuid.uuid4().hex,
                "kind": kind,
                "summary": summary,
                "timestamp": _utc_now_iso(),
                "status": str(status or "").strip().lower() or None,
                "source": str(source or "").strip().lower() or None,
                "label": _clip_text(label, limit=110) or None,
                "cisiv_stage": stage,
            }
        )
        mission["history"] = history[-160:]

    def _recommend_next_locked(self, active_mission: dict | None, missions: list[dict]) -> dict | None:
        if active_mission:
            critic = active_mission.get("critic") or {}
            if active_mission.get("status") == "blocked":
                return {
                    "mission_id": active_mission["id"],
                    "label": active_mission["title"],
                    "action": "clear_blocker",
                    "summary": active_mission.get("blocker") or "Clear the active blocker before moving forward.",
                }
            if critic.get("suggested_mission_status") == "blocked":
                return {
                    "mission_id": active_mission["id"],
                    "label": active_mission["title"],
                    "action": "review_critic_blocker",
                    "summary": critic.get("summary") or "Mission Critic sees a blocker that should be cleared first.",
                }
            if active_mission.get("next_step"):
                return {
                    "mission_id": active_mission["id"],
                    "label": active_mission["title"],
                    "action": "execute_next_step",
                    "summary": active_mission["next_step"],
                }
            if critic.get("recommended_next"):
                return {
                    "mission_id": active_mission["id"],
                    "label": active_mission["title"],
                    "action": "follow_critic",
                    "summary": critic["recommended_next"],
                }

        blocked = next((mission for mission in missions if mission.get("status") == "blocked"), None)
        if blocked:
            return {
                "mission_id": blocked["id"],
                "label": blocked["title"],
                "action": "review_blocker",
                "summary": blocked.get("blocker") or "Review the blocker and decide how to unblock it.",
            }

        queued = next((mission for mission in missions if mission.get("status") == "queued"), None)
        if queued:
            return {
                "mission_id": queued["id"],
                "label": queued["title"],
                "action": "promote_mission",
                "summary": queued.get("next_step") or "Promote the next queued mission into active focus.",
            }

        return None

    def _snapshot_locked(self, session_id: str | None = None, limit: int = 24) -> dict:
        missions = self._sorted_missions_locked()
        counts = {status: 0 for status in MISSION_STATUSES}
        for mission in missions:
            counts[mission.get("status", "active")] += 1

        active_mission = self._find_mission_locked(self._board.get("active_mission_id"))
        session_missions = [
            mission for mission in missions
            if session_id and mission.get("session_id") and mission.get("session_id") == session_id
        ]
        recommended_next = self._recommend_next_locked(active_mission, missions)

        if not missions:
            summary = "Mission Board is empty. Create the first mission to give Jarvis a durable objective."
        elif active_mission:
            summary = (
                f"Mission Board is focused on {active_mission['title']}. "
                f"{counts['active']} active, {counts['eligible']} eligible, "
                f"{counts['blocked']} blocked, and {counts['done']} completed."
            )
        else:
            summary = (
                f"Mission Board is tracking {len(missions)} missions. "
                f"{counts['active']} active, {counts['eligible']} eligible, "
                f"{counts['blocked']} blocked, and {counts['done']} completed."
            )

        return {
            "summary": summary,
            "cisiv_stage_sequence": list(CISIV_STAGE_SEQUENCE),
            "active_mission_id": self._board.get("active_mission_id"),
            "active_mission": (
                self._mission_payload(active_mission, session_id=session_id)
                if active_mission
                else None
            ),
            "mission_count": len(missions),
            "counts": counts,
            "updated_at": self._board.get("updated_at") or _utc_now_iso(),
            "recommended_next": recommended_next,
            "presets": self.list_presets(),
            "missions": [
                self._mission_payload(mission, session_id=session_id)
                for mission in missions[: max(1, int(limit or 24))]
            ],
            "session_missions": [
                self._mission_payload(mission, session_id=session_id)
                for mission in session_missions[:6]
            ],
        }


mission_board = MissionBoardController()
