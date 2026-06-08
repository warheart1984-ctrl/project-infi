"""Multi-being continuity runtime — cross-organism drift fusion and governed adoption (Stage 10 / Release 41)."""

# Mythic: Multi-Being Continuity Runtime
# Engineering: MultiBeingContinuityRuntimeEngine
from __future__ import annotations

import json
import os
import threading
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.multi_being_continuity_registry import PACT_VERSION, adopted_pacts, save_adopted_pact
from src.social_continuity_registry import adopted_bonds
from src.social_continuity_runtime import validate_bond_against_identity_narrative_and_agency

DRIFT_VERSION = "multi_being_drift.v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def validate_pact_against_identity_narrative_agency_and_social(
    pact: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Reject pacts that violate upstream layers or contradict adopted social bonds."""
    as_bond = {
        "summary": str(pact.get("summary") or ""),
        "bond_kind": "federated_peer",
    }
    bond_check = validate_bond_against_identity_narrative_and_agency(as_bond, repo_root=repo_root)
    violations = list(bond_check.get("violations") or [])
    social_aligned = True
    lowered = str(pact.get("summary") or "").lower()
    try:
        bonds = adopted_bonds(repo_root=repo_root)
        if bonds and any("override jarvis" in lowered or "bypass federation" in lowered):
            social_aligned = False
            violations.append("contradicts_social_posture")
    except Exception:
        pass
    aligned = bond_check.get("aligned") and social_aligned and len(violations) == 0
    return {
        "aligned": aligned,
        "identity_alignment": bool(bond_check.get("identity_alignment")),
        "narrative_alignment": bool(bond_check.get("narrative_alignment")),
        "agency_alignment": bool(bond_check.get("agency_alignment")),
        "social_alignment": social_aligned,
        "violations": violations,
        "claim_label": "asserted" if aligned else "rejected",
    }


class MultiBeingContinuityRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "multi_being_pact_candidates"
        self._federation_path = self._runtime_dir / "jarvis_memory_board_federation.v1.json"
        self._lock = threading.Lock()

    def observe_multi_being_drift(
        self,
        *,
        session_id: str | None = None,
        window_days: int = 30,
    ) -> dict[str, Any]:
        """MBC-0 observe-only drift from ledger, upstream postures, grants, graphs, receipts."""
        drift_events: list[dict[str, Any]] = []
        identity_posture = self._identity_posture_safe()
        narrative_posture = self._narrative_posture_safe()
        agency_posture = self._agency_posture_safe()
        social_posture = self._social_posture_safe()

        if not identity_posture.get("anchor_aligned", True):
            drift_events.append(
                self._drift_event(
                    severity="attention",
                    source="identity_posture",
                    summary="Identity posture misaligned with anchor",
                    identity_aligned=False,
                )
            )
        if not social_posture.get("identity_aligned", True):
            drift_events.append(
                self._drift_event(
                    severity="nominal",
                    source="social_posture",
                    summary="Social posture drift detected",
                    social_aligned=False,
                )
            )

        grants = self._accepted_federation_grants()
        digest_verified_count = 0
        for grant in grants:
            graph = self._safe_federation_graph(grant.grant_id)
            if graph.get("digest_verified"):
                digest_verified_count += 1

        if grants:
            drift_events.append(
                self._drift_event(
                    severity="nominal",
                    source="federation_grants",
                    summary=f"{len(grants)} accepted grant(s); {digest_verified_count} digest-verified",
                )
            )

        scopes = [str(session_id)] if session_id else ["global"]
        cross_tenant = 0
        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=max(1, window_days))).isoformat()
            for scope in scopes:
                for row in operator_decision_ledger_store.list_events(scope, since=since, limit=500):
                    if row.get("federation"):
                        cross_tenant += 1
                    kind = str(row.get("decision_kind") or "")
                    if kind in {"multi_being_drift", "social_drift", "autobiographical_drift"}:
                        drift_events.append(
                            self._drift_event(
                                severity="nominal",
                                source=f"ledger:{kind}",
                                summary=str(row.get("summary") or "")[:120],
                            )
                        )
        except Exception:
            pass

        candidates = self.surface_pact_candidates()
        for ladder_fn in (
            self.candidates_from_adopted_bonds,
            self.candidates_from_federation_grants,
            self.candidates_from_federation_graphs,
            self.candidates_from_mesh_clusters,
            self.candidates_from_paired_receipts,
        ):
            for item in ladder_fn():
                candidates.append(item)

        for candidate in candidates:
            self._persist_candidate(candidate)

        result = {
            "outcome": "observed",
            "mbc_class": "MBC-0",
            "drift_event_count": len(drift_events),
            "drift_events": drift_events,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "identity_aligned": identity_posture.get("anchor_aligned", True),
            "narrative_aligned": narrative_posture.get("identity_aligned", True),
            "agency_aligned": agency_posture.get("identity_aligned", True),
            "social_aligned": social_posture.get("identity_aligned", True),
            "digest_verified_count": digest_verified_count,
            "cross_organism_peer_count": len(grants),
            "cross_tenant_decisions": cross_tenant,
            "window_days": window_days,
            "federation_summary": self._federation_summary(),
            "claim_label": "asserted",
            "summary": f"Multi-being drift observed: {len(drift_events)} events, {len(candidates)} candidates",
        }
        if session_id:
            self._emit_multi_being_drift_ledger(session_id, result)
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

    def _social_posture_safe(self) -> dict[str, Any]:
        try:
            from src.social_continuity_runtime import social_continuity_runtime

            return social_continuity_runtime.social_posture()
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

    def _safe_federation_graph(self, grant_id: str) -> dict[str, Any]:
        try:
            from src.operator_decision_ledger import build_federation_graph

            home = os.getenv("UGR_HOME_TENANT", "tenant:acme")
            return build_federation_graph(
                grant_id,
                home_tenant_id=home.replace("tenant:", "") if home.startswith("tenant:") else home,
            )
        except Exception:
            return {}

    def _federation_summary(self) -> dict[str, Any]:
        grants = self._accepted_federation_grants()
        verified = sum(1 for g in grants if self._safe_federation_graph(g.grant_id).get("digest_verified"))
        return {
            "accepted_grant_count": len(grants),
            "digest_verified_count": verified,
            "grant_ids": [g.grant_id for g in grants[:8]],
        }

    def _drift_event(
        self,
        *,
        severity: str,
        source: str,
        summary: str,
        identity_aligned: bool = True,
        narrative_aligned: bool = True,
        agency_aligned: bool = True,
        social_aligned: bool = True,
    ) -> dict[str, Any]:
        return {
            "drift_version": DRIFT_VERSION,
            "drift_id": f"mdrift_{uuid4().hex[:12]}",
            "severity": severity,
            "source": source,
            "summary": summary,
            "identity_aligned": identity_aligned,
            "narrative_aligned": narrative_aligned,
            "agency_aligned": agency_aligned,
            "social_aligned": social_aligned,
            "mbc_class": "MBC-0",
            "observed_at": _utc_now_iso(),
        }

    def surface_pact_candidates(self) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        grants = self._accepted_federation_grants()
        if grants:
            grant = grants[0]
            candidate = self._build_candidate(
                summary=f"Cross-organism continuity posture for grant {grant.grant_id}",
                pact_kind="bilateral_organism",
                counterparty_organism_ref={
                    "tenant_id": grant.grantee_tenant,
                    "grant_id": grant.grant_id,
                },
                continuity_posture="federation_observed",
                trust_tier="governed_bilateral",
                evidence_refs=[f"grant:{grant.grant_id}"],
                stability_score=0.7,
                mbc_class="MBC-1",
            )
            validation = validate_pact_against_identity_narrative_agency_and_social(
                candidate, repo_root=self._repo_root
            )
            if validation.get("aligned"):
                candidate.update(
                    {
                        "identity_alignment": validation.get("identity_alignment"),
                        "narrative_alignment": validation.get("narrative_alignment"),
                        "agency_alignment": validation.get("agency_alignment"),
                        "social_alignment": validation.get("social_alignment"),
                    }
                )
                candidates.append(candidate)
        return candidates

    def candidates_from_adopted_bonds(self) -> list[dict[str, Any]]:
        """41c: SCC-2 bonds → MBC-1 pact candidates only."""
        try:
            bonds = adopted_bonds(repo_root=self._repo_root)
        except Exception:
            return []

        candidates: list[dict[str, Any]] = []
        for bond in bonds:
            if not bond.get("operator_promoted"):
                continue
            kind = str(bond.get("bond_kind") or "")
            if kind not in {"federated_peer", "organ_collaborator"}:
                continue
            pact_kind = "bilateral_organism" if kind == "federated_peer" else "federated_mesh_cluster"
            summary = f"Multi-being pact from social bond: {bond.get('summary', '')[:300]}"
            candidate = self._build_candidate(
                summary=summary,
                pact_kind=pact_kind,
                counterparty_organism_ref=dict(bond.get("counterparty_ref") or {}),
                continuity_posture="social_grounded",
                trust_tier=str(bond.get("trust_posture") or "archive_verified"),
                evidence_refs=[f"bond:{bond.get('bond_id')}"],
                stability_score=float(bond.get("stability_score") or 0.8),
                mbc_class="MBC-1",
                source_layers={"bond_id": bond.get("bond_id")},
            )
            validation = validate_pact_against_identity_narrative_agency_and_social(
                candidate, repo_root=self._repo_root
            )
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            candidate["agency_alignment"] = validation.get("agency_alignment")
            candidate["social_alignment"] = validation.get("social_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_federation_grants(self) -> list[dict[str, Any]]:
        """41c: accepted UGR grants → MBC-1 bilateral_organism candidates."""
        candidates: list[dict[str, Any]] = []
        for grant in self._accepted_federation_grants():
            summary = f"Bilateral organism pact: {grant.issuer_tenant} ↔ {grant.grantee_tenant}"
            candidate = self._build_candidate(
                summary=summary,
                pact_kind="bilateral_organism",
                counterparty_organism_ref={
                    "tenant_id": grant.grantee_tenant,
                    "grant_id": grant.grant_id,
                    "organism_id": grant.grantee_tenant,
                },
                continuity_posture="grant_active",
                trust_tier="bilateral_federation",
                evidence_refs=[f"grant:{grant.grant_id}"],
                stability_score=0.9,
                mbc_class="MBC-1",
                source_layers={"grant_id": grant.grant_id},
                digest_verified=False,
            )
            validation = validate_pact_against_identity_narrative_agency_and_social(
                candidate, repo_root=self._repo_root
            )
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            candidate["agency_alignment"] = validation.get("agency_alignment")
            candidate["social_alignment"] = validation.get("social_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_federation_graphs(self) -> list[dict[str, Any]]:
        """41c: verified dual-ledger graphs → MBC-1 cross_machine_peer candidates."""
        candidates: list[dict[str, Any]] = []
        for grant in self._accepted_federation_grants():
            graph = self._safe_federation_graph(grant.grant_id)
            if not graph.get("digest_verified"):
                continue
            summary = f"Cross-machine peer pact (digest verified): {grant.grant_id}"
            candidate = self._build_candidate(
                summary=summary,
                pact_kind="cross_machine_peer",
                counterparty_organism_ref={
                    "tenant_id": grant.grantee_tenant,
                    "grant_id": grant.grant_id,
                    "federation_digest": graph.get("federation_digest"),
                },
                continuity_posture="digest_verified",
                trust_tier="dual_ledger",
                evidence_refs=[f"graph:{grant.grant_id}"],
                stability_score=0.95,
                mbc_class="MBC-1",
                source_layers={"grant_id": grant.grant_id},
                digest_verified=True,
            )
            validation = validate_pact_against_identity_narrative_agency_and_social(
                candidate, repo_root=self._repo_root
            )
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            candidate["agency_alignment"] = validation.get("agency_alignment")
            candidate["social_alignment"] = validation.get("social_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_mesh_clusters(self) -> list[dict[str, Any]]:
        """41c: cross-tenant mesh signals → MBC-1 federated_mesh_cluster candidates."""
        cluster_counts: Counter[str] = Counter()
        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            for row in operator_decision_ledger_store.list_events("global", since=since, limit=500):
                if str(row.get("decision_kind") or "") != "organ_mesh_run":
                    continue
                fed = dict(row.get("federation") or {})
                if fed.get("grant_id"):
                    cluster_counts[str(fed.get("grant_id"))] += 1
        except Exception:
            return []

        candidates: list[dict[str, Any]] = []
        for grant_id, count in cluster_counts.most_common(6):
            if count < 2:
                continue
            summary = f"Federated mesh cluster pact: {grant_id} ({count} cross-tenant mesh runs)"
            candidate = self._build_candidate(
                summary=summary,
                pact_kind="federated_mesh_cluster",
                counterparty_organism_ref={"grant_id": grant_id},
                continuity_posture="mesh_cluster",
                trust_tier="mesh_verified",
                evidence_refs=[f"mesh_cluster:{grant_id}"],
                stability_score=min(float(count) / 10.0, 1.0),
                mbc_class="MBC-1",
                source_layers={"grant_id": grant_id, "mesh_run_count": count},
            )
            validation = validate_pact_against_identity_narrative_agency_and_social(
                candidate, repo_root=self._repo_root
            )
            candidate["identity_alignment"] = validation.get("identity_alignment")
            candidate["narrative_alignment"] = validation.get("narrative_alignment")
            candidate["agency_alignment"] = validation.get("agency_alignment")
            candidate["social_alignment"] = validation.get("social_alignment")
            if validation.get("aligned"):
                candidates.append(candidate)
        return candidates

    def candidates_from_paired_receipts(self) -> list[dict[str, Any]]:
        """41c: resolvable counterparty receipt refs → MBC-1 continuity candidates."""
        candidates: list[dict[str, Any]] = []
        seen: set[str] = set()
        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            for row in operator_decision_ledger_store.list_events("global", since=since, limit=200):
                fed = dict(row.get("federation") or {})
                ref = dict(fed.get("counterparty_receipt_ref") or {})
                if not ref:
                    continue
                key = json.dumps(ref, sort_keys=True)
                if key in seen:
                    continue
                seen.add(key)
                summary = f"Paired receipt continuity: {ref.get('tenant_id', 'peer')} mission {ref.get('mission_id', '')[:16]}"
                candidate = self._build_candidate(
                    summary=summary,
                    pact_kind="cross_machine_peer",
                    counterparty_organism_ref=ref,
                    continuity_posture="receipt_paired",
                    trust_tier="receipt_verified",
                    evidence_refs=[f"receipt:{ref.get('mission_id', 'unknown')}"],
                    stability_score=0.85,
                    mbc_class="MBC-1",
                    source_layers={"counterparty_receipt_ref": ref},
                )
                validation = validate_pact_against_identity_narrative_agency_and_social(
                    candidate, repo_root=self._repo_root
                )
                candidate["identity_alignment"] = validation.get("identity_alignment")
                candidate["narrative_alignment"] = validation.get("narrative_alignment")
                candidate["agency_alignment"] = validation.get("agency_alignment")
                candidate["social_alignment"] = validation.get("social_alignment")
                if validation.get("aligned"):
                    candidates.append(candidate)
        except Exception:
            pass
        return candidates[:6]

    def _build_candidate(
        self,
        *,
        summary: str,
        pact_kind: str,
        counterparty_organism_ref: dict[str, Any],
        continuity_posture: str,
        trust_tier: str,
        evidence_refs: list[str],
        stability_score: float,
        mbc_class: str = "MBC-1",
        **extra: Any,
    ) -> dict[str, Any]:
        return {
            "pact_version": PACT_VERSION,
            "candidate_id": f"mcand_{uuid4().hex[:12]}",
            "pact_kind": pact_kind,
            "counterparty_organism_ref": counterparty_organism_ref,
            "continuity_posture": continuity_posture,
            "trust_tier": trust_tier,
            "summary": summary[:500],
            "evidence_refs": evidence_refs,
            "stability_score": stability_score,
            "identity_alignment": False,
            "narrative_alignment": False,
            "agency_alignment": False,
            "social_alignment": False,
            "digest_verified": bool(extra.pop("digest_verified", False)),
            "claim_label": "asserted",
            "operator_promoted": False,
            "mbc_class": mbc_class,
            **extra,
        }

    def _persist_candidate(self, candidate: dict[str, Any]) -> None:
        cid = str(candidate.get("candidate_id") or f"mcand_{uuid4().hex[:12]}")
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

    def rank_multi_being_candidates(self, text: str = "") -> list[dict[str, Any]]:
        candidates = self.list_candidates(limit=100)
        if not candidates:
            observed = self.observe_multi_being_drift()
            candidates = list(observed.get("candidates") or [])
        lowered = str(text or "").lower()

        def score(item: dict[str, Any]) -> float:
            base = float(item.get("stability_score") or 0)
            for flag in ("identity_alignment", "narrative_alignment", "agency_alignment", "social_alignment"):
                if item.get(flag):
                    base += 2.0
            if item.get("digest_verified"):
                base += 3.0
            stmt = str(item.get("summary") or "").lower()
            ref = json.dumps(item.get("counterparty_organism_ref") or {}).lower()
            if lowered and (any(word in stmt for word in lowered.split() if len(word) > 3) or lowered in ref):
                base += 2.0
            return base

        return sorted(candidates, key=score, reverse=True)[:8]

    def adopt_multi_being_pact(
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

        validation = validate_pact_against_identity_narrative_agency_and_social(
            candidate, repo_root=self._repo_root
        )
        if not validation.get("aligned"):
            return {
                "outcome": "blocked",
                "reason": "alignment_validation_failed",
                "violations": validation.get("violations"),
            }

        pact_id = f"pact_{uuid4().hex[:12]}"
        pact = {
            "pact_version": PACT_VERSION,
            "pact_id": pact_id,
            "pact_kind": str(candidate.get("pact_kind") or "bilateral_organism"),
            "counterparty_organism_ref": dict(candidate.get("counterparty_organism_ref") or {}),
            "continuity_posture": str(candidate.get("continuity_posture") or "governed"),
            "trust_tier": str(candidate.get("trust_tier") or "governed_bilateral"),
            "summary": str(candidate.get("summary") or "")[:500],
            "evidence_refs": list(candidate.get("evidence_refs") or []),
            "source_layers": dict(candidate.get("source_layers") or {}),
            "identity_alignment": True,
            "narrative_alignment": True,
            "agency_alignment": True,
            "social_alignment": True,
            "stability_score": float(candidate.get("stability_score") or 0),
            "digest_verified": bool(candidate.get("digest_verified")),
            "claim_label": "asserted",
            "operator_promoted": True,
            "mbc_class": "MBC-2",
            "candidate_id": candidate.get("candidate_id"),
            "jarvis_receipt_id": auth.get("jarvis_receipt_id"),
        }
        save_adopted_pact(pact, repo_root=self._repo_root)
        self._write_federation_slot(pact)
        self._emit_multi_being_adoption_ledger(session_id, pact)
        return {"outcome": "adopted", "pact": pact, "mbc_class": "MBC-2"}

    def _write_federation_slot(self, pact: dict[str, Any]) -> None:
        with self._lock:
            payload: dict[str, Any] = {}
            if self._federation_path.is_file():
                try:
                    payload = json.loads(self._federation_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
            pacts = list(payload.get("adopted_pacts") or [])
            pacts = [p for p in pacts if str(p.get("pact_id")) != str(pact.get("pact_id"))]
            pacts.append(pact)
            payload = {
                "federation_overlay_version": "jarvis_memory_board_federation.v1",
                "slot_id": "slot_07",
                "module_id": "capability_federation_v1",
                "adopted_pacts": pacts,
                "updated_at": _utc_now_iso(),
            }
            self._federation_path.parent.mkdir(parents=True, exist_ok=True)
            self._federation_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def multi_being_posture(self) -> dict[str, Any]:
        candidates = self.list_candidates(limit=200)
        adopted = adopted_pacts(repo_root=self._repo_root)
        drift_count = len([c for c in candidates if not c.get("identity_alignment")])
        digest_verified = len([p for p in adopted if p.get("digest_verified")])
        cross_peers = len([p for p in adopted if p.get("pact_kind") in {"bilateral_organism", "cross_machine_peer"}])
        return {
            "candidate_pacts": len(candidates),
            "adopted_pacts": len(adopted),
            "multi_being_drift_events": drift_count,
            "identity_aligned": drift_count == 0,
            "narrative_aligned": drift_count == 0,
            "agency_aligned": drift_count == 0,
            "social_aligned": drift_count == 0,
            "digest_verified_count": digest_verified,
            "cross_organism_peer_count": cross_peers,
            "claim_label": "asserted",
        }

    def multi_being_snapshot(self) -> dict[str, Any]:
        return {
            "multi_being_version": "operator_multi_being.v1",
            "posture": self.multi_being_posture(),
            "adopted_pacts": adopted_pacts(repo_root=self._repo_root),
            "recent_candidates": self.list_candidates(limit=20),
            "federation_summary": self._federation_summary(),
            "claim_label": "asserted",
        }

    def _emit_multi_being_adoption_ledger(self, session_id: str, pact: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_multi_being_adoption_event

            append_multi_being_adoption_event(session_id, pact=pact)
        except Exception:
            pass

    def _emit_multi_being_drift_ledger(self, session_id: str, drift: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_multi_being_drift_event

            append_multi_being_drift_event(session_id, drift=drift)
        except Exception:
            pass


multi_being_continuity_runtime = MultiBeingContinuityRuntime()
