"""SSE mesh event stream (v21)."""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator

from platform.store import PlatformStore


async def mesh_event_stream(
    *,
    store: PlatformStore,
    org_id: str,
    poll_seconds: float = 2.0,
    limit: int = 20,
) -> AsyncIterator[str]:
    seen: set[str] = set()
    while True:
        events = store.list_mesh_events(org_id=org_id, limit=limit)
        for ev in reversed(events):
            eid = str(ev.get("event_id"))
            if eid in seen:
                continue
            seen.add(eid)
            yield f"data: {json.dumps(ev)}\n\n"
        await asyncio.sleep(poll_seconds)
