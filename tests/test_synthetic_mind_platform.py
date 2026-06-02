from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from platform.synthetic_mind import (
    build_synthetic_mind_ref,
    get_synthetic_mind_ref,
    register_synthetic_mind_for_org,
    ref_from_ai_factory_result,
)
from platform.store import PlatformStore


class SyntheticMindPlatformTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        db = Path(self._tmpdir.name) / "platform.sqlite3"
        self.store = PlatformStore(db_path=db)
        self.store.upsert_org({"org_id": "org-sm", "label": "test"})

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_register_and_get_ref(self) -> None:
        ref = build_synthetic_mind_ref(
            org_id="org-sm",
            build_id="nova-default",
            bundle_hash="a" * 64,
        )
        register_synthetic_mind_for_org(store=self.store, org_id="org-sm", ref=ref)
        loaded = get_synthetic_mind_ref(self.store, "org-sm")
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded["build_id"], "nova-default")
        self.assertTrue(loaded["read_only_projection_sample"]["read_only"])

    def test_ref_from_ai_factory_result(self) -> None:
        ref = ref_from_ai_factory_result(
            org_id="org-sm",
            result={
                "build_id": "nova-default",
                "output_dir": ".runtime/ai_factory/nova-default",
                "receipt": {"intent_summary": "test"},
                "hash_manifest": [],
            },
        )
        self.assertEqual(ref["family_id"], "nova.cortex")
        self.assertEqual(ref["ref_version"], "platform.synthetic_mind_ref.v1")


if __name__ == "__main__":
    unittest.main()
