"""Build correlation edges across normalized forensic claims."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from triangulation.common import (
    BRIDGE_MAP_PATH,
    DEFAULT_MECHANIC_ROOT,
    DEFAULT_SCORPION_ROOT,
    DEFAULT_SLINGSHOT_ROOT,
    DEFAULT_TRIANGULATION_ROOT,
    correlation_ledger_path,
    source_ref,
    triangulation_artifact_path,
    triangulation_case_dir,
)
from triangulation.normalize import (
    normalize_mechanic_claims,
    normalize_scorpion_claims,
    normalize_slingshot_claims,
)

TRIANGULATION_VERSION = "triangulation.v1"
TEMPORAL_WINDOW_SECONDS = 3600


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _load_bridge_map(path: Path | None = None) -> dict[str, list[str]]:
    bridge_path = path or BRIDGE_MAP_PATH
    if not bridge_path.is_file():
        return {}
    payload = json.loads(bridge_path.read_text(encoding="utf-8"))
    mapping: dict[str, list[str]] = {}
    for entry in payload.get("bridges") or []:
        mechanic_id = str(entry.get("mechanic_invariant_id") or "").strip()
        scorpion_ids = [str(x) for x in (entry.get("scorpion_invariant_ids") or [])]
        if mechanic_id and scorpion_ids:
            mapping[mechanic_id] = scorpion_ids
    return mapping


def _claim_index(claims: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for claim in claims:
        key = (str(claim["source"]), str(claim["claim_id"]))
        index[key] = claim
    return index


def build_temporal_edges(
    claims: list[dict[str, Any]],
    *,
    window_seconds: int = TEMPORAL_WINDOW_SECONDS,
) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    sorted_claims = sorted(
        claims,
        key=lambda c: _parse_ts(c.get("recorded_at_utc")) or datetime.min.replace(tzinfo=timezone.utc),
    )
    for i, left in enumerate(sorted_claims):
        left_ts = _parse_ts(left.get("recorded_at_utc"))
        if left_ts is None:
            continue
        for right in sorted_claims[i + 1 :]:
            if left.get("source") == right.get("source"):
                continue
            right_ts = _parse_ts(right.get("recorded_at_utc"))
            if right_ts is None:
                continue
            delta = abs((right_ts - left_ts).total_seconds())
            if delta > window_seconds:
                break
            edges.append(
                {
                    "edge_id": f"te-{uuid.uuid4().hex[:12]}",
                    "source_a": left["source"],
                    "claim_id_a": left["claim_id"],
                    "source_b": right["source"],
                    "claim_id_b": right["claim_id"],
                    "correlation_type": "temporal",
                    "rationale": f"same case_id, delta_t={int(delta)}s",
                    "claim_label": "asserted",
                }
            )
    return edges


def build_invariant_overlap_edges(
    claims: list[dict[str, Any]],
    *,
    bridge_map: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    bridge = bridge_map or _load_bridge_map()
    mechanic = [c for c in claims if c.get("source") == "mechanic"]
    scorpion = [c for c in claims if c.get("source") == "scorpion"]
    edges: list[dict[str, Any]] = []

    for left in mechanic:
        left_inv = str(left.get("invariant_id") or "")
        for right in scorpion:
            right_inv = str(right.get("invariant_id") or "")
            exact = left_inv and left_inv == right_inv
            bridged = right_inv in (bridge.get(left_inv) or [])
            if not exact and not bridged:
                continue
            edges.append(
                {
                    "edge_id": f"ie-{uuid.uuid4().hex[:12]}",
                    "source_a": "mechanic",
                    "claim_id_a": left["claim_id"],
                    "source_b": "scorpion",
                    "claim_id_b": right["claim_id"],
                    "correlation_type": "invariant_overlap",
                    "rationale": (
                        f"exact match on {left_inv}"
                        if exact
                        else f"bridge map {left_inv} -> {right_inv}"
                    )[:500],
                    "claim_label": "proven" if bridged else "asserted",
                }
            )
    return edges


def correlate_case(
    case_id: str,
    *,
    mechanic_root: Path | None = None,
    scorpion_root: Path | None = None,
    slingshot_root: Path | None = None,
    triangulation_root: Path | None = None,
    fixture_root: Path | None = None,
) -> dict[str, Any]:
    mech_root = (mechanic_root or DEFAULT_MECHANIC_ROOT).expanduser().resolve()
    scorp_root = (scorpion_root or DEFAULT_SCORPION_ROOT).expanduser().resolve()
    shot_root = (slingshot_root or DEFAULT_SLINGSHOT_ROOT).expanduser().resolve()
    tri_root = (triangulation_root or DEFAULT_TRIANGULATION_ROOT).expanduser().resolve()

    if fixture_root:
        fix = fixture_root.expanduser().resolve()
        mech_ledger = fix / "mechanic_diagnostic_ledger.jsonl"
        scorp_ledger = fix / "scorpion_anomaly_ledger.jsonl"
        shot_frame = fix / "SLINGSHOT_FRAME.v1.json"
        shot_ledger = fix / "slingshot_ledger.jsonl"
    else:
        mech_ledger = mech_root / "diagnostic_ledger.jsonl"
        if not mech_ledger.is_file():
            mech_ledger = mech_root / case_id / "diagnostic_ledger.jsonl"
        scorp_ledger = scorp_root / "anomaly_ledger.jsonl"
        shot_frame = shot_root / case_id / "SLINGSHOT_FRAME.v1.json"
        shot_ledger = shot_root / case_id / "slingshot_ledger.jsonl"

    claims: list[dict[str, Any]] = []
    claims.extend(normalize_mechanic_claims(ledger_path=mech_ledger, case_id=case_id))
    claims.extend(normalize_scorpion_claims(ledger_path=scorp_ledger, case_id=case_id))
    slingshot_claims = normalize_slingshot_claims(
        frame_path=shot_frame,
        ledger_path=shot_ledger if shot_ledger.is_file() else None,
        case_id=case_id,
    )
    claims.extend(slingshot_claims)

    sources = {
        "mechanic": source_ref(mech_ledger, present=mech_ledger.is_file()),
        "scorpion": source_ref(scorp_ledger, present=scorp_ledger.is_file()),
        "slingshot": source_ref(shot_frame, present=shot_frame.is_file()),
    }

    edges = build_temporal_edges(claims)
    edges.extend(build_invariant_overlap_edges(claims))

    launch_blocked = any(c.get("launch_blocked") for c in slingshot_claims)
    missing_sources = [name for name, ref in sources.items() if not ref.get("present")]
    overall_label = "asserted"
    if any(edge.get("claim_label") == "proven" for edge in edges):
        overall_label = "proven" if not missing_sources else "asserted"
    elif missing_sources:
        overall_label = "asserted"

    now = _utc_now_iso()
    payload = {
        "triangulation_version": TRIANGULATION_VERSION,
        "case_id": case_id,
        "sources": sources,
        "claims": claims,
        "correlation_edges": edges,
        "cisiv_stage": "implementation",
        "claim_label": overall_label,
        "summary": (
            f"{len(claims)} claims, {len(edges)} edges"
            + (f"; launch_blocked={launch_blocked}" if launch_blocked else "")
            + (f"; missing={','.join(missing_sources)}" if missing_sources else "")
        )[:500],
        "created_at_utc": now,
        "updated_at_utc": now,
        "launch_blocked": launch_blocked,
    }

    out_dir = triangulation_case_dir(case_id, runtime_root=tri_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact = triangulation_artifact_path(case_id, runtime_root=tri_root)
    artifact.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    ledger_path = correlation_ledger_path(case_id, runtime_root=tri_root)
    with ledger_path.open("a", encoding="utf-8") as handle:
        for edge in edges:
            handle.write(json.dumps(edge, sort_keys=True) + "\n")

    return payload


def load_triangulation(case_id: str, *, runtime_root: Path | None = None) -> dict[str, Any]:
    path = triangulation_artifact_path(case_id, runtime_root=runtime_root)
    if not path.is_file():
        raise FileNotFoundError(f"triangulation artifact not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
