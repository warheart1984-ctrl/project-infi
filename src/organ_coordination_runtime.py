"""Organ coordination runtime — mediated multi-organ mesh (Stage 4 / Release 35)."""

# Mythic: Organ Coordination Runtime
# Engineering: OrganCoordinationRuntimeEngine
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.workflow_chain_executor import workflow_chain_executor
from src.workflow_family_readiness import compute_family_readiness, family_detail_with_readiness
from src.workflow_family_registry import (
    family_by_id,
    handoffs_for,
    list_handoff_edges,
    validate_handoff_graph,
)

MESH_RUN_VERSION = "organ_mesh_run.v1"
HANDOFF_VERSION = "organ_handoff.v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


class OrganCoordinationRuntime:
    def __init__(self, *, runtime_dir: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._runs_dir = self._runtime_dir / "organ_mesh_runs"
        self._lock = threading.Lock()

    def mesh_snapshot(self) -> dict[str, Any]:
        graph_errors = validate_handoff_graph()
        edges = list_handoff_edges()
        families = []
        for edge in edges:
            src = str(edge.get("source_family_id") or "")
            if src and not any(f.get("family_id") == src for f in families):
                detail = family_detail_with_readiness(src)
                if detail:
                    families.append(
                        {
                            "family_id": src,
                            "readiness": detail.get("readiness"),
                            "handoffs": handoffs_for(src),
                        }
                    )
        return {
            "mesh_version": "organ_mesh.v1",
            "edge_count": len(edges),
            "edges": edges,
            "families": families,
            "graph_valid": len(graph_errors) == 0,
            "graph_errors": graph_errors,
            "claim_label": "asserted",
        }

    def plan_mesh_run(
        self,
        *,
        intent_text: str = "",
        source_family_id: str | None = None,
        handoff_edge_index: int = 0,
    ) -> dict[str, Any]:
        """OCC-0 plan from intent or explicit source + handoff edge."""
        edges = list_handoff_edges()
        if not edges:
            return {"outcome": "blocked", "reason": "no_handoff_edges"}

        edge = None
        if source_family_id:
            src_handoffs = handoffs_for(source_family_id)
            if handoff_edge_index < len(src_handoffs):
                edge = src_handoffs[handoff_edge_index]
        if edge is None:
            edge = self._select_edge_from_intent(intent_text, edges)
        if edge is None:
            return {"outcome": "blocked", "reason": "no_matching_handoff"}

        source_id = str(edge.get("source_family_id") or "")
        target_id = str(edge.get("target_family_id") or "")
        habit_boost = self._mesh_habit_boost_for_edge(edge)
        identity_boost = self._mesh_identity_boost_for_edge(edge)
        narrative_boost = self._mesh_narrative_boost_for_edge(edge)
        agency_boost = self._mesh_agency_boost_for_edge(edge)
        social_boost = self._mesh_social_boost_for_edge(edge)
        federation_boost = self._mesh_federation_boost_for_edge(edge)
        culture_boost = self._mesh_culture_of_beings_boost_for_edge(edge)
        ecosystem_boost = self._mesh_ecosystem_boost_for_edge(edge)
        membrane_boost = self._mesh_membrane_boost_for_edge(edge)
        source = family_by_id(source_id)
        target = family_by_id(target_id)
        if not source or not target:
            return {"outcome": "blocked", "reason": "unknown_family"}

        source_ready = compute_family_readiness(source)
        target_ready = compute_family_readiness(target)
        steps = [
            {
                "step_index": 0,
                "family_id": source_id,
                "chain_id": str(edge.get("source_chain_id") or edge.get("trigger", "").split(".")[0] or "research_brief"),
                "occ_class": str(edge.get("occ_class") or "OCC-1"),
            },
            {
                "step_index": 1,
                "family_id": target_id,
                "chain_id": str(edge.get("chain_id") or "creative_asset_package"),
                "occ_class": str(edge.get("occ_class") or "OCC-1"),
            },
        ]
        blocked_reason = None
        if source_ready.get("readiness") in {"missing", "empty"}:
            blocked_reason = f"source_not_ready:{source_id}"
        elif target_ready.get("readiness") in {"missing", "empty"}:
            blocked_reason = f"target_not_ready:{target_id}"

        return {
            "outcome": "planned" if not blocked_reason else "blocked",
            "reason": blocked_reason,
            "occ_class": "OCC-0",
            "plan_id": f"plan_{uuid4().hex[:12]}",
            "edge": edge,
            "steps": steps,
            "source_readiness": source_ready.get("readiness"),
            "target_readiness": target_ready.get("readiness"),
            "intent_text": intent_text[:500] if intent_text else None,
            "habit_boost": habit_boost,
            "identity_boost": identity_boost,
            "narrative_boost": narrative_boost,
            "agency_boost": agency_boost,
            "social_boost": social_boost,
            "federation_boost": federation_boost,
            "culture_of_beings_boost": culture_boost,
            "ecosystem_boost": ecosystem_boost,
            "membrane_boost": membrane_boost,
        }

    def _mesh_culture_of_beings_boost_for_edge(self, edge: dict[str, Any]) -> float:
        try:
            from src.culture_of_beings_registry import adopted_norms

            src = str(edge.get("source_family_id") or "")
            tgt = str(edge.get("target_family_id") or "")
            boost = 0.0
            for norm in adopted_norms():
                summary = str(norm.get("summary") or "").lower()
                if src and src in summary:
                    boost += 0.15
                if tgt and tgt in summary:
                    boost += 0.15
            return min(boost, 0.5)
        except Exception:
            return 0.0

    def _mesh_ecosystem_boost_for_edge(self, edge: dict[str, Any]) -> float:
        try:
            from src.constitutional_ecosystem_registry import adopted_charters

            return min(len(adopted_charters()) * 0.1, 0.5)
        except Exception:
            return 0.0

    def _mesh_membrane_boost_for_edge(self, edge: dict[str, Any]) -> float:
        try:
            from src.multi_organism_governance_membrane_registry import adopted_policies

            return min(len(adopted_policies()) * 0.1, 0.5)
        except Exception:
            return 0.0

    def _mesh_federation_boost_for_edge(self, edge: dict[str, Any]) -> float:
        try:
            from src.multi_being_continuity_registry import adopted_pacts

            src = str(edge.get("source_family_id") or "")
            tgt = str(edge.get("target_family_id") or "")
            boost = 0.0
            for pact in adopted_pacts():
                if str(pact.get("pact_kind") or "") not in {
                    "bilateral_organism",
                    "cross_machine_peer",
                    "federated_mesh_cluster",
                }:
                    continue
                summary = str(pact.get("summary") or "").lower()
                ref = json.dumps(pact.get("counterparty_organism_ref") or {}).lower()
                if src and (src in summary or src in ref):
                    boost += 0.25
                if tgt and (tgt in summary or tgt in ref):
                    boost += 0.25
                if pact.get("digest_verified"):
                    boost += 0.1
            return min(boost, 1.0)
        except Exception:
            return 0.0

    def _mesh_social_boost_for_edge(self, edge: dict[str, Any]) -> float:
        try:
            from src.social_continuity_registry import adopted_bonds

            src = str(edge.get("source_family_id") or "")
            tgt = str(edge.get("target_family_id") or "")
            boost = 0.0
            for bond in adopted_bonds():
                if str(bond.get("bond_kind") or "") not in {
                    "organ_collaborator",
                    "federated_peer",
                    "operator_dyad",
                }:
                    continue
                summary = str(bond.get("summary") or "").lower()
                ref = json.dumps(bond.get("counterparty_ref") or {}).lower()
                if src and (src in summary or src in ref):
                    boost += 0.2
                if tgt and (tgt in summary or tgt in ref):
                    boost += 0.2
            return min(boost, 1.0)
        except Exception:
            return 0.0

    def _mesh_agency_boost_for_edge(self, edge: dict[str, Any]) -> float:
        try:
            from src.autobiographical_agency_registry import adopted_episodes

            src = str(edge.get("source_family_id") or "")
            tgt = str(edge.get("target_family_id") or "")
            boost = 0.0
            for episode in adopted_episodes():
                if str(episode.get("episode_kind") or "") not in {"ongoing_work", "commitment_arc"}:
                    continue
                summary = str(episode.get("summary") or "").lower()
                if src and src in summary:
                    boost += 0.2
                if tgt and tgt in summary:
                    boost += 0.2
            return min(boost, 1.0)
        except Exception:
            return 0.0

    def _mesh_narrative_boost_for_edge(self, edge: dict[str, Any]) -> float:
        try:
            from src.narrative_continuity_registry import adopted_beats

            src = str(edge.get("source_family_id") or "")
            tgt = str(edge.get("target_family_id") or "")
            boost = 0.0
            for beat in adopted_beats():
                if str(beat.get("beat_kind") or "") not in {"thread", "arc"}:
                    continue
                summary = str(beat.get("summary") or "").lower()
                if src and src in summary:
                    boost += 0.2
                if tgt and tgt in summary:
                    boost += 0.2
            return min(boost, 1.0)
        except Exception:
            return 0.0

    def _mesh_identity_boost_for_edge(self, edge: dict[str, Any]) -> float:
        try:
            from src.identity_self_model_registry import adopted_claims

            src = str(edge.get("source_family_id") or "")
            tgt = str(edge.get("target_family_id") or "")
            boost = 0.0
            for claim in adopted_claims():
                if str(claim.get("claim_kind") or "") != "boundary":
                    continue
                statement = str(claim.get("statement") or "").lower()
                if src and src in statement:
                    boost += 0.25
                if tgt and tgt in statement:
                    boost += 0.25
            return min(boost, 1.0)
        except Exception:
            return 0.0

    def _mesh_habit_boost_for_edge(self, edge: dict[str, Any]) -> float:
        try:
            from src.culture_habit_runtime import culture_habit_runtime

            return culture_habit_runtime.mesh_habit_boost(edge)
        except Exception:
            return 0.0

    def _select_edge_from_intent(self, intent_text: str, edges: list[dict[str, Any]]) -> dict[str, Any] | None:
        lowered = str(intent_text or "").lower()
        scored: list[tuple[float, dict[str, Any]]] = []
        for edge in edges:
            score = 0.0
            src = str(edge.get("source_family_id") or "")
            tgt = str(edge.get("target_family_id") or "")
            if src.replace("_", " ") in lowered or tgt.replace("_", " ") in lowered:
                score += 3.0
            trigger = str(edge.get("trigger") or "").lower()
            if trigger and trigger.split(".")[0] in lowered:
                score += 2.0
            score += self._mesh_habit_boost_for_edge(edge)
            identity_boost = self._mesh_identity_boost_for_edge(edge)
            if identity_boost > 0:
                score += identity_boost
            narrative_boost = self._mesh_narrative_boost_for_edge(edge)
            if narrative_boost > 0:
                score += narrative_boost
            agency_boost = self._mesh_agency_boost_for_edge(edge)
            if agency_boost > 0:
                score += agency_boost
            social_boost = self._mesh_social_boost_for_edge(edge)
            if social_boost > 0:
                score += social_boost
            federation_boost = self._mesh_federation_boost_for_edge(edge)
            if federation_boost > 0:
                score += federation_boost
            culture_boost = self._mesh_culture_of_beings_boost_for_edge(edge)
            if culture_boost > 0:
                score += culture_boost
            ecosystem_boost = self._mesh_ecosystem_boost_for_edge(edge)
            if ecosystem_boost > 0:
                score += ecosystem_boost
            membrane_boost = self._mesh_membrane_boost_for_edge(edge)
            if membrane_boost > 0:
                score += membrane_boost
            scored.append((score, edge))
        if scored:
            scored.sort(key=lambda item: item[0], reverse=True)
            if scored[0][0] > 0:
                return scored[0][1]
        return edges[0] if edges else None

    def execute_mesh_run(
        self,
        plan: dict[str, Any],
        *,
        session_id: str = "global",
        operator_approved: bool = False,
        dry_run: bool = True,
        operator_ack: bool = False,
        jarvis_authorization: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if plan.get("outcome") == "blocked":
            return self._persist_run(
                {
                    "status": "blocked",
                    "reason": plan.get("reason"),
                    "plan": plan,
                    "dry_run": dry_run,
                    "operator_approved": operator_approved,
                },
                session_id=session_id,
            )

        auth = dict(jarvis_authorization or {})
        if not auth.get("authorized"):
            return {"outcome": "blocked", "reason": "jarvis_not_authorized", "status": 403}

        occ = str(plan.get("occ_class") or "OCC-1")
        if occ == "OCC-2" and not (operator_approved and operator_ack):
            return {"outcome": "blocked", "reason": "occ2_requires_operator_ack", "status": 403}

        run_id = f"mesh_{uuid4().hex[:12]}"
        steps_out: list[dict[str, Any]] = []
        handoffs_out: list[dict[str, Any]] = []
        steps = list(plan.get("steps") or [])
        prior_artifact = None

        for step in steps:
            chain_id = str(step.get("chain_id") or "")
            family_id = str(step.get("family_id") or "")
            args = {"session_id": session_id, "mesh_run_id": run_id}
            if prior_artifact:
                args["handoff_artifact_ref"] = prior_artifact
            chain_result = workflow_chain_executor.execute(
                chain_id,
                args=args,
                operator_approved=operator_approved,
                dry_run=dry_run,
            )
            steps_out.append({"step": step, "chain_result": chain_result})
            artifact_ref = f"{run_id}:{family_id}:{chain_id}"
            prior_artifact = artifact_ref

            if len(steps_out) < len(steps):
                next_step = steps[len(steps_out)]
                handoff = self._build_handoff_envelope(
                    source_family_id=family_id,
                    target_family_id=str(next_step.get("family_id") or ""),
                    source_chain_id=chain_id,
                    target_chain_id=str(next_step.get("chain_id") or ""),
                    artifact_ref=artifact_ref,
                    occ_class=occ,
                )
                handoffs_out.append(handoff)
                self._emit_handoff_ledger(session_id, handoff, run_id)

        run = {
            "mesh_run_version": MESH_RUN_VERSION,
            "run_id": run_id,
            "status": "completed",
            "dry_run": dry_run,
            "operator_approved": operator_approved,
            "jarvis_authorized": True,
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
            "occ_class": occ,
            "plan": plan,
            "steps": steps_out,
            "handoffs": handoffs_out,
            "session_id": session_id,
            "started_at": _utc_now_iso(),
            "completed_at": _utc_now_iso(),
        }
        self._persist_run(run, session_id=session_id)
        self._emit_mesh_run_ledger(session_id, run)
        return {"outcome": "completed", **run}

    def _build_handoff_envelope(
        self,
        *,
        source_family_id: str,
        target_family_id: str,
        source_chain_id: str,
        target_chain_id: str,
        artifact_ref: str,
        occ_class: str,
    ) -> dict[str, Any]:
        return {
            "handoff_version": HANDOFF_VERSION,
            "source_family_id": source_family_id,
            "target_family_id": target_family_id,
            "source_chain_id": source_chain_id,
            "chain_id": target_chain_id,
            "artifact_ref": artifact_ref,
            "ul_substrate": {"visibility": "operator", "stage": "handoff"},
            "claim_label": "asserted",
            "occ_class": occ_class,
            "operator_ack_required": occ_class == "OCC-2",
        }

    def _persist_run(self, run: dict[str, Any], *, session_id: str) -> dict[str, Any]:
        run_id = str(run.get("run_id") or f"mesh_{uuid4().hex[:12]}")
        run["run_id"] = run_id
        run.setdefault("mesh_run_version", MESH_RUN_VERSION)
        run.setdefault("session_id", session_id)
        with self._lock:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            path = self._runs_dir / f"{run_id}.json"
            path.write_text(json.dumps(run, sort_keys=True) + "\n", encoding="utf-8")
        return run

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        path = self._runs_dir / f"{run_id}.json"
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self._runs_dir.is_dir():
            return []
        runs: list[dict[str, Any]] = []
        for path in sorted(self._runs_dir.glob("*.json"), reverse=True)[:limit]:
            try:
                runs.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return runs

    def mesh_posture(self) -> dict[str, Any]:
        runs = self.list_runs(limit=100)
        active = [r for r in runs if r.get("status") == "running"]
        blocked = [r for r in runs if r.get("status") == "blocked"]
        return {
            "active_mesh_runs": len(active),
            "blocked_handoffs": len(blocked),
            "recent_runs": len(runs),
            "claim_label": "asserted",
        }

    def _emit_handoff_ledger(self, session_id: str, handoff: dict[str, Any], run_id: str) -> None:
        try:
            from src.operator_decision_ledger import append_organ_handoff_event

            append_organ_handoff_event(session_id, handoff=handoff, mesh_run_id=run_id)
        except Exception:
            pass

    def _emit_mesh_run_ledger(self, session_id: str, run: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_organ_mesh_run_event

            append_organ_mesh_run_event(session_id, run=run)
        except Exception:
            pass


organ_coordination_runtime = OrganCoordinationRuntime()


def plan_mesh_from_brain_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    mesh = dict(proposal.get("suggested_organ_mesh") or {})
    if mesh.get("edge"):
        edge = mesh["edge"]
        return organ_coordination_runtime.plan_mesh_run(
            source_family_id=str(edge.get("source_family_id") or ""),
            handoff_edge_index=0,
        )
    text = str(proposal.get("operator_text") or proposal.get("text") or "")
    return organ_coordination_runtime.plan_mesh_run(intent_text=text)
