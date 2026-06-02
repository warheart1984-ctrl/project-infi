from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.alt3_lineage import record_alt3_lineage
from src.mission_board import MissionBoardController
from src.ul_lineage import build_graph, emit_node


class TestAlt3Lineage(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.mkdtemp(prefix="alt3_lineage_test_"))
        self.lineage_root = self.temp_root / "lineage"
        self.board = MissionBoardController(runtime_dir=self.temp_root / "missions")
        os.environ["AAIS_LINEAGE_ENABLED"] = "1"

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_record_alt3_lineage_appends_capability_call(self) -> None:
        mission_id = "mission-alt3-lineage-001"
        emit_node(
            mission_id,
            node_type="chat_turn",
            cisiv_stage="concept",
            source_module="test.seed",
            root=self.lineage_root,
        )
        record_alt3_lineage(
            subsystem="recipe_module",
            action="create_mission",
            mission_id=mission_id,
            session_id="sess-alt3",
            payload={"recipe_id": "onboarding-v1"},
            root=self.lineage_root,
        )
        graph = build_graph(mission_id, root=self.lineage_root)
        nodes = graph["nodes"]
        self.assertGreaterEqual(len(nodes), 2)
        last = nodes[-1]
        self.assertEqual(last["node_type"], "capability_call")
        self.assertEqual(last["source_module"], "src.recipe_module")

    def test_create_from_recipe_records_lineage(self) -> None:
        import src.ul_lineage as ul_lineage_module

        with patch.object(ul_lineage_module, "DEFAULT_LINEAGE_ROOT", self.lineage_root):
            snapshot = self.board.create_from_recipe(
                "onboarding-v1",
                signoff_ack=True,
                recipe_root=self.temp_root / "recipe_module",
            )
        mission_id = snapshot["active_mission"]["id"]
        graph = build_graph(mission_id, root=self.lineage_root)
        sources = [n["source_module"] for n in graph["nodes"]]
        self.assertIn("src.recipe_module", sources)


if __name__ == "__main__":
    unittest.main()
