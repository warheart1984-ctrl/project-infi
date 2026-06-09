"""Tests for WorkOS governance bridge (AAIS operator lanes ↔ RBAC + audit logs)."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.workos_governance_bridge import (
    AAIS_CAPABILITY_TO_WORKOS_PERMISSION,
    decision_event_to_audit_log,
    emit_workos_audit_event,
    permission_for_aais_capability,
    session_has_permission,
    workos_bridge_enabled,
)


class WorkOSGovernanceBridgeTests(unittest.TestCase):
    def test_maps_genome_capabilities_to_permissions(self):
        self.assertEqual(
            permission_for_aais_capability("adopt_shared_norm"),
            "governance.norm.adopt",
        )
        self.assertEqual(
            permission_for_aais_capability("approve_policy_changes"),
            "governance.policy.approve",
        )
        self.assertIsNone(permission_for_aais_capability("unknown_capability"))

    def test_decision_event_uses_workos_action_naming(self):
        payload = decision_event_to_audit_log(
            {
                "kind": "otem_approval",
                "decision": "approve",
                "decision_id": "odl_abc123",
                "session_id": "sess-42",
                "recorded_at": "2026-06-07T12:00:00Z",
                "summary": "Operator approved OTEM handoff",
                "claim_label": "asserted",
                "jarvis_receipt_id": "jarvis-mgm-deadbeef",
            }
        )
        self.assertEqual(payload["action"], "governance.approval.approved")
        self.assertEqual(payload["actor"]["type"], "user")
        self.assertEqual(payload["metadata"]["jarvis_receipt_id"], "jarvis-mgm-deadbeef")
        self.assertTrue(any(t["type"] == "decision" for t in payload["targets"]))

    def test_emit_skips_without_api_key(self):
        with patch.dict(os.environ, {"AAIS_WORKOS_BRIDGE": "1", "WORKOS_API_KEY": ""}, clear=False):
            result = emit_workos_audit_event({"kind": "pipeline_turn", "decision": "allow"})
        self.assertTrue(result["skipped"])
        self.assertEqual(result["reason"], "workos_api_key_missing")

    def test_session_checks_permissions_not_role_slug(self):
        session = {"role": {"slug": "admin", "permissions": ["governance.ledger.read"]}}
        self.assertTrue(session_has_permission(session, "governance.ledger.read"))
        self.assertFalse(session_has_permission(session, "governance.policy.approve"))

    def test_bridge_disabled_by_default(self):
        env = os.environ.copy()
        env.pop("AAIS_WORKOS_BRIDGE", None)
        with patch.dict(os.environ, env, clear=True):
            self.assertFalse(workos_bridge_enabled())

    def test_all_genome_capabilities_have_permissions(self):
        expected = {
            "observe_culture_of_beings_drift",
            "adopt_shared_norm",
            "observe_multi_being_drift",
            "adopt_multi_being_pact",
            "observe_social_drift",
            "adopt_social_bond",
            "observe_autobiographical_drift",
            "adopt_autobiographical_episode",
            "observe_narrative_drift",
            "adopt_narrative_beat",
            "approve_policy_changes",
        }
        self.assertTrue(expected.issubset(set(AAIS_CAPABILITY_TO_WORKOS_PERMISSION)))


if __name__ == "__main__":
    unittest.main()
