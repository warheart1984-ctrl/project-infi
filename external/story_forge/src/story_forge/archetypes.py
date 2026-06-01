from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from story_forge.models import Archetype, CharacterGenerationContract, MemoryEntry


@dataclass(slots=True)
class ArchetypeVariantDefinition:
    variant_id: str
    name: str
    summary: str
    trait_pool: list[str] = field(default_factory=list)
    role_biases: list[str] = field(default_factory=list)
    stat_biases: dict[str, int] = field(default_factory=dict)
    modifier_overrides: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class ArchetypeDefinition:
    base_id: str
    display_name: str
    summary: str
    core_drive: str
    intent_keywords: dict[str, float] = field(default_factory=dict)
    memory_weights: dict[str, float] = field(default_factory=dict)
    default_traits: list[str] = field(default_factory=list)
    role_biases: list[str] = field(default_factory=list)
    default_modifiers: dict[str, float] = field(default_factory=dict)
    variants: list[ArchetypeVariantDefinition] = field(default_factory=list)


ARCHETYPE_DEFINITIONS: dict[str, ArchetypeDefinition] = {
    "guardian": ArchetypeDefinition(
        base_id="guardian",
        display_name="Guardian",
        summary="Protective, vow-centered, and anchored by responsibility.",
        core_drive="Keep people, places, and promises intact.",
        intent_keywords={
            "protect": 4.0,
            "guard": 4.0,
            "shield": 3.5,
            "save": 3.0,
            "keep safe": 4.5,
            "defend": 4.0,
            "care": 2.5,
            "hold the line": 4.5,
            "oath": 2.0,
            "rescue": 3.5,
        },
        memory_weights={
            "alliance": 2.0,
            "vow": 2.4,
            "oath_trace": 2.2,
            "protection": 2.0,
        },
        default_traits=["steady", "protective", "dutiful"],
        role_biases=["keeper", "escort", "shield"],
        default_modifiers={
            "scene_intensity": 0.95,
            "relationship_bias": 1.15,
            "observation_bias": 0.9,
        },
        variants=[
            ArchetypeVariantDefinition(
                variant_id="oathkeeper",
                name="Oathkeeper",
                summary="Turns promise into structure and carries duty past comfort.",
                trait_pool=["resolute", "loyal", "measured"],
                role_biases=["keeper", "sentinel"],
                stat_biases={"loyalty": 10, "stability": 6},
                modifier_overrides={"relationship_bias": 1.2},
            ),
            ArchetypeVariantDefinition(
                variant_id="hearthwarden",
                name="Hearthwarden",
                summary="Protects by creating a safe center others can return to.",
                trait_pool=["warm", "watchful", "grounded"],
                role_biases=["guardian", "host"],
                stat_biases={"stability": 8, "fear": -2},
                modifier_overrides={"scene_intensity": 0.92},
            ),
            ArchetypeVariantDefinition(
                variant_id="bulwark",
                name="Bulwark",
                summary="Absorbs pressure first and yields only when collapse would save more.",
                trait_pool=["unyielding", "brave", "scarred"],
                role_biases=["frontliner", "anchor"],
                stat_biases={"health": 10, "power": 2},
                modifier_overrides={"scene_intensity": 1.0},
            ),
        ],
    ),
    "seeker": ArchetypeDefinition(
        base_id="seeker",
        display_name="Seeker",
        summary="Curious, mobile, and driven toward hidden structure.",
        core_drive="Find what is concealed and keep moving toward the next threshold.",
        intent_keywords={
            "search": 3.5,
            "seek": 4.0,
            "find": 3.0,
            "discover": 4.0,
            "investigate": 4.5,
            "explore": 3.5,
            "map": 3.0,
            "follow": 2.5,
            "trace": 3.0,
            "archive": 2.5,
        },
        memory_weights={
            "discovery": 2.3,
            "travel": 2.0,
            "clarity": 1.8,
            "record_revelation": 2.0,
        },
        default_traits=["curious", "restless", "adaptive"],
        role_biases=["scout", "investigator", "finder"],
        default_modifiers={
            "scene_intensity": 1.0,
            "relationship_bias": 0.95,
            "observation_bias": 1.15,
        },
        variants=[
            ArchetypeVariantDefinition(
                variant_id="archivist",
                name="Archivist",
                summary="Tracks pattern through fragments, ledgers, and residue.",
                trait_pool=["methodical", "focused", "precise"],
                role_biases=["scholar", "investigator"],
                stat_biases={"power": 2, "stability": 4},
                modifier_overrides={"observation_bias": 1.2},
            ),
            ArchetypeVariantDefinition(
                variant_id="pathfinder",
                name="Pathfinder",
                summary="Prefers roads, thresholds, and untested routes over stale certainty.",
                trait_pool=["nimble", "alert", "independent"],
                role_biases=["scout", "guide"],
                stat_biases={"health": 4, "fear": -1},
                modifier_overrides={"scene_intensity": 1.04},
            ),
            ArchetypeVariantDefinition(
                variant_id="lanternbearer",
                name="Lanternbearer",
                summary="Brings light into the wrong places even when it changes what is found.",
                trait_pool=["hopeful", "tenacious", "attentive"],
                role_biases=["guide", "witness"],
                stat_biases={"morality": 3, "stability": 2},
                modifier_overrides={"relationship_bias": 1.0},
            ),
        ],
    ),
    "rebel": ArchetypeDefinition(
        base_id="rebel",
        display_name="Rebel",
        summary="Defiant, catalytic, and willing to break a bad system openly.",
        core_drive="Refuse coercion and force a new shape through direct pressure.",
        intent_keywords={
            "refuse": 3.0,
            "resist": 4.0,
            "defy": 4.5,
            "break": 4.0,
            "shatter": 4.0,
            "steal": 3.0,
            "fight": 3.5,
            "attack": 3.0,
            "burn": 3.5,
            "revolt": 4.5,
        },
        memory_weights={
            "betrayal": 2.2,
            "battle": 2.4,
            "unrest": 1.8,
            "pressure": 1.8,
        },
        default_traits=["bold", "volatile", "uncompromising"],
        role_biases=["breaker", "agitator", "outlaw"],
        default_modifiers={
            "scene_intensity": 1.12,
            "relationship_bias": 0.88,
            "observation_bias": 0.92,
        },
        variants=[
            ArchetypeVariantDefinition(
                variant_id="sparkbearer",
                name="Sparkbearer",
                summary="Starts change fast and trusts others to carry the flame forward.",
                trait_pool=["fiery", "charismatic", "reckless"],
                role_biases=["agitator", "vanguard"],
                stat_biases={"power": 4, "fear": -2},
                modifier_overrides={"scene_intensity": 1.15},
            ),
            ArchetypeVariantDefinition(
                variant_id="breaker",
                name="Breaker",
                summary="Targets structures directly and accepts the cost of rupture.",
                trait_pool=["hard", "direct", "ruthless"],
                role_biases=["saboteur", "duelist"],
                stat_biases={"power": 6, "morality": -1},
                modifier_overrides={"relationship_bias": 0.82},
            ),
            ArchetypeVariantDefinition(
                variant_id="wildcard",
                name="Wildcard",
                summary="Moves sideways through conflict and makes institutions lose rhythm.",
                trait_pool=["unreadable", "nimble", "audacious"],
                role_biases=["trickster", "escape-artist"],
                stat_biases={"health": 2, "power": 3},
                modifier_overrides={"observation_bias": 1.0},
            ),
        ],
    ),
    "strategist": ArchetypeDefinition(
        base_id="strategist",
        display_name="Strategist",
        summary="Ordered, deliberate, and focused on leverage, timing, and structure.",
        core_drive="Shape outcomes by controlling sequence, cost, and position.",
        intent_keywords={
            "plan": 4.0,
            "calculate": 4.5,
            "arrange": 3.5,
            "position": 3.0,
            "bargain": 3.5,
            "prepare": 3.0,
            "strategy": 4.5,
            "count": 2.0,
            "order": 2.5,
            "manage": 2.5,
        },
        memory_weights={
            "resolution": 2.3,
            "choice": 2.0,
            "language_correction": 1.8,
            "correction_debt": 1.6,
        },
        default_traits=["patient", "precise", "composed"],
        role_biases=["planner", "broker", "architect"],
        default_modifiers={
            "scene_intensity": 1.08,
            "relationship_bias": 0.92,
            "observation_bias": 1.05,
        },
        variants=[
            ArchetypeVariantDefinition(
                variant_id="broker",
                name="Broker",
                summary="Works through exchanges, clauses, and controlled concessions.",
                trait_pool=["diplomatic", "measured", "cold"],
                role_biases=["negotiator", "facilitator"],
                stat_biases={"morality": 1, "power": 3},
                modifier_overrides={"relationship_bias": 1.0},
            ),
            ArchetypeVariantDefinition(
                variant_id="tactician",
                name="Tactician",
                summary="Reads the room as a board and adjusts before others notice the pivot.",
                trait_pool=["disciplined", "fast-reading", "focused"],
                role_biases=["planner", "commander"],
                stat_biases={"stability": 6, "power": 2},
                modifier_overrides={"scene_intensity": 1.1},
            ),
            ArchetypeVariantDefinition(
                variant_id="architect",
                name="Architect",
                summary="Prefers durable systems and careful scaffolds over dramatic gestures.",
                trait_pool=["systemic", "patient", "exacting"],
                role_biases=["designer", "coordinator"],
                stat_biases={"stability": 5, "morality": 2},
                modifier_overrides={"observation_bias": 1.08},
            ),
        ],
    ),
    "witness": ArchetypeDefinition(
        base_id="witness",
        display_name="Witness",
        summary="Attentive, relational, and oriented toward memory, testimony, and meaning.",
        core_drive="See clearly, remember accurately, and hold truth where it would otherwise vanish.",
        intent_keywords={
            "watch": 3.5,
            "observe": 4.5,
            "listen": 4.0,
            "remember": 4.0,
            "record": 3.5,
            "witness": 4.5,
            "testify": 4.0,
            "note": 2.5,
            "study": 2.5,
            "understand": 2.0,
        },
        memory_weights={
            "confession": 2.1,
            "memory": 2.3,
            "confession_residue": 2.0,
            "record": 1.8,
        },
        default_traits=["attentive", "empathetic", "careful"],
        role_biases=["scribe", "listener", "confidant"],
        default_modifiers={
            "scene_intensity": 0.94,
            "relationship_bias": 1.08,
            "observation_bias": 1.18,
        },
        variants=[
            ArchetypeVariantDefinition(
                variant_id="chronicler",
                name="Chronicler",
                summary="Turns unstable experience into record before it can be revised away.",
                trait_pool=["exact", "patient", "devoted"],
                role_biases=["scribe", "archivist"],
                stat_biases={"stability": 4, "morality": 2},
                modifier_overrides={"observation_bias": 1.22},
            ),
            ArchetypeVariantDefinition(
                variant_id="listener",
                name="Listener",
                summary="Creates truth by giving another person enough stillness to say it plainly.",
                trait_pool=["gentle", "quiet", "receptive"],
                role_biases=["confidant", "mediator"],
                stat_biases={"morality": 3, "fear": -1},
                modifier_overrides={"relationship_bias": 1.12},
            ),
            ArchetypeVariantDefinition(
                variant_id="sentinel",
                name="Sentinel Witness",
                summary="Notices danger early and treats testimony as a form of defense.",
                trait_pool=["watchful", "steady", "guarded"],
                role_biases=["sentinel", "lookout"],
                stat_biases={"health": 4, "stability": 3},
                modifier_overrides={"scene_intensity": 0.98},
            ),
        ],
    ),
    "mystic": ArchetypeDefinition(
        base_id="mystic",
        display_name="Mystic",
        summary="Threshold-tuned, symbolic, and responsive to the hidden logics of a place.",
        core_drive="Touch the unseen pattern without letting it claim the whole self.",
        intent_keywords={
            "ritual": 4.0,
            "omen": 4.5,
            "ghost": 3.5,
            "magic": 3.5,
            "prophecy": 4.0,
            "whisper": 2.5,
            "dream": 3.0,
            "threshold": 3.5,
            "symbol": 3.0,
            "occult": 4.0,
        },
        memory_weights={
            "ritual_memory": 2.4,
            "living_script": 2.0,
            "overlap": 2.1,
            "loop_truth": 1.8,
            "uncanny_manifestation": 1.8,
        },
        default_traits=["intuitive", "sensitive", "symbol-minded"],
        role_biases=["seer", "ritualist", "threshold-walker"],
        default_modifiers={
            "scene_intensity": 1.05,
            "relationship_bias": 0.94,
            "observation_bias": 1.12,
        },
        variants=[
            ArchetypeVariantDefinition(
                variant_id="omen_reader",
                name="Omen Reader",
                summary="Finds the pattern first in signs, smells, and wrong repetitions.",
                trait_pool=["intuitive", "haunted", "perceptive"],
                role_biases=["seer", "interpreter"],
                stat_biases={"power": 2, "stability": -1},
                modifier_overrides={"observation_bias": 1.18},
            ),
            ArchetypeVariantDefinition(
                variant_id="veilwalker",
                name="Veilwalker",
                summary="Can cross the threshold, but never without bringing something back.",
                trait_pool=["brave", "porous", "adaptable"],
                role_biases=["ritualist", "threshold-walker"],
                stat_biases={"power": 3, "fear": -2},
                modifier_overrides={"scene_intensity": 1.08},
            ),
            ArchetypeVariantDefinition(
                variant_id="dreambound",
                name="Dreambound",
                summary="Treats symbol and memory as equally real terrain.",
                trait_pool=["reflective", "uncanny", "gentle"],
                role_biases=["visionary", "medium"],
                stat_biases={"morality": 2, "stability": -2},
                modifier_overrides={"relationship_bias": 0.98},
            ),
        ],
    ),
}

