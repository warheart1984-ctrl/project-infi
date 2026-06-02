from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from src.mission_board import MissionBoardController
from src.recipe_module import (
    FIXTURE_ROOT,
    append_ledger,
    draft_mission_fields,
    evaluate_gates,
    load_recipe_by_id,
    persist_pack,
    validate_pack,
)


class TestRecipeModule(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.mkdtemp(prefix="recipe_module_test_"))
        self.recipe_root = self.temp_root / "recipe_module"
        self.board = MissionBoardController(runtime_dir=self.temp_root / "missions")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_fixture_validates(self) -> None:
        pack = load_recipe_by_id("onboarding-v1")
        validate_pack(pack)
        self.assertEqual(pack["recipe_module_version"], "recipe_module.v1")

    def test_gate_halts_without_signoff(self) -> None:
        pack = load_recipe_by_id("onboarding-v1")
        result = evaluate_gates(pack, {"signoff_ack": False})
        self.assertFalse(result["passed"])
        self.assertTrue(any(g["gate_type"] == "human_signoff" for g in result["gates"]))

    def test_gate_passes_with_signoff(self) -> None:
        pack = load_recipe_by_id("onboarding-v1")
        result = evaluate_gates(pack, {"signoff_ack": True})
        self.assertTrue(result["passed"])

    def test_draft_mission_fields(self) -> None:
        pack = load_recipe_by_id("onboarding-v1")
        fields = draft_mission_fields(pack)
        self.assertEqual(fields["title"], "Operator Onboarding")
        self.assertIn("recipe_module", fields["tags"])

    def test_persist_and_ledger(self) -> None:
        pack = load_recipe_by_id("onboarding-v1")
        persist_pack(pack, root=self.recipe_root)
        append_ledger(
            "onboarding-v1",
            {"event": "test"},
            root=self.recipe_root,
        )
        ledger = self.recipe_root / "onboarding-v1" / "execution_ledger.jsonl"
        self.assertTrue(ledger.is_file())
        lines = ledger.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)

    def test_create_from_recipe_requires_signoff(self) -> None:
        with self.assertRaises(ValueError):
            self.board.create_from_recipe(
                "onboarding-v1",
                signoff_ack=False,
                recipe_root=self.recipe_root,
            )

    def test_create_from_recipe_with_signoff(self) -> None:
        snapshot = self.board.create_from_recipe(
            "onboarding-v1",
            signoff_ack=True,
            recipe_root=self.recipe_root,
        )
        active = snapshot.get("active_mission") or {}
        self.assertEqual(active.get("title"), "Operator Onboarding")
        self.assertIn("recipe_module", active.get("tags") or [])

    def test_fixture_path_exists(self) -> None:
        self.assertTrue((FIXTURE_ROOT / "onboarding-v1.json").is_file())


class TestRecipeModuleAPI(unittest.TestCase):
    def test_from_recipe_endpoint(self) -> None:
        import src.api as api

        with api.app.test_client() as client:
            blocked = client.post(
                "/api/jarvis/missions/from-recipe",
                json={"recipe_id": "onboarding-v1"},
            )
            self.assertEqual(blocked.status_code, 400)

            ok = client.post(
                "/api/jarvis/missions/from-recipe",
                json={"recipe_id": "onboarding-v1", "signoff_ack": True},
            )
            self.assertEqual(ok.status_code, 201)
            payload = ok.get_json()["mission_board"]
            self.assertEqual(payload["active_mission"]["title"], "Operator Onboarding")

            preset = client.post(
                "/api/jarvis/missions/from-preset",
                json={"preset_id": "ship_feature"},
            )
            self.assertEqual(preset.status_code, 201)
            self.assertEqual(preset.get_json()["mission_board"]["active_mission"]["title"], "Ship feature")


if __name__ == "__main__":
    unittest.main()
