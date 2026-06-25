"""Constitutional State Runtime — receipt-v2 extension over constitutional_state core."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path

from typing import Any

from constitutional.core.runtime import ConstitutionalStateRuntime as CoreCSR
from constitutional.runtime.constitutional_state import (
    ReplayResult,
    StateObject,
    replay_state,
    transition_from_receipt,
)
from constitutional.runtime.domain_receipts_store import append_domain_receipt as persist_domain_receipt
from constitutional.runtime.receipts_v2 import BaseReceiptV2, TransitionReceiptV2
from constitutional.runtime.transition_ledger import ConstitutionalTransitionLedger
from pydantic import BaseModel


class ConstitutionalStateRuntime(CoreCSR):
    """In-process CSR: register StateObjects, apply receipt-keyed transitions, replay."""

    def __init__(self, persist_root: Path | None = None) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self._receipts_by_state: dict[str, list[TransitionReceiptV2]] = {}
        self._domain_receipts_by_state: dict[str, list[BaseReceiptV2]] = {}
        self._domain_docs: dict[str, dict[str, Any]] = {}
        self._personal_snapshot: object | None = None
        self._global_snapshot: object | None = None
        self._invariant_registry: dict[str, str] = {}
        self._receipt_ledger = ConstitutionalTransitionLedger()
        self._persist_root = persist_root

    @property
    def invariant_registry(self) -> dict[str, str]:
        with self._lock:
            return dict(self._invariant_registry)

    def register_invariant(self, name: str, description: str) -> None:
        with self._lock:
            self._invariant_registry[name] = description

    def all_states(self) -> list[StateObject]:
        with self._lock:
            return [state.model_copy(deep=True) for state in self._states.values()]

    def all_receipts(self, before: datetime | None = None) -> list[BaseReceiptV2]:
        return self.get_all_receipts(before=before)

    @property
    def ledger(self) -> ConstitutionalTransitionLedger:
        return self._receipt_ledger

    def receipts_for(self, state_id: str) -> list[TransitionReceiptV2]:
        with self._lock:
            return list(self._receipts_by_state.get(state_id, []))

    def domain_receipts_for(self, state_id: str) -> list[BaseReceiptV2]:
        with self._lock:
            return list(self._domain_receipts_by_state.get(state_id, []))

    def register_or_replace_state(self, state: StateObject) -> None:
        with self._lock:
            if state.state_id in self._states:
                existing = self._states[state.state_id]
                state = state.model_copy(
                    update={
                        "version": existing.version,
                        "history": list(existing.history),
                        "current_state": existing.current_state,
                    }
                )
            self._states[state.state_id] = state.model_copy(deep=True)

    def put_domain_doc(self, state_id: str, state_type: str, doc: BaseModel) -> None:
        with self._lock:
            self._domain_docs[state_id] = {
                "state_type": state_type,
                "doc": doc.model_dump(mode="json"),
            }

    def get_domain_doc(self, state_id: str, model: type[BaseModel]) -> BaseModel:
        with self._lock:
            entry = self._domain_docs.get(state_id)
        if entry is None:
            raise KeyError(f"unknown domain doc: {state_id}")
        return model.model_validate(entry["doc"])

    def register_idea(self, idea: object) -> None:
        """Backward-compatible hook — prefer put_domain_doc from domain runtimes."""
        idea_id = getattr(idea, "state_id", None) or getattr(idea, "idea_id", None)
        if not idea_id:
            raise ValueError("idea must have state_id or idea_id")
        if isinstance(idea, BaseModel):
            self.put_domain_doc(str(idea_id), getattr(idea, "state_type", "idea"), idea)

    def states_of_type(self, state_type: str) -> list[BaseModel]:
        from constitutional.runtime.burnout_runtime import BurnoutState, RecoveryPlanState
        from constitutional.runtime.personal_continuity_runtime import (
            AssumptionState,
            CriticalContextState,
            IdeaState,
        )

        type_map: dict[str, type[BaseModel]] = {
            "idea": IdeaState,
            "assumption": AssumptionState,
            "critical_context": CriticalContextState,
            "burnout_state": BurnoutState,
            "recovery_plan": RecoveryPlanState,
        }
        model = type_map.get(state_type)
        if model is None:
            return []
        with self._lock:
            ids = [
                sid
                for sid, entry in self._domain_docs.items()
                if entry.get("state_type") == state_type
            ]
        return [self.get_domain_doc(sid, model) for sid in ids]

    def set_burnout_latest(self, burnout: BaseModel) -> None:
        self.put_domain_doc("burnout__latest", "burnout_state", burnout)

    def get_state_doc(self, key: str) -> BaseModel:
        from constitutional.runtime.burnout_runtime import BurnoutState

        if key == "burnout__latest":
            return self.get_domain_doc(key, BurnoutState)
        raise KeyError(f"unknown state_id: {key}")

    def register_personal_snapshot(self, state: object) -> None:
        with self._lock:
            self._personal_snapshot = state
        state_id = getattr(state, "state_id", "personal_constitutional_state__global")
        if isinstance(state, BaseModel):
            self.put_domain_doc(str(state_id), "personal_constitutional_state", state)

    def get_personal_snapshot(self) -> object:
        with self._lock:
            if self._personal_snapshot is None:
                raise KeyError("personal_constitutional_state__global")
            return self._personal_snapshot

    def register_global_snapshot(self, state: object) -> None:
        with self._lock:
            self._global_snapshot = state
        state_id = getattr(state, "state_id", "constitutional_state__global")
        if isinstance(state, BaseModel):
            self.put_domain_doc(str(state_id), "constitutional_state", state)

    def get_global_snapshot(self) -> object:
        with self._lock:
            if self._global_snapshot is None:
                raise KeyError("constitutional_state__global")
            return self._global_snapshot

    def append_observation_receipt(self, receipt: BaseReceiptV2) -> None:
        state_id = receipt.inputs.request_id
        with self._lock:
            self._domain_receipts_by_state.setdefault(state_id, []).append(receipt)
        persist_domain_receipt(receipt)

    def observation_receipts_for(self, state_object_id: str) -> list[BaseReceiptV2]:
        return self.domain_receipts_for(state_object_id)

    def get_all_receipts(self, before: datetime | None = None) -> list[BaseReceiptV2]:
        """Merged receipt stream (disk + CSR) up to ``before`` (cumulative window)."""
        from constitutional.runtime.global_constitutional_state import _merge_receipt_streams

        snapshot_at = before or datetime.now(UTC)
        return _merge_receipt_streams(self, snapshot_at=snapshot_at)

    def apply_transition(
        self,
        state_id: str,
        receipt: TransitionReceiptV2,
        *,
        accountable_party: str,
    ) -> StateObject:
        with self._lock:
            transition = transition_from_receipt(
                receipt,
                state_object_id=state_id,
                accountable_party=accountable_party,
            )
            state = super().apply_transition(transition)
            self._receipt_ledger.append_from_transition_receipt(
                receipt,
                state_object_id=state_id,
                accountable_party=accountable_party,
            )
            self._receipts_by_state.setdefault(state_id, []).append(receipt)
            self._persist_state(state_id)
            self._persist_receipt(state_id, receipt)
            return state

    def replay(self, state_id: str) -> ReplayResult:
        with self._lock:
            canonical = self._states[state_id]
            receipts = list(self._receipts_by_state.get(state_id, []))
        return replay_state(receipts, canonical.model_copy(deep=True))

    def load_task_persisted(self, state_id: str, task_dir: Path) -> None:
        state_path = task_dir / "constitutional_state.json"
        receipts_path = task_dir / "constitutional_receipts.jsonl"
        if state_path.is_file():
            with self._lock:
                self._states[state_id] = StateObject.model_validate(
                    json.loads(state_path.read_text(encoding="utf-8"))
                )
        if receipts_path.is_file():
            receipts: list[TransitionReceiptV2] = []
            with receipts_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if line:
                        receipts.append(TransitionReceiptV2.model_validate(json.loads(line)))
            with self._lock:
                self._receipts_by_state[state_id] = receipts
                for receipt in receipts:
                    if not self._receipt_ledger.has_receipt(receipt.receipt_id):
                        self._receipt_ledger.append_from_transition_receipt(
                            receipt,
                            state_object_id=state_id,
                            accountable_party="operator",
                        )

    def _persist_state(self, state_id: str) -> None:
        if self._persist_root is None:
            return
        task_dir = self._persist_root / state_id
        task_dir.mkdir(parents=True, exist_ok=True)
        state = self._states[state_id]
        (task_dir / "constitutional_state.json").write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def _persist_receipt(self, state_id: str, receipt: TransitionReceiptV2) -> None:
        if self._persist_root is None:
            return
        task_dir = self._persist_root / state_id
        task_dir.mkdir(parents=True, exist_ok=True)
        path = task_dir / "constitutional_receipts.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(receipt.model_dump_json() + "\n")
