"""Per-org rate limits and quotas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.policy.engine import load_org_policy
from platform.store import PlatformStore


class QuotaLimiter:
    def __init__(self, *, store: PlatformStore, redis_url: str = "") -> None:
        self.store = store
        self.redis_url = redis_url
        self._memory: dict[str, int] = {}

    def _day_key(self, org_id: str, metric: str) -> str:
        day = datetime.now(UTC).date().isoformat()
        return f"{org_id}:{day}:{metric}"

    def _incr(self, key: str, limit: int) -> tuple[bool, int]:
        if self.redis_url:
            try:
                import redis  # type: ignore[import-not-found]

                client = redis.from_url(self.redis_url, decode_responses=True)
                count = int(client.incr(key))
                if count == 1:
                    client.expire(key, 86400)
                return count <= limit, max(0, limit - count)
            except Exception:
                pass
        count = self._memory.get(key, 0) + 1
        self._memory[key] = count
        return count <= limit, max(0, limit - count)

    def check_job_submit(self, *, org_id: str, org: dict[str, Any] | None) -> tuple[bool, dict[str, str]]:
        policy = load_org_policy(org)
        key = self._day_key(org_id, "jobs")
        ok, remaining = self._incr(key, int(policy.get("jobs_per_day") or 1000))
        headers = {"Quota-Remaining-Jobs": str(remaining)}
        return ok, headers

    def running_jobs(self, org_id: str) -> int:
        return len([j for j in self.store.list_jobs(org_id=org_id) if j.get("status") in {"queued", "running"}])
