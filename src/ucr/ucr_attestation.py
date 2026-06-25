"""UCR attestation token and kernel registration syscall."""

# Mythic: Custody Seal
# Engineering: UCRAttestationToken, ucr_register
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from src.ucr.binary_law_key import CANONICAL_U128, validate_law_key
from src.ucr.corridor_loader import is_sealed
from src.ucr.hash_utils import digest_bytes
from src.ucr.trust_root import get_trust_root, is_trust_root_sealed, to_ucr_context

BOOT_NOT_SEALED = 1007
TOKEN_EXPIRED = 1008
TRUST_ROOT_MISMATCH = 1006
LAW_KEY_INVALID = 1001
CORRIDORS_HASH_MISMATCH = 1009
LAW_SPINE_HASH_MISMATCH = 1010
SIGNATURE_INVALID = 1011
UCR_NOT_REGISTERED = 1012

_ATTESTATION_SIGNATURE_DOMAIN = b"AAES-UCR-ATTEST-v1\x00"

_REGISTERED_HANDLE: UUID | None = None
_REGISTERED_INSTANCE_ID: str | None = None


class RegisterOutcome(str, Enum):
    OK = "OK"
    REFUSED = "REFUSED"


@dataclass(frozen=True, slots=True)
class UCRAttestationToken:
    token_id: UUID
    ucr_instance_id: str
    build_fingerprint: str
    law_key: int
    trust_root: str
    corridors_hash: str
    law_spine_hash: str
    issued_at: str
    expires_at: str
    nonce: bytes
    signature: bytes


@dataclass(frozen=True, slots=True)
class UCRRegisterResult:
    outcome: RegisterOutcome
    ucr_handle: UUID | None = None
    reason_code: int | None = None
    reason_detail: str = ""
    metadata: dict[str, Any] | None = None


def reset_ucr_registration_for_tests() -> None:
    global _REGISTERED_HANDLE, _REGISTERED_INSTANCE_ID
    _REGISTERED_HANDLE = None
    _REGISTERED_INSTANCE_ID = None


def get_registered_ucr_handle() -> UUID | None:
    return _REGISTERED_HANDLE


def issue_attestation_token(
    *,
    ucr_instance_id: str,
    build_fingerprint: str,
    law_key: int = CANONICAL_U128,
    trust_root: str,
    corridors_hash: str,
    law_spine_hash: str,
    issued_at: str | None = None,
    expires_at: str,
    nonce: bytes | None = None,
) -> UCRAttestationToken:
    if not ucr_instance_id.strip():
        raise ValueError("ucr_instance_id must be non-empty")
    if not build_fingerprint.strip():
        raise ValueError("build_fingerprint must be non-empty")
    if not trust_root.startswith("sha3-256:"):
        raise ValueError("trust_root must be a sha3-256 measurement")
    if not corridors_hash.startswith("sha3-256:"):
        raise ValueError("corridors_hash must be a sha3-256 measurement")
    if not law_spine_hash.startswith("sha3-256:"):
        raise ValueError("law_spine_hash must be a sha3-256 measurement")

    now = datetime.now(timezone.utc).replace(microsecond=0)
    issued = issued_at or now.isoformat().replace("+00:00", "Z")
    token_nonce = nonce if nonce is not None else digest_bytes(ucr_instance_id.encode("utf-8") + build_fingerprint.encode("utf-8"))

    token_id = uuid4()
    signature = _placeholder_signature(
        token_id=token_id,
        ucr_instance_id=ucr_instance_id,
        build_fingerprint=build_fingerprint,
        law_key=law_key,
        trust_root=trust_root,
        corridors_hash=corridors_hash,
        law_spine_hash=law_spine_hash,
        issued_at=issued,
        expires_at=expires_at,
        nonce=token_nonce,
    )
    return UCRAttestationToken(
        token_id=token_id,
        ucr_instance_id=ucr_instance_id,
        build_fingerprint=build_fingerprint,
        law_key=law_key,
        trust_root=trust_root,
        corridors_hash=corridors_hash,
        law_spine_hash=law_spine_hash,
        issued_at=issued,
        expires_at=expires_at,
        nonce=token_nonce,
        signature=signature,
    )


