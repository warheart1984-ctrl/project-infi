"""Tests for exporting lawful Nova turns into Jarvis LoRA training data."""

from __future__ import annotations

import json

from nova.governance import seams
from nova.lawful_llm import LawfulLLM
from training.nova_training_export import (
    append_lawful_turn_example,
    build_lawful_turn_training_example,
)
from training.prepare_messages_dataset import build_dataset


def test_lawful_turn_exports_to_messages_jsonl_shape(tmp_path, monkeypatch):
    seams.reset_seams_for_tests()
    monkeypatch.setenv("NOVA_GOVERNANCE_LEDGER_PATH", str(tmp_path / "events.jsonl"))
    llm = LawfulLLM(operator_session_id="session-train-1", signing_secret="test-secret")
    turn = llm.ask(
        "explain gravity",
        tenant_id="tenant-alpha",
        capability="reason",
        memory_facts=[("gravity", "is", "an attractive interaction between masses")],
    )

    example = build_lawful_turn_training_example(prompt="explain gravity", turn=turn)

    assert [message["role"] for message in example["messages"]] == [
        "system",
        "user",
        "assistant",
    ]
    assert "Nova Cortex" in example["messages"][0]["content"]
    assert example["messages"][1]["content"] == "explain gravity"
    assert example["messages"][2]["content"] == turn.text
    assert example["metadata"]["source"] == "nova_lawful_turn"
    assert example["metadata"]["receipt"]["signature"] == turn.receipt["signature"]
    assert example["metadata"]["rsl"]["status"] == "SATISFIED"
    assert example["metadata"]["ul"]["intent"] == "explain"
    assert example["metadata"]["lsg"]["facts_used"] == [
        "gravity is an attractive interaction between masses"
    ]


def test_lawful_turn_export_can_feed_prepare_messages_dataset(tmp_path, monkeypatch):
    seams.reset_seams_for_tests()
    monkeypatch.setenv("NOVA_GOVERNANCE_LEDGER_PATH", str(tmp_path / "events.jsonl"))
    llm = LawfulLLM(operator_session_id="session-train-2", signing_secret="test-secret")
    turn = llm.ask("summarize invariants", tenant_id="tenant-alpha", capability="summarize")
    private_path = tmp_path / "nova_lawful_turns.jsonl"

    append_lawful_turn_example(private_path, prompt="summarize invariants", turn=turn)
    records = [json.loads(line) for line in private_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1

    seed_path = tmp_path / "seed.jsonl"
    seed_path.write_text(
        json.dumps(
            {
                "messages": [
                    {"role": "user", "content": "seed question"},
                    {"role": "assistant", "content": "seed answer"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    examples, source_files = build_dataset(seed_path, [private_path])

    assert len(examples) == 2
    assert examples[-1]["messages"][-1]["content"] == turn.text
    assert source_files[-1]["source_kind"] == "private"
