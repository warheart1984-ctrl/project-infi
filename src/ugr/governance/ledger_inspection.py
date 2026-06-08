"""Inspectable UGR ledger — duplicate detection, balance replay, registry drift."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ugr.discovery.contribution_store import ContributionDiscoveryStore
from src.ugr.discovery.discovery_pod_ledger import DiscoveryPodLedger
from src.ugr.platform.tenant_registry import normalize_tenant_id
from src.ugr.rewards.operator_profile import OperatorProfile
from src.ugr.rewards.operator_reward_spec import (
    EVENT_LIBRARY_PATTERN_MATCHED,
    EVENT_RAIL_CREDITS_PURCHASED,
    EVENT_RAIL_CREDITS_RECEIVED,
    EVENT_RAIL_CREDITS_SENT,
)
from src.ugr.rewards.reward_ledger import RewardLedger, _operator_slug

_FLOAT_EPS = 1e-6

_STABLE_POD_FIELDS = (
    "pod_index",
    "display_name",
    "operator_id",
    "label",
    "status",
    "established_at_utc",
    "notes",
    "ledger_event_id",
)


def _float_close(a: float, b: float, *, eps: float = _FLOAT_EPS) -> bool:
    return abs(float(a) - float(b)) <= eps


def _list_operator_ids(ledger: RewardLedger) -> list[str]:
    operators_dir = ledger.base / "operators"
    if not operators_dir.is_dir():
        return []
    ids: list[str] = []
    for child in sorted(operators_dir.iterdir()):
        if not child.is_dir():
            continue
        balance_path = child / "operator_balances.json"
        if not balance_path.exists():
            continue
        try:
            data = json.loads(balance_path.read_text(encoding="utf-8"))
            op_id = str(data.get("operator_id") or "").strip()
            if op_id:
                ids.append(op_id)
                continue
        except json.JSONDecodeError:
            pass
        slug = child.name
        for row in ledger._iter_rewards_rows():
            row_op = str(row.get("operator_id") or "").strip()
            if row_op and _operator_slug(row_op) == slug:
                ids.append(row_op)
                break
    return sorted(set(ids))


def _replay_profile_from_events(
    operator_id: str,
    events: list[dict[str, Any]],
    *,
    tenant_id: str,
) -> OperatorProfile:
    profile = OperatorProfile(operator_id=operator_id, tenant_id=tenant_id)
    adoption_policy_cap = 3.0
    for row in sorted(events, key=lambda r: float(r.get("issued_at") or 0)):
        event_type = str(row.get("event_type") or "")
        issued_at = float(row.get("issued_at") or 0)
        deltas = dict(row.get("deltas") or {})

        if event_type == EVENT_RAIL_CREDITS_SENT:
            amount = float(row.get("amount") or 0)
            fee = float(row.get("fee") or 0)
            profile.earned_rail_credits = max(
                0.0, float(profile.earned_rail_credits or 0) - (amount + fee)
            )
            profile._sync_total_credits()
            profile.updated_at = issued_at
            continue

        if event_type == EVENT_RAIL_CREDITS_RECEIVED:
            amount = float(row.get("amount") or 0)
            profile.earned_rail_credits = max(0.0, float(profile.earned_rail_credits or 0) + amount)
            profile._sync_total_credits()
            profile.updated_at = issued_at
            continue

        if event_type == EVENT_RAIL_CREDITS_PURCHASED:
            purchased = float(
                row.get("amount") or deltas.get("purchased_rail_credits") or 0
            )
            profile.purchased_rail_credits = max(
                0.0, float(profile.purchased_rail_credits or 0) + purchased
            )
            profile._sync_total_credits()
            profile.updated_at = issued_at
            continue

        if deltas:
            profile.apply_deltas(
                reputation=float(deltas.get("reputation") or 0),
                earned_rail_credits=float(
                    deltas.get("earned_rail_credits") or deltas.get("rail_credits") or 0
                ),
                purchased_rail_credits=float(deltas.get("purchased_rail_credits") or 0),
                adoption_multiplier_delta=float(deltas.get("adoption_multiplier") or 0),
                contribution_id=str(
                    row.get("contribution_id") or row.get("subsystem_id") or ""
                ),
                multiplier_cap=adoption_policy_cap,
                issued_at=issued_at,
            )

    return profile


def _audit_reward_events(rows: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[str] = []
    event_ids: dict[str, int] = {}
    transfer_ids: dict[str, int] = {}
    pattern_matches: list[dict[str, Any]] = []

    for row in rows:
        eid = str(row.get("event_id") or "").strip()
        if eid:
            event_ids[eid] = event_ids.get(eid, 0) + 1
        tid = str(row.get("transfer_id") or "").strip()
        if tid:
            transfer_ids[tid] = transfer_ids.get(tid, 0) + 1
        if str(row.get("event_type") or "") == EVENT_LIBRARY_PATTERN_MATCHED:
            pattern_matches.append(
                {
                    "event_id": eid,
                    "operator_id": row.get("operator_id"),
                    "contribution_id": row.get("contribution_id") or row.get("subsystem_id"),
                    "pattern_id": (row.get("attribution") or {}).get("primary_anchor"),
                }
            )

    duplicate_event_ids = sorted(eid for eid, count in event_ids.items() if count > 1)
    if duplicate_event_ids:
        issues.append(
            f"duplicate event_id in rewards.jsonl: {', '.join(duplicate_event_ids[:5])}"
        )

    return {
        "event_count": len(rows),
        "unique_event_ids": len(event_ids),
        "duplicate_event_ids": duplicate_event_ids,
        "library_pattern_match_count": len(pattern_matches),
        "library_pattern_matches": pattern_matches,
        "issues": issues,
        "ok": not issues,
    }


def _audit_balance_replay(
    ledger: RewardLedger,
    *,
    tenant_id: str,
) -> dict[str, Any]:
    issues: list[str] = []
    operator_reports: list[dict[str, Any]] = []
    all_rows = ledger._iter_rewards_rows()

    for operator_id in _list_operator_ids(ledger):
        op_events = [
            row
            for row in all_rows
            if str(row.get("operator_id") or "") == operator_id
        ]
        stored = ledger.load_balances(operator_id)
        replayed = _replay_profile_from_events(
            operator_id, op_events, tenant_id=tenant_id
        )

        drift: dict[str, Any] = {}
        if not _float_close(stored.reputation_score, replayed.reputation_score):
            drift["reputation_score"] = {
                "stored": stored.reputation_score,
                "replayed": replayed.reputation_score,
            }
        if not _float_close(stored.earned_rail_credits, replayed.earned_rail_credits):
            drift["earned_rail_credits"] = {
                "stored": stored.earned_rail_credits,
                "replayed": replayed.earned_rail_credits,
            }
        if not _float_close(stored.purchased_rail_credits, replayed.purchased_rail_credits):
            drift["purchased_rail_credits"] = {
                "stored": stored.purchased_rail_credits,
                "replayed": replayed.purchased_rail_credits,
            }
        if not _float_close(stored.rail_credits, replayed.rail_credits):
            drift["rail_credits"] = {
                "stored": stored.rail_credits,
                "replayed": replayed.rail_credits,
            }

        if drift:
            issues.append(f"balance drift for {operator_id}: {list(drift.keys())}")

        operator_reports.append(
            {
                "operator_id": operator_id,
                "event_count": len(op_events),
                "drift": drift or None,
                "ok": not drift,
            }
        )

    return {
        "operator_count": len(operator_reports),
        "operators": operator_reports,
        "issues": issues,
        "ok": not issues,
    }


def _audit_discovery_pod_registry(
    *,
    ledger_path: str | Path | None = None,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    issues: list[str] = []
    ledger = DiscoveryPodLedger(ledger_path=ledger_path, registry_path=registry_path)
    built = ledger.build_registry()
    built_pods = dict(built.get("pods") or {})

    on_disk: dict[str, Any] = {}
    if ledger.registry_path.exists():
        try:
            on_disk = json.loads(ledger.registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(f"registry JSON invalid: {exc}")

    on_disk_pods = dict(on_disk.get("pods") or {})
    built_ids = set(built_pods)
    disk_ids = set(on_disk_pods)

    missing_on_disk = sorted(built_ids - disk_ids)
    stale_on_disk = sorted(disk_ids - built_ids)
    if missing_on_disk:
        issues.append(f"pods in ledger missing from registry: {', '.join(missing_on_disk[:5])}")
    if stale_on_disk:
        issues.append(f"pods on disk absent from ledger: {', '.join(stale_on_disk[:5])}")

    identity_drift: list[dict[str, Any]] = []
    for pod_id in sorted(built_ids & disk_ids):
        built_pod = built_pods.get(pod_id) or {}
        disk_pod = on_disk_pods.get(pod_id) or {}
        for field in _STABLE_POD_FIELDS:
            if built_pod.get(field) != disk_pod.get(field):
                identity_drift.append(
                    {
                        "pod_id": pod_id,
                        "field": field,
                        "ledger": built_pod.get(field),
                        "registry": disk_pod.get(field),
                    }
                )
    if identity_drift:
        issues.append(
            f"registry identity drift on {len(identity_drift)} field(s); run discovery_pod_ledger sync"
        )

    return {
        "ledger_pod_count": len(built_pods),
        "registry_pod_count": len(on_disk_pods),
        "missing_on_disk": missing_on_disk,
        "stale_on_disk": stale_on_disk,
        "identity_drift": identity_drift,
        "issues": issues,
        "ok": not issues,
    }


def _audit_contribution_store(
    runtime_dir: str | Path | None,
    *,
    tenant_id: str,
) -> dict[str, Any]:
    issues: list[str] = []
    store = ContributionDiscoveryStore(runtime_dir, tenant_id=tenant_id)
    discoveries = store._read_lines(store.discoveries_path)
    if not discoveries and store.legacy_discoveries_path.exists():
        discoveries = store._read_lines(store.legacy_discoveries_path)
    catalog = store._read_lines(store.catalog_path)
    withdrawals = store._read_lines(store.withdrawals_path)

    seen: dict[str, int] = {}
    for row in discoveries:
        cid = str(row.get("contribution_id") or row.get("subsystem_id") or "").strip()
        if cid:
            seen[cid] = seen.get(cid, 0) + 1

    duplicate_ids = sorted(cid for cid, count in seen.items() if count > 1)
    if duplicate_ids:
        issues.append(
            f"duplicate contribution_id in store: {', '.join(duplicate_ids[:5])}"
        )

    return {
        "discovery_count": len(discoveries),
        "catalog_count": len(catalog),
        "withdrawal_count": len(withdrawals),
        "unique_contribution_ids": len(seen),
        "duplicate_contribution_ids": duplicate_ids,
        "issues": issues,
        "ok": not issues,
    }


def inspect_ugr_ledger(
    runtime_dir: str | Path | None = None,
    *,
    tenant_id: str | None = None,
    ledger_path: str | Path | None = None,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run a full UGR ledger inspection and return a structured report."""
    tenant_norm = normalize_tenant_id(tenant_id or "global")
    ledger = RewardLedger(runtime_dir=runtime_dir, tenant_id=tenant_norm)
    reward_rows = ledger._iter_rewards_rows()

    rewards = _audit_reward_events(reward_rows)
    balances = _audit_balance_replay(ledger, tenant_id=tenant_norm)
    pods = _audit_discovery_pod_registry(
        ledger_path=ledger_path,
        registry_path=registry_path,
    )
    contributions = _audit_contribution_store(runtime_dir, tenant_id=tenant_norm)

    all_issues: list[str] = []
    for section in (rewards, balances, pods, contributions):
        all_issues.extend(section.get("issues") or [])

    return {
        "ok": not all_issues,
        "tenant_id": tenant_norm,
        "runtime_dir": str(ledger.runtime_root),
        "rewards": rewards,
        "balances": balances,
        "discovery_pods": pods,
        "contributions": contributions,
        "issues": all_issues,
    }