BASE_ARCHETYPE_IDS = tuple(ARCHETYPE_DEFINITIONS.keys())
_TOKEN_RE = re.compile(r"[^a-z0-9]+")


def available_variant_ids(base_archetype: str) -> tuple[str, ...]:
    definition = ARCHETYPE_DEFINITIONS[base_archetype]
    return tuple(variant.variant_id for variant in definition.variants)


def resolve_base_archetype(
    intent_text: str,
    memory_board: list[MemoryEntry] | None = None,
) -> str:
    normalized = _normalize_intent(intent_text)
    intent_scores = _intent_scores(normalized)
    if max(intent_scores.values(), default=0.0) > 0:
        scores = intent_scores
        seed_text = normalized or "default"
    else:
        scores = _memory_scores(memory_board or [])
        seed_text = normalized or _memory_signature(memory_board or []) or "default"
    best_score = max(scores.values(), default=0.0)
    if best_score <= 0:
        return BASE_ARCHETYPE_IDS[_stable_index(seed_text, len(BASE_ARCHETYPE_IDS))]
    tied = [base_id for base_id in BASE_ARCHETYPE_IDS if scores.get(base_id, 0.0) == best_score]
    if len(tied) == 1:
        return tied[0]
    return tied[_stable_index(seed_text, len(tied))]


