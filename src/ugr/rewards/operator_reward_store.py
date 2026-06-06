"""Backward-compatible facade over RewardLedger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ugr.rewards.operator_profile import OperatorProfile
from src.ugr.rewards.reward_ledger import RewardLedger


class OperatorRewardStore:
    def __init__(self, runtime_dir: str | Path | None = None, *, tenant_id: str | None = None):
        self._ledger = RewardLedger(runtime_dir, tenant_id=tenant_id)

    @property
    def tenant_id(self) -> str:
        return self._ledger.tenant_id

    @property
    def base(self) -> Path:
        return self._ledger.base

    @property
    def spend_dir(self) -> Path:
        return self._ledger.spend_dir

    def profile_path(self, operator_id: str) -> Path:
        return self._ledger.balances_path(operator_id)

    def rewards_path(self, operator_id: str) -> Path:
        legacy = self._ledger._operator_dir(operator_id) / "rewards.jsonl"
        return self._ledger.tenant_rewards_path if self._ledger.tenant_rewards_path.exists() else legacy

    def load_profile(self, operator_id: str) -> OperatorProfile:
        return self._ledger.load_balances(operator_id)

    def save_profile(self, profile: OperatorProfile) -> None:
        self._ledger.save_balances(profile)

    def has_event(self, event_id: str, operator_id: str) -> bool:
        _ = operator_id
        return self._ledger.has_event(event_id)

    def append_reward(self, record: dict[str, Any], *, operator_id: str) -> bool:
        _ = operator_id
        return self._ledger.append_event(record)

    def list_events(
        self,
        *,
        operator_id: str | None = None,
        subsystem_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        rows = self._ledger.list_events(
            operator_id=operator_id,
            subsystem_id=subsystem_id,
            limit=limit,
        )
        if rows:
            return rows
        if not operator_id:
            return rows
        legacy_path = self._ledger._operator_dir(operator_id) / "rewards.jsonl"
        if not legacy_path.exists():
            return []
        sid = str(subsystem_id or "").strip()
        legacy_rows: list[dict[str, Any]] = []
        for line in legacy_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if sid and str(row.get("subsystem_id") or "") != sid:
                continue
            legacy_rows.append(row)
        return legacy_rows[-limit:]

    def save_spend_token(self, spend_id: str, payload: dict[str, Any]) -> None:
        self._ledger.save_spend_token(spend_id, payload)

    def load_spend_token(self, spend_id: str) -> dict[str, Any] | None:
        return self._ledger.load_spend_token(spend_id)

    def mark_spend_consumed(self, spend_id: str) -> None:
        self._ledger.mark_spend_consumed(spend_id)
