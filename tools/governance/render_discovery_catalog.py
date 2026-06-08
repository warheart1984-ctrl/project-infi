"""Render discovery document catalog table from manifest."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "docs" / "proof" / "discovery" / "DISCOVERY_DOCUMENT_MANIFEST.json"
OUT = REPO_ROOT / "docs" / "proof" / "discovery" / "_catalog_table.md"


def _standing_cell(doc: dict) -> str:
    standing = doc.get("standing")
    label = str(doc.get("claim_label") or "asserted")
    if standing is None:
        from src.ugr.discovery.standing import standing_from_label

        standing = int(standing_from_label(label))
    admitted = doc.get("library_admitted")
    if admitted is False:
        return f"{standing} `{label}` (excluded)"
    return f"{standing} `{label}`"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    lines = ["| Title | Standing | Claim | Proof packet |", "|---|---|---|---|"]
    for doc in manifest["documents"]:
        title = doc["title"].replace("|", "/")
        if len(title) > 72:
            title = title[:69] + "..."
        if doc.get("duplicate_of"):
            title += " (dup)"
        if doc.get("canonical"):
            title += " **canonical**"
        lines.append(
            f"| {title} | {_standing_cell(doc)} | {doc['claim_label']} | `{doc['proof_path']}` |"
        )
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(lines) - 2} rows)")


if __name__ == "__main__":
    main()
