"""IntentLedger — append-only operator intent chain."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from governed_memory.types import IntentHorizon, IntentRecord


def _hash_record(
    *,
    intent_id: str,
    timestamp: float,
    operator_id: str,
    semantic_goal: str,
    constraints: tuple[str, ...],
    success_criteria: tuple[str, ...],
    horizon: IntentHorizon,
    version: int,
    signature: str,
    prev_hash: str | None,
) -> str:
    payload = json.dumps(
        {
            "intent_id": intent_id,
            "timestamp": timestamp,
            "operator_id": operator_id,
            "semantic_goal": semantic_goal,
            "constraints": list(constraints),
            "success_criteria": list(success_criteria),
            "horizon": horizon,
            "version": version,
            "signature": signature,
            "prev_hash": prev_hash,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class IntentLedger:
    def __init__(self) -> None:
        self._chain: list[IntentRecord] = []

    def append(
        self,
        *,
        operator_id: str,
        semantic_goal: str,
        constraints: list[str],
        success_criteria: list[str],
        horizon: IntentHorizon,
        signature: str,
    ) -> IntentRecord:
        prev = self._chain[-1] if self._chain else None
        version = (prev.version + 1) if prev else 1
        intent_id = str(uuid.uuid4())
        timestamp = time.time()
        prev_hash = prev.content_hash if prev else None
        content_hash = _hash_record(
            intent_id=intent_id,
            timestamp=timestamp,
            operator_id=operator_id,
            semantic_goal=semantic_goal,
            constraints=tuple(constraints),
            success_criteria=tuple(success_criteria),
            horizon=horizon,
            version=version,
            signature=signature,
            prev_hash=prev_hash,
        )
        record = IntentRecord(
            intent_id=intent_id,
            timestamp=timestamp,
            operator_id=operator_id,
            semantic_goal=semantic_goal,
            constraints=tuple(constraints),
            success_criteria=tuple(success_criteria),
            horizon=horizon,
            version=version,
            signature=signature,
            content_hash=content_hash,
            prev_hash=prev_hash,
        )
        self._chain.append(record)
        return record

    def latest(self) -> IntentRecord | None:
        return self._chain[-1] if self._chain else None

    def get_version(self, version: int) -> IntentRecord | None:
        for rec in self._chain:
            if rec.version == version:
                return rec
        return None

    def verify_chain(self) -> bool:
        for i, rec in enumerate(self._chain):
            expected_prev = self._chain[i - 1].content_hash if i else None
            if rec.prev_hash != expected_prev:
                return False
            recomputed = _hash_record(
                intent_id=rec.intent_id,
                timestamp=rec.timestamp,
                operator_id=rec.operator_id,
                semantic_goal=rec.semantic_goal,
                constraints=rec.constraints,
                success_criteria=rec.success_criteria,
                horizon=rec.horizon,
                version=rec.version,
                signature=rec.signature,
                prev_hash=rec.prev_hash,
            )
            if recomputed != rec.content_hash:
                return False
        return True

    def list(self) -> list[IntentRecord]:
        return list(self._chain)
