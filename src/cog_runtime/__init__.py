"""Nova Cortex — governed modular cognitive runtimes for Nova."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from src.cog_runtime.attention import attention_runtime_spec
from src.cog_runtime.base import CogRuntimeSession
from src.cog_runtime.deliberation import deliberation_runtime_spec
from src.cog_runtime.execution import execution_runtime_spec
from src.cog_runtime.memory import memory_runtime_spec
from src.cog_runtime.planning import planning_runtime_spec
from src.cog_runtime.reflection import reflection_runtime_spec
from src.cog_runtime.nova import (
    NOVA_CORTEX_ID,
    NOVA_COGNITIVE_FAMILY_ID,
    configure_nova_cognitive_turn,
    nova_cognitive_router,
    nova_cognitive_session,
    nova_speaking_adapter,
    run_nova_cognitive_turn,
    summarize_cognitive_runtime_state,
)
from src.cog_runtime.capability_governance import validate_nova_cortex_capability_governance
from src.jarvis_reasoning_protocol import reasoning_protocol_spec
from src.speaking_runtime import speaking_runtime_spec

NOVA_CORTEX_VERSION = "3.0"
NOVA_CORTEX_MILESTONE = "Persistent Narrative Continuity"
NOVA_CORTEX_DOC = "docs/runtime/NOVA_CORTEX.md"
COGNITIVE_RUNTIME_FAMILY_DOC = NOVA_CORTEX_DOC
COGNITIVE_RUNTIME_FAMILY_VERSION = NOVA_CORTEX_VERSION
DEFAULT_FAMILY_JSON = Path("docs/runtime/cognitive_runtime_family.v1.json")
DEFAULT_NOVA_CORTEX_JSON = DEFAULT_FAMILY_JSON

COMPOSITION_RULES: tuple[dict[str, str], ...] = (
    {
        "id": "single_authority",
        "rule": "Jarvis Core routes; cognitive runtimes do not compete for control.",
    },
    {
        "id": "speaking_required_for_user_output",
        "rule": "No user-visible output without Speaking Runtime when cognitive mode is active.",
    },
    {
        "id": "reasoning_required_for_actions",
        "rule": "No high-impact action without Reasoning Runtime.",
    },
    {
        "id": "deliberation_on_decision_only",
        "rule": "Deliberation Runtime activates only for decision frames.",
    },
    {
        "id": "reflection_planning_loop",
        "rule": "Reflection hands off to Planning when alignment gaps or companion turns require sequenced next actions.",
    },
    {
        "id": "planning_execution_loop",
        "rule": "Planning hands off to Execution to bind, verify, and report the planned next action.",
    },
    {
        "id": "multi_turn_arcs",
        "rule": "Goal-typed cortex arcs persist bounded turn history and open threads across companion turns.",
    },
    {
        "id": "self_tuning_invariants",
        "rule": "Cortex adjusts bounded verification thresholds from execution and reflection evidence each turn.",
    },
    {
        "id": "drift_guarded_tuning",
        "rule": "Self-tuning keeps bounded invariant history and clamps cumulative drift.",
    },
    {
        "id": "goal_closure",
        "rule": "Arc subgoals close on successful execution; parent goals close when children complete.",
    },
    {
        "id": "lobe_capability_justification",
        "rule": "Every lobe declares capability_metric, baseline_substitute, and evidence_status; unproven lobes are sunset candidates.",
    },
    {
        "id": "narrative_observe_only",
        "rule": "Nova Narrative observes, synthesizes, and records continuity; it is not a second authority.",
    },
    {
        "id": "intent_consult_only",
        "rule": "Nova Intent Core maintains commitments and tensions for lobes to consult; Jarvis remains executive.",
    },
    {
        "id": "shared_ledger",
        "rule": "All runtimes append to the shared cognitive ledger for the turn.",
    },
)

FAMILY_INVARIANTS: tuple[dict[str, str], ...] = (
    {"id": "clarity", "rule": "Every output understandable on first read."},
    {"id": "traceability", "rule": "Any reply segment maps to a named ledger stage."},
    {"id": "intent_alignment", "rule": "Every response serves the user's stated or inferred goal."},
    {"id": "no_raw_cot", "rule": "No hidden chain-of-thought; only inspectable stage records."},
    {
        "id": "identity_consistency",
        "rule": "Narrative may describe becoming but may not redefine Nova's core identity.",
    },
)

_RUNTIME_SPEC_FNS: dict[str, Callable[[], dict[str, Any]]] = {}


def register_runtime_spec(runtime_id: str, spec_fn: Callable[[], dict[str, Any]]) -> None:
    _RUNTIME_SPEC_FNS[runtime_id] = spec_fn


def _bootstrap_registry() -> None:
    if _RUNTIME_SPEC_FNS:
        return
    register_runtime_spec("speaking.runtime", speaking_runtime_spec)
    register_runtime_spec("jarvis.reasoning", reasoning_protocol_spec)
    register_runtime_spec("cognitive.deliberation", deliberation_runtime_spec)
    register_runtime_spec("cognitive.attention", attention_runtime_spec)
    register_runtime_spec("cognitive.memory", memory_runtime_spec)
    register_runtime_spec("cognitive.reflection", reflection_runtime_spec)
    register_runtime_spec("cognitive.planning", planning_runtime_spec)
    register_runtime_spec("cognitive.execution", execution_runtime_spec)


def nova_cortex_spec(*, edition: str = "wolf-cog-os-full") -> dict[str, Any]:
    _bootstrap_registry()
    runtimes = [_RUNTIME_SPEC_FNS[runtime_id]() for runtime_id in sorted(_RUNTIME_SPEC_FNS)]
    spec = {
        "name": "Nova Cortex",
        "family_id": NOVA_CORTEX_ID,
        "version": NOVA_CORTEX_VERSION,
        "edition": edition,
        "summary": (
            "Nova Cortex v3.0 — Persistent Narrative Continuity: cognition lobes plus "
            "observe-only narrative that maintains a journey across sessions."
        ),
        "milestone": NOVA_CORTEX_MILESTONE,
        "doc": NOVA_CORTEX_DOC,
        "anatomy": {
            "jarvis_core": "thalamus / router",
            "wolf_cog_os": "constitutional brainstem",
            "nova.intent": "agency layer (commitments · tensions · consult only)",
            "nova.narrative": "continuity layer (observe · synthesize · record)",
            "speaking.runtime": "prefrontal speech loop",
            "cognitive.deliberation": "decision lobe",
            "cognitive.attention": "focus lobe",
            "cognitive.memory": "hippocampus runtime",
            "cognitive.reflection": "cross-lobe reflection loop",
            "cognitive.planning": "sequencing lobe",
            "cognitive.execution": "action verification lobe",
            "jarvis.reasoning": "OODA routing plane",
        },
        "composition_rules": [dict(item) for item in COMPOSITION_RULES],
        "invariants": [dict(item) for item in FAMILY_INVARIANTS],
        "runtimes": runtimes,
        "turn_pipeline": [
            "jarvis.reasoning",
            "cognitive.attention",
            "cognitive.memory",
            "cognitive.deliberation",
            "cognitive.reflection",
            "cognitive.planning",
            "cognitive.execution",
            "speaking.runtime",
        ],
    }
    capability = validate_nova_cortex_capability_governance(spec)
    if not capability["valid"]:
        raise ValueError(f"nova cortex capability governance invalid: {capability['issues']}")
    spec["capability_governance"] = {
        "matrix_source": "src/cog_runtime/capability_governance.py",
        "runtime_count": capability["runtime_count"],
        "cortex_module_count": capability["cortex_module_count"],
    }
    return spec


def cognitive_runtime_family_spec(*, edition: str = "wolf-cog-os-full") -> dict[str, Any]:
    """Back-compat alias for nova_cortex_spec()."""
    return nova_cortex_spec(edition=edition)


def export_family_json(path: str | Path | None = None) -> Path:
    target = Path(path) if path is not None else DEFAULT_FAMILY_JSON
    target.parent.mkdir(parents=True, exist_ok=True)
    import json

    target.write_text(
        json.dumps(nova_cortex_spec(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


_bootstrap_registry()

__all__ = [
    "CogRuntimeSession",
    "COGNITIVE_RUNTIME_FAMILY_DOC",
    "COGNITIVE_RUNTIME_FAMILY_VERSION",
    "NOVA_CORTEX_DOC",
    "NOVA_CORTEX_ID",
    "NOVA_CORTEX_VERSION",
    "cognitive_runtime_family_spec",
    "configure_nova_cognitive_turn",
    "export_family_json",
    "nova_cognitive_router",
    "nova_cognitive_session",
    "nova_cortex_spec",
    "nova_speaking_adapter",
    "register_runtime_spec",
    "run_nova_cognitive_turn",
    "summarize_cognitive_runtime_state",
    "validate_nova_cortex_capability_governance",
]
