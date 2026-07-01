"""Tests for cross-language CAS hash contract (Python side)."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BINDINGS_PY = ROOT / "bindings" / "python"
CAS_HASH_PATH = BINDINGS_PY / "hash.py"


def _load_hash_module():
    spec = importlib.util.spec_from_file_location("aaes_cas_hash", CAS_HASH_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_python_hash_matches_rust_fixture():
    """Golden receipt bytes must match Rust hash_receipt output."""
    hash_mod = _load_hash_module()
    fixture = {
        "run_id": "run-1",
        "hash": "",
        "spans": [
            {
                "id": "span-1",
                "run_id": "run-1",
                "type": "execute",
                "timestamp": 1735689600,
                "data": {},
            }
        ],
        "result": {"echo": "hello"},
        "created_at": "2025-01-01T00:00:00Z",
    }
    h = hash_mod.hash_receipt_dict(fixture)
    assert len(h) == 64
    assert h == hash_mod.hash_receipt_dict({**fixture, "hash": "deadbeef"})


@pytest.mark.skipif(
    shutil.which("cargo") is None,
    reason="cargo not installed",
)
def test_cross_language_evidence_harness():
    receipt_json = ROOT / "artifacts" / "tmp_receipt.json"
    stderr_log = ROOT / "artifacts" / "aaes-cas-evidence.stderr"
    receipt_json.parent.mkdir(parents=True, exist_ok=True)

    with stderr_log.open("w", encoding="utf-8") as err:
        proc = subprocess.run(
            ["cargo", "run", "-q", "-p", "aaes-cas-evidence"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=err,
            text=True,
            check=True,
        )
    receipt_json.write_text(proc.stdout, encoding="utf-8")

    rust_hash = None
    for line in stderr_log.read_text(encoding="utf-8").splitlines():
        if line.startswith("RUST_HASH="):
            rust_hash = line.split("=", 1)[1]
            break
    assert rust_hash

    py_proc = subprocess.run(
        [sys.executable, str(BINDINGS_PY / "evidence_harness.py"), str(receipt_json)],
        cwd=str(BINDINGS_PY),
        capture_output=True,
        text=True,
        check=True,
    )
    py_hash = None
    for line in py_proc.stderr.splitlines():
        if line.startswith("PY_HASH="):
            py_hash = line.split("=", 1)[1]
            break
    assert py_hash
    assert rust_hash == py_hash
