#!/usr/bin/env python3
"""Linguistic drift risk predictor (Wave 8)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.linguistic_genome_lib import (  # noqa: E402
    build_linguistic_record,
    extract_doc_layers,
    extract_source_layers,
    is_grandfathered_gene,
    list_all_genes,
    list_snapshots,
    load_genome,
    load_json,
)


@dataclass
class DriftScore:
    gene: str
    drift_risk: int
    band: str
    signals: dict[str, float] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


def _band(score: int) -> str:
    if score >= 67:
        return "high"
    if score >= 34:
        return "medium"
    return "low"


def _alignment_gap(gene: str, root: Path) -> float:
    genome = load_genome(gene, root)
    if not genome:
        return 0.0
    ssp = genome.get("ssp") or {}
    eng = ssp.get("engineering_class", "")
    gap = 0.0
    module = ""
    for entry in (genome.get("runtime") or {}).get("surface") or []:
        if isinstance(entry, dict) and entry.get("kind") == "module":
            module = entry.get("path") or ""
            break
    if module:
        src = extract_source_layers(root / module)
        header_eng = (src.get("header") or {}).get("engineering", "")
        if not header_eng:
            gap += 40
        elif header_eng != eng:
            gap += 60
    cs = (genome.get("ssp") or {}).get("concept_spec")
    if cs:
        doc = extract_doc_layers(root / cs)
        doc_eng = doc.get("engineering_class", "")
        if doc_eng and doc_eng != eng:
            gap += 30
    return min(gap, 100.0)


def _snapshot_velocity(gene: str, root: Path, days: int = 30) -> float:
    snaps = list_snapshots(gene, root)
    if len(snaps) <= 1:
        return 0.0
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = 0
    for sp in snaps:
        data = load_json(sp)
        ts = data.get("captured_at", "")
        try:
            when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        if when >= cutoff:
            recent += 1
    return min(recent * 15.0, 100.0)


def _layer_skew(record_layers: dict) -> float:
    fps = record_layers.get("fingerprints") if isinstance(record_layers, dict) else None
    if not fps:
        return 0.0
    mythic = fps.get("mythic", "")
    eng = fps.get("engineering", "")
    if not mythic or not eng:
        return 20.0
    if mythic == eng:
        return 80.0
    return 0.0


def _gene_mythic_tokens(gene: str) -> float:
    if is_grandfathered_gene(gene):
        return 0.0
    tokens = {"summon", "wave", "fabric", "organ"}
    hits = sum(1 for t in gene.split("_") if t in tokens)
    return min(hits * 25.0, 100.0)


def _lineage_fanout(gene: str, root: Path) -> float:
    genome = load_genome(gene, root)
    if not genome:
        return 0.0
    children = (genome.get("lineage") or {}).get("children") or []
    n = len(children)
    if n >= 8:
        return 100.0
    if n >= 4:
        return 60.0
    if n >= 2:
        return 30.0
    return 0.0


def score_gene(gene: str, root: Path | None = None) -> DriftScore:
    root = root or ROOT
    record = build_linguistic_record(gene, root)
    layers = record.layers if record else {}
    fps = record.fingerprints if record else {}

    signals = {
        "alignment_gap": _alignment_gap(gene, root),
        "snapshot_velocity": _snapshot_velocity(gene, root),
        "layer_skew": _layer_skew({"fingerprints": fps}),
        "gene_mythic_tokens": _gene_mythic_tokens(gene),
        "lineage_fanout": _lineage_fanout(gene, root),
    }
    weights = {
        "alignment_gap": 0.35,
        "snapshot_velocity": 0.15,
        "layer_skew": 0.20,
        "gene_mythic_tokens": 0.15,
        "lineage_fanout": 0.15,
    }
    drift_risk = int(
        round(sum(signals[k] * weights[k] for k in weights))
    )
    drift_risk = max(0, min(100, drift_risk))
    recs: list[str] = []
    if signals["alignment_gap"] >= 40:
        recs.append("Wave 2: add source # Engineering: header aligned with genome ssp")
    if signals["snapshot_velocity"] >= 30:
        recs.append("Review recent MP-LING proposals; stabilize linguistic_version")
    if signals["gene_mythic_tokens"] > 0:
        recs.append("Rename gene at next MP-X or use engineering stem for new admissions")
    if drift_risk >= 67:
        recs.append("Run mythic_engineering_translator and plan MP-LING mutation")

    return DriftScore(
        gene=gene,
        drift_risk=drift_risk,
        band=_band(drift_risk),
        signals=signals,
        recommendations=recs,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Linguistic drift predictor")
    parser.add_argument("--gene", help="Score single gene")
    parser.add_argument("--top", type=int, default=20, help="Top N at-risk genes")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-o", "--output", help="Write JSON report path")
    parser.add_argument(
        "--fail-on-high",
        action="store_true",
        help="Exit 1 if any scored gene is high drift",
    )
    args = parser.parse_args()

    root = ROOT
    genes = [args.gene] if args.gene else list_all_genes(root)
    scores = [score_gene(g, root) for g in genes]
    scores.sort(key=lambda s: s.drift_risk, reverse=True)

    if args.gene and not args.json:
        s = scores[0]
        print(f"gene: {s.gene}")
        print(f"drift_risk: {s.drift_risk} ({s.band})")
        print("signals:", json.dumps(s.signals, indent=2))
        for r in s.recommendations:
            print(f"  - {r}")
    elif args.json or args.output:
        payload = {
            "linguistic_drift_report_version": "linguistic_drift_report.v1",
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "scores": [asdict(s) for s in scores],
        }
        text = json.dumps(payload, indent=2) + "\n"
        if args.output:
            out = root / args.output
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
            print(f"linguistic-drift: wrote {out}")
        else:
            print(text)
    else:
        print(f"{'gene':<40} {'risk':>4}  band")
        print("-" * 56)
        for s in scores[: args.top]:
            print(f"{s.gene:<40} {s.drift_risk:>4}  {s.band}")

    if args.fail_on_high and any(s.band == "high" for s in scores):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
