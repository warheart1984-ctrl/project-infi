"""Build exportable invariant bundles for mesh gossip."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.mesh.invariants import InvariantStore
from src.reasoning_exchange_protocol import ADMIT_CONFIDENCE_THRESHOLD

_EXPORT_REL = Path("deploy") / "mesh" / "invariants.export.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_export_overrides() -> dict:
    path = _project_root() / _EXPORT_REL
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def build_export_bundle(base_dir: str | Path | None = None) -> dict:
    """Compose peer-facing invariant bundle from protocol thresholds + deploy overrides."""
    store = InvariantStore(base_dir)
    bundle = store.load()
    overrides = _load_export_overrides()

    rules = {r["id"]: r for r in bundle.get("rules", []) if r.get("id")}
    rules.setdefault(
        "min_confidence",
        {
            "id": "min_confidence",
            "value": ADMIT_CONFIDENCE_THRESHOLD,
            "description": "Minimum confidence for ADMIT (from ReasoningExchangeProtocol)",
        },
    )
    rules["min_confidence"]["value"] = float(
        overrides.get("min_confidence", ADMIT_CONFIDENCE_THRESHOLD)
    )

    for rule in overrides.get("rules") or []:
        rid = rule.get("id")
        if not rid:
            continue
        existing = rules.get(rid, {"id": rid})
        existing.update(rule)
        rules[rid] = existing

    export = {
        "version": str(overrides.get("version") or bundle.get("version") or "1.0"),
        "bundle_id": str(overrides.get("bundle_id") or bundle.get("bundle_id") or "aais-mesh-export"),
        "rules": sorted(rules.values(), key=lambda r: r.get("id", "")),
        "updated_at": _utc_now(),
        "source": "aais",
    }
    store.save(export)
    return export
