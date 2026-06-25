"""Kernel hash utilities for trust-root measurements."""

from __future__ import annotations

import hashlib
from typing import Literal

HashAlg = Literal["sha3-256", "blake3-256"]

DEFAULT_HASH_ALG: HashAlg = "sha3-256"


def digest_bytes(data: bytes, hash_alg: HashAlg = DEFAULT_HASH_ALG) -> bytes:
    if hash_alg == "sha3-256":
        return hashlib.sha3_256(data).digest()
    if hash_alg == "blake3-256":
        try:
            import blake3  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ValueError("blake3-256 requested but blake3 package is not installed") from exc
        return blake3.blake3(data).digest()
    raise ValueError(f"unsupported hash algorithm: {hash_alg}")


def digest_hex(data: bytes, hash_alg: HashAlg = DEFAULT_HASH_ALG) -> str:
    return digest_bytes(data, hash_alg).hex()


def format_measurement(hash_alg: HashAlg, digest_hex_value: str) -> str:
    return f"{hash_alg}:{digest_hex_value}"


def parse_measurement(line_value: str) -> tuple[HashAlg, str]:
    if ":" not in line_value:
        raise ValueError(f"invalid measurement format: {line_value}")
    alg, digest = line_value.split(":", 1)
    if alg not in {"sha3-256", "blake3-256"}:
        raise ValueError(f"unsupported hash algorithm: {alg}")
    return alg, digest


def measurement_to_raw_bytes(measurement: str) -> bytes:
    _, digest_hex_value = parse_measurement(measurement)
    raw = bytes.fromhex(digest_hex_value)
    if len(raw) != 32:
        raise ValueError("measurement digest must be 256 bits")
    return raw
