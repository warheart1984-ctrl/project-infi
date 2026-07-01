from __future__ import annotations

import os
import json
import base64
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nova.node.ledger import stable_hash


@dataclass(frozen=True)
class NodeIdentity:
    node_id: str
    operator_id: str
    operator_key_id: str
    policy_hash: str

    @classmethod
    def load(cls, policy_path: str = "./policy.yaml") -> "NodeIdentity":
        policy_file = Path(policy_path)
        policy_bytes = policy_file.read_bytes() if policy_file.exists() else b""
        policy = _load_policy(policy_file) if policy_file.exists() else {}
        return cls(
            node_id=os.environ.get("NOVA_NODE_ID", str(policy.get("node_id") or "lawful-nova-node-local")),
            operator_id=os.environ.get("NOVA_OPERATOR_ID", str(policy.get("operator_id") or "operator-local")),
            operator_key_id=os.environ.get("NOVA_OPERATOR_KEY_ID", "operator-local"),
            policy_hash=stable_hash(policy_bytes.decode("utf-8", errors="ignore"))[7:],
        )


def _load_policy(policy_file: Path) -> dict[str, Any]:
    text = policy_file.read_text(encoding="utf-8")
    try:
        import yaml

        data = yaml.safe_load(text)
        return data or {}
    except Exception:
        return {}


def load_operator_private_key() -> dict[str, Any] | None:
    return _load_key_from_env("NOVA_NODE_OPERATOR_PRIVATE_KEY")


def load_operator_public_key() -> dict[str, Any] | None:
    return _load_key_from_env("NOVA_NODE_OPERATOR_PUBLIC_KEY")


def sign_payload(payload: dict[str, Any], private_key: dict[str, Any] | None = None) -> str | None:
    key = private_key or load_operator_private_key()
    if not key:
        return None
    n = int(str(key["n"]), 0)
    d = int(str(key["d"]), 0)
    digest = int.from_bytes(_canonical_digest(payload), "big") % n
    signature = pow(digest, d, n)
    byte_len = max(1, (n.bit_length() + 7) // 8)
    return base64.b64encode(signature.to_bytes(byte_len, "big")).decode("ascii")


def verify_payload_signature(
    payload: dict[str, Any],
    signature: str | None,
    public_key: dict[str, Any] | None = None,
) -> bool:
    key = public_key or load_operator_public_key()
    if not key or not signature:
        return False
    try:
        n = int(str(key["n"]), 0)
        e = int(str(key["e"]), 0)
        sig_int = int.from_bytes(base64.b64decode(signature), "big")
        digest = int.from_bytes(_canonical_digest(payload), "big") % n
        return pow(sig_int, e, n) == digest
    except Exception:
        return False


def _load_key_from_env(name: str) -> dict[str, Any] | None:
    value = os.environ.get(name)
    if not value:
        return None
    path = Path(value)
    raw = path.read_text(encoding="utf-8") if path.exists() else value
    return _parse_key_material(raw.strip())


def _parse_key_material(raw: str) -> dict[str, Any] | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    if "-----BEGIN" not in raw:
        return None
    try:
        label, der = _pem_to_der(raw)
        if label in {"RSA PRIVATE KEY", "RSA PUBLIC KEY"}:
            return _parse_rsa_pkcs1_key(der)
        if label == "PRIVATE KEY":
            return _parse_pkcs8_private_key(der)
        if label == "PUBLIC KEY":
            return _parse_spki_public_key(der)
    except Exception:
        return None
    return None


def _canonical_digest(payload: dict[str, Any]) -> bytes:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(body).digest()


def _pem_to_der(raw: str) -> tuple[str, bytes]:
    match = re.search(r"-----BEGIN ([^-]+)-----(.*?)-----END \1-----", raw, flags=re.S)
    if not match:
        raise ValueError("invalid PEM")
    label = match.group(1).strip()
    body = re.sub(r"\s+", "", match.group(2))
    return label, base64.b64decode(body)


def _parse_rsa_pkcs1_key(der: bytes) -> dict[str, Any]:
    seq, end = _read_tlv(der, 0, expected_tag=0x30)
    if end != len(der):
        raise ValueError("trailing data")
    ints: list[int] = []
    offset = 0
    while offset < len(seq):
        value, offset = _read_integer(seq, offset)
        ints.append(value)
    if len(ints) >= 9:
        return {"kty": "RSA", "n": str(ints[1]), "e": str(ints[2]), "d": str(ints[3])}
    if len(ints) == 2:
        return {"kty": "RSA", "n": str(ints[0]), "e": str(ints[1])}
    raise ValueError("unsupported RSA key")


def _parse_pkcs8_private_key(der: bytes) -> dict[str, Any]:
    seq, end = _read_tlv(der, 0, expected_tag=0x30)
    if end != len(der):
        raise ValueError("trailing data")
    _, offset = _read_integer(seq, 0)
    _, offset = _read_tlv(seq, offset, expected_tag=0x30)
    private_der, offset = _read_tlv(seq, offset, expected_tag=0x04)
    if offset > len(seq):
        raise ValueError("bad private key")
    return _parse_rsa_pkcs1_key(private_der)


def _parse_spki_public_key(der: bytes) -> dict[str, Any]:
    seq, end = _read_tlv(der, 0, expected_tag=0x30)
    if end != len(der):
        raise ValueError("trailing data")
    _, offset = _read_tlv(seq, 0, expected_tag=0x30)
    bitstring, offset = _read_tlv(seq, offset, expected_tag=0x03)
    if not bitstring:
        raise ValueError("empty public key")
    return _parse_rsa_pkcs1_key(bitstring[1:])


def _read_integer(data: bytes, offset: int) -> tuple[int, int]:
    value, offset = _read_tlv(data, offset, expected_tag=0x02)
    return int.from_bytes(value, "big", signed=False), offset


def _read_tlv(data: bytes, offset: int, *, expected_tag: int) -> tuple[bytes, int]:
    if offset >= len(data) or data[offset] != expected_tag:
        raise ValueError("unexpected ASN.1 tag")
    offset += 1
    if offset >= len(data):
        raise ValueError("missing ASN.1 length")
    length = data[offset]
    offset += 1
    if length & 0x80:
        count = length & 0x7F
        if count == 0 or offset + count > len(data):
            raise ValueError("invalid ASN.1 length")
        length = int.from_bytes(data[offset:offset + count], "big")
        offset += count
    end = offset + length
    if end > len(data):
        raise ValueError("truncated ASN.1 value")
    return data[offset:end], end