def select_archetype_variant(
    base_archetype: str,
    intent_text: str,
    world_pack_id: str | None = None,
) -> ArchetypeVariantDefinition:
    definition = ARCHETYPE_DEFINITIONS[base_archetype]
    variants = definition.variants or [
        ArchetypeVariantDefinition(
            variant_id=f"{base_archetype}_default",
            name=definition.display_name,
            summary=definition.summary,
        )
    ]
    seed_text = f"{_normalize_intent(intent_text) or 'steady-center'}|{world_pack_id or 'default'}"
    return variants[_stable_index(seed_text, len(variants))]


def build_character_generation_contract(
    base_archetype: str,
    variant: ArchetypeVariantDefinition,
    world_pack_id: str | None = None,
) -> CharacterGenerationContract:
    definition = ARCHETYPE_DEFINITIONS[base_archetype]
    return CharacterGenerationContract(
        base_archetype=base_archetype,
        variant_id=variant.variant_id,
        variant_name=variant.name,
        world_pack_id=world_pack_id,
        summary=f"{definition.display_name}: {variant.summary}",
        core_drive=definition.core_drive,
        trait_pool=sorted(set(definition.default_traits + variant.trait_pool)),
        role_biases=sorted(set(definition.role_biases + variant.role_biases)),
        stat_biases={
            key: int(value)
            for key, value in variant.stat_biases.items()
        },
    )


