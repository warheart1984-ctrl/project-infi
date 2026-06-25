"""Domain runtime invariant IDs — shared across personal/system runtimes."""

from __future__ import annotations

PERSONAL_CONTINUITY_INVARIANTS: frozenset[str] = frozenset(
    {"PC-1", "PC-2", "PC-3", "PC-4"}
)
RELATIONSHIP_INVARIANTS: frozenset[str] = frozenset({"RR-1", "RR-2", "RR-3"})
COGNITIVE_INVARIANTS: frozenset[str] = frozenset({"CR-1", "CR-2", "CR-3"})
FOUNDER_INVARIANTS: frozenset[str] = frozenset({"FR-1", "FR-2", "FR-3"})
OPPORTUNITY_INVARIANTS: frozenset[str] = frozenset({"OR-1", "OR-2", "OR-3"})
REPUTATION_INVARIANTS: frozenset[str] = frozenset({"RRp-1", "RRp-2", "RRp-3"})
BURNOUT_INVARIANTS: frozenset[str] = frozenset({"BR-1", "BR-2", "BR-3"})

ALL_DOMAIN_INVARIANTS: dict[str, frozenset[str]] = {
    "personal_continuity": PERSONAL_CONTINUITY_INVARIANTS,
    "relationship": RELATIONSHIP_INVARIANTS,
    "cognitive": COGNITIVE_INVARIANTS,
    "founder": FOUNDER_INVARIANTS,
    "opportunity": OPPORTUNITY_INVARIANTS,
    "reputation": REPUTATION_INVARIANTS,
    "burnout": BURNOUT_INVARIANTS,
}
