"""CRK-T1 boundary — no extra first-class kernel objects."""

from __future__ import annotations

import json
from pathlib import Path

from src.continuity.crk1_compliance import CANONICAL_OBJECTS, check_objects

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "fixtures" / "continuity"


def test_five_canonical_object_schemas_present() -> None:
    missing, extra = check_objects()
    assert not missing, f"missing kernel objects: {missing}"
    assert not extra, f"extra kernel objects: {extra}"


def test_schema_titles_match_canonical_set() -> None:
    titles: set[str] = set()
    for path in SCHEMA_DIR.glob("*.schema.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        title = str(payload.get("title") or "")
        if title == "EvidenceRecord":
            title = "EvidenceObject"
        if title.endswith("Object"):
            titles.add(title)
    assert CANONICAL_OBJECTS.issubset(titles)