def resolve_active_archetype(
    memory_board: list[MemoryEntry],
    player_intent: str = "",
    world_pack_id: str | None = None,
    decision_trace: list[str] | None = None,
) -> Archetype:
    source_intent = _select_source_intent(player_intent, decision_trace or [], memory_board)
    base_archetype = resolve_base_archetype(source_intent, memory_board)
    definition = ARCHETYPE_DEFINITIONS[base_archetype]
    variant = select_archetype_variant(base_archetype, source_intent, world_pack_id)
    modifiers = dict(definition.default_modifiers)
    modifiers.update(variant.modifier_overrides)
    contract = build_character_generation_contract(base_archetype, variant, world_pack_id)
    signature_seed = f"{base_archetype}|{variant.variant_id}|{_normalize_intent(source_intent)}|{world_pack_id or 'default'}"
    return Archetype(
        archetype_type=base_archetype,
        variant_id=variant.variant_id,
        variant_name=variant.name,
        source_intent=source_intent,
        intent_signature=hashlib.sha256(signature_seed.encode("utf-8")).hexdigest()[:12],
        modifiers=modifiers,
        character_contract=contract,
    )


def _normalize_intent(intent_text: str) -> str:
    normalized = _TOKEN_RE.sub(" ", str(intent_text or "").lower()).strip()
    return re.sub(r"\s+", " ", normalized)


