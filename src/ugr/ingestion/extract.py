"""Extract candidate graph signals from normalized ingestion events."""

from __future__ import annotations

import re
from typing import Any


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_./-]{2,}", str(text or ""))
    deduped: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        lowered = token.lower()
        if lowered not in seen:
            seen.add(lowered)
            deduped.append(lowered)
    return deduped[:12]


def extract_signals(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    for event in events:
        event_id = str(event.get("event_id") or "")
        title = str(event.get("title") or "")
        summary = str(event.get("summary") or "")
        source_uri = str(event.get("source_uri") or "")
        terms = _tokenize(f"{title} {summary}")
        subject = title[:120] or (terms[0] if terms else "unknown-subject")
        proposals.append(
            {
                "proposal_id": f"{event_id}-primary",
                "event_id": event_id,
                "source_uri": source_uri,
                "claim": {
                    "subject": subject,
                    "predicate": "mentions_topic",
                    "object": terms[0] if terms else "general",
                    "confidence": 0.62,
                    "source_lane": "ingestion",
                    "status": "proposed",
                    "evidence_refs": [event_id],
                },
                "entities": [{"label": term, "type": "concept"} for term in terms[:6]],
                "relations": [
                    {
                        "from": subject,
                        "relation_type": "references",
                        "to": term,
                        "confidence": 0.55,
                    }
                    for term in terms[1:4]
                ],
            }
        )
        if event.get("source_type") == "github_releases":
            proposals.append(
                {
                    "proposal_id": f"{event_id}-release",
                    "event_id": event_id,
                    "source_uri": source_uri,
                    "claim": {
                        "subject": subject,
                        "predicate": "published_release",
                        "object": str(event.get("title") or "release"),
                        "confidence": 0.74,
                        "source_lane": "ingestion",
                        "status": "proposed",
                        "evidence_refs": [event_id],
                    },
                    "entities": [],
                    "relations": [],
                }
            )
    return proposals
