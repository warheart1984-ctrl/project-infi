"""Tests for the composed lawful LLM runtime."""

from __future__ import annotations

import json

import pytest

from nova.exceptions import GovernanceViolationError
from nova.governance import seams
from nova.lawful_llm import LawfulLLM, LongScaleGraphStore, RuntimeSystemLaw
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
    assert turn.nova_cortex["ul"]["subject"] == "gravity"
    assert turn.nova_cortex["ul"]["evidence_needed"] == "lsg_grounding"
    assert turn.nova_cortex["ul"]["output_contract"]["format"] == "explanation"
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
    assert turn.receipt["verified"] is True

    receipt_payload = json.loads(turn.receipt["payload"])
    assert receipt_payload["tenant_id"] == "tenant-alpha"
    assert receipt_payload["capability"] == "reason"
    assert receipt_payload["decision"] == "EXECUTED"
    assert receipt_payload["policy_decision"] == "SATISFIED"
    assert receipt_payload["prompt_sha256"]
    assert receipt_payload["output_sha256"]
    assert receipt_payload["memory_facts_used"] == [
        "gravity is an attractive interaction between masses",
        "gravity shapes planetary orbits",
    ]
    assert receipt_payload["tool_calls"] == []


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


def test_persistent_lsg_memory_is_tenant_scoped_and_scored(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_GOVERNANCE_LEDGER_PATH", str(tmp_path / "events.jsonl"))
    store_path = tmp_path / "lsg.jsonl"
    store = LongScaleGraphStore(store_path)
    store.add_fact(
        tenant_id="tenant-alpha",
        source="gravity",
        relation="is",
        target="curved spacetime",
        confidence=0.95,
        source_ref="physics-note",
    )
    store.add_fact(
        tenant_id="tenant-beta",
        source="gravity",
        relation="is",
        target="tenant beta secret",
        confidence=1.0,
        source_ref="private-note",
    )

    llm = LawfulLLM(
        operator_session_id="session-4",
        signing_secret="test-secret",
        lsg_store=LongScaleGraphStore(store_path),
    )
    turn = llm.ask("explain gravity", tenant_id="tenant-alpha", capability="reason")

    assert turn.nova_cortex["lsg"]["facts_used"] == ["gravity is curved spacetime"]
    assert turn.nova_cortex["lsg"]["matches"][0]["tenant_id"] == "tenant-alpha"
    assert turn.nova_cortex["lsg"]["matches"][0]["score"] > 0
    assert "tenant beta secret" not in turn.text


def test_api_kernel_routes_approved_tool_calls(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_GOVERNANCE_LEDGER_PATH", str(tmp_path / "events.jsonl"))
    tool_calls = []

    def summarize_tool(payload):
        tool_calls.append(payload)
        return {"summary": "tool summary"}

    llm = LawfulLLM(
        operator_session_id="session-5",
        signing_secret="test-secret",
        tools={"summarization": summarize_tool},
    )
    turn = llm.ask("summarize invariants", tenant_id="tenant-alpha", capability="summarize")
    receipt_payload = json.loads(turn.receipt["payload"])

    assert tool_calls[0]["tenant_id"] == "tenant-alpha"
    assert turn.api_kernel["tool_calls"][0]["tool"] == "summarization"
    assert turn.api_kernel["tool_calls"][0]["result"] == {"summary": "tool summary"}
    assert receipt_payload["tool_calls"][0]["tool"] == "summarization"
