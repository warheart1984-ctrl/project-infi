from __future__ import annotations

from collections import Counter
from typing import Any


def policy_hash_consensus(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    trusted = [
        summary for summary in summaries
        if summary.get("signature_valid") is True or summary.get("trust_level") in {"trusted", "self"}
    ]
    if trusted:
        summaries = trusted
    hashes = [str(summary.get("policy_hash") or "") for summary in summaries if summary.get("policy_hash")]
    if not hashes:
        return {"consensus_reached": False, "policy_hash": None, "agreement_ratio": 0.0}
    counts = Counter(hashes)
    policy_hash, count = counts.most_common(1)[0]
    return {
        "consensus_reached": count / len(hashes) >= 0.5,
        "policy_hash": policy_hash,
        "agreement_ratio": count / len(hashes),
    }
