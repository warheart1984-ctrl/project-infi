"""Jarvis modular memory-board law and controller primitives."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any

from src.datetime_compat import UTC


class MemoryBoardViolation(ValueError):
    """Raised when a memory-board action violates slot/controller law."""


@dataclass(frozen=True, slots=True)
class MemoryModule:
    """One installable Jarvis memory module."""

    module_id: str
    module_version: str
    module_class: str
    supported_slot: str
    capacity: int
    trust_class: str
    retrieval_priority: int
    retention_policy: str
    eviction_policy: str
    promotion_rules: tuple[str, ...] = ()
    migration_rules: tuple[str, ...] = ()
    display_name: str = ""
    summary: str = ""
    linked_subsystem: str = ""
    board_family: str = ""
    enabled: bool = True


@dataclass(slots=True)
class MemorySlot:
    """One fixed-purpose slot on the Jarvis memory board."""

    slot_id: str
    slot_name: str
    accepted_class: str
    active: bool = True
    module: MemoryModule | None = None
    retired_modules: list[MemoryModule] = field(default_factory=list)

    def install(
        self,
        module: MemoryModule,
        *,
        controller_approved: bool = False,
        replacing: bool = False,
    ) -> MemoryModule:
        """Install a module only through controller-approved validation."""
        if not controller_approved:
            raise MemoryBoardViolation(
                f"{self.slot_id} rejects direct install; controller approval is required."
            )
        if not self.active:
            raise MemoryBoardViolation(f"{self.slot_id} is reserved and inactive.")
        if module.supported_slot != self.slot_id:
            raise MemoryBoardViolation(
                f"{module.module_id} targets {module.supported_slot}, not {self.slot_id}."
            )
        if module.module_class != self.accepted_class:
            raise MemoryBoardViolation(
                f"{self.slot_id} preserves purpose={self.accepted_class}; "
                f"{module.module_class} cannot replace it."
            )
        if self.module is not None and not replacing:
            raise MemoryBoardViolation(
                f"{self.slot_id} is occupied; use controller swap instead of direct install."
            )
        self.module = module
        return module


@dataclass(frozen=True, slots=True)
class MigrationRecord:
    """One migrated memory record that must preserve trust class and slot role."""

    record_id: str
    slot_id: str
    slot_role: str
    trust_class: str
    text: str = ""


@dataclass(frozen=True, slots=True)
class MemoryBoardProfile:
    """Named board metadata shared with Memory Bank and the controller."""

    board_id: str
    board_label: str
    board_version: str
    board_family: str
    summary: str
    linked_subsystems: tuple[str, ...] = ()
    retired_board: dict[str, str] = field(default_factory=dict)


class MemoryController:
    """Controller authority for install, swap, routing, and migration checks."""

    def __init__(
        self,
        slots: list[MemorySlot],
        *,
        board_profile: MemoryBoardProfile | None = None,
    ):
        self.slots = {slot.slot_id: slot for slot in slots}
        self.board_profile = board_profile
        self.migration_log: list[dict[str, object]] = []

    def register_module(self, slot_id: str, module: MemoryModule) -> MemoryModule:
        """Install a module into an empty slot after controller validation."""
        slot = self._require_slot(slot_id)
        if slot.module is not None:
            raise MemoryBoardViolation(
                f"{slot_id} already has {slot.module.module_id}; use swap_module."
            )
        return slot.install(module, controller_approved=True)

    def swap_module(
        self,
        slot_id: str,
        module: MemoryModule,
        migration_records: list[MigrationRecord | dict[str, object]] | None = None,
    ) -> dict[str, object]:
        """Replace a module only if slot purpose and lawful migration are preserved."""
        slot = self._require_slot(slot_id)
        current = slot.module
        if current is None:
            raise MemoryBoardViolation(f"{slot_id} has no installed module to replace.")

        validated_records = self._validate_migration(
            slot,
            current,
            module,
            migration_records or [],
        )
        retired = replace(current, enabled=False)
        slot.retired_modules.append(retired)
        slot.module = None
        activated = slot.install(module, controller_approved=True, replacing=True)
        event = {
            "slot_id": slot.slot_id,
            "slot_role": slot.slot_name,
            "retired_module_id": current.module_id,
            "activated_module_id": activated.module_id,
            "migrated_record_count": len(validated_records),
        }
        self.migration_log.append(event)
        return {
            "slot_id": slot.slot_id,
            "retired_module": retired,
            "activated_module": activated,
            "migrated_records": validated_records,
            "event": event,
        }

    def get_active_modules(self) -> list[MemoryModule]:
        """Return all enabled modules installed in active slots."""
        return [
            slot.module
            for slot in self.slots.values()
            if slot.active and slot.module and slot.module.enabled
        ]

    def route_query(self, query_type: str) -> list[str]:
        """Return the doctrine-aligned slot order for a query type."""
        routing = {
            "identity": ["slot_01", "slot_02"],
            "task": ["slot_03", "slot_02", "slot_04"],
            "preference": ["slot_06", "slot_03", "slot_02"],
            "history": ["slot_04", "slot_02"],
            "signal": ["slot_05", "slot_03"],
        }
        return routing.get(query_type, [])

    def _require_slot(self, slot_id: str) -> MemorySlot:
        try:
            return self.slots[slot_id]
        except KeyError as exc:
            raise MemoryBoardViolation(f"Unknown memory slot: {slot_id}") from exc

    def _normalize_record(
        self,
        raw: MigrationRecord | dict[str, object],
    ) -> MigrationRecord:
        if isinstance(raw, MigrationRecord):
            return raw
        try:
            return MigrationRecord(
                record_id=str(raw["record_id"]),
                slot_id=str(raw["slot_id"]),
                slot_role=str(raw["slot_role"]),
                trust_class=str(raw["trust_class"]),
                text=str(raw.get("text", "")),
            )
        except KeyError as exc:
            raise MemoryBoardViolation(
                f"Migration record is incomplete; missing {exc.args[0]}."
            ) from exc

    def _validate_migration(
        self,
        slot: MemorySlot,
        current: MemoryModule,
        replacement: MemoryModule,
        migration_records: list[MigrationRecord | dict[str, object]],
    ) -> list[MigrationRecord]:
        if replacement.module_class != slot.accepted_class:
            raise MemoryBoardViolation(
                f"{slot.slot_id} keeps purpose={slot.accepted_class}; "
                f"{replacement.module_class} is incompatible."
            )
        if replacement.trust_class != current.trust_class:
            raise MemoryBoardViolation(
                f"{slot.slot_id} swap must preserve trust class; "
                f"{current.trust_class} -> {replacement.trust_class} is not lawful."
            )

        validated: list[MigrationRecord] = []
        seen: set[tuple[str, str]] = set()
        for raw_record in migration_records:
            record = self._normalize_record(raw_record)
            if record.slot_id != slot.slot_id:
                raise MemoryBoardViolation(
                    f"{slot.slot_id} migration must preserve slot_id; got {record.slot_id}."
                )
            if record.slot_role != slot.slot_name:
                raise MemoryBoardViolation(
                    f"{slot.slot_id} migration must preserve slot role={slot.slot_name}; "
                    f"got {record.slot_role}."
                )
            if record.trust_class != current.trust_class:
                raise MemoryBoardViolation(
                    f"{slot.slot_id} migration must preserve trust class={current.trust_class}; "
                    f"got {record.trust_class}."
                )
            dedupe_key = (record.record_id, record.text)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            validated.append(record)
        return validated


def default_memory_slots() -> list[MemorySlot]:
    """Return the canonical 10-slot Jarvis memory board layout."""
    return [
        MemorySlot("slot_01", "foundation", "foundation", active=True),
        MemorySlot("slot_02", "operational", "operational", active=True),
        MemorySlot("slot_03", "session", "session", active=True),
        MemorySlot("slot_04", "archive", "archive", active=True),
        MemorySlot("slot_05", "signal", "signal", active=True),
        MemorySlot("slot_06", "preference", "preference", active=True),
        MemorySlot("slot_07", "reserved_07", "reserved", active=False),
        MemorySlot("slot_08", "reserved_08", "reserved", active=False),
        MemorySlot("slot_09", "reserved_09", "reserved", active=False),
        MemorySlot("slot_10", "reserved_10", "reserved", active=False),
    ]


def default_active_modules() -> list[MemoryModule]:
    """Return the capability-aware six-card board now installed in Memory Bank."""
    return [
        MemoryModule(
            module_id="capability_foundation_v2",
            module_version="2.0.0",
            module_class="foundation",
            supported_slot="slot_01",
            capacity=128,
            trust_class="canonical",
            retrieval_priority=100,
            retention_policy="explicit_only",
            eviction_policy="none",
            promotion_rules=(),
            migration_rules=(),
            display_name="Capability Foundation",
            summary="Holds the deterministic result law, error taxonomy, and adapter doctrine for governed capability execution.",
            linked_subsystem="aais_capability_module",
            board_family="capability_adapter_board",
            enabled=True,
        ),
        MemoryModule(
            module_id="capability_adapter_registry_v2",
            module_version="2.0.0",
            module_class="operational",
            supported_slot="slot_02",
            capacity=256,
            trust_class="verified",
            retrieval_priority=80,
            retention_policy="persistent",
            eviction_policy="age_and_rank",
            promotion_rules=("from_session_if_execution_verified",),
            migration_rules=("to_archive_after_provider_rotation",),
            display_name="Adapter Registry",
            summary="Tracks which capability adapters are admitted, provider-isolated, and safe for live AAIS routing.",
            linked_subsystem="aais_capability_module",
            board_family="capability_adapter_board",
            enabled=True,
        ),
        MemoryModule(
            module_id="capability_intent_buffer_v2",
            module_version="2.0.0",
            module_class="session",
            supported_slot="slot_03",
            capacity=96,
            trust_class="working",
            retrieval_priority=90,
            retention_policy="rolling_window",
            eviction_policy="window_trim",
            promotion_rules=("to_operational_if_execution_verified",),
            migration_rules=("discard_on_expiry",),
            display_name="Intent Buffer",
            summary="Stores short-lived intent translations, trace ids, and turn-scoped capability context before durable admission.",
            linked_subsystem="memory_bank",
            board_family="capability_adapter_board",
            enabled=True,
        ),
        MemoryModule(
            module_id="capability_audit_archive_v2",
            module_version="2.0.0",
            module_class="archive",
            supported_slot="slot_04",
            capacity=1024,
            trust_class="preserved",
            retrieval_priority=30,
            retention_policy="long_term",
            eviction_policy="none",
            promotion_rules=(),
            migration_rules=("from_operational_after_governance_review",),
            display_name="Audit Archive",
            summary="Preserves admitted capability traces, retired board cards, and structured failure lineage for review.",
            linked_subsystem="memory_bank",
            board_family="capability_adapter_board",
            enabled=True,
        ),
        MemoryModule(
            module_id="capability_semantic_guard_v2",
            module_version="2.0.0",
            module_class="signal",
            supported_slot="slot_05",
            capacity=64,
            trust_class="low_confidence",
            retrieval_priority=20,
            retention_policy="short_lived",
            eviction_policy="rapid_decay",
            promotion_rules=("to_operational_if_semantically_verified",),
            migration_rules=("discard_if_unverified",),
            display_name="Semantic Guard",
            summary="Carries low-confidence provider signals until semantic validation proves they are safe to admit.",
            linked_subsystem="aais_capability_module",
            board_family="capability_adapter_board",
            enabled=True,
        ),
        MemoryModule(
            module_id="capability_routing_preferences_v2",
            module_version="2.0.0",
            module_class="preference",
            supported_slot="slot_06",
            capacity=128,
            trust_class="stable_user",
            retrieval_priority=70,
            retention_policy="persistent",
            eviction_policy="age_and_rank",
            promotion_rules=("from_session_if_operator_stable",),
            migration_rules=("to_archive_on_operator_reset",),
            display_name="Routing Preferences",
            summary="Stores operator-approved defaults for capability routing, provider choice, and admission behavior.",
            linked_subsystem="memory_bank",
            board_family="capability_adapter_board",
            enabled=True,
        ),
    ]


def default_memory_board_profile() -> MemoryBoardProfile:
    """Return the canonical board metadata shared with Memory Bank."""
    return MemoryBoardProfile(
        board_id="capability_adapter_board",
        board_label="Capability Adapter Board",
        board_version="2.0.0",
        board_family="capability_adapter",
        summary=(
            "A capability-aware board that links Memory Bank to deterministic adapter law, "
            "semantic guards, audit archive, and operator routing defaults."
        ),
        linked_subsystems=("memory_bank", "aais_capability_module"),
        retired_board={
            "board_id": "legacy_memory_board_v1",
            "board_label": "Legacy Six-Card Memory Board",
        },
    )


def build_default_memory_controller() -> MemoryController:
    """Build the canonical controller with the installed capability-aware board."""
    profile = default_memory_board_profile()
    controller = MemoryController(default_memory_slots(), board_profile=profile)
    for module in default_active_modules():
        controller.register_module(module.supported_slot, module)
    return controller


def build_memory_board_snapshot(controller: MemoryController) -> dict[str, object]:
    """Return an inspectable snapshot of the current memory board state."""
    slots = []
    active_slots = 0
    installed_slots = 0
    for slot in controller.slots.values():
        if slot.active:
            active_slots += 1
        if slot.module is not None:
            installed_slots += 1
        slots.append(
            {
                "slot_id": slot.slot_id,
                "slot_name": slot.slot_name,
                "accepted_class": slot.accepted_class,
                "active": slot.active,
                "installed": slot.module is not None,
                "reserved": not slot.active,
                "module": (
                    {
                        "module_id": slot.module.module_id,
                        "module_version": slot.module.module_version,
                        "module_class": slot.module.module_class,
                        "supported_slot": slot.module.supported_slot,
                        "capacity": slot.module.capacity,
                        "trust_class": slot.module.trust_class,
                        "retrieval_priority": slot.module.retrieval_priority,
                        "retention_policy": slot.module.retention_policy,
                        "eviction_policy": slot.module.eviction_policy,
                        "promotion_rules": list(slot.module.promotion_rules),
                        "migration_rules": list(slot.module.migration_rules),
                        "display_name": slot.module.display_name,
                        "summary": slot.module.summary,
                        "linked_subsystem": slot.module.linked_subsystem,
                        "board_family": slot.module.board_family,
                        "enabled": slot.module.enabled,
                    }
                    if slot.module
                    else None
                ),
            }
        )
    board_profile = controller.board_profile or default_memory_board_profile()
    return {
        "board": {
            "board_id": board_profile.board_id,
            "board_label": board_profile.board_label,
            "board_version": board_profile.board_version,
            "board_family": board_profile.board_family,
            "summary": board_profile.summary,
            "linked_subsystems": list(board_profile.linked_subsystems),
            "retired_board": dict(board_profile.retired_board),
        },
        "max_slots": len(controller.slots),
        "active_slots": active_slots,
        "installed_slots": installed_slots,
        "reserved_slots": len(controller.slots) - active_slots,
        "slots": slots,
    }


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def to_memory_board_envelope(
    snapshot: dict[str, object],
    *,
    cisiv_stage: str = "implementation",
    claim_label: str = "asserted",
) -> dict[str, Any]:
    """Map a memory board snapshot to jarvis_memory_board.v1."""
    now = _utc_now_iso()
    board = dict(snapshot.get("board") or {})
    slot_rows = []
    for slot in list(snapshot.get("slots") or []):
        if not isinstance(slot, dict):
            continue
        installed = slot.get("module")
        slot_row: dict[str, Any] = {
            "slot_id": str(slot.get("slot_id") or ""),
            "slot_name": str(slot.get("slot_name") or ""),
            "accepted_class": str(slot.get("accepted_class") or ""),
            "active": bool(slot.get("active")),
            "claim_label": claim_label,
        }
        if isinstance(installed, dict):
            slot_row["installed_module"] = {
                "module_id": str(installed.get("module_id") or ""),
                "module_version": str(installed.get("module_version") or ""),
                "module_class": str(installed.get("module_class") or ""),
                "supported_slot": str(installed.get("supported_slot") or ""),
                "trust_class": str(installed.get("trust_class") or ""),
                "enabled": bool(installed.get("enabled", True)),
                "claim_label": claim_label,
            }
        slot_rows.append(slot_row)

    return {
        "jarvis_memory_board_version": "jarvis_memory_board.v1",
        "board_id": str(board.get("board_id") or "jarvis.memory_board"),
        "profile_name": str(board.get("board_label") or ""),
        "slots": slot_rows,
        "controller_state": {
            "approval_required": True,
            "claim_label": claim_label,
        },
        "migrations": [],
        "cisiv_stage": cisiv_stage,
        "claim_label": claim_label,
        "created_at_utc": now,
        "updated_at_utc": now,
    }
