"""Session-scoped governance bootstrap for AAIS pytest harness."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class GovernanceBootstrapState:
    admission_token: str
    runtime_root: str


def _register_core_lanes() -> None:
    from src.phase_gate import (
        ComponentNotRegisteredError,
        GovernedComponent,
        Phase,
        get_component,
        register_component,
    )

    lanes = [
        (
            "jarvis.memory_board_enforcer",
            "Memory Board Enforcer",
            "memory_gateway",
        ),
        (
            "jarvis.otem_execution_substrate",
            "OTEM Execution Substrate",
            "execution_substrate",
        ),
    ]
    for component_id, name, component_type in lanes:
        try:
            get_component(component_id)
        except ComponentNotRegisteredError:
            register_component(
                GovernedComponent(
                    component_id=component_id,
                    name=name,
                    component_type=component_type,
                    phase=Phase.ACTIVE,
                    allowed_contexts=["operator_runtime", "live_runtime", "test_harness"],
                )
            )


def _seed_memory_membrane() -> dict[str, Any] | None:
    try:
        from types import SimpleNamespace

        from src.memory_governance_membrane import seed_session_memory_membrane

        session = SimpleNamespace(metadata={})
        return seed_session_memory_membrane(session, companion_turn=False)
    except Exception:
        return None


def ensure_constitutional_substrate() -> None:
    """Load Meta Architect Lawbook spine; refuse start when constitutionally required."""
    try:
        from src.substrate.meta_law_engine import bootstrap_constitutional_lawbook

        bootstrap_constitutional_lawbook()
    except Exception:
        return


def ensure_collaboration_charter_ready() -> None:
    """Verify Human-AI Co-Collaboration Charter readiness for governed turn ingress."""
    try:
        from src.substrate.ingress.collaboration_membrane import bootstrap_collaboration_charter

        bootstrap_collaboration_charter()
    except Exception:
        return


def ensure_memory_board_gateway_admitted() -> None:
    """Admit the live memory board gateway after module-governance resets in tests."""
    try:
        import src.api as api
        from src.memory_board_enforcer import build_memory_board_enforcer_module_spec
    except Exception:
        return

    enforcer = api.jarvis_operator.memory_enforcer
    controller = enforcer.module_governance_controller
    component_id = enforcer.component_id
    record = controller.get_module(component_id)
    if record is not None and str(record.get("status") or "").strip().lower() == "admitted":
        return

    controller.admit_module(
        build_memory_board_enforcer_module_spec(component_id),
        actor_id="test_harness",
        actor_role="system",
    )


def bootstrap_governance_harness(*, runtime_root: str | None = None) -> GovernanceBootstrapState:
    """Initialize UL substrate hooks, gateway admission, lanes, and test admission token."""
    token = os.environ.get("AAIS_TEST_ADMISSION_TOKEN") or uuid.uuid4().hex
    os.environ["AAIS_TEST_ADMISSION_TOKEN"] = token
    os.environ["AAIS_TEST_COLD_START"] = "1"
    os.environ.setdefault("AAIS_GOVERNED_PIPELINE_CACHE_SEC", "0")
    os.environ.setdefault("AAIS_COHERENCE_FABRIC_CACHE_SEC", "0")
    os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

    if runtime_root:
        os.environ["AAIS_RUNTIME_DIR"] = runtime_root
        os.environ["AAIS_DATA_DIR"] = runtime_root

    _register_core_lanes()
    ensure_constitutional_substrate()
    ensure_collaboration_charter_ready()
    _seed_memory_membrane()

    ensure_memory_board_gateway_admitted()

    try:
        from src.aais_ul_substrate import attach_ul_substrate

        attach_ul_substrate({"governance_bootstrap": "ready", "admission_token_present": bool(token)})
    except Exception:
        pass

    return GovernanceBootstrapState(admission_token=token, runtime_root=runtime_root or "")


def reset_governance_test_group() -> None:
    """Explicit per-group reset for tests that mutate module governance or phase registry."""
    from src.governed_direct_pipeline import clear_governed_pipeline_cache
    from src.otem_execution_substrate import reset_otem_execution_substrate
    from src.phase_gate import reset_registry

    reset_registry()
    clear_governed_pipeline_cache()
    reset_otem_execution_substrate(clear_persisted=True)
    bootstrap_governance_harness()
