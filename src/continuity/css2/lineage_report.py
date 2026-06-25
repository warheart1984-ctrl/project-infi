"""Threshold lineage reports and chart specs for RA-COS demo."""

from __future__ import annotations

from typing import Any

from src.continuity.css2.threshold_store import ThresholdVersion


def generate_lineage_report(history: list[ThresholdVersion]) -> str:
    if not history:
        return "# No history found.\n"

    th_id = history[0].threshold_id
    lines = [
        "# Threshold Lineage Report",
        "",
        f"**Threshold ID:** {th_id}",
        "",
        "## Version History",
        "",
    ]
    for version in history:
        snap = version.snapshot
        lines.extend(
            [
                f"### Version {version.version}",
                f"- **Timestamp:** {snap.last_updated_at}",
                f"- **Value:** {snap.value!s}",
                f"- **Comparator:** {snap.comparator}",
                f"- **Intent:** {snap.intent}",
                f"- **Rationale:** {version.delta_rationale}",
            ]
        )
        if version.recalibration_event_id:
            lines.append(f"- **Recalibration Event:** {version.recalibration_event_id}")
        lines.append(f"- **Updated By:** {snap.last_updated_by}")
        lines.append("")
    return "\n".join(lines)


def generate_threshold_chart_spec(history: list[ThresholdVersion]) -> dict[str, Any]:
    th_id = history[0].threshold_id if history else "unknown"
    return {
        "type": "line-chart",
        "title": f"Threshold Lineage: {th_id}",
        "xField": "timestamp",
        "yField": "value",
        "points": [
            {
                "version": v.version,
                "timestamp": v.snapshot.last_updated_at,
                "value": v.snapshot.value,
                "rationale": v.delta_rationale,
                "eventId": v.recalibration_event_id,
            }
            for v in history
        ],
    }
