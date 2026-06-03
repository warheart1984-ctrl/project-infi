#!/usr/bin/env python3
"""Linguistic diff — mythic/engineering layer evolution for a subsystem gene."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.linguistic_genome_lib import (  # noqa: E402
    LinguisticDiff,
    compute_fingerprints,
    diff_records,
    extract_doc_layers,
    extract_genome_layers,
    extract_source_layers,
    format_diff_markdown,
    genome_linked_paths,
    load_genome,
    load_snapshot,
    list_snapshots,
)


def snapshot_timeline(gene: str, root: Path) -> list[LinguisticDiff]:

    snaps = list_snapshots(gene, root)
    diffs: list[LinguisticDiff] = []
    prev = None
    for sp in snaps:
        cur = load_snapshot(sp)
        if prev:
            d = diff_records(prev, cur)
            if d.changes:
                diffs.append(d)
        prev = cur
    return diffs


def git_timeline(
    gene: str, root: Path, since: str | None
) -> list[LinguisticDiff]:
    paths = genome_linked_paths(gene, root)
    if not paths:
        return []

    cmd = ["git", "log", "--follow", "--format=%H|%ci", "--"]
    if since:
        cmd.insert(-1, f"--since={since}")
    cmd.extend(paths)

    try:
        proc = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []

    if proc.returncode != 0 or not proc.stdout.strip():
        return []

    commits = []
    for line in proc.stdout.strip().splitlines():
        if "|" not in line:
            continue
        h, ts = line.split("|", 1)
        commits.append((h.strip()[:12], ts.strip()))

    diffs: list[LinguisticDiff] = []
    prev_layers: dict | None = None
    prev_fp: str | None = None

    for commit_hash, captured_at in reversed(commits):
        layers = _layers_at_commit(root, paths, commit_hash, gene)
        if not layers:
            continue
        fps = compute_fingerprints(layers)
        if prev_fp and fps.get("combined") == prev_fp:
            continue
        new_snap = {
            "gene": gene,
            "captured_at": captured_at,
            "capture_source": f"git|{commit_hash}",
            "layers": layers,
            "fingerprints": fps,
        }
        if prev_layers is not None:
            old_snap = {
                "gene": gene,
                "capture_source": "git|parent",
                "layers": prev_layers,
                "fingerprints": {"combined": prev_fp or ""},
            }
            d = diff_records(old_snap, new_snap)
            if d.changes:
                diffs.append(d)
        prev_layers = layers
        prev_fp = fps.get("combined")

    return list(reversed(diffs))


def _layers_at_commit(
    root: Path, paths: list[str], commit: str, gene: str
) -> dict | None:
    genome_layer: dict = {"gene": gene}
    source_layer: dict | None = None
    docs_layer: dict = {}

    for rel in paths:
        try:
            proc = subprocess.run(
                ["git", "show", f"{commit}:{rel}"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            continue
        if proc.returncode != 0:
            continue
        text = proc.stdout
        if rel.endswith(".genome.v1.json"):
            try:
                g = json.loads(text)
                genome_layer = extract_genome_layers(g)
            except json.JSONDecodeError:
                pass
        elif rel.endswith(".py") and "src/" in rel:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as tf:
                tf.write(text)
                tf.flush()
                tmp = Path(tf.name)
            source_layer = extract_source_layers(tmp)
            source_layer["path"] = rel
            tmp.unlink(missing_ok=True)
        elif rel.endswith(".md"):
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False, encoding="utf-8"
            ) as tf:
                tf.write(text)
                tf.flush()
                tmp = Path(tf.name)
            doc = extract_doc_layers(tmp)
            tmp.unlink(missing_ok=True)
            if "ideas_pending" in rel or "concept" in rel.lower():
                docs_layer["concept_spec"] = doc
            else:
                docs_layer["active_doc"] = doc

    layers = {"genome": genome_layer}
    if source_layer:
        layers["source"] = source_layer
    if docs_layer:
        layers["docs"] = docs_layer
    return layers if genome_layer.get("engineering_class") or source_layer or docs_layer else layers


def hybrid_timeline(
    gene: str, root: Path, since: str | None, use_git: bool
) -> list:
    snap_diffs = snapshot_timeline(gene, root)
    if not use_git:
        return snap_diffs
    git_diffs = git_timeline(gene, root, since)
    if not snap_diffs:
        return git_diffs
    if not git_diffs:
        return snap_diffs
    seen = {d.captured_at for d in snap_diffs}
    merged = list(snap_diffs)
    for d in git_diffs:
        if d.captured_at not in seen:
            merged.append(d)
    merged.sort(key=lambda x: x.captured_at)
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description="Linguistic diff for a subsystem gene")
    parser.add_argument("--gene", required=True, help="Subsystem gene name")
    parser.add_argument(
        "--git",
        action="store_true",
        help="Include git history (hybrid with snapshots by default)",
    )
    parser.add_argument("--snapshots-only", action="store_true", help="Snapshots only")
    parser.add_argument("--since", help="Git history since date (ISO)")
    parser.add_argument("-o", "--output", help="Write markdown report to file")
    args = parser.parse_args()

    root = _ROOT
    genome = load_genome(args.gene, root)
    if not genome:
        print(f"ERROR: no genome for gene {args.gene!r}", file=sys.stderr)
        return 1

    use_git = args.git or not args.snapshots_only
    if args.snapshots_only:
        use_git = False

    diffs = hybrid_timeline(args.gene, root, args.since, use_git)
    report = format_diff_markdown(diffs, args.gene)

    if args.output:
        out = root / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"linguistic-diff: wrote {out}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
