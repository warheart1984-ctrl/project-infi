"""Nova kernel loop — record → validate → converge → evolve → inherit."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from src.continuity.constitutional_chain import CONSTITUTIONAL_CHAIN, chain_index
from src.continuity.convergence_algebra import (
    DEFAULT_DELTA_MAX,
    DEFAULT_PHI_MIN,
    convergence_fitness,
    fitness_within_tolerance,
)
from src.continuity.continuity_math import continuity_monotone, lineage_math_view
from src.continuity.creation_operator import CreationOperator, SubstrateState
from src.continuity.genesis_lineage import (
    GENESIS_EVENT_ID,
    GENESIS_MEANING_CLASS,
    genesis_lineage,
)
from src.continuity.inheritance import DEFAULT_INVARIANT_LAWS, operator_state_from_lineage
from src.continuity.invariant_engine import DEFAULT_INVARIANT_ENGINE
from src.continuity.lci_stack import apply_lci_stack
from src.continuity.lineage import Lineage, continuity_trace, generativity
from src.continuity.meaning_ledger import MeaningEntryKind, MeaningLedger, MeaningLedgerEntry
from src.continuity.temporal_governance import TemporalState, evaluate_temporal_coherence
from src.continuity.universal_semantics import verify_meaning


L0_GENESIS_ID = "L0-GENESIS"
L1_OPERATOR_WORKSPACE_ID = "L1-OPERATOR-WORKSPACE"
KERNEL_LOOP_LOG_ID = "KERNEL-LOOP-0001"
ML_GENESIS_EVENT_ID = "ML-GENESIS-0001"
INVARIANTS_REF = "IE-0001:UGR-C8"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def continuity_hash(events: frozenset[str]) -> str:
    payload = json.dumps(sorted(events), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class Event:
    event_id: str
    kind: str
    actor: str
    lineage: str
    timestamp: str
    payload: dict[str, Any]


@dataclass
class GenesisEvent(Event):
    event_id: str = "EVT-GENESIS-0001"
    kind: str = "creation.intent"
    actor: str = "OPERATOR:JON"
    lineage: str = L0_GENESIS_ID
    timestamp: str = field(default_factory=_now_iso)
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.payload:
            self.payload = {
                "kind": "founding.declaration",
                "version": "1.0",
                "statement": (
                    "This is the first lawful creation event of the Nova continuity substrate."
                ),
                "tags": ["genesis", "continuity", "lawful_creation"],
            }


@dataclass
class LineageRecord:
    lineage_id: str
    parent_id: str | None
    created_at: str
    state: str
    generativity: float
    invariants_ref: str
    continuity_hash: str
    lineage: Lineage

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_id": self.lineage_id,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "state": self.state,
            "generativity": self.generativity,
            "invariants_ref": self.invariants_ref,
            "continuity_hash": self.continuity_hash,
            "lineage": self.lineage.to_dict(),
        }


@dataclass
class KernelResult:
    event_id: str
    lineage: str
    phi: float
    continuity_hash: str
    status: Literal["ok", "error"]
    errors: list[str] = field(default_factory=list)
    loop_id: str = KERNEL_LOOP_LOG_ID

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "lineage": self.lineage,
            "phi": self.phi,
            "continuity_hash": self.continuity_hash,
            "status": self.status,
            "errors": list(self.errors),
            "loop_id": self.loop_id,
        }


class TraceStore:
    """Append-only event trace with monotonic timestamps."""

    def __init__(self) -> None:
        self._events: list[Event] = []

    def append(self, event: Event) -> None:
        self._events.append(event)

    def all(self) -> list[Event]:
        return list(self._events)


class NovaKernel:
    """v0.1 governed runtime kernel context."""

    def __init__(
        self,
        *,
        phi_min: float = DEFAULT_PHI_MIN,
        delta_max: float = DEFAULT_DELTA_MAX,
        online_dir: Path | None = None,
    ) -> None:
        self.phi_min = phi_min
        self.delta_max = delta_max
        self.trace_store = TraceStore()
        self.lineages: dict[str, LineageRecord] = {}
        self.current_phi = 1.0
        self.current_continuity_hash = continuity_hash(frozenset())
        self._phi_history: list[float] = []
        self._kernel_log: list[dict[str, Any]] = []
        self._online_dir = online_dir or self._default_online_dir()
        self._creation = CreationOperator()
        self._invariants = DEFAULT_INVARIANT_ENGINE
        self._seed_l0()

    @staticmethod
    def _default_online_dir() -> Path:
        configured = os.environ.get("AAIS_ONLINE_RUNTIME_DIR", "").strip()
        if configured:
            return Path(configured).expanduser().resolve()
        return Path(__file__).resolve().parents[2] / ".runtime" / "online"

    def _seed_l0(self) -> None:
        genesis = genesis_lineage(operator_id="OPERATOR:JON")
        genesis = Lineage(
            lineage_id=L0_GENESIS_ID,
            event_ids=frozenset({GENESIS_EVENT_ID}),
            meaning_class=GENESIS_MEANING_CLASS,
            generativity=1.0,
            metadata={
                **genesis.metadata,
                "codename": "LINEAGE-0001",
                "state": "GENESIS",
                "invariant_laws": sorted(DEFAULT_INVARIANT_LAWS),
            },
        )
        self.register_lineage(
            LineageRecord(
                lineage_id=L0_GENESIS_ID,
                parent_id=None,
                created_at=_now_iso(),
                state="GENESIS",
                generativity=1.0,
                invariants_ref=INVARIANTS_REF,
                continuity_hash=continuity_hash(continuity_trace(genesis)),
                lineage=genesis,
            )
        )

    def register_lineage(self, record: LineageRecord) -> None:
        self.lineages[record.lineage_id] = record
        self.current_continuity_hash = record.continuity_hash

    def get_lineage(self, lineage_id: str) -> LineageRecord:
        if lineage_id not in self.lineages:
            raise KeyError(f"unknown lineage: {lineage_id}")
        return self.lineages[lineage_id]

    def active_runtime_lineages(self) -> list[Lineage]:
        return [record.lineage for record in self.lineages.values()]

    def update_continuity_hash(self, event: Event) -> None:
        record = self.get_lineage(event.lineage)
        events = continuity_trace(record.lineage) | {event.event_id}
        self.current_continuity_hash = continuity_hash(events)

    def validate_continuity(self, event: Event) -> None:
        record = self.get_lineage(event.lineage)
        projected = continuity_trace(record.lineage) | {event.event_id}
        if not continuity_monotone(continuity_trace(record.lineage), projected):
            raise ValueError("C1 continuity violation")

    def validate_reconstruction(self, event: Event) -> None:
        if not event.payload:
            raise ValueError("C2 reconstruction violation — empty payload")

    def validate_verification(self, event: Event) -> None:
        record = self.get_lineage(event.lineage)
        if not verify_meaning(record.lineage.meaning_class, record.lineage.meaning_class):
            raise ValueError("C3 verification violation")

    def validate_invariants(self, event: Event) -> None:
        record = self.get_lineage(event.lineage)
        if record.invariants_ref != INVARIANTS_REF:
            raise ValueError("C4 invariant reference violation")

    def validate_identity_wave(self, event: Event) -> None:
        if not event.actor:
            raise ValueError("C5 identity wave violation")

    def validate_universal_meaning(self, event: Event) -> None:
        record = self.get_lineage(event.lineage)
        if not record.lineage.meaning_class:
            raise ValueError("C6 universal meaning violation")

    def validate_convergence_operator(self) -> None:
        if len(self.active_runtime_lineages()) < 1:
            raise ValueError("C7 convergence operator violation")

    def validate_lci(self, event: Event) -> None:
        record = self.get_lineage(event.lineage)
        projected_events = continuity_trace(record.lineage) | {event.event_id}
        projected = Lineage(
            lineage_id=record.lineage_id,
            event_ids=projected_events,
            meaning_class=record.lineage.meaning_class,
            generativity=record.lineage.generativity,
            metadata=record.lineage.metadata,
        )
        enforcement = self._invariants.enforce_or_reject(record.lineage, projected)
        if enforcement["action"] != "accept":
            raise ValueError("C8 LCI violation")

    def validate_convergence_fitness(self) -> None:
        fitness = convergence_fitness(self.active_runtime_lineages(), phi_min=self.phi_min)
        if not fitness["passed"]:
            raise ValueError("C9 convergence fitness violation")
        self.current_phi = float(fitness["phi"])

    def update_convergence_fitness(self, lineage_id: str) -> None:
        self.update_convergence_fitness_for_lineages([lineage_id])

    def update_convergence_fitness_for_lineages(self, lineage_ids: list[str]) -> None:
        selected = [self.get_lineage(item).lineage for item in lineage_ids]
        fitness = convergence_fitness(selected, phi_min=self.phi_min)
        self.current_phi = float(fitness["phi"])

    def ensure_phi_above_min(self) -> None:
        if self.current_phi < self.phi_min:
            raise ValueError("Φ below Φ_min")

    def evolve_lineage(self, lineage_id: str, *, event: Event) -> None:
        record = self.get_lineage(lineage_id)
        state = SubstrateState(state_id=f"kernel-{lineage_id}", lineage=record.lineage)
        evolved = self._creation.create(
            state,
            add_events=frozenset({event.event_id}),
            generativity_delta=0.0 if lineage_id == L0_GENESIS_ID else 0.25,
        )
        new_state = "GENESIS_CONFIRMED" if lineage_id == L0_GENESIS_ID else record.state
        updated = LineageRecord(
            lineage_id=record.lineage_id,
            parent_id=record.parent_id,
            created_at=record.created_at,
            state=new_state,
            generativity=generativity(evolved.lineage),
            invariants_ref=record.invariants_ref,
            continuity_hash=continuity_hash(continuity_trace(evolved.lineage)),
            lineage=evolved.lineage,
        )
        self.register_lineage(updated)

    def persist_chain_snapshot(self) -> None:
        snapshot_path = self._online_dir / "constitutional-chain-snapshot.json"
        self._online_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(
            json.dumps(chain_index(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def persist_phi_history(self) -> None:
        history = load_phi_history(self._online_dir / "phi-history.jsonl")
        previous = history[-1]["phi"] if history else self.current_phi
        delta = round(self.current_phi - previous, 6)
        status = "ok" if self.current_phi >= self.phi_min else "violation"
        if history and not fitness_within_tolerance(
            [row["phi"] for row in history],
            self.current_phi,
            delta_max=self.delta_max,
        ):
            status = "violation"
        append_phi_history(
            {
                "timestamp": _now_iso(),
                "lineages": sorted(self.lineages.keys()),
                "phi": round(self.current_phi, 6),
                "phi_min": self.phi_min,
                "delta": delta,
                "status": status,
            },
            path=self._online_dir / "phi-history.jsonl",
        )
        from src.continuity.constitutional_apply import append_fitness_observation

        append_fitness_observation(
            self.current_phi,
            metadata={"source": "nova_kernel_loop", "lineages": sorted(self.lineages.keys())},
        )

    def persist_lineage_state(self, lineage_id: str) -> None:
        record = self.get_lineage(lineage_id)
        path = self._online_dir / "lineages" / f"{lineage_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def persist_state(self) -> None:
        self.persist_chain_snapshot()
        self.persist_phi_history()

    def log_kernel_loop(self, result: KernelResult) -> None:
        row = {"logged_at": _now_iso(), **result.to_dict()}
        self._kernel_log.append(row)
        log_path = self._online_dir / "kernel-loop-log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    def log_lineage_fork(self, source_id: str, new_id: str, reason: str) -> None:
        row = {
            "logged_at": _now_iso(),
            "source_lineage": source_id,
            "new_lineage": new_id,
            "reason": reason,
            "phi": self.current_phi,
        }
        path = self._online_dir / "lineage-fork-log.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def load_phi_history(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if cleaned:
            rows.append(json.loads(cleaned))
    return rows


def append_phi_history(row: dict[str, Any], *, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def run_kernel_loop(event: Event, kernel: NovaKernel) -> KernelResult:
    errors: list[str] = []
    try:
        kernel.trace_store.append(event)
        kernel.update_continuity_hash(event)
        kernel.validate_continuity(event)
        kernel.validate_reconstruction(event)
        kernel.validate_verification(event)
        kernel.validate_invariants(event)
        kernel.validate_identity_wave(event)
        kernel.validate_universal_meaning(event)
        kernel.validate_convergence_operator()
        kernel.validate_lci(event)
        kernel.validate_convergence_fitness()
        kernel.update_convergence_fitness(event.lineage)
        kernel.evolve_lineage(event.lineage, event=event)
        kernel.persist_state()
        kernel.persist_lineage_state(event.lineage)
        status: Literal["ok", "error"] = "ok"
    except Exception as exc:
        errors.append(str(exc))
        status = "error"

    result = KernelResult(
        event_id=event.event_id,
        lineage=event.lineage,
        phi=kernel.current_phi,
        continuity_hash=kernel.current_continuity_hash,
        status=status,
        errors=errors,
    )
    if status == "ok":
        kernel.log_kernel_loop(result)
    return result


def handle_genesis_event(event: GenesisEvent, kernel: NovaKernel) -> KernelResult:
    result = run_kernel_loop(event, kernel)
    if result.status != "ok":
        return result

    ledger = MeaningLedger()
    if ledger.get(ML_GENESIS_EVENT_ID) is None:
        ledger.append(
            MeaningLedgerEntry(
                entry_id=ML_GENESIS_EVENT_ID,
                kind=MeaningEntryKind.CONTINUITY_FREEZE,
                title="First lawful creation event (EVT-GENESIS-0001)",
                body=json.dumps(
                    {
                        "event_id": event.event_id,
                        "actor": event.actor,
                        "lineage": event.lineage,
                        "payload": event.payload,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                lineage=[L0_GENESIS_ID, "ML-LINEAGE-GENESIS-001"],
                law_surfaces=["EVT-GENESIS-0001", "ugr.continuity", "UGR-C8"],
                metadata={"kernel_loop": KERNEL_LOOP_LOG_ID, "phi": result.phi},
                created_at=_now_iso(),
            )
        )
    apply_lci_stack(ledger=ledger)
    return result


def fork_lineage(kernel: NovaKernel, source_id: str, new_id: str, reason: str) -> LineageRecord:
    source = kernel.get_lineage(source_id)
    fork_event = Event(
        event_id="EVT-LINEAGE-FORK-0001",
        kind="lineage.fork",
        actor="OPERATOR:JON",
        lineage=new_id,
        timestamp=_now_iso(),
        payload={
            "source_lineage": source_id,
            "new_lineage": new_id,
            "reason": reason,
            "constraints": {
                "inherits_invariants": True,
                "inherits_meaning_anchors": True,
                "cannot_weaken_C8_C9": True,
            },
        },
    )
    forked_lineage = Lineage(
        lineage_id=new_id,
        event_ids=continuity_trace(source.lineage),
        meaning_class=source.lineage.meaning_class,
        generativity=source.generativity,
        metadata={
            **source.lineage.metadata,
            "parent_id": source_id,
            "state": "FORKED",
            "fork_reason": reason,
        },
    )
    record = LineageRecord(
        lineage_id=new_id,
        parent_id=source_id,
        created_at=_now_iso(),
        state="FORKED",
        generativity=source.generativity,
        invariants_ref=source.invariants_ref,
        continuity_hash=continuity_hash(continuity_trace(forked_lineage)),
        lineage=forked_lineage,
    )
    kernel.register_lineage(record)
    kernel.update_convergence_fitness_for_lineages([source_id, new_id])
    kernel.ensure_phi_above_min()
    kernel.log_lineage_fork(source_id, new_id, reason)
    kernel.trace_store.append(fork_event)
    return record


def run_genesis_kernel_loop_proof(*, kernel: NovaKernel | None = None) -> dict[str, Any]:
    active = kernel or NovaKernel()
    result = handle_genesis_event(GenesisEvent(), active)
    return {
        "capability_id": KERNEL_LOOP_LOG_ID,
        "result": result.to_dict(),
        "lineage_view": lineage_math_view(active.get_lineage(L0_GENESIS_ID).lineage).to_dict(),
        "constitutional_laws_checked": [item.code for item in CONSTITUTIONAL_CHAIN],
        "passed": result.status == "ok" and result.phi >= active.phi_min,
    }
