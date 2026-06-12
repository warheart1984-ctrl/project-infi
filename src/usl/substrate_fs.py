"""Governed filesystem substrate for Phase 1."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO


def _sha256(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


class GovernedFS:
    """In-memory or path-backed governed FS."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root
        self._memory: dict[str, bytes] = {}
        self._state_hash = (
            "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

    @property
    def state_hash(self) -> str:
        return self._state_hash

    def _normalize_path(self, locator: str) -> str:
        p = locator.replace("\\", "/")
        if self.root:
            return str((self.root / p.lstrip("/")).resolve())
        return p

    def write(self, locator: str, data: bytes, *, mode: str = "create_or_truncate") -> dict:
        """Governed write; returns post-state metadata."""
        path_key = self._normalize_path(locator)
        created = path_key not in self._memory
        if self.root:
            target = Path(path_key)
            target.parent.mkdir(parents=True, exist_ok=True)
            flags = "wb" if mode in ("create", "create_or_truncate", "truncate") else "ab"
            with open(target, flags) as fh:
                fh.write(data)
        else:
            if mode == "append" and path_key in self._memory:
                self._memory[path_key] = self._memory[path_key] + data
            else:
                self._memory[path_key] = bytes(data)

        self._recompute_state()
        return {
            "bytes_written": len(data),
            "objects_created": 1 if created else 0,
            "path": path_key,
            "post_state_hash": self._state_hash,
        }

    def read(self, locator: str) -> bytes:
        path_key = self._normalize_path(locator)
        if self.root:
            return Path(path_key).read_bytes()
        return self._memory.get(path_key, b"")

    def _recompute_state(self) -> None:
        if self.root:
            entries: list[tuple[str, bytes]] = []
            for p in sorted(self.root.rglob("*")):
                if p.is_file():
                    entries.append((str(p), p.read_bytes()))
        else:
            entries = sorted((k, v) for k, v in self._memory.items())
        h = hashlib.sha256()
        for path, content in entries:
            h.update(path.encode("utf-8"))
            h.update(content)
        self._state_hash = f"sha256:{h.hexdigest()}"
