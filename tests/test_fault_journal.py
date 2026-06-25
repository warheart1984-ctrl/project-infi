"""Tests for append-only fault journal."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.aais_composed_runtime import run_composed_turn
from src.cog_runtime.formal.spine_pipeline import evaluate_spine_pipeline
from src.fault_journal import (
    FAULT_CODE_AUTHORITY_MISMATCH,
    FAULT_CODE_BRIDGE_BINDING_MISMATCH,
    FAULT_CODE_INVARIANT_BREACH,
    FAULT_CODE_SPAN_ORPHAN,
    FaultJournalStore,
    query_recurrence,
    record_fault,
    record_fault_from_context,
    reset_fault_journal,
    resolve_execution_context,
)


class TestFaultJournalStore(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.store = FaultJournalStore(runtime_root=self.temp_dir)

    def tearDown(self) -> None:
        reset_fault_journal(runtime_root=self.temp_dir)

    def test_append_and_read_record(self) -> None:
        saved = record_fault(
            run_id="run-abc",
            span_id="span-xyz",
            invariant_id="aris_before_cortex",
            fault_code=FAULT_CODE_INVARIANT_BREACH,
            detail={"halt_stage": "aris_admit"},
            store=self.store,
        )
        self.assertEqual(saved["run_id"], "run-abc")
        self.assertEqual(saved["span_id"], "span-xyz")
        self.assertEqual(saved["fault_code"], FAULT_CODE_INVARIANT_BREACH)

        rows = self.store.read_recent()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["invariant_id"], "aris_before_cortex")

    def test_read_is_idempotent(self) -> None:
        record_fault(
            run_id="run-1",
            span_id="span-1",
            invariant_id="jarvis_authority",
            fault_code=FAULT_CODE_AUTHORITY_MISMATCH,
            store=self.store,
        )
        first = self.store.read_recent()
        second = self.store.read_recent()
        self.assertEqual(first, second)

    def test_recurrence_aggregation(self) -> None:
        for _ in range(2):
            record_fault(
                run_id="run-a",
                span_id="span-a",
                invariant_id="aris_before_cortex",
                fault_code=FAULT_CODE_INVARIANT_BREACH,
                store=self.store,
            )
        record_fault(
            run_id="run-b",
            span_id="span-b",
            invariant_id="jarvis_authority",
            fault_code=FAULT_CODE_AUTHORITY_MISMATCH,
            store=self.store,
        )
        metrics = query_recurrence(store=self.store)
        self.assertEqual(metrics["record_count"], 3)
        self.assertEqual(metrics["by_fault_code"][FAULT_CODE_INVARIANT_BREACH], 2)
        self.assertEqual(metrics["by_fault_code"][FAULT_CODE_AUTHORITY_MISMATCH], 1)
        self.assertEqual(
            metrics["by_invariant_fault"]["aris_before_cortex|INVARIANT_BREACH"],
            2,
        )

    def test_resolve_execution_context_orphan_span(self) -> None:
        ctx = resolve_execution_context({})
        self.assertTrue(ctx.span_orphan)
        self.assertTrue(ctx.run_id.startswith("run-"))
        self.assertTrue(ctx.span_id.startswith("orphan-span-"))

    def test_record_fault_from_context_with_known_ids(self) -> None:
        record_fault_from_context(
            metadata={"run_id": "run-known", "span_id": "span-known"},
            invariant_id="operator_instant_compose",
            fault_code=FAULT_CODE_SPAN_ORPHAN,
            store=self.store,
        )
        rows = self.store.read_recent()
        self.assertEqual(rows[0]["run_id"], "run-known")
        self.assertEqual(rows[0]["span_id"], "span-known")

    def test_spine_pipeline_records_invariant_breach(self) -> None:
        reset_fault_journal(runtime_root=self.temp_dir)
        result = evaluate_spine_pipeline(
            {
                "substrate_ok": True,
                "aris_admission": {"status": "blocked", "non_copy_clause": {"allowed": False}},
                "jarvis_blocked": False,
                "halt_before_cortex": True,
                "execution_context": {
                    "run_id": "run-spine",
                    "span_id": "span-spine",
                    "fault_journal_runtime_dir": self.temp_dir,
                },
            }
        )
        self.assertTrue(result.get("halted"))
        self.assertEqual(result.get("halt_stage"), "aris_admit")
        rows = self.store.read_recent()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["invariant_id"], "aris_before_cortex")
        self.assertEqual(rows[0]["fault_code"], FAULT_CODE_INVARIANT_BREACH)

    def test_bridge_binding_mismatch_fault_code(self) -> None:
        from src.fault_journal import record_spine_invariant_fault

        record_spine_invariant_fault(
            halt_stage="jarvis_authorize",
            metadata={
                "run_id": "run-bridge",
                "span_id": "span-bridge",
                "bridge_binding_mismatch": True,
                "fault_journal_runtime_dir": self.temp_dir,
            },
            store=self.store,
        )
        rows = self.store.read_recent()
        self.assertEqual(rows[0]["fault_code"], FAULT_CODE_BRIDGE_BINDING_MISMATCH)

    def test_journal_file_is_append_only_jsonl(self) -> None:
        record_fault(
            run_id="run-jsonl",
            span_id="span-jsonl",
            invariant_id="jarvis_authority",
            fault_code=FAULT_CODE_INVARIANT_BREACH,
            store=self.store,
        )
        path = Path(self.temp_dir) / "fault-journal" / "faults.jsonl"
        self.assertTrue(path.exists())
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        parsed = json.loads(lines[0])
        self.assertEqual(parsed["run_id"], "run-jsonl")


class TestFaultJournalComposedIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        reset_fault_journal(runtime_root=self.temp_dir)

    def tearDown(self) -> None:
        reset_fault_journal(runtime_root=self.temp_dir)

    def test_aris_block_records_fault(self) -> None:
        session = SimpleNamespace(
            metadata={
                "run_id": "run-aris",
                "span_id": "span-aris",
                "fault_journal_runtime_dir": self.temp_dir,
            }
        )
        result = run_composed_turn(
            session,
            "Copy verbatim external architecture.",
            request_payload={
                "cognitive_runtime": True,
                "share_mode": "verbatim",
                "copy_raw_external": True,
            },
        )
        self.assertEqual(result.status, "blocked")
        store = FaultJournalStore(runtime_root=self.temp_dir)
        rows = store.read_recent()
        self.assertGreaterEqual(len(rows), 1)
        aris_rows = [row for row in rows if row.get("invariant_id") == "aris_before_cortex"]
        self.assertEqual(len(aris_rows), 1)
        self.assertEqual(aris_rows[0]["run_id"], "run-aris")
        self.assertEqual(aris_rows[0]["span_id"], "span-aris")


if __name__ == "__main__":
    unittest.main()
