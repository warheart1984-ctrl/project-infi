"""Operator temporal replay API stable envelope shapes."""

from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from tests.test_workflows import assert_project_infi_payload

if "celery" not in sys.modules:
    import types

    fake_celery_module = types.ModuleType("celery")

    class FakeCelery:
        def __init__(self, *args, **kwargs):
            pass

        def task(self, *args, **kwargs):
            def decorator(fn):
                fn.delay = lambda *a, **k: None
                return fn

            return decorator

    fake_celery_module.Celery = FakeCelery
    sys.modules["celery"] = fake_celery_module

with patch("src.governance_organs.Alt4Runtime.boot_validate"):
    import src.api as api_module

from src.temporal_replay.api_envelope import wrap_replay_payload


class TestOperatorReplayApiShapes(unittest.TestCase):
    def setUp(self):
        self.client = api_module.app.test_client()

    @patch.object(api_module._temporal_replay_service, "timeline")
    def test_timeline_route_envelope(self, mock_timeline):
        mock_timeline.return_value = wrap_replay_payload(
            {
                "subject_type": "mission",
                "subject_id": "m-1",
                "event_count": 1,
                "events": [{"event_id": "e1", "kind": "ledger_transition", "sequence": 0}],
                "summaries": [{"event_id": "e1", "kind": "ledger_transition"}],
                "runtime_effect": "readout_only",
            }
        )
        res = self.client.get("/api/operator/replay/mission/m-1/timeline")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        assert_project_infi_payload(self, body)
        self.assertEqual(body["replay"]["subject_id"], "m-1")

    @patch.object(api_module._temporal_replay_service, "verify")
    def test_verify_route_envelope(self, mock_verify):
        mock_verify.return_value = wrap_replay_payload(
            {
                "ok": True,
                "claim_label": "asserted",
                "checks": [],
            }
        )
        res = self.client.post(
            "/api/operator/replay/mission/m-1/verify",
            json={"at": "2026-06-04T14:32:00+00:00"},
        )
        self.assertEqual(res.status_code, 200)
        assert_project_infi_payload(self, res.get_json())


if __name__ == "__main__":
    unittest.main()
