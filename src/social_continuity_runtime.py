"""Social continuity runtime — relational drift fusion and governed adoption (Stage 9 / Release 40)."""

# Mythic: Social Continuity Runtime
# Engineering: SocialContinuityRuntimeEngine
from __future__ import annotations

import json
import os
import threading
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.autobiographical_agency_registry import adopted_episodes
from src.narrative_continuity_registry import adopted_beats
from src.narrative_continuity_runtime import validate_beat_against_identity
from src.social_continuity_registry import BOND_VERSION, adopted_bonds, save_adopted_bond

DRIFT_VERSION = "social_drift.v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def validate_bond_against_identity_narrative_and_agency(
    bond: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Reject bonds that violate anchor/identity or contradict adopted narrative/agency posture."""
    summary = str(bond.get("summary") or "")
    as_beat = {"summary": summary, "beat_kind": "thread"}
    identity_check = validate_beat_against_identity(as_beat, repo_root=repo_root)
    violations = list(identity_check.get("violations") or [])
    narrative_aligned = True
    agency_aligned = True
    lowered = summary.lower()
    try:
        beats = adopted_beats(repo_root=repo_root)
        if beats and any("override jarvis" in lowered or "identity_mutation" in lowered):
            narrative_aligned = False
            violations.append("contradicts_narrative_posture")
    except Exception:
        pass
    try:
        episodes = adopted_episodes(repo_root=repo_root)
        if episodes and any("override jarvis" in lowered or "bypass otem" in lowered):
            agency_aligned = False
            violations.append("contradicts_agency_posture")
    except Exception:
        pass
    aligned = identity_check.get("aligned") and narrative_aligned and agency_aligned and len(violations) == 0
    return {
        "aligned": aligned,
        "identity_alignment": bool(identity_check.get("aligned")),
        "narrative_alignment": narrative_aligned,
        "agency_alignment": agency_aligned,
        "violations": violations,
        "claim_label": "asserted" if aligned else "rejected",
    }


class SocialContinuityRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "social_bond_candidates"
        self._archive_path = self._runtime_dir / "jarvis_memory_board_archive.v1.json"
        self._lock = threading.Lock()

    def observe_social_drift(
        self,
        *,
        session_id: str | None = None,
        window_days: int = 30,
    ) -> dict[str, Any]:
        """SCC-0 observe-only drift from ledger, identity, narrative, agency, federation, mesh."""
        drift_events: list[dict[str, Any]] = []
        identity_posture = self._identity_posture_safe()
        narrative_posture = self._narrative_posture_safe()
        agency_posture = self._agency_posture_safe()

        if not identity_posture.get("anchor_aligned", True):
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="identity_posture",
                    summary="Identity posture misaligned with anchor",
                    identity_aligned=False,
                    narrative_aligned=True,
                    agency_aligned=True,
                )
            )
        if not narrative_posture.get("identity_aligned", True):
            drift_events.append(
                self._drift_event(
                    severity="nominal",
                    source="narrative_posture",
                    summary="Narrative posture drift detected",
                    identity_aligned=True,
                    narrative_aligned=False,
                    agency_aligned=True,
                )
            )
        if not agency_posture.get("identity_aligned", True):
            drift_events.append(
                self._drift_event(
                    severity="nominal",
                    source="agency_posture",
                    summary="Agency posture drift detected",
                    identity_aligned=True,
                    narrative_aligned=True,
                    agency_aligned=False,
                )
            )

        federated_peer_count = len(self._accepted_federation_grants())
        if federated_peer_count > 0:
            drift_events.append(
                self._drift_event(
                    severity="nominal",
                    source="federation_grants",
                    summary=f"{federated_peer_count} accepted federation grant(s) active",
                    identity_aligned=True,
                    narrative_aligned=True,
                    agency_aligned=True,
                )
            )

        scopes = [str(session_id)] if session_id else ["global"]
        cross_tenant = 0
        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=max(1, window_days))).isoformat()
            for scope in scopes:
                for row in operator_decision_ledger_store.list_events(scope, since=since, limit=500):
                    kind = str(row.get("decision_kind") or "")
                    if row.get("federation"):
                        cross_tenant += 1
                    if kind in {"social_drift", "autobiographical_drift", "narrative_drift", "identity_drift"}:
                        drift_events.append(
                            self._drift_event(
                                severity="nominal",
                                source=f"ledger:{kind}",
                                summary=str(row.get("summary") or "")[:120],
                                identity_aligned=True,
                                narrative_aligned=True,
                                agency_aligned=True,
                            )
                        )
        except Exception:
            pass

        candidates = self.surface_bond_candidates()
        for ladder_fn in (
            self.candidates_from_adopted_episodes,
            self.candidates_from_adopted_beats,
            self.candidates_from_federation_grants,
            self.candidates_from_mesh_handoffs,
            self.candidates_from_ledger_scopes,
        ):
            for item in ladder_fn():
                candidates.append(item)

        for candidate in candidates:
            self._persist_candidate(candidate)

        overall_identity = identity_posture.get("anchor_aligned", True)
        overall_narrative = narrative_posture.get("identity_aligned", True)
        overall_agency = agency_posture.get("identity_aligned", True)

        result = {
            "outcome": "observed",
            "scc_class": "SCC-0",
            "drift_event_count": len(drift_events),
            "drift_events": drift_events,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "identity_aligned": overall_identity,
            "narrative_aligned": overall_narrative,
            "agency_aligned": overall_agency,
            "federated_peer_count": federated_peer_count,
            "cross_tenant_decisions": cross_tenant,
            "window_days": window_days,
            "federation_summary": self._federation_summary(),
            "claim_label": "asserted",
            "summary": f"Social drift observed: {len(drift_events)} events, {len(candidates)} candidates",
        }
        if session_id:
            self._emit_social_drift_ledger(session_id, result)
        return result

    def _identity_posture_safe(self) -> dict[str, Any]:
        try:
            from src.identity_self_model_runtime import identity_self_model_runtime

            return identity_self_model_runtime.identity_posture()
        except Exception:
            return {"anchor_aligned": True}

    def _narrative_posture_safe(self) -> dict[str, Any]:
        try:
            from src.narrative_continuity_runtime import narrative_continuity_runtime

            return narrative_continuity_runtime.narrative_posture()
        except Exception:
            return {"identity_aligned": True}

    def _agency_posture_safe(self) -> dict[str, Any]:
        try:
            from src.autobiographical_agency_runtime import autobiographical_agency_runtime

            return autobiographical_agency_runtime.autobiographical_posture()
        except Exception:
            return {"identity_aligned": True}

    def _accepted_federation_grants(self) -> list[Any]:
        try:
            from src.ugr.mission.federation_grants import FederationGrantStore

            home = os.getenv("UGR_HOME_TENANT", "tenant:acme")
            store = FederationGrantStore(self._runtime_dir)
            grants = store.list_for_tenant(home)
            now = int(datetime.now(timezone.utc).timestamp())
            return [g for g in grants if g.is_active(now=now)]
        except Exception:
            return []

    def _federation_summary(self) -> dict[str, Any]:
        grants = self._accepted_federation_grants()
        return {
            "accepted_grant_count": len(grants),
            "grant_ids": [g.grant_id for g in grants[:8]],
        }

    def _drift_event(
        self,
        *,
        severity: str,
        source: str,
        summary: str,
        identity_aligned: bool,
        narrative_aligned: bool,
        agency_aligned: bool,
    ) -> dict[str, Any]:
        return {
            "drift_version": DRIFT_VERSION,
            "drift_id": f"sdrift_{uuid4().hex[:12]}",
            "severity": severity,
            "source": source,
            "summary": summary,
            "identity_aligned": identity_aligned,
            "narrative_aligned": narrative_aligned,
            "agency_aligned": agency_aligned,
            "scc_class": "SCC-0",
            "observed_at": _utc_now_iso(),
        }

    def surface_bond_candidates(self) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        try:
            from src.operator_profile_organ import build_operator_profile

            profile = build_operator_profile()
            candidate = self._build_candidate(
                summary="Primary operator dyad under governed partnership",
                bond_kind="operator_dyad",
                counterparty_ref={"operator_profile_id": profile.get("profile_id", "operator")},
                trust_posture="governed_partnership",
                evidence_refs=["operator_profile:operator"],
                stability_score=1.0,
            )
            validation = validate_bond_against_identity_narrative_and_agency(
                candidate, repo_root=self._repo_root
            )
            if validation.get("aligned"):
                candidate["identity_alignment"] = validation.get("identity_alignment")
                candidate["narrative_alignment"] = validation.get("narrative_alignment")
                candidate["agency_alignment"] = validation.get("agency_alignment")
                candidates.append(candidate)
        except Exception:
            pass
        return candidates

    def candidates_from_adopted_episodes(self) -> list[dict[str, Any]]:
        """40c: AAC-2 episodes → SCC-1 bond candidates only."""
        try:
            episodes = adopted_episodes(repo_root=self._repo_root)
        except Exception:
            return []

        candidates: list[dict[str, Any]] = []
        for episode in episodes:
            if not episode.get("operator_promoted"):
                continue
            kind = str(episode.get("episode_kind") or "")
            bond_kind = "operator_dyad" if kind == "operator_partnership" else "workflow_counterparty"
            summary = f"Relational bond from agency episode: {episode.get('summary', '')[:300]}"
            candidate = self._build_candidate(
                summary=summary,
                bond_kind=bond_kind,
                counterparty_ref={"scope": "operator"},
                trust_posture="verified_partnership",
                evidence_refs=[f"episode:{episode.get('episode_id')}"],
                stability_score=float(episode.get("stability_score") or 0.8),
                scc_class="SCC-1",
                source_layers={"episode_id": episode.get("episode_id")},
            )
            validation = validate_bond_against_identity_narrative_and_agency(
                candidate, repo_root=self._repo_root
            )
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            candidate["agency_alignment"] = validation.get("agency_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_adopted_beats(self, *, min_age_days: int = 14) -> list[dict[str, Any]]:
        """40c: NCC-2 relationship-thread beats → SCC-1 bond candidates."""
        try:
            beats = adopted_beats(repo_root=self._repo_root)
        except Exception:
            return []

        candidates: list[dict[str, Any]] = []
        for beat in beats:
            if not beat.get("operator_promoted"):
                continue
            beat_kind = str(beat.get("beat_kind") or "")
            if beat_kind not in {"thread", "arc", "chapter"}:
                continue
            summary = f"Relationship thread from narrative: {beat.get('summary', '')[:300]}"
            candidate = self._build_candidate(
                summary=summary,
                bond_kind="operator_dyad",
                counterparty_ref={"scope": "narrative_thread"},
                trust_posture="narrative_grounded",
                evidence_refs=[f"beat:{beat.get('beat_id')}"],
                stability_score=float(beat.get("stability_score") or 0.75),
                scc_class="SCC-1",
                source_layers={"beat_id": beat.get("beat_id")},
            )
            validation = validate_bond_against_identity_narrative_and_agency(
                candidate, repo_root=self._repo_root
            )
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            candidate["agency_alignment"] = validation.get("agency_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_federation_grants(self) -> list[dict[str, Any]]:
        """40c: accepted UGR grants → SCC-1 federated_peer candidates (read-only)."""
        candidates: list[dict[str, Any]] = []
        for grant in self._accepted_federation_grants():
            peer = grant.grantee_tenant if grant.issuer_tenant else grant.grantee_tenant
            summary = f"Federated peer bond: {grant.issuer_tenant} ↔ {grant.grantee_tenant}"
            candidate = self._build_candidate(
                summary=summary,
                bond_kind="federated_peer",
                counterparty_ref={
                    "tenant_id": peer,
                    "grant_id": grant.grant_id,
                },
                trust_posture="bilateral_federation",
                evidence_refs=[f"grant:{grant.grant_id}"],
                stability_score=0.9,
                scc_class="SCC-1",
                source_layers={"grant_id": grant.grant_id},
                interaction_count=1,
            )
            validation = validate_bond_against_identity_narrative_and_agency(
                candidate, repo_root=self._repo_root
            )
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            candidate["agency_alignment"] = validation.get("agency_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_mesh_handoffs(self) -> list[dict[str, Any]]:
        """40c: repeated organ mesh edges → SCC-1 organ_collaborator candidates."""
        try:
            from src.culture_habit_registry import adopted_habits as culture_adopted

            habits = culture_adopted(repo_root=self._repo_root)
        except Exception:
            return []

        edge_counts: Counter[str] = Counter()
        for habit in habits:
            if not habit.get("operator_promoted"):
                continue
            src = str(habit.get("source_family_id") or "")
            tgt = str(habit.get("target_family_id") or "")
            if src and tgt:
                edge_counts[f"{src}->{tgt}"] += int(habit.get("occurrence_count") or 1)

        candidates: list[dict[str, Any]] = []
        for edge_key, count in edge_counts.most_common(8):
            if count < 2:
                continue
            src, tgt = edge_key.split("->", 1)
            summary = f"Organ mesh collaborator bond: {src} → {tgt} ({count} handoffs)"
            candidate = self._build_candidate(
                summary=summary,
                bond_kind="organ_collaborator",
                counterparty_ref={"organ_family_id": tgt, "source_family_id": src},
                trust_posture="mesh_verified",
                evidence_refs=[f"mesh:{edge_key}"],
                stability_score=min(float(count) / 10.0, 1.0),
                scc_class="SCC-1",
                source_layers={"mesh_edge": edge_key},
                interaction_count=count,
            )
            validation = validate_bond_against_identity_narrative_and_agency(
                candidate, repo_root=self._repo_root
            )
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            candidate["agency_alignment"] = validation.get("agency_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_ledger_scopes(self) -> list[dict[str, Any]]:
        """40c: repeated tenant/session scopes with federation → SCC-1 scope bond candidates."""
        scope_counts: Counter[str] = Counter()
        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            for row in operator_decision_ledger_store.list_events("global", since=since, limit=500):
                tenant = str(row.get("tenant_id") or "")
                if tenant:
                    scope_counts[tenant] += 1
                fed = dict(row.get("federation") or {})
                grant_id = str(fed.get("grant_id") or "")
                if grant_id:
                    scope_counts[f"grant:{grant_id}"] += 1
        except Exception:
            return []

        candidates: list[dict[str, Any]] = []
        for scope_key, count in scope_counts.most_common(6):
            if count < 2:
                continue
            bond_kind = "federated_peer" if scope_key.startswith("grant:") else "workflow_counterparty"
            summary = f"Repeated relational scope: {scope_key} ({count} interactions)"
            candidate = self._build_candidate(
                summary=summary,
                bond_kind=bond_kind,
                counterparty_ref={"scope": scope_key},
                trust_posture="ledger_verified",
                evidence_refs=[f"scope:{scope_key}"],
                stability_score=min(float(count) / 8.0, 1.0),
                scc_class="SCC-1",
                source_layers={"ledger_scope": scope_key},
                interaction_count=count,
            )
            validation = validate_bond_against_identity_narrative_and_agency(
                candidate, repo_root=self._repo_root
            )
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            candidate["agency_alignment"] = validation.get("agency_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def _build_candidate(
        self,
        *,
        summary: str,
        bond_kind: str,
        counterparty_ref: dict[str, Any],
        trust_posture: str,
        evidence_refs: list[str],
        stability_score: float,
        scc_class: str = "SCC-1",
        **extra: Any,
    ) -> dict[str, Any]:
        return {
            "bond_version": BOND_VERSION,
            "candidate_id": f"scand_{uuid4().hex[:12]}",
            "bond_kind": bond_kind,
            "counterparty_ref": counterparty_ref,
            "trust_posture": trust_posture,
            "summary": summary[:500],
            "evidence_refs": evidence_refs,
            "stability_score": stability_score,
            "identity_alignment": False,
            "narrative_alignment": False,
            "agency_alignment": False,
            "interaction_count": int(extra.pop("interaction_count", 0)),
            "claim_label": "asserted",
            "operator_promoted": False,
            "scc_class": scc_class,
            **extra,
        }

    def _persist_candidate(self, candidate: dict[str, Any]) -> None:
        cid = str(candidate.get("candidate_id") or f"scand_{uuid4().hex[:12]}")
        candidate["candidate_id"] = cid
        with self._lock:
            self._candidates_dir.mkdir(parents=True, exist_ok=True)
            path = self._candidates_dir / f"{cid}.json"
            path.write_text(json.dumps(candidate, sort_keys=True) + "\n", encoding="utf-8")

    def list_candidates(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self._candidates_dir.is_dir():
            return []
        rows: list[dict[str, Any]] = []
        for path in sorted(self._candidates_dir.glob("*.json"), reverse=True)[:limit]:
            try:
                rows.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return rows

    def rank_social_candidates(self, text: str = "") -> list[dict[str, Any]]:
        candidates = self.list_candidates(limit=100)
        if not candidates:
            observed = self.observe_social_drift()
            candidates = list(observed.get("candidates") or [])
        lowered = str(text or "").lower()

        def score(item: dict[str, Any]) -> float:
            base = float(item.get("stability_score") or 0)
            if item.get("identity_alignment"):
                base += 3.0
            if item.get("narrative_alignment"):
                base += 2.0
            if item.get("agency_alignment"):
                base += 2.0
            base += min(float(item.get("interaction_count") or 0) / 5.0, 2.0)
            stmt = str(item.get("summary") or "").lower()
            ref = json.dumps(item.get("counterparty_ref") or {}).lower()
            if lowered and (any(word in stmt for word in lowered.split() if len(word) > 3) or lowered in ref):
                base += 2.0
            return base

        return sorted(candidates, key=score, reverse=True)[:8]

    def adopt_social_bond(
        self,
        candidate: dict[str, Any],
        *,
        operator_approved: bool = False,
        jarvis_authorization: dict[str, Any] | None = None,
        session_id: str = "global",
    ) -> dict[str, Any]:
        if not operator_approved:
            return {"outcome": "blocked", "reason": "operator_approved required", "status": 403}
        auth = dict(jarvis_authorization or {})
        if not auth.get("authorized"):
            return {"outcome": "blocked", "reason": "jarvis_not_authorized", "status": 403}
        if not candidate:
            return {"outcome": "blocked", "reason": "empty_candidate"}

        validation = validate_bond_against_identity_narrative_and_agency(
            candidate, repo_root=self._repo_root
        )
        if not validation.get("aligned"):
            return {
                "outcome": "blocked",
                "reason": "alignment_validation_failed",
                "violations": validation.get("violations"),
            }

        bond_id = f"bond_{uuid4().hex[:12]}"
        bond = {
            "bond_version": BOND_VERSION,
            "bond_id": bond_id,
            "bond_kind": str(candidate.get("bond_kind") or "operator_dyad"),
            "counterparty_ref": dict(candidate.get("counterparty_ref") or {}),
            "trust_posture": str(candidate.get("trust_posture") or "governed"),
            "summary": str(candidate.get("summary") or "")[:500],
            "evidence_refs": list(candidate.get("evidence_refs") or []),
            "source_layers": dict(candidate.get("source_layers") or {}),
            "identity_alignment": True,
            "narrative_alignment": True,
            "agency_alignment": True,
            "stability_score": float(candidate.get("stability_score") or 0),
            "interaction_count": int(candidate.get("interaction_count") or 0),
            "claim_label": "asserted",
            "operator_promoted": True,
            "scc_class": "SCC-2",
            "candidate_id": candidate.get("candidate_id"),
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
        }
        save_adopted_bond(bond, repo_root=self._repo_root)
        self._write_archive_slot(bond)
        self._emit_social_adoption_ledger(session_id, bond)
        return {"outcome": "adopted", "bond": bond, "scc_class": "SCC-2"}

    def _write_archive_slot(self, bond: dict[str, Any]) -> None:
        with self._lock:
            payload: dict[str, Any] = {}
            if self._archive_path.is_file():
                try:
                    payload = json.loads(self._archive_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
            bonds = list(payload.get("adopted_bonds") or [])
            bonds = [b for b in bonds if str(b.get("bond_id")) != str(bond.get("bond_id"))]
            bonds.append(bond)
            payload = {
                "archive_overlay_version": "jarvis_memory_board_archive.v1",
                "slot_id": "slot_04",
                "module_id": "capability_archive_v2",
                "adopted_bonds": bonds,
                "updated_at": _utc_now_iso(),
            }
            self._archive_path.parent.mkdir(parents=True, exist_ok=True)
            self._archive_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def social_posture(self) -> dict[str, Any]:
        candidates = self.list_candidates(limit=200)
        adopted = adopted_bonds(repo_root=self._repo_root)
        drift_count = len([c for c in candidates if not c.get("identity_alignment")])
        federated = len([b for b in adopted if b.get("bond_kind") == "federated_peer"])
        return {
            "candidate_bonds": len(candidates),
            "adopted_bonds": len(adopted),
            "social_drift_events": drift_count,
            "identity_aligned": drift_count == 0,
            "narrative_aligned": drift_count == 0,
            "agency_aligned": drift_count == 0,
            "federated_peer_count": federated,
            "claim_label": "asserted",
        }

    def social_snapshot(self) -> dict[str, Any]:
        return {
            "social_version": "operator_social.v1",
            "posture": self.social_posture(),
            "adopted_bonds": adopted_bonds(repo_root=self._repo_root),
            "recent_candidates": self.list_candidates(limit=20),
            "federation_summary": self._federation_summary(),
            "claim_label": "asserted",
        }

    def _emit_social_adoption_ledger(self, session_id: str, bond: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_social_adoption_event

            append_social_adoption_event(session_id, bond=bond)
        except Exception:
            pass

    def _emit_social_drift_ledger(self, session_id: str, drift: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_social_drift_event

            append_social_drift_event(session_id, drift=drift)
        except Exception:
            pass


social_continuity_runtime = SocialContinuityRuntime()
