"""Tenant-scoped reward ledger and operator balances."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from src.ugr.mission.tenant_manifold import tenant_path_slug
from src.ugr.platform.tenant_registry import normalize_tenant_id
from src.ugr.rewards.operator_profile import OperatorProfile
from src.ugr.rewards.operator_reward_spec import EVENT_RAIL_CREDITS_SENT, TRANSFER_EVENT_TYPES


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / ".runtime"


def _operator_slug(operator_id: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_:" else "_" for c in operator_id) or "default"
    return safe


class RewardLedger:
    def __init__(self, runtime_dir: str | Path | None = None, *, tenant_id: str | None = None):
        root = Path(runtime_dir or _default_runtime_dir())
        self.runtime_root = root
        self.tenant_id = normalize_tenant_id(tenant_id or "global")
        slug = tenant_path_slug(self.tenant_id)
        self.base = root / "urg" / "rewards" / slug
        self.base.mkdir(parents=True, exist_ok=True)
        self.tenant_rewards_path = self.base / "rewards.jsonl"
        self.spend_dir = self.base / "spend"
        self.spend_dir.mkdir(parents=True, exist_ok=True)

    def _operator_dir(self, operator_id: str) -> Path:
        path = self.base / "operators" / _operator_slug(operator_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def balances_path(self, operator_id: str) -> Path:
        return self._operator_dir(operator_id) / "operator_balances.json"

    def _legacy_profile_path(self, operator_id: str) -> Path:
        return self._operator_dir(operator_id) / "profile.json"

    def load_balances(self, operator_id: str) -> OperatorProfile:
        path = self.balances_path(operator_id)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            profile = OperatorProfile.from_dict(data)
            profile.operator_id = operator_id
            profile.tenant_id = self.tenant_id
            return profile
        legacy = self._legacy_profile_path(operator_id)
        if legacy.exists():
            data = json.loads(legacy.read_text(encoding="utf-8"))
            profile = OperatorProfile.from_dict(data)
            profile.operator_id = operator_id
            profile.tenant_id = self.tenant_id
            self.save_balances(profile)
            return profile
        return OperatorProfile(operator_id=operator_id, tenant_id=self.tenant_id)

    def save_balances(self, profile: OperatorProfile) -> None:
        path = self.balances_path(profile.operator_id)
        path.write_text(json.dumps(profile.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    def _iter_rewards_rows(self) -> list[dict[str, Any]]:
        if not self.tenant_rewards_path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.tenant_rewards_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows

    def has_event(self, event_id: str) -> bool:
        eid = str(event_id or "").strip()
        if not eid:
            return False
        for row in self._iter_rewards_rows():
            if str(row.get("event_id") or "") == eid:
                return True
        return False

    def has_transfer(self, transfer_id: str) -> bool:
        tid = str(transfer_id or "").strip()
        if not tid:
            return False
        for row in self._iter_rewards_rows():
            if str(row.get("transfer_id") or "") == tid:
                return True
        return False

    def append_event(self, record: dict[str, Any]) -> bool:
        event_id = str(record.get("event_id") or "")
        if event_id and self.has_event(event_id):
            return False
        with self.tenant_rewards_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")
        return True

    def list_events(
        self,
        *,
        operator_id: str | None = None,
        contribution_id: str | None = None,
        subsystem_id: str | None = None,
        event_types: frozenset[str] | set[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        cid = str(contribution_id or subsystem_id or "").strip()
        op = str(operator_id or "").strip()
        allowed = frozenset(event_types) if event_types else None
        for row in self._iter_rewards_rows():
            if op and str(row.get("operator_id") or "") != op:
                continue
            if cid:
                row_cid = str(row.get("contribution_id") or row.get("subsystem_id") or "")
                if row_cid != cid:
                    continue
            if allowed and str(row.get("event_type") or "") not in allowed:
                continue
            rows.append(row)
        return rows[-limit:]

    def sum_purchases_today(
        self,
        operator_id: str,
        *,
        now: float | None = None,
    ) -> float:
        from src.ugr.rewards.operator_reward_spec import EVENT_RAIL_CREDITS_PURCHASED

        op = str(operator_id or "").strip()
        ts = now if now is not None else time.time()
        day_start = ts - (ts % 86400)
        total = 0.0
        for row in self._iter_rewards_rows():
            if str(row.get("operator_id") or "") != op:
                continue
            if str(row.get("event_type") or "") != EVENT_RAIL_CREDITS_PURCHASED:
                continue
            if float(row.get("issued_at") or 0) >= day_start:
                total += float(row.get("amount") or row.get("deltas", {}).get("purchased_rail_credits") or 0)
        return total

    def list_transfer_events(
        self,
        *,
        operator_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self.list_events(
            operator_id=operator_id,
            event_types=TRANSFER_EVENT_TYPES,
            limit=limit,
        )

    def sum_outbound_transfers(
        self,
        operator_id: str,
        *,
        window_seconds: float = 86400,
        now: float | None = None,
    ) -> float:
        """Sum rail_credits_sent amounts for operator in rolling window."""
        op = str(operator_id or "").strip()
        cutoff = (now if now is not None else time.time()) - window_seconds
        total = 0.0
        for row in self._iter_rewards_rows():
            if str(row.get("operator_id") or "") != op:
                continue
            if str(row.get("event_type") or "") != EVENT_RAIL_CREDITS_SENT:
                continue
            issued = float(row.get("issued_at") or 0)
            if issued < cutoff:
                continue
            total += float(row.get("amount") or 0)
        return total

    def count_outbound_transfers_today(
        self,
        operator_id: str,
        *,
        now: float | None = None,
    ) -> int:
        op = str(operator_id or "").strip()
        ts = now if now is not None else time.time()
        day_start = ts - (ts % 86400)
        count = 0
        for row in self._iter_rewards_rows():
            if str(row.get("operator_id") or "") != op:
                continue
            if str(row.get("event_type") or "") != EVENT_RAIL_CREDITS_SENT:
                continue
            if float(row.get("issued_at") or 0) >= day_start:
                count += 1
        return count

    def last_outbound_transfer_at(self, operator_id: str) -> float | None:
        op = str(operator_id or "").strip()
        last: float | None = None
        for row in self._iter_rewards_rows():
            if str(row.get("operator_id") or "") != op:
                continue
            if str(row.get("event_type") or "") != EVENT_RAIL_CREDITS_SENT:
                continue
            issued = float(row.get("issued_at") or 0)
            if last is None or issued > last:
                last = issued
        return last

    def save_spend_token(self, spend_id: str, payload: dict[str, Any]) -> None:
        path = self.spend_dir / f"{spend_id}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def load_spend_token(self, spend_id: str) -> dict[str, Any] | None:
        path = self.spend_dir / f"{spend_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def mark_spend_consumed(self, spend_id: str) -> None:
        payload = self.load_spend_token(spend_id) or {}
        payload["consumed"] = True
        payload["consumed_at"] = time.time()
        self.save_spend_token(spend_id, payload)
