from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cep.replay_engine import ReplayStore


@dataclass
class TemporalAPI:
    replay_store: ReplayStore

    def get_replay(self, replay_id: str) -> list[dict[str, Any]]:
        return self.replay_store.get_replay(replay_id)

    def append_frame(self, replay_id: str, frame: dict[str, Any]) -> None:
        self.replay_store.append(replay_id, frame)

    def save_replay(self, replay_id: str, frames: list[dict[str, Any]]) -> None:
        self.replay_store.save_replay(replay_id, frames)
