"""Forge substrate classification engine (registry v2)."""
from __future__ import annotations

import fnmatch
from typing import Any


def glob_match(path: str, pattern: str) -> bool:
    return fnmatch.fnmatch(path, pattern)


def resolve_spec(registry: dict[str, Any], substrate_id: str) -> tuple[str, dict[str, Any]]:
    substrates = registry.get("substrates", {})
    if substrate_id == "auto":
        substrate_id = registry.get("default_substrate_id", "generic-live-squashfs")
    spec = dict(substrates.get(substrate_id, {}))
    parent = spec.get("extends")
    if parent and parent in substrates:
        merged = dict(substrates[parent])
        detect = merged.setdefault("detect", {"path_globs": [], "path_any": [], "path_markers": []})
        child_detect = spec.get("detect", {"path_globs": [], "path_any": [], "path_markers": []})
        for key in ("path_globs", "path_any", "path_markers"):
            detect[key] = list(dict.fromkeys(detect.get(key, []) + child_detect.get(key, [])))
        merged.update({k: v for k, v in spec.items() if k != "detect"})
        merged["detect"] = detect
        spec = merged
    return substrate_id, spec


def _match_detect(detect: dict[str, Any], paths: set[str]) -> dict[str, int]:
    glob_hits = sum(
        1 for pattern in detect.get("path_globs", []) if any(glob_match(path, pattern) for path in paths)
    )
    any_hits = sum(1 for needle in detect.get("path_any", []) if any(needle in path for path in paths))
    marker_hits = sum(1 for marker in detect.get("path_markers", []) if marker in paths)
    specificity = sum(
        len(pattern.split("/"))
        for pattern in detect.get("path_globs", [])
        if any(glob_match(path, pattern) for path in paths)
    )
    return {
        "glob_hits": glob_hits,
        "any_hits": any_hits,
        "marker_hits": marker_hits,
        "specificity": specificity,
    }


def score_substrate(substrate_id: str, spec: dict[str, Any], paths: set[str]) -> dict[str, Any] | None:
    detect = spec.get("detect", {})
    hits = _match_detect(detect, paths)
    glob_hits = hits["glob_hits"]
    any_hits = hits["any_hits"]
    marker_hits = hits["marker_hits"]
    if glob_hits == 0 and any_hits == 0 and marker_hits == 0:
        return None
    priority = int(spec.get("priority", 0))
    score = glob_hits * 100 + any_hits * 10 + marker_hits * 5 + priority + hits["specificity"]
    return {
        "substrate_id": substrate_id,
        "score": score,
        "priority": priority,
        "class": spec.get("class", ""),
        "family": spec.get("family", ""),
        "replay_adapter": spec.get("replay_adapter", ""),
        "contract_version": spec.get("contract_version", registry_contract_version({})),
        **hits,
    }


def registry_contract_version(registry: dict[str, Any]) -> str:
    version = registry.get("registry_version", "")
    if version == "substrate-registry.v2":
        return registry.get("default_contract_version", "forge-substrate.v2")
    return "forge-substrate.v1"


def classify_substrates(registry: dict[str, Any], paths: set[str]) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for substrate_id in registry.get("substrates", {}):
        effective_id, spec = resolve_spec(registry, substrate_id)
        row = score_substrate(effective_id, spec, paths)
        if row:
            ranked.append(row)
    ranked.sort(key=lambda row: (-row["score"], -row["priority"], row["substrate_id"]))
    return ranked


def classify_with_confidence(registry: dict[str, Any], paths: set[str]) -> dict[str, Any]:
    ranked = classify_substrates(registry, paths)
    if not ranked:
        fallback = registry.get("default_substrate_id", "generic-live-squashfs")
        return {
            "substrate_id": fallback,
            "confidence": 0.0,
            "method": "fallback-default",
            "candidates": [],
        }
    best = ranked[0]
    runner_up_score = ranked[1]["score"] if len(ranked) > 1 else 0
    if best["score"] <= 0:
        confidence = 0.0
    elif runner_up_score <= 0:
        confidence = 1.0
    else:
        confidence = round((best["score"] - runner_up_score) / max(best["score"], 1), 4)
    return {
        "substrate_id": best["substrate_id"],
        "confidence": confidence,
        "method": "weighted-detect-v2",
        "candidates": ranked[:5],
    }


def detect_substrate(registry: dict[str, Any], paths: set[str]) -> str:
    return classify_with_confidence(registry, paths)["substrate_id"]