def issue_attestation_from_sealed_trust(
    *,
    ucr_instance_id: str,
    build_fingerprint: str,
    law_key: int = CANONICAL_U128,
    expires_at: str,
    issued_at: str | None = None,
) -> UCRAttestationToken:
    sealed = get_trust_root()
    return issue_attestation_token(
        ucr_instance_id=ucr_instance_id,
        build_fingerprint=build_fingerprint,
        law_key=law_key,
        trust_root=sealed.h_trust_root,
        corridors_hash=sealed.h_corridors,
        law_spine_hash=sealed.h_law_spine,
        issued_at=issued_at,
        expires_at=expires_at,
    )


def ucr_register(token: UCRAttestationToken) -> UCRRegisterResult:
    global _REGISTERED_HANDLE, _REGISTERED_INSTANCE_ID

    if not isinstance(token, UCRAttestationToken):
        raise TypeError("token must be UCRAttestationToken")

    if not is_trust_root_sealed() or not is_sealed():
        return _refused(BOOT_NOT_SEALED, "kernel trust root and corridor loader must be sealed before registration")

    if _parse_iso(token.expires_at) <= datetime.now(timezone.utc):
        return _refused(TOKEN_EXPIRED, f"token expired at {token.expires_at}")

    if not validate_law_key(token.law_key).ok:
        return _refused(LAW_KEY_INVALID, "BLK_UCR_V0 validation failed for attestation law_key")

    if not token.signature:
        return _refused(SIGNATURE_INVALID, "attestation signature missing")

    expected_sig = _placeholder_signature(
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
    )
    if token.signature != expected_sig:
        return _refused(SIGNATURE_INVALID, "attestation signature mismatch")

    sealed = get_trust_root()
    if token.trust_root != sealed.h_trust_root:
        return _refused(TRUST_ROOT_MISMATCH, "token trust_root does not match sealed H_TRUST_ROOT")

    if token.corridors_hash != sealed.h_corridors:
        return _refused(CORRIDORS_HASH_MISMATCH, "token corridors_hash does not match sealed H_CORRIDORS")

    if token.law_spine_hash != sealed.h_law_spine:
        return _refused(LAW_SPINE_HASH_MISMATCH, "token law_spine_hash does not match sealed H_LAW_SPINE")

    context = to_ucr_context(sealed)
    if context.h_trust_root != token.trust_root:
        return _refused(TRUST_ROOT_MISMATCH, "UCR trust context mismatch")

    handle = uuid4()
    _REGISTERED_HANDLE = handle
    _REGISTERED_INSTANCE_ID = token.ucr_instance_id
    return UCRRegisterResult(
        outcome=RegisterOutcome.OK,
        ucr_handle=handle,
        metadata={
            "token_id": str(token.token_id),
            "ucr_instance_id": token.ucr_instance_id,
            "h_trust_root": sealed.h_trust_root,
        },
    )


def _refused(reason_code: int, reason_detail: str) -> UCRRegisterResult:
    return UCRRegisterResult(
        outcome=RegisterOutcome.REFUSED,
        reason_code=reason_code,
        reason_detail=reason_detail,
    )


def _parse_iso(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _placeholder_signature(
    *,
    token_id: UUID,
    ucr_instance_id: str,
    build_fingerprint: str,
    law_key: int,
    trust_root: str,
    corridors_hash: str,
    law_spine_hash: str,
    issued_at: str,
    expires_at: str,
    nonce: bytes,
) -> bytes:
    payload = _ATTESTATION_SIGNATURE_DOMAIN + b"|".join(
        [
            str(token_id).encode("utf-8"),
            ucr_instance_id.encode("utf-8"),
            build_fingerprint.encode("utf-8"),
            f"{law_key:032x}".encode("ascii"),
            trust_root.encode("utf-8"),
            corridors_hash.encode("utf-8"),
            law_spine_hash.encode("utf-8"),
            issued_at.encode("utf-8"),
            expires_at.encode("utf-8"),
            nonce,
        ]
    )
    return digest_bytes(payload)
