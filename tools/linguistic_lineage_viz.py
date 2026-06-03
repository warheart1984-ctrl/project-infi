#!/usr/bin/env python3
"""Subsystem lineage visualization with linguistic labels (Wave 7)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.linguistic_genome_lib import load_json  # noqa: E402
from tools.linguistic_drift_predictor import score_gene  # noqa: E402


def _node_id(gene: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", gene)
    return f"gene_{safe}"


def _label(gene: str, ssp: dict, stage: str, drift_band: str | None) -> str:
    mythic = (ssp.get("mythic_label") or "")[:24]
    eng = (ssp.get("engineering_class") or "")[:28]
    parts = [gene]
    if mythic:
        parts.append(mythic)
    if eng:
        parts.append(eng)
    if drift_band:
        parts.append(f"drift:{drift_band}")
    parts.append(stage)
    return "<br/>".join(parts)


def load_genomes(root: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    gdir = root / "governance" / "subsystem_genomes"
    for path in gdir.glob("*.genome.v1.json"):
        data = load_json(path)
        gene = (data.get("identity") or {}).get("gene")
        if gene:
            out[gene] = data
    return out


def ego_genes(genes: dict[str, dict], center: str, depth: int) -> set[str]:
    if center not in genes:
        return set()
    keep = {center}
    frontier = {center}
    for _ in range(depth):
        nxt: set[str] = set()
        for g in frontier:
            lin = genes[g].get("lineage") or {}
            for p in lin.get("parents") or []:
                if p in genes:
                    nxt.add(p)
            for c in lin.get("children") or []:
                if c in genes:
                    nxt.add(c)
        keep |= nxt
        frontier = nxt
    return keep


def build_mermaid(
    genes: dict[str, dict],
    *,
    include: set[str] | None = None,
    stage: str | None = None,
    batch_id: str | None = None,
    color_drift: bool = False,
    root: Path | None = None,
) -> str:
    root = root or ROOT
    lines = ["flowchart TB", "  legend[Grandfathered *_organ genes use legacy paths]", ""]

    selected = set(genes.keys())
    if include:
        selected &= include
    if stage:
        selected = {
            g
            for g in selected
            if (genes[g].get("identity") or {}).get("stage") == stage
        }
    if batch_id:
        selected = {
            g
            for g in selected
            if (genes[g].get("activation") or {}).get("batch_id") == batch_id
        }

    drift_bands: dict[str, str] = {}
    if color_drift:
        for g in selected:
            drift_bands[g] = score_gene(g, root).band

    for gene in sorted(selected):
        data = genes[gene]
        identity = data.get("identity") or {}
        ssp = data.get("ssp") or {}
        nid = _node_id(gene)
        lbl = _label(gene, ssp, identity.get("stage", ""), drift_bands.get(gene))
        lines.append(f'  {nid}["{lbl}"]')

    lines.append("")
    for gene in sorted(selected):
        data = genes[gene]
        child_id = _node_id(gene)
        for parent in (data.get("lineage") or {}).get("parents") or []:
            if parent not in selected:
                continue
            parent_id = _node_id(parent)
            lines.append(f"  {parent_id} --> {child_id}")

    return "\n".join(lines) + "\n"


def build_json_graph(genes: dict[str, dict], include: set[str] | None = None) -> dict:
    selected = include or set(genes.keys())
    nodes = []
    edges = []
    for gene in sorted(selected):
        if gene not in genes:
            continue
        data = genes[gene]
        ssp = data.get("ssp") or {}
        nodes.append(
            {
                "id": gene,
                "mythic_label": ssp.get("mythic_label"),
                "engineering_class": ssp.get("engineering_class"),
                "stage": (data.get("identity") or {}).get("stage"),
            }
        )
        for parent in (data.get("lineage") or {}).get("parents") or []:
            if parent in selected:
                edges.append({"from": parent, "to": gene})
    return {"nodes": nodes, "edges": edges}


def main() -> int:
    parser = argparse.ArgumentParser(description="Linguistic lineage visualization")
    parser.add_argument("--gene", help="Ego network center gene")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--stage", help="Filter by genome stage")
    parser.add_argument("--batch-id", help="Filter by activation.batch_id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--color-drift", action="store_true")
    parser.add_argument(
        "--cascade-from",
        help="Highlight cascade subtree from parent gene (includes affected children)",
    )
    parser.add_argument("-o", "--output", help="Write markdown with mermaid block")
    args = parser.parse_args()

    root = ROOT
    genes = load_genomes(root)
    include = None
    cascade_note = ""
    if args.cascade_from:
        from src.governance_organs.linguistic_cascade_engine import affected_children

        include = {args.cascade_from}
        for child, _depth in affected_children(args.cascade_from, root):
            include.add(child)
        cascade_note = (
            f"%% cascade subtree from {args.cascade_from} "
            f"({len(include)} nodes)\n"
        )
    elif args.gene:
        include = ego_genes(genes, args.gene, args.depth)

    if args.json:
        print(json.dumps(build_json_graph(genes, include), indent=2))
        return 0

    mermaid = build_mermaid(
        genes,
        include=include,
        stage=args.stage,
        batch_id=args.batch_id,
        color_drift=args.color_drift,
        root=root,
    )

    if args.output:
        out = root / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        title = args.cascade_from or args.gene or "full"
        md = f"# Linguistic lineage graph — `{title}`\n\n{cascade_note}```mermaid\n{mermaid}```\n"
        out.write_text(md, encoding="utf-8")
        print(f"linguistic-lineage-viz: wrote {out}")
    else:
        if cascade_note:
            print(cascade_note, end="")
        print("```mermaid")
        print(mermaid, end="")
        print("```")

    return 0


if __name__ == "__main__":
    sys.exit(main())
