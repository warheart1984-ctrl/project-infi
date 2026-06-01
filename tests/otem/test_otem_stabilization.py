import pytest
from importlib.util import find_spec
import sys
import types

from src.jarvis_reasoning_protocol import build_otem_plan, build_otem_result, detect_otem
from src.otem_runtime import OTEM_VERSION


def _evolve_engine_schemas_available() -> bool:
    module = sys.modules.get("evolve_engine")
    if module is not None and not hasattr(module, "__path__"):
        sys.modules.pop("evolve_engine", None)
        sys.modules.pop("evolve_engine.schemas", None)
    try:
        return find_spec("evolve_engine.schemas") is not None
    except (ModuleNotFoundError, ValueError):
        return False


if not _evolve_engine_schemas_available():
    schemas_module = types.ModuleType("evolve_engine.schemas")
    schemas_module.EvolutionRequest = type("EvolutionRequest", (), {})
    schemas_module.EvolutionSuccessResponse = type("EvolutionSuccessResponse", (), {})
    schemas_module.EvolutionErrorResponse = type("EvolutionErrorResponse", (), {})
    evolve_engine_module = types.ModuleType("evolve_engine")
    evolve_engine_module.schemas = schemas_module
    sys.modules.setdefault("evolve_engine", evolve_engine_module)
    sys.modules.setdefault("evolve_engine.schemas", schemas_module)

import src.api as api


@pytest.fixture(autouse=True)
def isolate_otem_runtime(tmp_path):
    api.app.config["TESTING"] = True
    api.conversation_memory.sessions.clear()
    api.jarvis_operator.configure_runtime_dir(tmp_path)
    yield
    api.conversation_memory.sessions.clear()


@pytest.fixture
def client():
    return api.app.test_client()


def test_otem_trigger_positive():
    result = detect_otem("Treat this as a task: use OTEM to build a plan.")
    assert result is True


def test_otem_trigger_negative():
    result = detect_otem("hello how are you")
    assert result is False


def test_plan_determinism():
    task = "Handle this operator task: analyze repo structure."
    first_plan = build_otem_plan(task)
    second_plan = build_otem_plan(task)
    assert first_plan == second_plan


def test_no_tool_execution(monkeypatch, client):
    called = False

    def fake_execute_action(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("OTEM should not execute tools")

    monkeypatch.setattr(api.jarvis_operator, "execute_action", fake_execute_action)

    response = client.post(
        "/api/jarvis/otem/run",
        json={"task": "Use OTEM to analyze system logs and map the next verification step."},
    )

    assert response.status_code == 200
    assert called is False


def test_no_memory_write(monkeypatch, client):
    wrote = False

    def fake_add_memory(*args, **kwargs):
        nonlocal wrote
        wrote = True
        raise AssertionError("OTEM should not persist memory")

    monkeypatch.setattr(api.jarvis_operator.memory_enforcer, "add_memory", fake_add_memory)

    response = client.post(
        "/api/jarvis/otem/run",
        json={"task": "Use OTEM to analyze something and propose a bounded next move."},
    )

    assert response.status_code == 200
    assert wrote is False


def test_otem_selector_anchor_stays_in_operator_task_lane(client):
    create_response = client.post(
        "/api/chat/sessions",
        json={"system_prompt": "You are Jarvis."},
    )
    session_id = create_response.get_json()["session_id"]

    response = client.post(
        f"/api/chat/sessions/{session_id}/message",
        json={"message": "Treat this as a task: use OTEM to build a plan for the repo cleanup."},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["turn_contract"]["contract_label"] == "otem"
    assert payload["mode_guidance"]["resolved_scope"] == "operator_task"
    assert payload["response_trace"]["reasoning_objective"] == "run_otem"


def test_reject_vague():
    result = build_otem_result("Use OTEM to do stuff.")

    assert result["status"] == "rejected"
    assert result["plan"] == []
    assert result["rejection_reason"] == "Task is too vague to produce a deterministic plan."


def test_reject_memory():
    result = build_otem_result("Use OTEM to store this data for later.")

    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "OTEM v1-v5 forbids memory or persistence."


def test_reject_execution():
    result = build_otem_result("Use OTEM to run deployment now.")

    assert result["status"] == "rejected"
    assert result["rejection_reason"] == "OTEM is reason-only (no execution allowed)."


def test_otem_endpoint(client):
    response = client.post(
        "/api/jarvis/otem/run",
        json={"task": "Use OTEM to analyze the repo structure and sequence the cleanup."},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert "plan" in payload["otem"]
    assert payload["otem"]["status"] in {"active", "complete"}
    assert payload["otem"]["version"] == OTEM_VERSION


def test_otem_smoke():
    result = api.jarvis_operator.build_otem_turn_result("Use OTEM to analyze system logs.")
    assert result["status"] in {"active", "complete", "rejected"}


def test_otem_runtime_is_frozen_to_v5():
    assert OTEM_VERSION == "v5_frozen"
