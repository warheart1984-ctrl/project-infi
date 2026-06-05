"""Universal module admission and phase-gate entry wrapper."""

# Engineering: ModuleEntryGateEngine
from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from src.module_governance import module_governance
from src.phase_gate import PhaseViolationError, assert_executable

F = TypeVar("F", bound=Callable[..., Any])

# Components registered for universal coverage reporting.
UNIVERSAL_ENTRY_COMPONENTS: tuple[str, ...] = (
    "jarvis.memory_board_enforcer",
    "jarvis.realtime_event_cause_predictor",
    "jarvis.dreamspace",
    "jarvis.media_processor_family",
    "jarvis.capability_service_bridge",
    "jarvis.forge_contractor",
    "jarvis.evolve_engine",
    "jarvis.otem_execution_substrate",
)


def require_admitted_module(
    component_id: str,
    *,
    runtime_context: str = "operator_runtime",
    admit_if_missing: bool = False,
) -> Callable[[F], F]:
    """Decorator enforcing phase gate + module admission before entry."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _enforce_entry(
                component_id,
                runtime_context=runtime_context,
                admit_if_missing=admit_if_missing,
            )
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def _enforce_entry(
    component_id: str,
    *,
    runtime_context: str,
    admit_if_missing: bool,
) -> None:
    normalized = str(runtime_context or "operator_runtime").strip().lower()
    assert_executable(component_id, normalized)
    try:
        module = module_governance.get_module(component_id)
        if module is None:
            raise LookupError(component_id)
    except LookupError:
        if not admit_if_missing:
            raise
        spec = {
            "module_id": component_id,
            "label": component_id.replace(".", " ").title(),
            "lane": "governed_entry",
            "declared_scope": ["api"],
            "declared_surfaces": ["operator_runtime"],
            "capabilities": ["governed_entry"],
            "cisiv": {
                "concept": {"status": "passed", "summary": "Auto-admitted entry gate."},
                "identity": {"status": "passed", "summary": "Universal entry coverage."},
                "structure": {"status": "passed", "summary": "Phase-gated entry."},
                "implementation": {"status": "implemented", "summary": "Entry gate active."},
                "verification": {"status": "verified", "summary": "Gate enforced."},
            },
            "compliance": {
                "stores_persistent_user_metadata": False,
                "bypasses_jarvis_authority": False,
            },
        }
        module_governance.admit_module(spec, actor_id="module_entry_gate", actor_role="system")


def entry_gate_coverage_ratio(*, registered: int | None = None) -> float:
    total = len(UNIVERSAL_ENTRY_COMPONENTS)
    if total == 0:
        return 1.0
    if registered is None:
        registered = sum(
            1
            for component_id in UNIVERSAL_ENTRY_COMPONENTS
            if _component_registered(component_id)
        )
    return min(1.0, registered / total)


def _component_registered(component_id: str) -> bool:
    try:
        from src.phase_gate import ComponentNotRegisteredError, get_component

        get_component(component_id)
        return True
    except ComponentNotRegisteredError:
        return False
    except Exception:
        return False


def build_module_entry_gate_status() -> dict[str, Any]:
    registered = sum(
        1 for cid in UNIVERSAL_ENTRY_COMPONENTS if _component_registered(cid)
    )
    ratio = entry_gate_coverage_ratio(registered=registered)
    universal = ratio >= 1.0
    return {
        "module_entry_gate_version": "module_entry_gate.v1",
        "universal_entry_coverage": universal,
        "entry_coverage_ratio": ratio,
        "registered_components": registered,
        "total_components": len(UNIVERSAL_ENTRY_COMPONENTS),
        "component_ids": list(UNIVERSAL_ENTRY_COMPONENTS),
    }
