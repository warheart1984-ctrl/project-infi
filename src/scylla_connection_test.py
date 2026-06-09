"""Minimal ScyllaDB Cloud connectivity smoke test."""

from __future__ import annotations

import sys

from src.memory_vector_store import scylla_configured, scylla_session


def main() -> int:
    if not scylla_configured():
        print("ScyllaDB is not configured. Set SCYLLA_CONTACT_POINTS and SCYLLA_LOCAL_DC.")
        return 1
    try:
        session = scylla_session()
        row = session.execute("SELECT release_version FROM system.local").one()
        print(f"Connected. ScyllaDB release: {row.release_version}")
        return 0
    except Exception as exc:
        print(f"Connection failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
