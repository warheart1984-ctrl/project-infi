from __future__ import annotations

import hashlib
import unittest

from src.usl.canonical_serialize import canonical_bytes, event_hash
from src.usl.types import (
    ActorInfo,
    CapabilityInfo,
    ContextInfo,
    CryptoInfo,
    DeltaSummary,
    LawInfo,
    ResourceInfo,
    StateInfo,
    VossInfo,
    VossTransition,
)


def _golden_transition() -> VossTransition:
    return VossTransition(
        version="v1",
        transition_id="00000000-0000-4000-8000-000000000001",
        timestamp="2026-06-09T12:00:00+00:00",
        actor=ActorInfo(
            binary_id="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            profile_id="daily-driver",
            principal_id="principal:test",
            sigil_id="sigil:test",
        ),
        context=ContextInfo(
            os_family="windows",
            process_id="win-guest-1",
            thread_id="tid-1",
            session_id="sess-1",
            usl_node_id="usl-node-1",
        ),
        capability=CapabilityInfo(
            capability_id="fs.write",
            ceiling_id="fs.basic",
            resource=ResourceInfo(
                kind="file",
                locator="C:/Users/jon/test.txt",
                extra={
                    "method": "writefile",
                    "mode": "create_or_truncate",
                    "direction": "outbound",
                },
            ),
        ),
        state=StateInfo(
            pre_state_hash="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            post_state_hash="sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            delta_hash="sha256:2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
            delta_summary=DeltaSummary(bytes_written=5, objects_created=1),
        ),
        law=LawInfo(
            policy_id="policy:daily-driver",
            lawbook_id="lawbook:usl-v1",
            decision="allow",
            decision_reason="policy_allow",
            decision_detail="fs.write permitted under fs.basic",
        ),
        voss=VossInfo(
            lambda_coupling_id="sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            debt_id="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            scar_id="sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
            cycle_id=1,
            lane_id="lane-default",
        ),
        crypto=CryptoInfo(
            event_hash="",
            prev_ledger_root="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            ledger_root="",
        ),
    )


class CanonicalSerializeTests(unittest.TestCase):
    def test_field_order_and_omission(self) -> None:
        transition = _golden_transition()
        raw = canonical_bytes(transition).decode("utf-8")
        keys = [part.split("=", 1)[0] for part in raw.split("|")]
        self.assertEqual(keys[0], "version")
        self.assertIn("actor.binary_id", keys)
        self.assertIn("crypto.prev_ledger_root", keys)
        self.assertNotIn("crypto.event_hash", raw)
        self.assertNotIn("crypto.ledger_root", raw)
        self.assertNotIn("state.delta_summary.bytes_read", raw)

    def test_stable_event_hash(self) -> None:
        transition = _golden_transition()
        first = event_hash(transition)
        second = event_hash(transition)
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("sha256:"))
        digest = first.split(":", 1)[1]
        self.assertEqual(len(digest), 64)

    def test_lowercase_enums_in_canonical_form(self) -> None:
        transition = _golden_transition()
        raw = canonical_bytes(transition).decode("utf-8")
        self.assertIn("context.os_family=windows", raw)
        self.assertIn("law.decision=allow", raw)

    def test_event_hash_matches_sha256_of_canonical_bytes(self) -> None:
        transition = _golden_transition()
        expected = hashlib.sha256(canonical_bytes(transition)).hexdigest()
        self.assertEqual(event_hash(transition), f"sha256:{expected}")


if __name__ == "__main__":
    unittest.main()
