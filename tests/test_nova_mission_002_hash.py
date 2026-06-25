"""Mission #002 integration hash tests."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[1] / "nova-observer-bundle"
HASH_TOOL = BUNDLE / "tools" / "integration_hash.py"
EXPECTED = BUNDLE / "expected_integration_hash.txt"


def _reference_metadata() -> dict[str, str]:
    return {
        "adapter_version": "1.0",
        "cursor_version": "unknown",
        "nemotron_model": "Nemotron Ultra",
        "nova_version": "unknown",
        "protocol_version": "1.0",
        "tunnel_url": "https://mission-002-reference.example/v1",
    }


def test_integration_hash_is_deterministic() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(HASH_TOOL),
            "--tunnel-url",
            "https://mission-002-reference.example/v1",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(BUNDLE),
    )
    digest_line = None
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if len(stripped) == 64 and all(c in "0123456789abcdef" for c in stripped):
            digest_line = stripped
    assert digest_line is not None
    metadata = _reference_metadata()
    expected = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    assert digest_line == expected


def test_expected_integration_hash_matches_reference_tunnel() -> None:
    text = EXPECTED.read_text(encoding="utf-8")
    metadata = _reference_metadata()
    expected = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    assert f"SHA256: {expected}" in text


def test_integration_hash_writes_observed_file() -> None:
    subprocess.run(
        [
            sys.executable,
            str(HASH_TOOL),
            "--tunnel-url",
            "https://mission-002-reference.example/v1",
        ],
        check=True,
        cwd=str(BUNDLE),
    )
    observed = BUNDLE / "integration_hash_observed.txt"
    assert observed.is_file()
    assert len(observed.read_text(encoding="utf-8").strip()) == 64
