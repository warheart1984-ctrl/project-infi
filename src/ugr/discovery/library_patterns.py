"""Library reference patterns — match future contributions without rewarding registration."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.ugr.discovery.proof_promotion import load_promotion_policy, policy_path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _matches_regex(pattern: str, haystack: str) -> bool:
    try:
        return bool(re.search(pattern, haystack))
    except re.error:
        return False


def load_library_patterns(policy: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    pol = policy if policy is not None else load_promotion_policy()
    patterns = pol.get("library_patterns") or []
    return [dict(p) for p in patterns if isinstance(p, dict)]


def build_match_haystack(receipt: dict[str, Any], *, repo_root: Path | None = None) -> str:
    """Concatenate receipt fields and proof text for pattern matching."""
    root = repo_root or _repo_root()
    payload = dict(receipt.get("payload") or {})
    parts: list[str] = [
        str(receipt.get("contribution_id") or ""),
        str(receipt.get("contribution_type") or ""),
        str(payload.get("title") or ""),
        str(payload.get("slug") or ""),
        str(payload.get("library_pattern_slug") or ""),
        str(payload.get("canonical_path") or ""),
        str(payload.get("source_document_path") or ""),
        str(payload.get("proof_path") or ""),
    ]
    for key in ("gene", "law_id", "discovery_pod_id"):
        val = payload.get(key)
        if val:
            parts.append(str(val))

    proof_path = str(payload.get("proof_path") or "").strip()
    if proof_path:
        path = Path(proof_path)
        if not path.is_absolute():
            path = root / proof_path
        if path.is_file():
            try:
                parts.append(path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass

    canonical = str(payload.get("canonical_path") or "").strip()
    if canonical:
        path = Path(canonical)
        if not path.is_absolute():
            path = root / canonical
        if path.is_file():
            try:
                parts.append(path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass

    return "\n".join(p for p in parts if p).lower()


def match_library_patterns(
    haystack: str,
    *,
    policy: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return library pattern definitions whose signal thresholds are met."""
    matches: list[dict[str, Any]] = []
    for pattern in load_library_patterns(policy):
        matcher = dict(pattern.get("matcher") or {})
        signals = matcher.get("signals") or []
        min_hits = int(matcher.get("min_signal_hits") or len(signals) or 1)
        hit_ids: list[str] = []
        for signal in signals:
            if not isinstance(signal, dict):
                continue
            regex = str(signal.get("regex") or "").strip()
            if regex and _matches_regex(regex, haystack):
                hit_ids.append(str(signal.get("id") or "signal"))
        if len(hit_ids) >= min_hits:
            matches.append(
                {
                    "pattern_id": str(pattern.get("id") or ""),
                    "title": str(pattern.get("title") or ""),
                    "reference_slug": str(pattern.get("reference_slug") or ""),
                    "signal_hits": hit_ids,
                    "reward_event": str(pattern.get("reward_event") or "library_pattern_matched"),
                }
            )
    return matches


def match_library_patterns_from_receipt(
    receipt: dict[str, Any],
    *,
    policy: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> list[dict[str, Any]]:
    haystack = build_match_haystack(receipt, repo_root=repo_root)
    return match_library_patterns(haystack, policy=policy)


def is_library_reference_contribution(
    receipt: dict[str, Any],
    *,
    policy: dict[str, Any] | None = None,
) -> bool:
    """True when this contribution is a library reference entry (no registration rewards)."""
    payload = dict(receipt.get("payload") or {})
    if payload.get("library_reference") or payload.get("rewards_suppressed"):
        return True
    if str(payload.get("kind") or "").strip().lower() == "library_pattern":
        return True
    slug = str(payload.get("slug") or payload.get("library_pattern_slug") or "").strip()
    if not slug:
        return False
    for pattern in load_library_patterns(policy):
        ref = str(pattern.get("reference_slug") or "").strip()
        if ref and slug == ref:
            return True
    return False


def rewards_suppressed_for_receipt(receipt: dict[str, Any]) -> bool:
    payload = dict(receipt.get("payload") or {})
    return bool(payload.get("rewards_suppressed") or payload.get("library_reference"))