def _intent_scores(normalized_intent: str) -> dict[str, float]:
    scores = {base_id: 0.0 for base_id in BASE_ARCHETYPE_IDS}
    if not normalized_intent:
        return scores
    for base_id, definition in ARCHETYPE_DEFINITIONS.items():
        for keyword, weight in definition.intent_keywords.items():
            if keyword in normalized_intent:
                scores[base_id] += weight
    return scores


def _memory_scores(memory_board: list[MemoryEntry]) -> dict[str, float]:
    scores = {base_id: 0.0 for base_id in BASE_ARCHETYPE_IDS}
    for entry in memory_board:
        for base_id, definition in ARCHETYPE_DEFINITIONS.items():
            weight = definition.memory_weights.get(entry.memory_type)
            if weight is not None:
                scores[base_id] += entry.weight * weight
    return scores


def _memory_signature(memory_board: list[MemoryEntry]) -> str:
    memory_types = [entry.memory_type for entry in sorted(memory_board, key=lambda item: item.weight, reverse=True)[:4]]
    return "|".join(memory_types)


def _select_source_intent(
    player_intent: str,
    decision_trace: list[str],
    memory_board: list[MemoryEntry],
) -> str:
    if str(player_intent or "").strip():
        return str(player_intent).strip()
    for decision in reversed(decision_trace):
        if str(decision or "").strip():
            return str(decision).strip()
    if memory_board:
        memory_types = [entry.memory_type for entry in sorted(memory_board, key=lambda item: item.weight, reverse=True)[:3]]
        return " ".join(memory_types)
    return "steady center"


def _stable_index(seed_text: str, count: int) -> int:
    if count <= 0:
        return 0
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % count
