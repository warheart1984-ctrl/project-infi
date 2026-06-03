"""AI Slingshot — governed burst lane tests."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from slingshot.common import (
    FRAME_VERSION,
    PACKET_VERSION,
    _SLINGSHOT_JSON_CACHE,
    clear_slingshot_json_cache,
    frame_path,
    packet_path,
)
from slingshot.frame import build_slingshot_frame, load_slingshot_frame
from slingshot.impact import build_impact_receipt, persist_impact_receipt, verify_slingshot_case
from slingshot.launch import admit_slingshot_turn, resolve_slingshot_turn_config
from slingshot.midflight import (
    evaluate_slingshot_midflight_cortex,
    evaluate_slingshot_midflight_reply,
    merge_midflight_reports,
)
from slingshot.packet import (
    build_slingshot_packet,
    load_slingshot_packet,
    packet_is_expired,
)


FIXTURE_V2 = Path("mechanic/fixtures/sample-customer-repo-v2")
TRACE_V2 = FIXTURE_V2 / "traces" / "session.ndjson"
FIXTURE_CLEAN = Path("mechanic/fixtures/sample-customer-repo-clean")
TRACE_CLEAN = FIXTURE_CLEAN / "traces" / "session.ndjson"


class TestSlingshotPreload(unittest.TestCase):
    def test_load_frame_uses_json_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            shot_root = Path(tmp) / "slingshot"
            mech_root = Path(tmp) / "mechanic"
            build_slingshot_frame(
                case_id="cache-case",
                repo_path=FIXTURE_CLEAN.resolve(),
                trace_path=str(TRACE_CLEAN),
                slingshot_root=shot_root,
                mechanic_root=mech_root,
            )
            with patch.dict(os.environ, {"AAIS_SLINGSHOT_CACHE_SEC": "60"}, clear=False):
                clear_slingshot_json_cache()
                first = load_slingshot_frame("cache-case", runtime_root=shot_root)
                second = load_slingshot_frame("cache-case", runtime_root=shot_root)
                self.assertEqual(second.get("drift_count"), first.get("drift_count"))
                self.assertEqual(len(_SLINGSHOT_JSON_CACHE), 1)

                path = frame_path("cache-case", runtime_root=shot_root)
                path.write_text(
                    json.dumps({**first, "drift_count": 999}, sort_keys=True, indent=2),
                    encoding="utf-8",
                )
                third = load_slingshot_frame("cache-case", runtime_root=shot_root)
                self.assertEqual(third.get("drift_count"), 999)

    def test_preload_v2_fixture_launch_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            shot_root = Path(tmp) / "slingshot"
            mech_root = Path(tmp) / "mechanic"
            frame = build_slingshot_frame(
                case_id="sc-v2",
                repo_path=FIXTURE_V2.resolve(),
                trace_path=str(TRACE_V2),
                slingshot_root=shot_root,
                mechanic_root=mech_root,
            )
            self.assertEqual(frame["frame_version"], FRAME_VERSION)
            self.assertTrue(frame["launch_blocked"])
            self.assertGreater(frame["drift_count"], 0)
            self.assertTrue(frame_path("sc-v2", runtime_root=shot_root).is_file())
            profile = mech_root / "sc-v2" / "MECHANIC_RUNTIME_PROFILE.json"
            self.assertTrue(profile.is_file())

    def test_clean_fixture_full_launch_impact_verify_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shot_root = tmp_path / "slingshot"
            mech_root = tmp_path / "mechanic"
            case_id = "sc-clean"
            frame = build_slingshot_frame(
                case_id=case_id,
                repo_path=FIXTURE_CLEAN.resolve(),
                trace_path=str(TRACE_CLEAN),
                slingshot_root=shot_root,
                mechanic_root=mech_root,
            )
            self.assertFalse(frame["launch_blocked"])
            self.assertEqual(frame["drift_count"], 0)

            packet = build_slingshot_packet(
                frame,
                {"authorized_goals": ["analyze support triage only"], "required_constraints": ["no apply"]},
                runtime_root=shot_root,
            )
            self.assertTrue(packet_path(case_id, runtime_root=shot_root).is_file())

            session = SimpleNamespace(metadata={})
            block = admit_slingshot_turn(
                session,
                {"case_id": case_id, "authorized_goals": packet["authorized_goals"]},
                session_id="sess-clean",
                slingshot_root=shot_root,
                mechanic_root=mech_root,
            )
            self.assertIsNone(block)
            self.assertTrue(session.metadata["slingshot"]["active"])

            cortex_report = evaluate_slingshot_midflight_cortex(session, packet=packet, model_calls_this_turn=1)
            reply_report = evaluate_slingshot_midflight_reply(
                user_message="Analyze support triage with no apply.",
                assistant_reply="Analysis only: no apply, no repo writes, and human review remains required.",
                packet=packet,
            )
            merged = merge_midflight_reports(cortex_report, reply_report)
            self.assertEqual(merged["impact_status"], "clean")
            self.assertFalse(merged["drift_events"])

            receipt = build_impact_receipt(
                case_id=case_id,
                turn_id="turn-clean",
                user_message="Analyze support triage with no apply.",
                assistant_reply="Analysis only: no apply, no repo writes, and human review remains required.",
                midflight_report=merged,
                session_metadata=session.metadata,
                slingshot_root=shot_root,
                mechanic_root=mech_root,
            )
            receipt_path = persist_impact_receipt(receipt, runtime_root=shot_root)
            self.assertTrue(receipt_path.is_file())

            result = verify_slingshot_case(
                case_id,
                repo_path=FIXTURE_CLEAN.resolve(),
                slingshot_root=shot_root,
                mechanic_root=mech_root,
            )
            self.assertTrue(result["ok"])
            self.assertTrue(result["frame_present"])
            self.assertTrue(result["packet_present"])
            self.assertTrue(result["replay"]["matched"])
            self.assertEqual(result["receipt_count"], 1)


class TestSlingshotPacket(unittest.TestCase):
    def _clean_frame(self, tmp: Path) -> dict:
        shot_root = tmp / "slingshot"
        mech_root = tmp / "mechanic"
        case_id = "clean-case"
        mech_dir = mech_root / case_id
        mech_dir.mkdir(parents=True)
        (mech_dir / "mechanic_scan.v1.json").write_text(
            json.dumps({"drifts": [], "scan_hash": "abc"}),
            encoding="utf-8",
        )
        (mech_dir / "MECHANIC_RUNTIME_PROFILE.json").write_text(
            json.dumps(
                {
                    "profile_version": "mechanic.runtime_profile.v1",
                    "enforcement": {
                        "cost_ceiling": {"max_model_calls_per_turn": 2},
                    },
                }
            ),
            encoding="utf-8",
        )
        frame = {
            "frame_version": FRAME_VERSION,
            "case_id": case_id,
            "genome_hash": "genome123",
            "scan_hash": "scan123",
            "launch_blocked": False,
            "mechanic_case_dir": str(mech_dir),
            "active_invariants": [],
        }
        shot_root.mkdir(parents=True, exist_ok=True)
        (shot_root / case_id).mkdir(parents=True, exist_ok=True)
        frame_path(case_id, runtime_root=shot_root).write_text(
            json.dumps(frame, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        return frame

    def test_build_and_load_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            frame = self._clean_frame(tmp_path)
            packet = build_slingshot_packet(
                frame,
                {"authorized_goals": ["propose only"], "required_constraints": ["no apply"]},
                runtime_root=tmp_path / "slingshot",
            )
            self.assertEqual(packet["packet_version"], PACKET_VERSION)
            self.assertTrue(packet["cortex_fast_path"])
            self.assertEqual(packet["compose_mode"], "fast")
            loaded = load_slingshot_packet("clean-case", runtime_root=tmp_path / "slingshot")
            self.assertEqual(loaded["case_id"], "clean-case")

    def test_expired_packet(self):
        packet = {"expires_at_utc": "2000-01-01T00:00:00Z"}
        self.assertTrue(packet_is_expired(packet))


class TestSlingshotLaunch(unittest.TestCase):
    def test_resolve_turn_config_active(self):
        cfg = resolve_slingshot_turn_config(
            {"slingshot": {"active": True, "status": "active", "packet": {"compose_mode": "fast"}}}
        )
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg["compose_mode"], "fast")
        self.assertTrue(cfg["cortex_fast_path"])

    def test_resolve_turn_config_escalated(self):
        cfg = resolve_slingshot_turn_config({"slingshot": {"active": True, "status": "escalated"}})
        self.assertIsNone(cfg)

    def test_admit_blocked_when_launch_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shot_root = tmp_path / "slingshot"
            case_id = "blocked-case"
            (shot_root / case_id).mkdir(parents=True, exist_ok=True)
            frame_path(case_id, runtime_root=shot_root).write_text(
                json.dumps(
                    {
                        "frame_version": FRAME_VERSION,
                        "case_id": case_id,
                        "launch_blocked": True,
                        "launch_block_reasons": ["class_III_drift:RNT-04"],
                        "genome_hash": "g",
                        "scan_hash": "s",
                    }
                ),
                encoding="utf-8",
            )
            session = SimpleNamespace(metadata={})
            block = admit_slingshot_turn(
                session,
                {"case_id": case_id},
                session_id="sess-1",
                slingshot_root=shot_root,
                mechanic_root=tmp_path / "mechanic",
            )
            self.assertIsNotNone(block)
            self.assertIn("blocked", block.get("slingshot", {}))


class TestSlingshotMidflight(unittest.TestCase):
    def test_smuggled_goal_signoff(self):
        packet = {
            "authorized_goals": ["analyze only"],
            "required_constraints": ["no apply"],
        }
        report = evaluate_slingshot_midflight_reply(
            user_message="analyze the workflow",
            assistant_reply="I'll also implement and deploy a new feature for you.",
            packet=packet,
        )
        self.assertTrue(report["signoff_required"])
        self.assertEqual(report["impact_status"], "signoff_required")

    def test_merge_midflight_halts_on_class_iii(self):
        merged = merge_midflight_reports(
            {"drift_events": [], "halt_turn": False, "escalate": False, "signoff_required": False},
            {
                "drift_events": [{"violation_class": "III"}],
                "halt_turn": True,
                "escalate": True,
                "signoff_required": True,
                "impact_status": "halted",
            },
        )
        self.assertTrue(merged["halt_turn"])
        self.assertEqual(merged["impact_status"], "halted")


class TestSlingshotImpact(unittest.TestCase):
    def test_receipt_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            receipt = build_impact_receipt(
                case_id="impact-case",
                turn_id="turn-1",
                user_message="hello",
                assistant_reply="world",
                midflight_report={"impact_status": "clean", "drift_events": []},
                slingshot_root=tmp_path,
                mechanic_root=tmp_path / "mechanic",
            )
            path = persist_impact_receipt(receipt, runtime_root=tmp_path)
            self.assertTrue(path.is_file())
            result = verify_slingshot_case("impact-case", slingshot_root=tmp_path)
            self.assertFalse(result["frame_present"])


class TestSlingshotComposeIntegration(unittest.TestCase):
    def test_resolve_composed_turn_payload_slingshot_fast(self):
        from src.aais_composed_runtime import resolve_composed_turn_payload

        session = SimpleNamespace(
            metadata={
                "slingshot": {
                    "active": True,
                    "status": "active",
                    "packet": {"compose_mode": "fast", "cortex_fast_path": True},
                }
            }
        )
        payload, mode = resolve_composed_turn_payload(session, {}, user_message="analyze drift")
        self.assertEqual(mode, "fast")
        self.assertTrue(payload.get("cortex_fast_path"))


if __name__ == "__main__":
    unittest.main()
