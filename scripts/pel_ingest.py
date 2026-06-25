#!/usr/bin/env python3
"""
pel_ingest.py

Normalize artifacts and write canonical PEL records into data/pel.sqlite3.

Usage:
  python scripts/pel_ingest.py --file docs/governance/charter.md --type artifact --author jon
  python scripts/pel_ingest.py --dir docs/ --type artifact --author jon
  python scripts/pel_ingest.py --jsonl data/continuity_export.jsonl --type execution --author system
  python scripts/pel_ingest.py --url https://example.com/policy --type artifact --author jon
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.cori.pel.normalize import (  # noqa: E402
    normalize_continuity_row,
    normalize_file,
    normalize_jsonl_row,
    normalize_panel_row,
    normalize_url,
)
from src.cori.pel.store import (  # noqa: E402
    build_pel_record,
    ensure_db,
    upsert_pel_record,
)
from src.cori.store_paths import pel_store_path  # noqa: E402


def _parse_links(raw: str | None) -> list[dict[str, str]]:
    if not raw:
        return []
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError("--links must be a JSON array")
    return [dict(item) for item in parsed]


def _ingest_normalized(
    conn,
    *,
    norm: dict[str, Any],
    type_: str,
    author: str,
    steward_role: str | None,
    description: str | None,
    links: list[dict[str, str]],
    evidence_strength: str,
    created_at: str | None,
    skip_duplicates: bool,
) -> dict[str, Any]:
    record = build_pel_record(
        type_=type_,
        author=author,
        norm=norm,
        steward_role=steward_role,
        description=description,
        links=links,
        evidence_strength=evidence_strength,
        created_at=created_at,
    )
    stored, inserted = upsert_pel_record(conn, record, skip_duplicates=skip_duplicates)
    stored["_inserted"] = inserted
    return stored


def ingest_file(
    conn,
    path: Path,
    *,
    type_: str,
    author: str,
    steward_role: str | None,
    description: str | None,
    links: list[dict[str, str]],
    evidence_strength: str,
    skip_duplicates: bool,
) -> dict[str, Any]:
    norm = normalize_file(path)
    return _ingest_normalized(
        conn,
        norm=norm,
        type_=type_,
        author=author,
        steward_role=steward_role,
        description=description or f"File ingested from {path}",
        links=links,
        evidence_strength=evidence_strength,
        created_at=None,
        skip_duplicates=skip_duplicates,
    )


def ingest_url(
    conn,
    url: str,
    *,
    type_: str,
    author: str,
    steward_role: str | None,
    description: str | None,
    links: list[dict[str, str]],
    evidence_strength: str,
    skip_duplicates: bool,
    title: str | None,
) -> dict[str, Any]:
    norm = normalize_url(url, title=title)
    return _ingest_normalized(
        conn,
        norm=norm,
        type_=type_,
        author=author,
        steward_role=steward_role,
        description=description or f"URL ingested: {url}",
        links=links,
        evidence_strength=evidence_strength,
        created_at=None,
        skip_duplicates=skip_duplicates,
    )


def _row_normalizer(type_: str):
    if type_ == "panel":
        return normalize_panel_row
    if type_ in {"execution", "validation"}:
        return normalize_continuity_row
    return normalize_jsonl_row


def ingest_jsonl(
    conn,
    jsonl_path: Path,
    *,
    type_: str,
    author: str,
    steward_role: str | None,
    evidence_strength: str,
    skip_duplicates: bool,
) -> list[dict[str, Any]]:
    normalize = _row_normalizer(type_)
    created: list[dict[str, Any]] = []
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"line {line_no}: expected JSON object")
            norm = normalize(row)
            record = _ingest_normalized(
                conn,
                norm=norm,
                type_=type_,
                author=author,
                steward_role=steward_role,
                description=f"JSONL row ingested from {jsonl_path}:{line_no}",
                links=row.get("links") or [],
                evidence_strength=evidence_strength,
                created_at=row.get("created_at"),
                skip_duplicates=skip_duplicates,
            )
            created.append(record)
    return created


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PEL ingest utility")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=str, help="Single file to ingest")
    group.add_argument("--dir", type=str, help="Directory to ingest recursively")
    group.add_argument("--jsonl", type=str, help="JSONL file with exported rows to ingest")
    group.add_argument("--url", type=str, help="URL artifact to ingest (metadata hash)")
    parser.add_argument("--type", required=True, help="PEL record type")
    parser.add_argument("--author", required=True, help="Author/steward id")
    parser.add_argument("--steward-role", default=None, help="steward role")
    parser.add_argument(
        "--evidence-strength",
        default="primary",
        choices=["primary", "secondary", "inferred"],
    )
    parser.add_argument("--description", default=None)
    parser.add_argument("--title", default=None, help="Optional title for --url ingest")
    parser.add_argument("--links", default=None, help='JSON array of links [{"relation":"supports","target_id":"PEL-..."}]')
    parser.add_argument("--db", default=None, help="Override PEL sqlite path")
    parser.add_argument("--force", action="store_true", help="Insert even when hash already exists")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    db_path = Path(args.db).expanduser() if args.db else pel_store_path()
    conn = ensure_db(db_path)
    links = _parse_links(args.links)
    skip_duplicates = not args.force

    try:
        if args.file:
            path = Path(args.file)
            if not path.is_file():
                print(f"File not found: {path}", file=sys.stderr)
                return 2
            rec = ingest_file(
                conn,
                path,
                type_=args.type,
                author=args.author,
                steward_role=args.steward_role,
                description=args.description,
                links=links,
                evidence_strength=args.evidence_strength,
                skip_duplicates=skip_duplicates,
            )
            conn.commit()
            print(json.dumps(rec, indent=2, default=str))
            return 0

        if args.url:
            rec = ingest_url(
                conn,
                args.url,
                type_=args.type,
                author=args.author,
                steward_role=args.steward_role,
                description=args.description,
                links=links,
                evidence_strength=args.evidence_strength,
                skip_duplicates=skip_duplicates,
                title=args.title,
            )
            conn.commit()
            print(json.dumps(rec, indent=2, default=str))
            return 0

        if args.dir:
            base = Path(args.dir)
            if not base.is_dir():
                print(f"Directory not found: {base}", file=sys.stderr)
                return 2
            created: list[dict[str, Any]] = []
            skipped = 0
            conn.execute("BEGIN")
            for path in sorted(base.rglob("*")):
                if not path.is_file():
                    continue
                try:
                    rec = ingest_file(
                        conn,
                        path,
                        type_=args.type,
                        author=args.author,
                        steward_role=args.steward_role,
                        description=args.description,
                        links=links,
                        evidence_strength=args.evidence_strength,
                        skip_duplicates=skip_duplicates,
                    )
                    if rec.get("_inserted"):
                        created.append(rec)
                    else:
                        skipped += 1
                except OSError as exc:
                    print(f"Skipping {path}: {exc}", file=sys.stderr)
            conn.commit()
            print(json.dumps({"ingested": len(created), "skipped_duplicates": skipped}, indent=2))
            return 0

        if args.jsonl:
            path = Path(args.jsonl)
            if not path.is_file():
                print(f"JSONL not found: {path}", file=sys.stderr)
                return 2
            conn.execute("BEGIN")
            created = ingest_jsonl(
                conn,
                path,
                type_=args.type,
                author=args.author,
                steward_role=args.steward_role,
                evidence_strength=args.evidence_strength,
                skip_duplicates=skip_duplicates,
            )
            conn.commit()
            inserted = sum(1 for row in created if row.get("_inserted"))
            print(json.dumps({"ingested": inserted, "rows_processed": len(created)}, indent=2))
            return 0
    finally:
        conn.close()

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
