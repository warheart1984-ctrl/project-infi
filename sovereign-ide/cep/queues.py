from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

PROMOTIONS_IN = "cep.promotions.in"
EVIDENCE_JOBS = "cep.evidence.jobs"
LINEAGE_JOBS = "cep.lineage.jobs"
REPLAY_JOBS = "cep.replay.jobs"
CONFORMANCE_JOBS = "cep.conformance.jobs"
AUDIT_OUT = "cep.audit.out"
DECISIONS_OUT = "cep.decisions.out"


@dataclass
class Queue:
    _topics: dict[str, list[Any]] = field(default_factory=lambda: defaultdict(list))

    def publish(self, topic: str, message: Any) -> None:
        self._topics[topic].append(message)

    def consume(self, topic: str) -> list[Any]:
        return list(self._topics.get(topic, ()))

    def drain(self, topic: str) -> list[Any]:
        messages = list(self._topics.get(topic, ()))
        self._topics[topic].clear()
        return messages

    def count(self, topic: str) -> int:
        return len(self._topics.get(topic, ()))

    def snapshot(self) -> dict[str, int]:
        return {topic: len(messages) for topic, messages in self._topics.items()}
