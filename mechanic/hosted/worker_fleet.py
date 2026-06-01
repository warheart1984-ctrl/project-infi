"""Redis-backed hosted worker loop."""

from __future__ import annotations

import json
import os
import time
from typing import Any

from mechanic.hosted.control_plane import HostedMechanicService
from mechanic.hosted.settings import HostedSettings


def main() -> int:
    try:
        import redis  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("redis package is required for worker fleet mode") from exc

    settings = HostedSettings.from_env()
    client = redis.Redis.from_url(settings.redis_url or "redis://127.0.0.1:6379/0")
    service = HostedMechanicService(
        artifact_root=settings.artifact_root,
        database_url=settings.database_url,
        artifact_signing_secret=settings.artifact_signing_secret,
        max_workers=1,
        settings=settings,
    )
    queue_name = os.environ.get("MECHANIC_REDIS_SCAN_QUEUE", "mechanic:scan-jobs")
    while True:
        item = client.blpop(queue_name, timeout=5)
        if item is None:
            time.sleep(0.2)
            continue
        _, raw = item
        payload: dict[str, Any] = json.loads(raw.decode("utf-8"))
        try:
            payload["wait"] = True
            service.create_scan(payload)
        except Exception as exc:
            client.rpush("mechanic:scan-failures", json.dumps({"payload": payload, "error": str(exc)}, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
