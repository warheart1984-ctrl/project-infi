from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .models import PromotionRequest, ReplayResult
from .queues import AUDIT_OUT, REPLAY_JOBS, Queue


@dataclass
class ReplayStore:
    _frames: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))

    def append(self, replay_id: str, frame: dict[str, Any]) -> None:
        self._frames[replay_id].append(dict(frame))

    def save_replay(self, replay_id: str, frames: list[dict[str, Any]]) -> None:
        self._frames[replay_id] = [dict(frame) for frame in frames]

    def get_replay(self, replay_id: str) -> list[dict[str, Any]]:
        return [dict(frame) for frame in self._frames.get(replay_id, [])]


def enqueue_replay_jobs(queue: Queue, requests: list[PromotionRequest]) -> None:
    for request in requests:
        queue.publish(REPLAY_JOBS, request)


def run_replay_engine(queue: Queue, replay_store: ReplayStore) -> list[ReplayResult]:
    results: list[ReplayResult] = []
    for request in queue.drain(REPLAY_JOBS):
        replay_id = f"replay-{request.request_id}"
        frames = replay_store.get_replay(replay_id)
        passed = bool(frames)
        result = ReplayResult(
            request_id=request.request_id,
            replay_id=replay_id,
            passed=passed,
            violations=[] if passed else [{"reason": "replay frames unavailable"}],
        )
        queue.publish(AUDIT_OUT, result)
        results.append(result)
    return results
