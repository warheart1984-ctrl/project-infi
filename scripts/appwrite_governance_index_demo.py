"""Index AAIS governance contracts into Appwrite Tables (optional cloud projection).

Complements scripts/tpuf_governance_search_demo.py:
  - Turbopuffer = BM25 / vector retrieval for agents
  - Appwrite    = durable table store for operator dashboards & mobile clients

Requires: AAIS_APPWRITE_SINK=1 and APPWRITE_* credentials (see deploy/appwrite/.env.example).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.appwrite_governance_sink import (  # noqa: E402
    appwrite_sink_enabled,
    contract_rows_from_paths,
    upsert_governance_contracts,
)

TARGET_FILES = [
    "docs/contracts/MEMORY_VECTOR_BACKEND_ADMISSION.md",
    "docs/contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md",
    "docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md",
    "docs/contracts/AAIS_ADAPTIVE_GOVERNANCE.md",
    "docs/contracts/NARRATIVE_CONTINUITY_CONTRACT.md",
    "docs/contracts/IDENTITY_SELF_MODEL_CONTRACT.md",
]

DEMO_QUERY = "Where does constitutional truth live vs optional cloud projections?"


def main() -> int:
    rows = contract_rows_from_paths(TARGET_FILES, root=str(ROOT))
    print(f"Prepared {len(rows)} governance contract rows from project-infi.")

    if not appwrite_sink_enabled():
        print("\nAppwrite sink is OFF. Set AAIS_APPWRITE_SINK=1 and APPWRITE_* vars.")
        print("See deploy/appwrite/README.md for table setup and .env.example.")
        print("\nWould index:")
        for row in rows:
            print(f"  - {row['path']} ({len(row['content'])} chars)")
        print(f"\nDemo query for operators: {DEMO_QUERY!r}")
        return 0

    result = upsert_governance_contracts(rows)
    print(f"\nAppwrite upsert complete: {result}")
    print(f"Query your Appwrite console or SDK for doc_type=contract and path filters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
