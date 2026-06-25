"""Append-only Discovery Pod ledger — durable record of every registered pod name."""

# Engineering: DiscoveryPodLedgerEngine

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
import re
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.ugr.discovery.proven_contribution import is_proven_contribution
from src.ugr.discovery.standing import (
    build_epistemic_envelope,
    epistemic_from_receipt,
    standing_from_receipt,
)

LEDGER_ID = "ugr.discovery.pods"
LEDGER_VERSION = "1.0"
EVENT_POD_REGISTERED = "pod_registered"
EVENT_POD_DISCOVERED = "pod_discovered"
EVENT_POD_PROVEN = "pod_proven"
EVENT_POD_ARC_REACTIVATED = "pod_arc_reactivated"
EVENT_POD_ARC_RELABELLED = "pod_arc_relabelled"

LEDGER_PATH_ENV = "UGR_DISCOVERY_POD_LEDGER_PATH"
REGISTRY_PATH_ENV = "UGR_DISCOVERY_POD_REGISTRY_PATH"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_ledger_path() -> Path:
    override = os.environ.get(LEDGER_PATH_ENV, "").strip()
    if override:
        return Path(override)
    return _repo_root() / "docs" / "proof" / "discovery" / "discovery-pods.jsonl"


def default_registry_path() -> Path:
    override = os.environ.get(REGISTRY_PATH_ENV, "").strip()
    if override:
        return Path(override)
    return _repo_root() / "deploy" / "ugr" / "discovery-pods.json"


def slugify_pod_name(display_name: str) -> str:
    """Turn a human display name into a stable pod slug (lowercase, hyphenated)."""
    raw = str(display_name or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return slug or "unnamed"


def pod_id_from_display_name(display_name: str) -> str:
    return f"pod:{slugify_pod_name(display_name)}"


def operator_id_from_display_name(display_name: str) -> str:
    return f"operator:{slugify_pod_name(display_name)}"


def display_name_from_slug(slug: str) -> str:
    parts = [part for part in str(slug or "").strip().split("-") if part]
    return " ".join(part.capitalize() for part in parts) or "Unnamed"


def id_slug_from_prefixed_id(value: str, *, prefix: str) -> str:
    raw = str(value or "").strip()
    needle = f"{prefix}:"
    if raw.startswith(needle):
        return raw[len(needle) :]
    return slugify_pod_name(raw)


def resolve_pod_context(
    *,
    operator_id: str = "",
    spec_payload: dict[str, Any] | None = None,
    ledger: DiscoveryPodLedger | None = None,
) -> dict[str, str] | None:
    """Resolve pod identity from a contribution discovery payload."""
    payload = dict(spec_payload or {})
    ledger = ledger or DiscoveryPodLedger()

    pod_id = str(payload.get("discovery_pod_id") or payload.get("pod_id") or "").strip()
    display_name = str(
        payload.get("pod_display_name") or payload.get("display_name") or ""
    ).strip()
    op_id = str(operator_id or payload.get("operator_id") or "").strip()

    if pod_id:
        existing = ledger.get_by_pod_id(pod_id)
        if existing and not display_name:
            display_name = str(existing.get("display_name") or "").strip()
        if not display_name:
            display_name = display_name_from_slug(id_slug_from_prefixed_id(pod_id, prefix="pod"))

    if not pod_id and display_name:
        pod_id = pod_id_from_display_name(display_name)

    if not pod_id and op_id:
        slug = ""
        if op_id.startswith("operator:"):
            slug = id_slug_from_prefixed_id(op_id, prefix="operator")
        elif ":" not in op_id:
            slug = slugify_pod_name(op_id)
        if slug:
            pod_id = f"pod:{slug}"
            existing = ledger.get_by_pod_id(pod_id)
            if existing and not display_name:
                display_name = str(existing.get("display_name") or "").strip()
            if not display_name:
                display_name = display_name_from_slug(slug)
            if not op_id.startswith("operator:"):
                op_id = f"operator:{slug}"

    if not pod_id or not display_name:
        return None

    if not op_id:
        op_id = operator_id_from_display_name(display_name)

    return {
        "pod_id": pod_id,
        "display_name": display_name,
        "operator_id": op_id,
    }


@dataclass
class PodRegisterResult:
    ok: bool
    idempotent: bool = False
    pod_id: str = ""
    operator_id: str = ""
    pod_index: int = 0
    display_name: str = ""
    event_id: str = ""
    errors: list[str] = field(default_factory=list)
    record: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "idempotent": self.idempotent,
            "pod_id": self.pod_id,
            "operator_id": self.operator_id,
            "pod_index": self.pod_index,
            "display_name": self.display_name,
            "event_id": self.event_id,
            "errors": list(self.errors),
            "record": dict(self.record),
        }


