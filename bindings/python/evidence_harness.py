"""Cross-language CAS evidence harness (Python)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from cas import Receipt, Span

# Avoid shadowing the stdlib `hash` module when importing sibling hash.py
_HASH_PATH = Path(__file__).with_name("hash.py")
_spec = importlib.util.spec_from_file_location("aaes_cas_hash", _HASH_PATH)
assert _spec and _spec.loader
_hash_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_hash_mod)
hash_receipt_dict = _hash_mod.hash_receipt_dict

FIXED_TIMESTAMP = 1735689600


def build_sample_receipt() -> Receipt:
    span = Span(
        id="span-1",
        run_id="run-1",
        type="execute",
        timestamp=FIXED_TIMESTAMP,
    )
    return Receipt(
        run_id="run-1",
        hash="",
        spans=[span],
        result={"echo": "hello"},
        created_at="2025-01-01T00:00:00Z",
    )


def main_from_rust_json(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        receipt = json.load(f)
    return hash_receipt_dict(receipt)


if __name__ == "__main__":
    py_hash = main_from_rust_json(sys.argv[1])
    print(f"PY_HASH={py_hash}", file=sys.stderr)
