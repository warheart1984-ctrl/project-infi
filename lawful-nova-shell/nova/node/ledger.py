from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def runtime_dir() -> Path:
    return Path(os.environ.get("NOVA_NODE_RUNTIME_DIR", ".runtime/node"))


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def append_jsonl(path: Path, entry: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(stable_json(entry) + "\n")
    return entry


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def governance_ledger_path() -> Path:
    return runtime_dir() / "governance-ledger.jsonl"


def append_ledger(entry: dict[str, Any]) -> dict[str, Any]:
    return append_jsonl(governance_ledger_path(), entry)


def read_ledger() -> list[dict[str, Any]]:
    return read_jsonl(governance_ledger_path())
