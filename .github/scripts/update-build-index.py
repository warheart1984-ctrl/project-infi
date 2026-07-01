#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def main():
    parser = argparse.ArgumentParser(description="Update CoGOS build index JSON files.")
    parser.add_argument("--index", required=True)
    parser.add_argument("--stable", required=True)
    parser.add_argument("--latest", required=True)
    parser.add_argument("--entry-json", required=True)
    parser.add_argument("--channel", required=True, choices=["nightly", "rc", "stable"])
    parser.add_argument("--max-entries", type=int, default=200)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate entry JSON and print planned update without writing index files.",
    )
    args = parser.parse_args()

    index_path = Path(args.index)
    stable_path = Path(args.stable)
    latest_path = Path(args.latest)
    entry_path = Path(args.entry_json)

    entry = load(entry_path, {})
    if not entry:
        raise SystemExit(f"Entry JSON is empty or invalid: {entry_path}")

    if args.dry_run:
        print(
            f"build-index dry-run: channel={args.channel} index={index_path} "
            f"stable={stable_path} latest={latest_path} entry={entry_path.name}"
        )
        return 0

    run = entry.get("run", {})
    run["channel"] = args.channel
    run["updated_at"] = datetime.now(timezone.utc).isoformat()
    entry["run"] = run

    index = load(index_path, {"builds": []})
    builds = index.get("builds", [])
    builds.insert(0, entry)
    index["builds"] = builds[: args.max_entries]
    index["updated_at"] = datetime.now(timezone.utc).isoformat()

    index_path.parent.mkdir(parents=True, exist_ok=True)
    stable_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.parent.mkdir(parents=True, exist_ok=True)

    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    latest_path.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    if args.channel == "stable":
        stable_path.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
