"""Redis job queue for platform workers."""

from __future__ import annotations

import json
from typing import Any

QUEUE_KEY = "platform:jobs"


def queue_key_for_region(region: str) -> str:
    return f"platform:jobs:{region.lower()}"


class JobQueue:
    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._client: Any = None

    def _redis(self) -> Any:
        if self._client is not None:
            return self._client
        if not self.redis_url:
            return None
        try:
            import redis  # type: ignore[import-not-found]
        except ImportError:
            return None
        self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    def enqueue(self, job_id: str, *, region: str = "") -> bool:
        client = self._redis()
        if client is None:
            return False
        key = queue_key_for_region(region) if region else QUEUE_KEY
        client.lpush(key, json.dumps({"job_id": job_id, "region": region or "us"}))
        return True

    def dequeue(self, *, timeout: int = 1, region: str = "") -> str | None:
        client = self._redis()
        if client is None:
            return None
        key = queue_key_for_region(region) if region else QUEUE_KEY
        result = client.brpop(key, timeout=timeout)
        if not result:
            return None
        _, raw = result
        payload = json.loads(raw)
        return str(payload.get("job_id") or "")

    def pending_count(self) -> int:
        client = self._redis()
        if client is None:
            return 0
        return int(client.llen(QUEUE_KEY))
