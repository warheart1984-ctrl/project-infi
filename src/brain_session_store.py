"""Brain session CRUD and operator decisions."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.brain_deliberation_runtime import deliberate
from src.brain_proposal_validator import build_brain_proposal

VALID_DECISIONS = frozenset({"accept", "reject", "defer"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


class BrainSessionStore:
    def __init__(self, *, runtime_dir: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._dir = self._runtime_dir / "brain_sessions"
        self._lock = threading.Lock()

    def _path(self, session_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
        return self._dir / f"{safe}.json"

    def list_sessions(self) -> list[dict[str, Any]]:
        if not self._dir.is_dir():
            return []
        sessions: list[dict[str, Any]] = []
        for path in sorted(self._dir.glob("*.json")):
            try:
                sessions.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return sessions

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        path = self._path(session_id)
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _write(self, session: dict[str, Any]) -> dict[str, Any]:
        session["updated_at"] = _utc_now_iso()
        path = self._path(str(session["session_id"]))
        with self._lock:
            self._dir.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(session, sort_keys=True) + "\n", encoding="utf-8")
        return session

    def create_session(self, text: str, *, include_deliberation: bool = False) -> dict[str, Any]:
        session_id = f"sess-{uuid4()}"
        proposal = build_brain_proposal(text, emitter="brain_session_store")
        session = {
            "brain_session_version": "brain_session.v1",
            "session_id": session_id,
            "created_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
            "status": "open",
            "operator_decision": "pending",
            "operator_text": text[:500],
            "proposals": [proposal],
            "deliberations": [],
            "active_deliberation_id": None,
        }
        if include_deliberation:
            deliberation = deliberate(text, session_id=session_id)
            session["deliberations"] = [deliberation]
            session["active_deliberation_id"] = deliberation.get("deliberation_id")
        return self._write(session)

    def append_proposal(self, session_id: str, text: str) -> dict[str, Any] | None:
        session = self.get_session(session_id)
        if not session:
            return None
        session.setdefault("proposals", []).append(build_brain_proposal(text, emitter="brain_session_store"))
        return self._write(session)

    def decide(self, session_id: str, decision: str) -> dict[str, Any] | None:
        if decision not in VALID_DECISIONS:
            return None
        session = self.get_session(session_id)
        if not session:
            return None
        mapping = {"accept": "accepted", "reject": "rejected", "defer": "deferred"}
        session["operator_decision"] = mapping[decision]
        if decision == "accept":
            proposals = list(session.get("proposals") or [])
            latest = proposals[-1] if proposals else {}
            try:
                from src.organ_coordination_runtime import plan_mesh_from_brain_proposal
                from src.organ_mesh_approval_bridge import maybe_enqueue_organ_mesh_approval

                mesh_plan = plan_mesh_from_brain_proposal(latest)
                if mesh_plan.get("outcome") == "planned":
                    queue = maybe_enqueue_organ_mesh_approval(
                        session_id,
                        mesh_plan,
                        proposal=latest,
                    )
                    session["mesh_plan"] = mesh_plan
                    session["mesh_approval_queue"] = queue
            except Exception:
                pass
            try:
                from src.culture_habit_runtime import culture_habit_runtime
                from src.habit_adoption_bridge import maybe_enqueue_habit_adoption_approval

                habits = culture_habit_runtime.rank_habit_candidates(
                    str(latest.get("intent", {}).get("restated_task") or session.get("operator_text") or "")
                )
                routing = dict(latest.get("routing") or {})
                if not habits:
                    habits = list(routing.get("suggested_habits") or [])
                if habits:
                    top = habits[0]
                    queue = maybe_enqueue_habit_adoption_approval(
                        session_id,
                        top,
                        proposal=latest,
                    )
                    session["habit_candidate"] = top
                    session["habit_adoption_queue"] = queue
            except Exception:
                pass
            try:
                from src.identity_claim_adoption_bridge import maybe_enqueue_identity_claim_adoption_approval
                from src.identity_self_model_runtime import identity_self_model_runtime

                text = str(latest.get("intent", {}).get("restated_task") or session.get("operator_text") or "")
                claims = identity_self_model_runtime.rank_identity_candidates(text)
                routing = dict(latest.get("routing") or {})
                if not claims:
                    claims = list(routing.get("suggested_identity_claims") or [])
                if claims:
                    top = claims[0]
                    queue = maybe_enqueue_identity_claim_adoption_approval(
                        session_id,
                        top,
                        proposal=latest,
                    )
                    session["identity_candidate"] = top
                    session["identity_adoption_queue"] = queue
            except Exception:
                pass
            try:
                from src.narrative_beat_adoption_bridge import maybe_enqueue_narrative_beat_adoption_approval
                from src.narrative_continuity_runtime import narrative_continuity_runtime

                text = str(latest.get("intent", {}).get("restated_task") or session.get("operator_text") or "")
                beats = narrative_continuity_runtime.rank_narrative_candidates(text)
                routing = dict(latest.get("routing") or {})
                if not beats:
                    beats = list(routing.get("suggested_narrative_beats") or [])
                if beats:
                    top = beats[0]
                    queue = maybe_enqueue_narrative_beat_adoption_approval(
                        session_id,
                        top,
                        proposal=latest,
                    )
                    session["narrative_candidate"] = top
                    session["narrative_adoption_queue"] = queue
            except Exception:
                pass
            try:
                from src.autobiographical_episode_adoption_bridge import (
                    maybe_enqueue_autobiographical_episode_adoption_approval,
                )
                from src.autobiographical_agency_runtime import autobiographical_agency_runtime

                text = str(latest.get("intent", {}).get("restated_task") or session.get("operator_text") or "")
                episodes = autobiographical_agency_runtime.rank_autobiographical_candidates(text)
                routing = dict(latest.get("routing") or {})
                if not episodes:
                    episodes = list(routing.get("suggested_autobiographical_episodes") or [])
                if episodes:
                    top = episodes[0]
                    queue = maybe_enqueue_autobiographical_episode_adoption_approval(
                        session_id,
                        top,
                        proposal=latest,
                    )
                    session["autobiographical_candidate"] = top
                    session["autobiographical_adoption_queue"] = queue
            except Exception:
                pass
            try:
                from src.social_bond_adoption_bridge import maybe_enqueue_social_bond_adoption_approval
                from src.social_continuity_runtime import social_continuity_runtime

                text = str(latest.get("intent", {}).get("restated_task") or session.get("operator_text") or "")
                bonds = social_continuity_runtime.rank_social_candidates(text)
                routing = dict(latest.get("routing") or {})
                if not bonds:
                    bonds = list(routing.get("suggested_social_bonds") or [])
                if bonds:
                    top = bonds[0]
                    queue = maybe_enqueue_social_bond_adoption_approval(
                        session_id,
                        top,
                        proposal=latest,
                    )
                    session["social_candidate"] = top
                    session["social_adoption_queue"] = queue
            except Exception:
                pass
            try:
                from src.multi_being_pact_adoption_bridge import (
                    maybe_enqueue_multi_being_pact_adoption_approval,
                )
                from src.multi_being_continuity_runtime import multi_being_continuity_runtime

                text = str(latest.get("intent", {}).get("restated_task") or session.get("operator_text") or "")
                pacts = multi_being_continuity_runtime.rank_multi_being_candidates(text)
                routing = dict(latest.get("routing") or {})
                if not pacts:
                    pacts = list(routing.get("suggested_multi_being_pacts") or [])
                if pacts:
                    top = pacts[0]
                    queue = maybe_enqueue_multi_being_pact_adoption_approval(
                        session_id,
                        top,
                        proposal=latest,
                    )
                    session["multi_being_candidate"] = top
                    session["multi_being_adoption_queue"] = queue
            except Exception:
                pass
            try:
                from src.culture_of_beings_runtime import culture_of_beings_runtime
                from src.shared_norm_adoption_bridge import maybe_enqueue_shared_norm_adoption_approval

                text = str(latest.get("intent", {}).get("restated_task") or session.get("operator_text") or "")
                norms = culture_of_beings_runtime.rank_shared_norm_candidates(text)
                routing = dict(latest.get("routing") or {})
                if not norms:
                    norms = list(routing.get("suggested_shared_norms") or [])
                if norms:
                    top = norms[0]
                    queue = maybe_enqueue_shared_norm_adoption_approval(session_id, top, proposal=latest)
                    session["shared_norm_candidate"] = top
                    session["shared_norm_adoption_queue"] = queue
            except Exception:
                pass
            try:
                from src.constitutional_ecosystem_runtime import constitutional_ecosystem_runtime

                text = str(latest.get("intent", {}).get("restated_task") or session.get("operator_text") or "")
                charters = constitutional_ecosystem_runtime.rank_ecosystem_candidates(text)
                routing = dict(latest.get("routing") or {})
                if not charters:
                    charters = list(routing.get("suggested_ecosystem_charters") or [])
                if charters:
                    session["ecosystem_charter_candidate"] = charters[0]
            except Exception:
                pass
            try:
                from src.multi_organism_governance_membrane_runtime import (
                    multi_organism_governance_membrane_runtime,
                )

                text = str(latest.get("intent", {}).get("restated_task") or session.get("operator_text") or "")
                policies = multi_organism_governance_membrane_runtime.rank_membrane_candidates(text)
                routing = dict(latest.get("routing") or {})
                if not policies:
                    policies = list(routing.get("suggested_membrane_policies") or [])
                if policies:
                    session["membrane_policy_candidate"] = policies[0]
            except Exception:
                pass
        if decision in {"accept", "reject", "defer"}:
            session["status"] = "closed"
        return self._write(session)

    def append_deliberation(self, session_id: str, text: str) -> dict[str, Any] | None:
        session = self.get_session(session_id)
        if not session:
            return None
        deliberation = deliberate(text, session_id=session_id)
        session.setdefault("deliberations", []).append(deliberation)
        session["active_deliberation_id"] = deliberation.get("deliberation_id")
        return self._write(session)


brain_session_store = BrainSessionStore()
