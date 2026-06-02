from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ul_lineage import (
    LINEAGE_VERSION,
    build_graph,
    emit_node,
    lineage_root,
    record_lineage_event,
    resolve_mission_id,
    validate_graph,
)


class TestUlLineage(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.mkdtemp(prefix="ul_lineage_test_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_emit_all_node_types_multi_hop(self) -> None:
        mission_id = "mission-test-001"
        for node_type, stage in [
            ("chat_turn", "verification"),
            ("memory_promotion", "structure"),
            ("capability_call", "implementation"),
            ("forge_handoff", "implementation"),
        ]:
            emit_node(
                mission_id,
                node_type=node_type,
                cisiv_stage=stage,
                session_id="sess-001",
                source_module=f"test.{node_type}",
                root=self.temp_root,
            )
        graph = build_graph(mission_id, root=self.temp_root)
        self.assertEqual(graph["lineage_version"], LINEAGE_VERSION)
        self.assertEqual(len(graph["nodes"]), 4)
        self.assertGreaterEqual(len(graph["edges"]), 3)
        report = validate_graph(graph)
        self.assertTrue(report["passed"], report["failures"])

    def test_memory_bypass_regression_detected(self) -> None:
        mission_id = "mission-bypass-001"
        for node_type, stage in [
            ("chat_turn", "verification"),
            ("capability_call", "implementation"),
            ("forge_handoff", "implementation"),
        ]:
            emit_node(
                mission_id,
                node_type=node_type,
                cisiv_stage=stage,
                root=self.temp_root,
            )
        graph = build_graph(mission_id, root=self.temp_root)
        report = validate_graph(graph)
        self.assertFalse(report["passed"])
        self.assertIn("memory_promotion", " ".join(report["failures"]))

    def test_record_skips_without_mission(self) -> None:
        node = record_lineage_event(
            node_type="chat_turn",
            cisiv_stage="verification",
            root=self.temp_root,
        )
        self.assertIsNone(node)
        self.assertFalse(any(lineage_root(self.temp_root).iterdir()))

    def test_fixture_graph_validates(self) -> None:
        fixture = (
            Path(__file__).resolve().parents[1]
            / "tools"
            / "ul"
            / "fixtures"
            / "lineage_multi_hop.json"
        )
        graph = json.loads(fixture.read_text(encoding="utf-8"))
        report = validate_graph(graph)
        self.assertTrue(report["passed"], report["failures"])

    def test_resolve_mission_from_metadata(self) -> None:
        mission_id = resolve_mission_id(
            session_metadata={
                "mission_board": {"active_mission": {"id": "abc123"}}
            }
        )
        self.assertEqual(mission_id, "abc123")


if __name__ == "__main__":
    unittest.main()
