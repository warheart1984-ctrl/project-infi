from __future__ import annotations

import hashlib
import unittest

from src.usl.types import ActorInfo
from src.usl.voss_scar import (
    EMPTY_DEBT_SENTINEL,
    bind_voss,
    derive_debt_id,
    derive_lambda_coupling_id,
    derive_scar_id,
)


class VossScarTests(unittest.TestCase):
    def setUp(self) -> None:
        self.actor = ActorInfo(
            binary_id="sha256:aa" + "a" * 62,
            profile_id="daily-driver",
            principal_id="principal:test",
            sigil_id="sigil:test",
        )
        self.pre = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        self.post = "sha256:bb" + "b" * 62
        self.cap = "fs.write"

    def test_lambda_coupling_derivation(self) -> None:
        got = derive_lambda_coupling_id(self.pre, self.cap, self.post, self.actor)
        h = hashlib.sha256()
        h.update(self.pre[7:].encode())
        h.update(self.cap.encode())
        h.update(self.post[7:].encode())
        h.update(self.actor.blob())
        self.assertEqual(got, f"sha256:{h.hexdigest()}")

    def test_scar_derivation(self) -> None:
        lam = derive_lambda_coupling_id(self.pre, self.cap, self.post, self.actor)
        got = derive_scar_id(lam, "allow", 42)
        h = hashlib.sha256()
        h.update(lam[7:].encode())
        h.update(b"allow")
        h.update(b"42")
        self.assertEqual(got, f"sha256:{h.hexdigest()}")

    def test_empty_debt_sentinel(self) -> None:
        self.assertEqual(derive_debt_id(None), EMPTY_DEBT_SENTINEL)
        self.assertEqual(derive_debt_id([]), EMPTY_DEBT_SENTINEL)

    def test_bind_voss_populates_fields(self) -> None:
        info = bind_voss(
            pre_state_hash=self.pre,
            post_state_hash=self.post,
            capability_id=self.cap,
            actor=self.actor,
            decision="allow",
            cycle_id=7,
            lane_id="lane-a",
        )
        self.assertTrue(info.lambda_coupling_id.startswith("sha256:"))
        self.assertTrue(info.scar_id.startswith("sha256:"))
        self.assertEqual(info.debt_id, EMPTY_DEBT_SENTINEL)
        self.assertEqual(info.cycle_id, 7)
        self.assertEqual(info.lane_id, "lane-a")


if __name__ == "__main__":
    unittest.main()
