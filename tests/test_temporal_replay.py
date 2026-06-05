"""Temporal Replay Machine tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.project_infi_law import PROJECT_INFI_CONTRACT_VERSION
from src.temporal_replay.api_envelope import wrap_replay_payload
from src.temporal_replay.emitter_registry import live_fork_allowed, resolve_emitter
from src.temporal_replay.event import new_event_id, payload_hash, sort_events
from src.temporal_replay.ingestors import ingest_subject
from src.temporal_replay.law_pin import resolve_law_pin
from src.temporal_replay.timeline import build_timeline
from src.temporal_replay.bridge_audit import append_bridge_audit_event
from src.ugr.mission.ledger_merkle import compute_ledger_merkle_root, transition_leaf_hash


def assert_replay_envelope(testcase: unittest.TestCase, payload: dict) -> None:
    testcase.assertIn("law_enforcement", payload)
    testcase.assertIn("ul_snapshot", payload)
    testcase.assertIn("law_event_log", payload)
    testcase.assertEqual(payload["law_enforcement"]["contract_version"], PROJECT_INFI_CONTRACT_VERSION)
    testcase.assertEqual(payload["law_enforcement"]["source_of_truth"], "project_infi_law")


class TestTemporalReplayEvent(unittest.TestCase):
    def test_sort_events_stable(self):
        events = [
            {"timestamp_utc": "2026-01-02T10:00:00+00:00", "sequence": 1},
            {"timestamp_utc": "2026-01-01T10:00:00+00:00", "sequence": 0},
        ]
        ordered = sort_events(events)
        self.assertEqual(ordered[0]["sequence"], 0)

    def test_new_event_id_deterministic_length(self):
        eid = new_event_id("ledger_transition", "m1", 0)
        self.assertTrue(eid.startswith("tre-"))


class TestTemporalReplayIngest(unittest.TestCase):
    def test_mission_ingest_empty_without_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            events = ingest_subject("mission", "nonexistent-mission", runtime_dir=Path(tmp))
            self.assertIsInstance(events, list)

    def test_timeline_build_and_wrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger_path = root / "collective-pattern-ledger" / "tenants" / "global" / "missions.jsonl"
            ledger_path.parent.mkdir(parents=True, exist_ok=True)
            row = {
                "mission_id": "mission-test-1",
                "action_id": "act-1",
                "timestamp": "2026-06-04T14:32:00+00:00",
                "type": "step",
                "tenant_id": "default",
            }
            ledger_path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
            tl = build_timeline("mission", "mission-test-1", runtime_dir=root, rebuild=True)
            self.assertGreaterEqual(tl["event_count"], 1)
            wrapped = wrap_replay_payload(tl)
            assert_replay_envelope(self, wrapped)


class TestTemporalReplayLawPin(unittest.TestCase):
    def test_resolve_law_pin_at_t(self):
        events = [
            {
                "event_id": "e1",
                "timestamp_utc": "2026-06-04T14:00:00+00:00",
                "law_context": {"invariant_version": "3.0", "law_version": "1.4"},
                "boundary": {"tenant_id": "tenant-acme", "boundary_digest": "abc"},
            },
            {
                "event_id": "e2",
                "timestamp_utc": "2026-06-04T14:32:00+00:00",
                "law_context": {"invariant_version": "3.0", "law_version": "1.4"},
                "boundary": {"tenant_id": "tenant-acme", "boundary_digest": "abc"},
            },
        ]
        pin = resolve_law_pin(events, at="2026-06-04T14:32:00+00:00")
        self.assertEqual(pin["tenant_id"], "tenant-acme")
        self.assertEqual(pin["invariant_version"], "3.0")


class TestTemporalReplayMerkle(unittest.TestCase):
    def test_ledger_merkle_tamper_detected(self):
        row = {"action_id": "a1", "mission_id": "m1"}
        root1 = compute_ledger_merkle_root([row])
        tampered = dict(row)
        tampered["mission_id"] = "m2"
        root2 = compute_ledger_merkle_root([tampered])
        self.assertNotEqual(root1, root2)
        self.assertEqual(transition_leaf_hash(row), transition_leaf_hash(dict(row)))


class TestTemporalReplayForward(unittest.TestCase):
    def test_live_fork_allowlist(self):
        self.assertTrue(live_fork_allowed("invariant_engine_organ"))
        self.assertFalse(live_fork_allowed("unknown_subsystem"))

    def test_emitter_registry(self):
        em = resolve_emitter("lineage_node")
        self.assertIn("subsystem_id", em)


class TestTemporalReplayBridgeAudit(unittest.TestCase):
    def test_append_bridge_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            import os

            os.environ["AAIS_RUNTIME_DIR"] = tmp
            append_bridge_audit_event(
                "session-1",
                {"sequence": 1, "capability_id": "cap.test", "ok": True},
                runtime_dir=Path(tmp),
            )
            path = Path(tmp) / "temporal_replay" / "capability_audit" / "session-1" / "events.jsonl"
            self.assertTrue(path.is_file())


class TestTemporalReplayDiff(unittest.TestCase):
    def test_build_reasoning_diff_empty(self):
        from src.temporal_replay.diff import build_reasoning_diff

        with self.assertRaises(ValueError):
            build_reasoning_diff(
                subject_type="mission",
                subject_id="m1",
                events=[],
                fork_at="not-a-date",
            )


class TestTemporalReplayService(unittest.TestCase):
    def test_compare_endpoint_shape(self):
        from src.temporal_replay.service import TemporalReplayService

        with tempfile.TemporaryDirectory() as tmp:
            svc = TemporalReplayService(runtime_dir=Path(tmp))
            out = svc.compare(
                {
                    "left": {"subject_type": "mission", "subject_id": "a"},
                    "right": {"subject_type": "mission", "subject_id": "b"},
                }
            )
            assert_replay_envelope(self, out)
            self.assertIn("replay", out)


if __name__ == "__main__":
    unittest.main()
