"""Integration tests for cog_act_commit with trust root, attestation, and corridors."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from src.ucr.act_codec import serialize_act_payload
from src.ucr.authority_envelope import AuthorityEnvelope, PermissionSet, encode_envelope
from src.ucr.binary_law_key import CANONICAL_U128
from src.ucr.cog_act_commit import (
    CommitOutcome,
    UCR_NOT_REGISTERED,
    cog_act_commit,
    register_trusted_producer,
    reset_commit_state_for_tests,
)
from src.ucr.corridor import NOVA_DEV_CORRIDOR_ID, build_nova_dev_corridor
from src.ucr.corridor_loader import reset_corridor_loader_for_tests, write_corridor_fixture
from src.ucr.kernel_boot import run_early_boot
from src.ucr.trust_root import reset_trust_root_for_tests
from src.ucr.types import UnifiedCognitiveAct
from src.ucr.ucr_attestation import (
    RegisterOutcome,
    issue_attestation_from_sealed_trust,
    reset_ucr_registration_for_tests,
    ucr_register,
)


class CogActCommitTests(unittest.TestCase):
    BOOT_TS = "2026-06-18T10:00:00Z"

    def setUp(self) -> None:
        reset_trust_root_for_tests()
        reset_corridor_loader_for_tests()
        reset_ucr_registration_for_tests()
        reset_commit_state_for_tests()
        register_trusted_producer("ucr.default")

    def tearDown(self) -> None:
        reset_trust_root_for_tests()
        reset_corridor_loader_for_tests()
        reset_ucr_registration_for_tests()
        reset_commit_state_for_tests()

    def _future_expiry(self) -> str:
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        return future.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _seal_boot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "corridors"
            registry.mkdir(parents=True)
            write_corridor_fixture(registry, build_nova_dev_corridor())
            result = run_early_boot(registry, boot_timestamp=self.BOOT_TS)
            self.assertEqual(result.boot_result.value, "OK")

    def _register_ucr(self) -> None:
        token = issue_attestation_from_sealed_trust(
            ucr_instance_id="ucr.test",
            build_fingerprint="ucr-build-v0.1",
            expires_at=self._future_expiry(),
        )
        reg = ucr_register(token)
        self.assertEqual(reg.outcome, RegisterOutcome.OK)

    def _build_envelope(self) -> AuthorityEnvelope:
        current = datetime.now(timezone.utc)
        envelope = AuthorityEnvelope(
            envelope_id=uuid4(),
            subject_id=uuid4(),
            principal_id=uuid4(),
            corridor_id=NOVA_DEV_CORRIDOR_ID,
            permissions=PermissionSet(
                scopes=["code_write", "data_read", "tool_call"],
                max_risk="high",
                max_span=64,
                allow_tools=True,
                allow_memory=True,
            ),
            law_key=CANONICAL_U128,
            issued_at=current,
            expires_at=current.replace(microsecond=0) + timedelta(seconds=3600),
            nonce=1,
        )
        envelope.sign()
        return envelope

    def _commit_args(self, act_id: UUID | None = None) -> tuple[UUID, bytes, bytes, bytes]:
        act_uuid = act_id or uuid4()
        act = UnifiedCognitiveAct(
            act_id=str(act_uuid),
            turn_id="turn-1",
            contract_id="contract-1",
            status="merged",
        )
        payload = serialize_act_payload(
            act,
            risk_level="low",
            producer_id="ucr.default",
            required_scopes=["code_write"],
        )
        authority = encode_envelope(self._build_envelope())
        return act_uuid, authority, payload, b""

    def test_commit_happy_path_after_boot_and_register(self) -> None:
        self._seal_boot()
        self._register_ucr()
        act_id, authority, payload, ledger_ref = self._commit_args()

        result = cog_act_commit(
            act_id,
            CANONICAL_U128,
            authority,
            payload,
            ledger_ref,
            b"",
        )

        self.assertEqual(result.outcome, CommitOutcome.OK)
        self.assertIsNotNone(result.receipt_id)
        self.assertEqual(result.state_version, 1)

    def test_refused_without_ucr_registration(self) -> None:
        self._seal_boot()
        act_id, authority, payload, ledger_ref = self._commit_args()

        result = cog_act_commit(
            act_id,
            CANONICAL_U128,
            authority,
            payload,
            ledger_ref,
            b"",
        )

        self.assertEqual(result.outcome, CommitOutcome.REFUSED)
        self.assertEqual(result.reason_code, UCR_NOT_REGISTERED)


if __name__ == "__main__":
    unittest.main()
