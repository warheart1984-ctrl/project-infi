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

    def has_event(self, event_id: str) -> bool:
        eid = str(event_id or "").strip()
        if not eid or not self.tenant_rewards_path.exists():
            return False
        for line in self.tenant_rewards_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(row.get("event_id") or "") == eid:
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
        subsystem_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if not self.tenant_rewards_path.exists():
            return []
        rows: list[dict[str, Any]] = []
        sid = str(subsystem_id or "").strip()
        op = str(operator_id or "").strip()
        for line in self.tenant_rewards_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if op and str(row.get("operator_id") or "") != op:
                continue
            if sid and str(row.get("subsystem_id") or "") != sid:
                continue
            rows.append(row)
        return rows[-limit:]

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
