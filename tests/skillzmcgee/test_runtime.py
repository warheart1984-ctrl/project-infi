from __future__ import annotations

import json
import subprocess
import sys

import pytest

from skillzmcgee.core.workflow import Workflow
from skillzmcgee.core.adapters.llm_adapter import LawfulLLMAdapter, NovaAAISClient
from skillzmcgee.governance.continuity_ledger import (
    FileContinuityLedger,
    SQLiteContinuityLedger,
    ValidatedLedger,
)
from skillzmcgee.governance.state_accumulator import StateAccumulator
from skillzmcgee.governance.validator import MinimalValidator
from skillzmcgee.main import boot


def valid_entry(**overrides):
    entry = {
        "id": "run-1",
        "timestamp": "2026-06-26T00:00:00Z",
        "actor": "skillz",
        "slice": "slice_math",
        "input": {"value": 41},
        "output": {"value": 42},
        "status": "ok",
    }
    entry.update(overrides)
    return entry


def test_validated_ledger_accepts_valid_receipts_and_rejects_invalid_status():
    ledger = ValidatedLedger(MinimalValidator())

    receipt_id = ledger.append(valid_entry())

    assert receipt_id == "run-1"
    assert ledger.all() == [valid_entry()]

    with pytest.raises(ValueError, match="status"):
        ledger.append(valid_entry(id="run-2", status="pending"))


def test_ledger_readback_is_append_only_copy():
    ledger = ValidatedLedger(MinimalValidator())
    ledger.append(valid_entry())

    readback = ledger.all()
    readback.append(valid_entry(id="run-2"))

    assert ledger.all() == [valid_entry()]


def test_state_accumulator_rebuilds_state_from_ledger():
    ledger = ValidatedLedger(MinimalValidator())
    ledger.append(valid_entry(id="run-1", output={"value": 1}))
    ledger.append(valid_entry(id="run-2", output={"value": 2}))
    accumulator = StateAccumulator()

    accumulator.rebuild_from_ledger(ledger)

    assert accumulator.get_slice_state("slice_math") == {
        "last_status": "ok",
        "last_output": {"value": 2},
        "last_run_id": "run-2",
    }


def test_workflow_runs_slice_and_records_receipt_and_state():
    ledger = ValidatedLedger(MinimalValidator())
    accumulator = StateAccumulator()
    workflow = Workflow(ledger=ledger, accumulator=accumulator, actor="skillz")

    receipt = workflow.run_slice(
        "slice_math",
        {"value": 41},
        lambda payload: {"value": payload["value"] + 1},
    )

    assert receipt["actor"] == "skillz"
    assert receipt["slice"] == "slice_math"
    assert receipt["status"] == "ok"
    assert receipt["output"] == {"value": 42}
    assert ledger.all() == [receipt]
    assert accumulator.get_slice_state("slice_math")["last_run_id"] == receipt["id"]


def test_llm_adapter_adds_state_context_and_logs_the_call():
    captured_prompts = []
    ledger = ValidatedLedger(MinimalValidator())
    accumulator = StateAccumulator()
    accumulator.apply_entry(valid_entry(output={"value": 42}))

    def llm(prompt: str) -> str:
        captured_prompts.append(prompt)
        return "state says 42"

    adapter = LawfulLLMAdapter(llm, ledger, accumulator, actor="skillz")

    output = adapter.ask("Summarize the slice.", context_slice="slice_math")

    assert output == "state says 42"
    assert "slice_math" in captured_prompts[0]
    assert "42" in captured_prompts[0]
    assert ledger.all()[0]["slice"] == "llm:slice_math"
    assert ledger.all()[0]["status"] == "ok"


def test_nova_aais_client_posts_prompt_and_extracts_text(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"text":"adapter ready"}'

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    client = NovaAAISClient(base_url="http://127.0.0.1:8000", timeout=3)

    assert client("ping") == "adapter ready"
    assert captured["url"] == "http://127.0.0.1:8000/legacy_api/api/text/generate"
    assert captured["payload"]["prompt"] == "ping"
    assert captured["timeout"] == 3


def test_boot_wires_env_llm_adapter(monkeypatch, tmp_path):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"response":"env adapter ready"}'

    monkeypatch.setenv("AAIS_BASE_URL", "http://127.0.0.1:8000")
    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout: FakeResponse())

    workflow = boot(ledger_path=tmp_path / "receipts.jsonl")

    assert workflow.llm_adapter is not None
    assert workflow.llm_adapter.ask("hello") == "env adapter ready"


def test_file_ledger_persists_jsonl_receipts(tmp_path):
    ledger_path = tmp_path / "receipts.jsonl"
    ledger = FileContinuityLedger(ledger_path, MinimalValidator())

    ledger.append(valid_entry())

    assert ledger_path.exists()
    assert json.loads(ledger_path.read_text(encoding="utf-8").strip()) == valid_entry()
    assert FileContinuityLedger(ledger_path, MinimalValidator()).all() == [valid_entry()]


def test_sqlite_ledger_persists_receipts(tmp_path):
    ledger_path = tmp_path / "receipts.sqlite3"
    ledger = SQLiteContinuityLedger(ledger_path, MinimalValidator())

    ledger.append(valid_entry())

    assert ledger_path.exists()
    assert SQLiteContinuityLedger(ledger_path, MinimalValidator()).all() == [valid_entry()]


def test_boot_rebuilds_state_from_existing_ledger(tmp_path):
    ledger_path = tmp_path / "receipts.jsonl"
    ledger = FileContinuityLedger(ledger_path, MinimalValidator())
    ledger.append(valid_entry())

    workflow = boot(ledger_path=ledger_path)

    assert workflow.accumulator.get_slice_state("slice_math") == {
        "last_status": "ok",
        "last_output": {"value": 42},
        "last_run_id": "run-1",
    }


def test_boot_auto_selects_sqlite_for_sqlite_suffix(tmp_path):
    ledger_path = tmp_path / "receipts.sqlite3"

    workflow = boot(ledger_path=ledger_path)
    workflow.run_slice("slice_custom", {"message": "hello"}, lambda payload: payload)

    reloaded = boot(ledger_path=ledger_path)
    assert reloaded.accumulator.get_slice_state("slice_custom")["last_output"] == {
        "message": "hello"
    }


def test_cli_run_demo_writes_receipt_and_state_reads_it(tmp_path):
    ledger_path = tmp_path / "receipts.jsonl"

    run_result = subprocess.run(
        [sys.executable, "-m", "skillzmcgee", "run-demo", "--ledger", str(ledger_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    state_result = subprocess.run(
        [sys.executable, "-m", "skillzmcgee", "state", "--ledger", str(ledger_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "SkillzMcGee ready" in run_result.stdout
    state = json.loads(state_result.stdout)
    assert state["slice_custom"]["last_output"] == {"message": "SkillzMcGee ready"}


def test_cli_run_demo_supports_sqlite_ledger(tmp_path):
    ledger_path = tmp_path / "receipts.sqlite3"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "skillzmcgee",
            "run-demo",
            "--ledger",
            str(ledger_path),
            "--ledger-backend",
            "sqlite",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    state_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "skillzmcgee",
            "state",
            "--ledger",
            str(ledger_path),
            "--ledger-backend",
            "sqlite",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    state = json.loads(state_result.stdout)
    assert state["slice_custom"]["last_output"] == {"message": "SkillzMcGee ready"}
