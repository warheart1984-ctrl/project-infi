"""Tests for the composed lawful LLM runtime."""

from __future__ import annotations

import json

import pytest

from nova.exceptions import GovernanceViolationError
from nova.governance import seams
from nova.lawful_llm import LawfulLLM, RuntimeSystemLaw
from src.jarvis_protocol import ProviderResponse


@pytest.fixture(autouse=True)
def _reset_seams():
    seams.reset_seams_for_tests()
    yield
    seams.reset_seams_for_tests()


def test_lawful_llm_executes_prompt_through_all_declared_parts(tmp_path, monkeypatch):
    ledger_path = tmp_path / "nova_governance_events.jsonl"
    monkeypatch.setenv("NOVA_GOVERNANCE_LEDGER_PATH", str(ledger_path))

    llm = LawfulLLM(operator_session_id="session-1", signing_secret="test-secret")
    turn = llm.ask(
        "explain gravity",
        tenant_id="tenant-alpha",
        capability="reason",
        memory_facts=[
            ("gravity", "is", "an attractive interaction between masses"),
            ("gravity", "shapes", "planetary orbits"),
        ],
    )

    assert turn.gates_of_wonder["presentation"] == "human_readable_insight"
    assert turn.nova_cortex["ul"]["intent"] == "explain"
    assert turn.nova_cortex["lsg"]["facts_used"] == [
        "gravity is an attractive interaction between masses",
        "gravity shapes planetary orbits",
    ]
    assert turn.api_kernel["tenant_id"] == "tenant-alpha"
    assert turn.api_kernel["capability"] == "reason"
    assert turn.voss_runtime["decision"] == "EXECUTED"
    assert turn.rsl["status"] == "SATISFIED"
    assert turn.text.startswith("Under RSL, Nova Cortex reads")
    assert llm.verify_receipt(turn.receipt) is True

    receipt_payload = json.loads(turn.receipt["payload"])
    assert receipt_payload["tenant_id"] == "tenant-alpha"
    assert receipt_payload["capability"] == "reason"
    assert receipt_payload["decision"] == "EXECUTED"


def test_lawful_llm_rejects_disallowed_capability_before_cognition(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_GOVERNANCE_LEDGER_PATH", str(tmp_path / "events.jsonl"))
    law = RuntimeSystemLaw(allowed_capabilities=frozenset({"observe"}))
    llm = LawfulLLM(
        operator_session_id="session-2",
        signing_secret="test-secret",
        law=law,
    )

    with pytest.raises(GovernanceViolationError) as exc:
        llm.ask("explain gravity", tenant_id="tenant-alpha", capability="reason")

    assert exc.value.code == "RSL-CAPABILITY-DENIED"
    assert llm.cognition_count == 0


class _FakeProvider:
    provider_id = "nvidia"
    model = "nvidia/nemotron-3-ultra-550b-a55b"

    def __init__(self):
        self.calls = []

    async def invoke(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        return ProviderResponse(
            content="Nemotron answered through the lawful Nova runtime.",
            provider="nvidia",
            model="nvidia/nemotron-3-ultra-550b-a55b",
            input_tokens=7,
            output_tokens=9,
        )


def test_lawful_llm_can_use_nvidia_provider_backend(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_GOVERNANCE_LEDGER_PATH", str(tmp_path / "events.jsonl"))
    provider = _FakeProvider()
    llm = LawfulLLM(
        operator_session_id="session-3",
        signing_secret="test-secret",
        provider=provider,
    )

    turn = llm.ask(
        "explain gravity",
        tenant_id="tenant-alpha",
        capability="reason",
        memory_facts=[("gravity", "is", "curved spacetime in general relativity")],
    )

    assert turn.text == "Nemotron answered through the lawful Nova runtime."
    assert turn.nova_cortex["provider"] == "nvidia"
    assert turn.nova_cortex["model"] == "nvidia/nemotron-3-ultra-550b-a55b"
    assert provider.calls[0][0][0]["role"] == "system"
    assert "gravity is curved spacetime" in provider.calls[0][0][0]["content"]
    assert provider.calls[0][1]["model"] == "nvidia/nemotron-3-ultra-550b-a55b"
