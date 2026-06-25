"""AuthorityEnvelope — closed-custody kernel authority token."""

# Mythic: Authority Corridor Envelope
# Engineering: AuthorityEnvelope
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from src.ucr.binary_law_key import CANONICAL_U128, validate_law_key

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

# Test-only signing key; production must use HSM-backed custody per contract.
_TEST_SIGNING_KEY = b"aaes-os-authority-envelope-test-key-v0"


@dataclass(slots=True)
class PermissionSet:
    scopes: list[str]
    max_risk: str
    max_span: int
    allow_tools: bool
    allow_memory: bool

    def __post_init__(self) -> None:
        if self.max_risk not in RISK_ORDER:
            raise ValueError(f"max_risk must be one of {tuple(RISK_ORDER)}")


@dataclass(slots=True)
class AuthorityEnvelope:
    envelope_id: UUID
    subject_id: UUID
    principal_id: UUID
    corridor_id: UUID
    permissions: PermissionSet
    law_key: int
    issued_at: datetime
    expires_at: datetime
    nonce: int
    signature: bytes = field(default=b"", repr=False)

    def risk_allows(self, risk_level: str) -> bool:
        return RISK_ORDER.get(risk_level, 99) <= RISK_ORDER[self.permissions.max_risk]

    def signing_payload(self) -> dict[str, Any]:
        return {
            "envelope_id": str(self.envelope_id),
            "subject_id": str(self.subject_id),
            "principal_id": str(self.principal_id),
            "corridor_id": str(self.corridor_id),
            "permissions": asdict(self.permissions),
            "law_key": self.law_key,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "nonce": self.nonce,
        }

    def sign(self, *, key: bytes | None = None) -> None:
        payload = json.dumps(self.signing_payload(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.signature = hmac.new(key or _TEST_SIGNING_KEY, payload, hashlib.sha256).digest()

    def verify_signature(self, *, key: bytes | None = None) -> bool:
        original = self.signature
        self.sign(key=key)
        expected = self.signature
        self.signature = original
        return hmac.compare_digest(original, expected)


@dataclass(frozen=True, slots=True)
class AuthorityValidationResult:
    ok: bool
    reason_code: int | None = None
    reason_detail: str = ""


def encode_envelope(envelope: AuthorityEnvelope) -> bytes:
    if not envelope.signature:
        raise ValueError("envelope must be signed before encoding")
    payload = {
        "envelope_id": str(envelope.envelope_id),
        "subject_id": str(envelope.subject_id),
        "principal_id": str(envelope.principal_id),
        "corridor_id": str(envelope.corridor_id),
        "permissions": asdict(envelope.permissions),
        "law_key": envelope.law_key,
        "issued_at": envelope.issued_at.isoformat(),
        "expires_at": envelope.expires_at.isoformat(),
        "nonce": envelope.nonce,
        "signature": envelope.signature.hex(),
    }
    return json.dumps(payload, sort_keys=True).encode("utf-8")


def decode_envelope(authority_token: bytes) -> AuthorityEnvelope:
    data = json.loads(authority_token.decode("utf-8"))
    envelope = AuthorityEnvelope(
        envelope_id=UUID(data["envelope_id"]),
        subject_id=UUID(data["subject_id"]),
        principal_id=UUID(data["principal_id"]),
        corridor_id=UUID(data["corridor_id"]),
        permissions=PermissionSet(**data["permissions"]),
        law_key=int(data["law_key"]),
        issued_at=datetime.fromisoformat(data["issued_at"]),
        expires_at=datetime.fromisoformat(data["expires_at"]),
        nonce=int(data["nonce"]),
        signature=bytes.fromhex(data["signature"]),
    )
    return envelope


def build_test_envelope(
    *,
    law_key: int = CANONICAL_U128,
    max_risk: str = "high",
    allow_tools: bool = True,
    allow_memory: bool = True,
    ttl_seconds: int = 3600,
    now: datetime | None = None,
) -> AuthorityEnvelope:
    current = now or datetime.now(timezone.utc)
    envelope = AuthorityEnvelope(
        envelope_id=uuid4(),
        subject_id=uuid4(),
        principal_id=uuid4(),
        corridor_id=uuid4(),
        permissions=PermissionSet(
            scopes=["code_write", "data_read", "tool_call"],
            max_risk=max_risk,
            max_span=64,
            allow_tools=allow_tools,
            allow_memory=allow_memory,
        ),
        law_key=law_key,
        issued_at=current,
        expires_at=current.replace(microsecond=0) + __import__("datetime").timedelta(seconds=ttl_seconds),
        nonce=1,
    )
    envelope.sign()
    return envelope


def validate_envelope(
    envelope: AuthorityEnvelope,
    *,
    syscall_law_key: int,
    now: datetime | None = None,
    signing_key: bytes | None = None,
) -> AuthorityValidationResult:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    issued = envelope.issued_at
    expires = envelope.expires_at
    if issued.tzinfo is None:
        issued = issued.replace(tzinfo=timezone.utc)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if current < issued or current > expires:
        return AuthorityValidationResult(
            ok=False,
            reason_code=1002,
            reason_detail="authority envelope expired or not yet valid",
        )

    if envelope.law_key != syscall_law_key:
        return AuthorityValidationResult(
            ok=False,
            reason_code=1002,
            reason_detail="authority envelope law_key does not match syscall law_key",
        )

    if not validate_law_key(syscall_law_key).ok:
        return AuthorityValidationResult(
            ok=False,
            reason_code=1002,
            reason_detail="syscall law_key failed BLK_UCR_V0 validation",
        )

    if not envelope.verify_signature(key=signing_key):
        return AuthorityValidationResult(
            ok=False,
            reason_code=1002,
            reason_detail="authority envelope signature invalid",
        )

    return AuthorityValidationResult(ok=True)
