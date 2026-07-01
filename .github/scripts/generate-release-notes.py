#!/usr/bin/env python3
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run_git(args):
    try:
        out = subprocess.check_output(["git", *args], text=True).strip()
        return out
    except Exception:
        return ""


def load_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def commit_lines(prev_tag: str, target_tag: str):
    if prev_tag:
        rng = f"{prev_tag}..{target_tag}"
    else:
        rng = target_tag
    out = run_git(["log", "--pretty=format:%h %s", rng])
    if not out:
        return []
    return [line for line in out.splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description="Generate CoGOS release notes.")
    parser.add_argument("--target-tag", required=True)
    parser.add_argument("--previous-tag", default="")
    parser.add_argument("--metadata-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print summary without writing release notes.",
    )
    args = parser.parse_args()

    if args.dry_run:
        meta_dir = Path(args.metadata_dir)
        print(
            f"release-notes dry-run: target={args.target_tag} "
            f"previous={args.previous_tag or 'n/a'} metadata={meta_dir} output={args.output}"
        )
        return 0

    meta_dir = Path(args.metadata_dir)
    rc_index = load_json(meta_dir / "rc-index.json")
    state = load_json(meta_dir / "state.json")
    build_meta = load_json(meta_dir / "build-metadata.json")
    nightly = load_json(meta_dir / "nightly-index.json")

    commits = commit_lines(args.previous_tag, args.target_tag)
    run_info = (
        build_meta.get("run")
        or nightly.get("run")
        or rc_index
        or {}
    )

    steps = state.get("steps", [])
    completed = [s for s in steps if s.get("status") == "completed"]
    failed = [s for s in steps if s.get("status") == "failed"]

    artifacts = (
        build_meta.get("artifacts")
        or nightly.get("artifacts")
        or []
    )

    lines = []
    lines.append(f"# CoGOS Release Notes: {args.target_tag}")
    lines.append("")
    lines.append("## Build Metadata")
    lines.append(f"- Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"- Target tag: `{args.target_tag}`")
    lines.append(f"- Previous tag: `{args.previous_tag or 'n/a'}`")
    lines.append(f"- CoGOS tag: `{run_info.get('cogos_tag', 'unknown')}`")
    lines.append(f"- Commit SHA: `{run_info.get('sha', 'unknown')}`")
    lines.append(f"- Run ID: `{run_info.get('run_id', 'unknown')}`")
    lines.append("")
    lines.append("## Installer Validation")
    lines.append(f"- Steps completed: `{len(completed)}`")
    lines.append(f"- Steps failed: `{len(failed)}`")
    if failed:
        lines.append("- Failed steps:")
        for step in failed:
            lines.append(f"  - `{step.get('name', 'unknown')}`: {step.get('error', 'no error payload')}")
    lines.append("")
    lines.append("## Commit Summary")
    if commits:
        for c in commits[:200]:
            lines.append(f"- {c}")
    else:
        lines.append("- No commits discovered in selected range.")
    lines.append("")
    lines.append("## Artifact Manifest")
    if artifacts:
        for art in artifacts:
            name = art.get("name", "unknown")
            size = art.get("size_bytes", "n/a")
            sha = art.get("sha256", "n/a")
            lines.append(f"- `{name}` size=`{size}` sha256=`{sha}`")
    else:
        lines.append("- No artifact manifest entries available.")
    lines.append("")

    Path(args.output).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
