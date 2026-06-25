"""Tests for UCR attestation token and ucr_register syscall."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.ucr.corridor import build_nova_dev_corridor
from src.ucr.corridor_loader import reset_corridor_loader_for_tests, write_corridor_fixture
from src.ucr.kernel_boot import run_early_boot
from src.ucr.trust_root import get_trust_root, reset_trust_root_for_tests
from src.ucr.ucr_attestation import (
    UCRAttestationToken,
    BOOT_NOT_SEALED,
    CORRIDORS_HASH_MISMATCH,
    LAW_KEY_INVALID,
    LAW_SPINE_HASH_MISMATCH,
    RegisterOutcome,
    SIGNATURE_INVALID,
    TOKEN_EXPIRED,
    TRUST_ROOT_MISMATCH,
    get_registered_ucr_handle,
    issue_attestation_from_sealed_trust,
    issue_attestation_token,
    reset_ucr_registration_for_tests,
    ucr_register,
)


class UCRAttestationTests(unittest.TestCase):
    BOOT_TS = "2026-06-18T10:00:00Z"

    def setUp(self) -> None:
        reset_trust_root_for_tests()
        reset_corridor_loader_for_tests()
        reset_ucr_registration_for_tests()

    def tearDown(self) -> None:
        reset_trust_root_for_tests()
        reset_corridor_loader_for_tests()
        reset_ucr_registration_for_tests()

    def _seal_boot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "corridors"
            registry.mkdir(parents=True)
            write_corridor_fixture(registry, build_nova_dev_corridor())
            result = run_early_boot(registry, boot_timestamp=self.BOOT_TS)
            self.assertEqual(result.boot_result.value, "OK")
            self._sealed_trust = get_trust_root()

    def _future_expiry(self) -> str:
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        return future.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def test_register_happy_path_after_boot(self) -> None:
        self._seal_boot()
        token = issue_attestation_from_sealed_trust(
            ucr_instance_id="ucr.test",
            build_fingerprint="ucr-build-v0.1",
            expires_at=self._future_expiry(),
        )
        result = ucr_register(token)
        self.assertEqual(result.outcome, RegisterOutcome.OK)
        self.assertIsNotNone(result.ucr_handle)
        self.assertEqual(get_registered_ucr_handle(), result.ucr_handle)

    def test_refused_boot_not_sealed(self) -> None:
        token = issue_attestation_token(
            ucr_instance_id="ucr.test",
            build_fingerprint="ucr-build-v0.1",
            trust_root="sha3-256:" + "a" * 64,
            corridors_hash="sha3-256:" + "b" * 64,
            law_spine_hash="sha3-256:" + "c" * 64,
            expires_at=self._future_expiry(),
        )
        result = ucr_register(token)
        self.assertEqual(result.outcome, RegisterOutcome.REFUSED)
        self.assertEqual(result.reason_code, BOOT_NOT_SEALED)

    def test_refused_token_expired(self) -> None:
        self._seal_boot()
        trust = self._sealed_trust
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        past_str = past.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        token = issue_attestation_token(
            ucr_instance_id="ucr.test",
            build_fingerprint="ucr-build-v0.1",
            trust_root=trust.h_trust_root,
            corridors_hash=trust.h_corridors,
            law_spine_hash=trust.h_law_spine,
            issued_at=past_str,
            expires_at=past_str,
        )
        result = ucr_register(token)
        self.assertEqual(result.outcome, RegisterOutcome.REFUSED)
        self.assertEqual(result.reason_code, TOKEN_EXPIRED)

    def test_refused_trust_root_mismatch(self) -> None:
        self._seal_boot()
        trust = self._sealed_trust
        token = issue_attestation_token(
            ucr_instance_id="ucr.test",
            build_fingerprint="ucr-build-v0.1",
            trust_root="sha3-256:" + "f" * 64,
            corridors_hash=trust.h_corridors,
            law_spine_hash=trust.h_law_spine,
            expires_at=self._future_expiry(),
        )
        result = ucr_register(token)
        self.assertEqual(result.outcome, RegisterOutcome.REFUSED)
        self.assertEqual(result.reason_code, TRUST_ROOT_MISMATCH)

    def test_refused_corridors_hash_mismatch(self) -> None:
        self._seal_boot()
        trust = self._sealed_trust
        token = issue_attestation_token(
            ucr_instance_id="ucr.test",
            build_fingerprint="ucr-build-v0.1",
            trust_root=trust.h_trust_root,
            corridors_hash="sha3-256:" + "d" * 64,
            law_spine_hash=trust.h_law_spine,
            expires_at=self._future_expiry(),
        )
        result = ucr_register(token)
        self.assertEqual(result.outcome, RegisterOutcome.REFUSED)
        self.assertEqual(result.reason_code, CORRIDORS_HASH_MISMATCH)

    def test_refused_law_spine_hash_mismatch(self) -> None:
        self._seal_boot()
        trust = self._sealed_trust
        token = issue_attestation_token(
            ucr_instance_id="ucr.test",
            build_fingerprint="ucr-build-v0.1",
            trust_root=trust.h_trust_root,
            corridors_hash=trust.h_corridors,
            law_spine_hash="sha3-256:" + "e" * 64,
            expires_at=self._future_expiry(),
        )
        result = ucr_register(token)
        self.assertEqual(result.outcome, RegisterOutcome.REFUSED)
        self.assertEqual(result.reason_code, LAW_SPINE_HASH_MISMATCH)

    def test_refused_invalid_law_key(self) -> None:
        self._seal_boot()
        trust = self._sealed_trust
        token = issue_attestation_token(
            ucr_instance_id="ucr.test",
            build_fingerprint="ucr-build-v0.1",
            law_key=0,
            trust_root=trust.h_trust_root,
            corridors_hash=trust.h_corridors,
            law_spine_hash=trust.h_law_spine,
            expires_at=self._future_expiry(),
        )
        result = ucr_register(token)
        self.assertEqual(result.outcome, RegisterOutcome.REFUSED)
        self.assertEqual(result.reason_code, LAW_KEY_INVALID)

    def test_refused_signature_invalid(self) -> None:
        self._seal_boot()
        token = issue_attestation_from_sealed_trust(
            ucr_instance_id="ucr.test",
            build_fingerprint="ucr-build-v0.1",
            expires_at=self._future_expiry(),
        )
        tampered = UCRAttestationToken(
            token_id=token.token_id,
            ucr_instance_id=token.ucr_instance_id,
            build_fingerprint=token.build_fingerprint,
            law_key=token.law_key,
            trust_root=token.trust_root,
            corridors_hash=token.corridors_hash,
            law_spine_hash=token.law_spine_hash,
            issued_at=token.issued_at,
            expires_at=token.expires_at,
            nonce=token.nonce,
            signature=b"\x00" * 32,
        )
        result = ucr_register(tampered)
        self.assertEqual(result.outcome, RegisterOutcome.REFUSED)
        self.assertEqual(result.reason_code, SIGNATURE_INVALID)


if __name__ == "__main__":
    unittest.main()
