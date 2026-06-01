# Jarvis Memory Board Doctrine

This document defines the canonical Jarvis memory-upgrade doctrine for a
modular memory board architecture.

It describes how Jarvis memory should grow, upgrade, and migrate without
becoming one undifferentiated flat memory bank.

Important truth rule:

- this doctrine is the canonical design and upgrade law for Jarvis memory
- it is not, by itself, proof that every sibling Jarvis runtime already
  implements the full board/controller/module system exactly as written

Live reference implementation:

- [../../src/jarvis_memory_board.py](../../src/jarvis_memory_board.py)
- [../../tests/test_jarvis_memory_board.py](../../tests/test_jarvis_memory_board.py)

Current implementation status:

- the six active slots are now populated in the live AAIS memory-board model
- the canonical installed cards are `foundation_v1`, `operational_v1`,
  `session_v1`, `archive_v1`, `signal_v1`, and `preference_v1`
- the board can be inspected through `GET /api/jarvis/memory/board`

## Non-Negotiables

These rules are mandatory:

- slot purpose stays fixed
  - a better module may upgrade a slot, but it may not change what that slot is
    for
- controller must approve install or swap
  - no random module may be dropped in without compatibility checks
- migration must be lawful
  - old memory may move to a new module only if trust class and slot role are
    preserved

## Core Idea

Jarvis memory is not one flat bank.

Jarvis uses a Memory Board with:

- fixed expansion slots
- installable memory modules
- a central memory controller
- upgrade and migration rules

This allows Jarvis memory to grow like RAM upgrades:

- add a new module into an empty slot
- replace an older module with a better one
- keep the board stable while improving memory quality

## Main Components

### 1. Memory Board

The board is the fixed chassis.

Board rules:

- supports up to `10` slots
- only `6` slots are active at the current stage
- remaining slots are reserved for future expansion
- each slot accepts only approved module classes
- slots define purpose, not just capacity
- slot purpose remains fixed even when a module is upgraded or replaced

### 2. Memory Controller

The controller governs the whole memory system.

Controller responsibilities:

- detect installed modules
- validate slot compatibility
- register active modules
- route retrieval requests
- enforce trust and priority rules
- control promotion and demotion
- approve upgrade and migration
- reject invalid modules

The controller is the final authority.

### 3. Memory Modules

Each module is like a RAM stick, but specialized.

Each module must declare:

- `module_id`
- `module_version`
- `module_class`
- `supported_slot`
- `capacity`
- `trust_class`
- `retrieval_priority`
- `retention_policy`
- `eviction_policy`
- `promotion_rules`
- `migration_rules`
- `enabled`

## Slot Layout

Active now:

- `slot_01` — Foundation Module
- `slot_02` — Operational Module
- `slot_03` — Session Module
- `slot_04` — Archive Module
- `slot_05` — Signal Module
- `slot_06` — Preference Module

Current installed cards:

- `slot_01` — `foundation_v1`
- `slot_02` — `operational_v1`
- `slot_03` — `session_v1`
- `slot_04` — `archive_v1`
- `slot_05` — `signal_v1`
- `slot_06` — `preference_v1`

Reserved for later:

- `slot_07` — empty
- `slot_08` — empty
- `slot_09` — empty
- `slot_10` — empty

## Active Module Roles

### Slot 01 — Foundation

Purpose:

- law
- doctrine
- identity truths
- canonical truths

Rules:

- highest trust
- no auto-eviction
- explicit write/admission only
- highest retrieval priority

### Slot 02 — Operational

Purpose:

- stable working knowledge
- verified recurring patterns
- persistent architecture truths
- accepted system behavior

Rules:

- medium-large capacity
- promotion from session allowed if verified
- may be archived later

### Slot 03 — Session

Purpose:

- current thread continuity
- active tasks
- temporary work context
- near-term memory

Rules:

- rolling window
- short retention
- evictable
- promotable upward if repeated or verified

### Slot 04 — Archive

Purpose:

- old validated records
- historical memory
- prior states
- deprecated but preserved knowledge

Rules:

- large or unbounded
- low default retrieval priority
- queried intentionally or when needed

### Slot 05 — Signal

Purpose:

- transient observations
- low-confidence inputs
- noisy data
- pending interpretation

Rules:

- short lifespan
- lowest trust
- cannot define identity or doctrine
- must be validated before promotion

### Slot 06 — Preference

Purpose:

- operator preferences
- recurring workflow habits
- handling style
- stable user-level patterns

Rules:

- separate from identity
- medium trust
- not equal to doctrine
- retrievable for personalization inside law