@dataclass
class PodDiscoveryResult:
    ok: bool
    skipped: bool = False
    skip_reason: str = ""
    newly_registered: bool = False
    pod_id: str = ""
    operator_id: str = ""
    display_name: str = ""
    event_id: str = ""
    discovery_count: int = 0
    admission: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    record: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "ok": self.ok,
            "skipped": self.skipped,
            "newly_registered": self.newly_registered,
            "pod_id": self.pod_id,
            "operator_id": self.operator_id,
            "display_name": self.display_name,
            "event_id": self.event_id,
            "discovery_count": self.discovery_count,
            "errors": list(self.errors),
            "record": dict(self.record),
        }
        if self.skip_reason:
            out["skip_reason"] = self.skip_reason
        if self.admission:
            out["admission"] = dict(self.admission)
        return out


class DiscoveryPodLedger:
    """Append-only JSONL ledger plus derived registry snapshot."""

    def __init__(
        self,
        ledger_path: str | Path | None = None,
        registry_path: str | Path | None = None,
    ):
        self.ledger_path = Path(ledger_path or default_ledger_path())
        self.registry_path = Path(registry_path or default_registry_path())
        self._lock = threading.Lock()

    def _read_lines(self) -> list[dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows

    def list_entries(self, *, event_type: str | None = None) -> list[dict[str, Any]]:
        rows = self._read_lines()
        if event_type:
            rows = [r for r in rows if str(r.get("event_type") or "") == event_type]
        return rows

    def list_pods(self) -> list[dict[str, Any]]:
        return self.list_entries(event_type=EVENT_POD_REGISTERED)

    def list_pod_discoveries(self, *, pod_id: str | None = None) -> list[dict[str, Any]]:
        rows = self.list_entries(event_type=EVENT_POD_DISCOVERED)
        if pod_id:
            pid = str(pod_id).strip()
            rows = [r for r in rows if str(r.get("pod_id") or "") == pid]
        return rows

    def list_pod_arc_reactivated(self, *, pod_id: str | None = None) -> list[dict[str, Any]]:
        rows = self.list_entries(event_type=EVENT_POD_ARC_REACTIVATED)
        if pod_id:
            pid = str(pod_id).strip()
            rows = [r for r in rows if str(r.get("pod_id") or "") == pid]
        return rows

    def list_pod_arc_relabelled(self, *, pod_id: str | None = None) -> list[dict[str, Any]]:
        rows = self.list_entries(event_type=EVENT_POD_ARC_RELABELLED)
        if pod_id:
            pid = str(pod_id).strip()
            rows = [r for r in rows if str(r.get("pod_id") or "") == pid]
        return rows

    def list_pod_proven(self, *, pod_id: str | None = None) -> list[dict[str, Any]]:
        rows = self.list_entries(event_type=EVENT_POD_PROVEN)
        if pod_id:
            pid = str(pod_id).strip()
            rows = [r for r in rows if str(r.get("pod_id") or "") == pid]
        return rows

    def discovery_stats(self, pod_id: str) -> dict[str, Any]:
        events = self.list_pod_discoveries(pod_id=pod_id)
        if not events:
            return {"discovery_count": 0}
        last = events[-1]
        return {
            "discovery_count": len(events),
            "last_discovered_at_utc": last.get("recorded_at_utc"),
            "last_contribution_id": last.get("contribution_id"),
            "last_contribution_type": last.get("contribution_type"),
            "last_receipt_id": last.get("receipt_id"),
        }

    def arc_stats(self, pod_id: str) -> dict[str, Any]:
        """Highest multiplier from arc-bearing events; narrative tier from latest relabel."""
        from src.ugr.discovery.pod_arc_multiplier import TIER_NONE, tier_rank

        tier = TIER_NONE
        multiplier = 1.0
        arc_rows = (
            self.list_pod_discoveries(pod_id=pod_id)
            + self.list_pod_proven(pod_id=pod_id)
            + self.list_pod_arc_reactivated(pod_id=pod_id)
        )
        for row in arc_rows:
            row_tier = str(row.get("governance_arc_tier") or TIER_NONE)
            row_mult = float(row.get("pod_reward_multiplier") or 1.0)
            if tier_rank(row_tier) >= tier_rank(tier):
                if tier_rank(row_tier) > tier_rank(tier) or row_mult >= multiplier:
                    tier = row_tier
                    multiplier = max(multiplier, row_mult)

        relabels = self.list_pod_arc_relabelled(pod_id=pod_id)
        narrative_tier = tier
        narrative_note = ""
        if relabels:
            last_relabel = relabels[-1]
            narrative_tier = str(last_relabel.get("governance_arc_tier") or tier)
            narrative_note = str(last_relabel.get("narrative_note") or "")

        out: dict[str, Any] = {
            "governance_arc_tier": narrative_tier,
            "pod_reward_multiplier": multiplier if tier != TIER_NONE else 1.0,
        }
        if relabels:
            out["governance_arc_tier_economic"] = tier
            out["narrative_relabel_count"] = len(relabels)
            if narrative_note:
                out["narrative_note"] = narrative_note
        return out

    def proven_stats(self, pod_id: str) -> dict[str, Any]:
        events = self.list_pod_proven(pod_id=pod_id)
        if not events:
            return {"proven_count": 0, "total_reputation_awarded": 0.0}
        last = events[-1]
        total_rep = sum(float(e.get("reputation_awarded") or 0) for e in events)
        arc_events = self.list_pod_arc_reactivated(pod_id=pod_id)
        total_rep += sum(float(e.get("reputation_adjustment") or 0) for e in arc_events)
        last_rep = last.get("reputation_awarded")
        if arc_events:
            last_arc = arc_events[-1]
            last_time = str(last.get("recorded_at_utc") or "")
            arc_time = str(last_arc.get("recorded_at_utc") or "")
            if not last_time or not arc_time or arc_time >= last_time:
                last_rep = last_arc.get("reputation_awarded") or last_rep
        return {
            "proven_count": len(events),
            "total_reputation_awarded": total_rep,
            "last_proven_at_utc": last.get("recorded_at_utc"),
            "last_proven_contribution_id": last.get("contribution_id"),
            "last_reputation_awarded": last_rep,
            "last_reward_status": last.get("reward_status"),
        }

    def get_by_pod_id(self, pod_id: str) -> dict[str, Any] | None:
        pid = str(pod_id or "").strip()
        for row in reversed(self.list_pods()):
            if str(row.get("pod_id") or "") == pid:
                return row
        return None

    def get_by_display_name(self, display_name: str) -> dict[str, Any] | None:
        normalized = str(display_name or "").strip().casefold()
        if not normalized:
            return None
        for row in reversed(self.list_pods()):
            if str(row.get("display_name") or "").strip().casefold() == normalized:
                return row
        return None

    def _next_pod_index(self) -> int:
        pods = self.list_pods()
        if not pods:
            return 1
        return max(int(r.get("pod_index") or 0) for r in pods) + 1

    def register(
        self,
        display_name: str,
        *,
        label: str = "",
        notes: str = "",
        registered_by: str = "",
        status: str = "active",
    ) -> PodRegisterResult:
        name = str(display_name or "").strip()
        if not name:
            return PodRegisterResult(ok=False, errors=["display_name is required"])

        pod_id = pod_id_from_display_name(name)
        operator_id = operator_id_from_display_name(name)

        existing = self.get_by_pod_id(pod_id)
        if existing:
            return PodRegisterResult(
                ok=True,
                idempotent=True,
                pod_id=pod_id,
                operator_id=str(existing.get("operator_id") or operator_id),
                pod_index=int(existing.get("pod_index") or 0),
                display_name=str(existing.get("display_name") or name),
                event_id=str(existing.get("event_id") or ""),
                record=existing,
            )

        by_name = self.get_by_display_name(name)
        if by_name and str(by_name.get("pod_id") or "") != pod_id:
            return PodRegisterResult(
                ok=False,
                errors=[f"display_name already registered under pod_id {by_name.get('pod_id')}"],
            )

        pod_index = self._next_pod_index()
        event_id = f"pod-{uuid4().hex[:12]}"
        record = {
            "event_id": event_id,
            "event_type": EVENT_POD_REGISTERED,
            "ledger_id": LEDGER_ID,
            "ledger_version": LEDGER_VERSION,
            "recorded_at_utc": _utc_now_iso(),
            "pod_index": pod_index,
            "pod_id": pod_id,
            "display_name": name,
            "operator_id": operator_id,
            "label": str(label or "").strip(),
            "notes": str(notes or "").strip(),
            "registered_by": str(registered_by or "").strip(),
            "status": str(status or "active").strip() or "active",
        }

        with self._lock:
            duplicate = self.get_by_pod_id(pod_id)
            if duplicate:
                return PodRegisterResult(
                    ok=True,
                    idempotent=True,
                    pod_id=pod_id,
                    operator_id=str(duplicate.get("operator_id") or operator_id),
                    pod_index=int(duplicate.get("pod_index") or 0),
                    display_name=str(duplicate.get("display_name") or name),
                    event_id=str(duplicate.get("event_id") or ""),
                    record=duplicate,
                )
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with self.ledger_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")
            self.sync_registry()

        return PodRegisterResult(
            ok=True,
            pod_id=pod_id,
            operator_id=operator_id,
            pod_index=pod_index,
            display_name=name,
            event_id=event_id,
            record=record,
        )

    def record_discovery(
        self,
        *,
        operator_id: str,
        tenant_id: str,
        contribution_id: str,
        contribution_type: str,
        spec_payload: dict[str, Any] | None = None,
        receipt_id: str = "",
        receipt: dict[str, Any] | None = None,
        receipt_verified: bool | None = None,
        idempotent_rediscovery: bool = False,
        label: str = "",
    ) -> PodDiscoveryResult:
        ctx = resolve_pod_context(
            operator_id=operator_id,
            spec_payload=spec_payload,
            ledger=self,
        )
        if not ctx:
            return PodDiscoveryResult(ok=True, skipped=True, skip_reason="no_pod_context")

        pod_id = ctx["pod_id"]
        display_name = ctx["display_name"]
        op_id = ctx["operator_id"]

        existing_pod = self.get_by_pod_id(pod_id)
        admission: dict[str, Any] = {}
        if not existing_pod:
            from src.ugr.discovery.pod_admission import evaluate_pod_admission
            from src.ugr.discovery.pod_admission_metrics import (
                record_admission_admit,
                record_admission_skip,
            )

            slug = id_slug_from_prefixed_id(op_id, prefix="operator")
            verdict = evaluate_pod_admission(
                operator_id=op_id,
                contribution_type=contribution_type,
                spec_payload=spec_payload,
                receipt=receipt,
                receipt_verified=receipt_verified,
                operator_slug=slug,
            )
            admission = verdict.to_dict()
            if not verdict.eligible:
                record_admission_skip(verdict.reason)
                return PodDiscoveryResult(
                    ok=True,
                    skipped=True,
                    skip_reason=verdict.reason,
                    pod_id=pod_id,
                    operator_id=op_id,
                    display_name=display_name,
                    admission=admission,
                )
            record_admission_admit(verdict.reason)

        registration = self.register(
            display_name,
            label=label or f"Discovered via {contribution_type}",
            registered_by=operator_id,
        )
        if not registration.ok:
            return PodDiscoveryResult(
                ok=False,
                pod_id=pod_id,
                operator_id=op_id,
                display_name=display_name,
                errors=list(registration.errors),
            )

        event_id = f"pdisc-{uuid4().hex[:12]}"
        from src.ugr.discovery.pod_arc_multiplier import resolve_pod_arc_context

        arc = resolve_pod_arc_context(spec_payload=spec_payload, receipt=receipt)
        record = {
            "event_id": event_id,
            "event_type": EVENT_POD_DISCOVERED,
            "ledger_id": LEDGER_ID,
            "ledger_version": LEDGER_VERSION,
            "recorded_at_utc": _utc_now_iso(),
            "pod_id": pod_id,
            "display_name": display_name,
            "operator_id": op_id,
            "tenant_id": str(tenant_id or "").strip(),
            "contribution_id": str(contribution_id or "").strip(),
            "contribution_type": str(contribution_type or "").strip(),
            "receipt_id": str(receipt_id or "").strip(),
            "idempotent_rediscovery": bool(idempotent_rediscovery),
            "discovery_pod_id": str((spec_payload or {}).get("discovery_pod_id") or pod_id),
            **arc.to_dict(),
        }

        with self._lock:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with self.ledger_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")
            self.sync_registry()

        stats = self.discovery_stats(pod_id)
        return PodDiscoveryResult(
            ok=True,
            newly_registered=not registration.idempotent,
            pod_id=pod_id,
            operator_id=op_id,
            display_name=display_name,
            event_id=event_id,
            discovery_count=int(stats.get("discovery_count") or 0),
            admission=admission,
            record=record,
        )

    def record_proven(
        self,
        *,
        operator_id: str,
        tenant_id: str,
        contribution_id: str,
        contribution_type: str,
        spec_payload: dict[str, Any] | None = None,
        receipt_id: str = "",
        operator_rewards: dict[str, Any] | None = None,
        receipt: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ctx = resolve_pod_context(
            operator_id=operator_id,
            spec_payload=spec_payload,
            ledger=self,
        )
        if not ctx:
            return {"ok": True, "skipped": True, "skip_reason": "no_pod_context"}

        pod_id = ctx["pod_id"]
        display_name = ctx["display_name"]
        op_id = ctx["operator_id"]

        if not self.get_by_pod_id(pod_id):
            registration = self.register(
                display_name,
                label=f"Proven via {contribution_type}",
                registered_by=operator_id,
            )
            if not registration.ok:
                return {
                    "ok": False,
                    "pod_id": pod_id,
                    "errors": list(registration.errors),
                }

        rewards = dict(operator_rewards or {})
        reward_status = str(rewards.get("status") or "").strip()
        deltas = dict(rewards.get("deltas") or {})
        reputation_awarded = float(deltas.get("reputation") or 0)

        from src.ugr.discovery.pod_arc_multiplier import resolve_pod_arc_context

        arc = resolve_pod_arc_context(spec_payload=spec_payload)
        if str(deltas.get("governance_arc_tier") or ""):
            arc.tier = str(deltas["governance_arc_tier"])
        if float(deltas.get("pod_reward_multiplier") or 0) > 1.0:
            arc.multiplier = float(deltas["pod_reward_multiplier"])

        # Skip duplicate proven ledger rows when rewards were already issued earlier.
        if reward_status == "idempotent":
            existing = self.list_pod_proven(pod_id=pod_id)
            for row in existing:
                if str(row.get("contribution_id") or "") == str(contribution_id or "").strip():
                    return {"ok": True, "skipped": True, "idempotent": True, "pod_id": pod_id}

        event_id = f"pprov-{uuid4().hex[:12]}"
        receipt_obj = dict(receipt or {})
        if receipt_obj:
            payload = dict(receipt_obj.get("payload") or {})
            proof = dict(receipt_obj.get("proof") or {})
            epistemic = build_epistemic_envelope(
                standing_from_receipt(receipt_obj),
                claim_label=str(payload.get("claim_label") or proof.get("claim_label") or ""),
                rejection_source=str(
                    payload.get("rejection_source") or proof.get("rejection_source") or ""
                )
                or None,
                falsity_fingerprint=str(payload.get("falsity_fingerprint") or "") or None,
                contribution_id=str(receipt_obj.get("contribution_id") or "").strip() or None,
            )
        else:
            epistemic = {}
        record = {
            "event_id": event_id,
            "event_type": EVENT_POD_PROVEN,
            "ledger_id": LEDGER_ID,
            "ledger_version": LEDGER_VERSION,
            "recorded_at_utc": _utc_now_iso(),
            "pod_id": pod_id,
            "display_name": display_name,
            "operator_id": op_id,
            "tenant_id": str(tenant_id or "").strip(),
            "contribution_id": str(contribution_id or "").strip(),
            "contribution_type": str(contribution_type or "").strip(),
            "receipt_id": str(receipt_id or "").strip(),
            "reward_status": reward_status,
            "reputation_awarded": reputation_awarded,
            "rail_credits_awarded": float(
                deltas.get("earned_rail_credits") or deltas.get("rail_credits") or 0
            ),
            "reward_event_id": str(rewards.get("event_id") or ""),
            "epistemic_state": epistemic.get("epistemic_state")
            or (epistemic_from_receipt(receipt_obj).value if receipt_obj else ""),
            "rejection_source": epistemic.get("rejection_source"),
            **arc.to_dict(),
        }

        with self._lock:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with self.ledger_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")
            self.sync_registry()

        stats = self.proven_stats(pod_id)
        return {
            "ok": True,
            "pod_id": pod_id,
            "operator_id": op_id,
            "display_name": display_name,
            "event_id": event_id,
            "proven_count": int(stats.get("proven_count") or 0),
            "reputation_awarded": reputation_awarded,
            "reward_status": reward_status,
            "record": record,
        }

    def build_registry(self) -> dict[str, Any]:
        pods: dict[str, Any] = {}
        for row in self.list_pods():
            pid = str(row.get("pod_id") or "").strip()
            if not pid:
                continue
            stats = self.discovery_stats(pid)
            proven = self.proven_stats(pid)
            arc = self.arc_stats(pid)
            pods[pid] = {
                "pod_index": int(row.get("pod_index") or 0),
                "display_name": row.get("display_name"),
                "operator_id": row.get("operator_id"),
                "label": row.get("label") or "",
                "status": row.get("status") or "active",
                "established_at_utc": row.get("recorded_at_utc"),
                "notes": row.get("notes") or "",
                "ledger_event_id": row.get("event_id"),
                "discovery_count": int(stats.get("discovery_count") or 0),
                "last_discovered_at_utc": stats.get("last_discovered_at_utc"),
                "last_contribution_id": stats.get("last_contribution_id"),
                "last_contribution_type": stats.get("last_contribution_type"),
                "last_receipt_id": stats.get("last_receipt_id"),
                "proven_count": int(proven.get("proven_count") or 0),
                "total_reputation_awarded": proven.get("total_reputation_awarded"),
                "last_proven_at_utc": proven.get("last_proven_at_utc"),
                "last_proven_contribution_id": proven.get("last_proven_contribution_id"),
                "last_reputation_awarded": proven.get("last_reputation_awarded"),
                "last_reward_status": proven.get("last_reward_status"),
                **arc,
            }
        return {
            "registry_version": LEDGER_VERSION,
            "authority": "docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md",
            "ledger_path": str(
                self.ledger_path.relative_to(_repo_root())
                if self.ledger_path.is_relative_to(_repo_root())
                else self.ledger_path
            ).replace("\\", "/"),
            "pods": pods,
        }

    def sync_registry(self) -> dict[str, Any]:
        registry = self.build_registry()
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(
            json.dumps(registry, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return registry


def register_discovery_pod(
    display_name: str,
    *,
    label: str = "",
    notes: str = "",
    registered_by: str = "",
    ledger_path: str | Path | None = None,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    ledger = DiscoveryPodLedger(ledger_path=ledger_path, registry_path=registry_path)
    return ledger.register(
        display_name,
        label=label,
        notes=notes,
        registered_by=registered_by,
    ).to_dict()


def upgrade_pod_on_discovery(
    *,
    operator_id: str,
    tenant_id: str,
    contribution_id: str,
    contribution_type: str,
    spec_payload: dict[str, Any] | None = None,
    receipt_id: str = "",
    idempotent_rediscovery: bool = False,
    label: str = "",
    ledger_path: str | Path | None = None,
    registry_path: str | Path | None = None,
    operator_rewards: dict[str, Any] | None = None,
    receipt: dict[str, Any] | None = None,
    receipt_verified: bool | None = None,
) -> dict[str, Any]:
    """Register pod if needed, append pod_discovered, and pod_proven when applicable."""
    ledger = DiscoveryPodLedger(ledger_path=ledger_path, registry_path=registry_path)
    if receipt_verified is None and receipt:
        receipt_verified = bool(str(receipt.get("receipt_sig") or "").strip())

    discovery_result = ledger.record_discovery(
        operator_id=operator_id,
        tenant_id=tenant_id,
        contribution_id=contribution_id,
        contribution_type=contribution_type,
        spec_payload=spec_payload,
        receipt_id=receipt_id,
        receipt=receipt,
        receipt_verified=receipt_verified,
        idempotent_rediscovery=idempotent_rediscovery,
        label=label,
    ).to_dict()

    proven_result: dict[str, Any] | None = None
    receipt_obj = dict(receipt or {})
    if receipt_obj and is_proven_contribution(receipt_obj):
        proven_result = ledger.record_proven(
            operator_id=operator_id,
            tenant_id=tenant_id,
            contribution_id=contribution_id,
            contribution_type=contribution_type,
            spec_payload=spec_payload,
            receipt_id=receipt_id,
            operator_rewards=operator_rewards,
            receipt=receipt_obj,
        )
        discovery_result["pod_proven"] = proven_result
        try:
            from src.urg_operator_knowledge_bridge import promote_from_receipt

            promotion = promote_from_receipt(
                receipt_obj,
                operator_id=operator_id,
                tenant_id=tenant_id,
            )
            discovery_result["operator_knowledge_promotion"] = promotion
        except Exception as exc:
            discovery_result["operator_knowledge_promotion"] = {
                "ok": False,
                "skipped": True,
                "reason": str(exc),
            }

    return discovery_result


def attach_discovery_pod_ledger(
    *,
    operator_id: str,
    tenant_id: str,
    contribution_id: str,
    contribution_type: str,
    spec_payload: dict[str, Any] | None = None,
    receipt: dict[str, Any] | None = None,
    idempotent_rediscovery: bool = False,
    operator_rewards: dict[str, Any] | None = None,
    receipt_verified: bool | None = None,
    ledger_path: str | Path | None = None,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    """Best-effort pod ledger upgrade for any discovery route (never raises)."""
    try:
        receipt_id = str((receipt or {}).get("receipt_id") or "")
        return upgrade_pod_on_discovery(
            operator_id=operator_id,
            tenant_id=tenant_id,
            contribution_id=contribution_id,
            contribution_type=contribution_type,
            spec_payload=spec_payload,
            receipt_id=receipt_id,
            idempotent_rediscovery=idempotent_rediscovery,
            operator_rewards=operator_rewards,
            receipt=receipt,
            receipt_verified=receipt_verified,
            ledger_path=ledger_path,
            registry_path=registry_path,
        )
    except Exception as exc:
        return {"ok": False, "errors": [str(exc)]}


def _cli(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Discovery Pod ledger — register and list pods")
    sub = parser.add_subparsers(dest="command", required=True)

    reg = sub.add_parser("register", help="Register a new pod display name")
    reg.add_argument("display_name", help="Human display name for the pod")
    reg.add_argument("--label", default="", help="Optional short label")
    reg.add_argument("--notes", default="", help="Optional notes")
    reg.add_argument("--registered-by", default="", help="Who recorded this registration")

    sub.add_parser("list", help="List all registered pods from the ledger")
    sub.add_parser("sync", help="Rebuild deploy/ugr/discovery-pods.json from the ledger")

    react = sub.add_parser(
        "reactivate-arc",
        help="Retroactively apply governance-arc pod multiplier to a prior proven reward",
    )
    react.add_argument("--pod", required=True, help="Pod id, e.g. pod:jon-halstead")
    react.add_argument("--contribution-id", default="", help="Contribution id (default: last proven)")
    react.add_argument(
        "--arc",
        default="civilizational",
        help="Arc tier: civilizational, high, beyond_body (default: civilizational)",
    )

    relabel = sub.add_parser(
        "relabel-arc",
        help="Narrative-only arc relabel (no reward or multiplier changes)",
    )
    relabel.add_argument("--pod", required=True, help="Pod id, e.g. pod:jon-halstead")
    relabel.add_argument("--contribution-id", default="", help="Contribution id (optional scope)")
    relabel.add_argument(
        "--arc",
        default="high",
        help="Display tier: high, beyond_body, civilizational (default: high)",
    )
    relabel.add_argument(
        "--note",
        default="",
        help="Narrative note explaining the relabel (e.g. arc evolved over time)",
    )

    args = parser.parse_args(argv)
    ledger = DiscoveryPodLedger()

    if args.command == "register":
        result = ledger.register(
            args.display_name,
            label=args.label,
            notes=args.notes,
            registered_by=args.registered_by,
        )
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.ok else 1

    if args.command == "list":
        print(json.dumps(ledger.list_pods(), indent=2, sort_keys=True))
        return 0

    if args.command == "sync":
        registry = ledger.sync_registry()
        print(json.dumps({"pod_count": len(registry.get("pods") or {}), "registry_path": str(ledger.registry_path)}, indent=2))
        return 0

    if args.command == "reactivate-arc":
        from src.ugr.discovery.pod_arc_reactivation import reactivate_pod_arc_multiplier

        result = reactivate_pod_arc_multiplier(
            pod_id=args.pod,
            contribution_id=args.contribution_id or None,
            arc_tier=args.arc,
            ledger=ledger,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ok") else 1

    if args.command == "relabel-arc":
        from src.ugr.discovery.pod_arc_relabel import relabel_pod_arc_tier

        result = relabel_pod_arc_tier(
            pod_id=args.pod,
            contribution_id=args.contribution_id or None,
            arc_tier=args.arc,
            narrative_note=args.note,
            ledger=ledger,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ok") else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