## Retrieval Order

Jarvis does not search all modules equally.

Identity / law query:

- Foundation
- Operational

Current task query:

- Session
- Operational
- Archive

User preference query:

- Preference
- Session
- Operational

Historical query:

- Archive
- Operational

Noisy signal query:

- Signal
- Session

## Upgrade Model

### Add Module

Used when an empty slot exists.

Flow:

- define new module
- validate slot compatibility
- install
- register with controller
- activate retrieval rules

### Replace Module

Used when a better module exists for an occupied slot.

Flow:

- validate replacement compatibility
- freeze old module
- migrate approved memory
- verify integrity
- activate new module
- retire old module

### Upgrade Law

A module may be replaced only if:

- slot compatibility is preserved
- slot purpose remains unchanged
- controller accepts the module
- trust rules remain valid
- slot purpose is not violated
- migration passes verification

## Migration Rules

Migration is not automatic dumping.

Migration must:

- preserve memory class
- preserve trust level
- preserve slot role/purpose
- remove invalid or duplicate entries
- log what was moved
- verify no slot-purpose violation happened

Examples:

- Session memory can move into Operational if verified
- Operational truths can move into Archive when aging
- nothing moves into Foundation without explicit admission

## Core Doctrine

### Jarvis Memory Doctrine

1. Jarvis memory is slot-based and module-driven.
2. The memory board supports up to ten slots, with six active at the current stage.
3. Each slot has a declared purpose, trust class, and retrieval role.
4. Memory modules may be installed, replaced, or upgraded only through controller approval.
5. Better memory capability is gained by installing superior modules, not by mutating one undifferentiated memory pool.
6. No module may violate the declared purpose of its slot.
7. Lower-trust memory may inform higher layers but may not redefine them.
8. Migration between modules must be validated before activation.
9. Reserved slots exist as structural expansion capacity and remain inactive until explicitly enabled.
10. Jarvis memory growth shall remain bounded, governed, and auditable.

## Simple Data Shape

```json
{
  "slot_id": "slot_02",
  "slot_name": "operational",
  "installed": true,
  "module": {
    "module_id": "operational_v1",
    "module_version": "1.0.0",
    "module_class": "operational",
    "supported_slot": "slot_02",
    "capacity": 256,
    "trust_class": "verified",
    "retrieval_priority": 80,
    "retention_policy": "persistent",
    "eviction_policy": "age_and_rank",
    "promotion_rules": ["from_session_verified"],
    "migration_rules": ["to_archive_on_age"],
    "enabled": true
  }
}
```

## Suggested Python Structure

```python
class MemoryModule:
    def __init__(
        self,
        module_id,
        module_version,
        module_class,
        supported_slot,
        capacity,
        trust_class,
        retrieval_priority,
        retention_policy,
        eviction_policy,
        promotion_rules,
        migration_rules,
        enabled=True,
    ):
        self.module_id = module_id
        self.module_version = module_version
        self.module_class = module_class
        self.supported_slot = supported_slot
        self.capacity = capacity
        self.trust_class = trust_class
        self.retrieval_priority = retrieval_priority
        self.retention_policy = retention_policy
        self.eviction_policy = eviction_policy
        self.promotion_rules = promotion_rules
        self.migration_rules = migration_rules
        self.enabled = enabled


class MemorySlot:
    def __init__(self, slot_id, slot_name, accepted_class):
        self.slot_id = slot_id
        self.slot_name = slot_name
        self.accepted_class = accepted_class
        self.module = None

    def install(self, module):
        if module.module_class != self.accepted_class:
            raise ValueError("Incompatible module class for slot")
        self.module = module


class MemoryController:
    def __init__(self, slots):
        self.slots = {slot.slot_id: slot for slot in slots}

    def register_module(self, slot_id, module):
        self.slots[slot_id].install(module)

    def get_active_modules(self):
        return [
            slot.module for slot in self.slots.values()
            if slot.module and slot.module.enabled
        ]

    def route_query(self, query_type):
        routing = {
            "identity": ["slot_01", "slot_02"],
            "task": ["slot_03", "slot_02", "slot_04"],
            "preference": ["slot_06", "slot_03", "slot_02"],
            "history": ["slot_04", "slot_02"],
            "signal": ["slot_05", "slot_03"],
        }
        return routing.get(query_type, [])
```

## Design Constraint

Jarvis memory upgrades must improve quality without violating structure.

That means:

- board stability first
- slot purpose fixed first
- slot purpose preserved
- controller authority preserved
- migration validated before activation
- auditability preserved through every upgrade step
