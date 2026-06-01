"""OBD-style reports for AI platform teams."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from mechanic.hosted.models import ConfidenceLabel, SignoffPolicy

FAMILY_LABELS = {
    "GOV": "governance",
    "RNT": "runtime",
    "CST": "cost",
    "HUM": "human_control",
}


def risk_class(drift: dict[str, Any]) -> str:
    severity = str(drift.get("severity") or "").lower()
    ma13 = str(drift.get("ma13_class") or "").upper()
    if severity == "critical" or ma13 == "III":
        return "red"
    if severity == "high" or ma13 == "II":
        return "amber"
    if severity == "medium":
        return "yellow"
    return "green"


def affected_workflow(drift: dict[str, Any]) -> str:
    evidence = drift.get("evidence") or {}
    return str(
        evidence.get("source_path")
        or evidence.get("workflow")
        or evidence.get("node_id")
        or evidence.get("path")
        or "unknown"
    )


def likely_owner(drift: dict[str, Any]) -> str:
    family = str(drift.get("family") or "").upper()
    if family == "CST":
        return "AI platform cost owner"
    if family == "HUM":
        return "workflow owner"
    if family == "RNT":
        return "AI runtime owner"
    return "AI governance owner"


def build_obd_report(
    *,
    case_id: str,
    scan: dict[str, Any],
    policy: SignoffPolicy | None = None,
    confidence_label: ConfidenceLabel = "asserted",
    artifact_links: dict[str, str] | None = None,
) -> dict[str, Any]:
    signoff_policy = policy or SignoffPolicy()
    drifts = list(scan.get("drifts") or [])
    findings: list[dict[str, Any]] = []
    for drift in drifts:
        family = str(drift.get("family") or "").upper()
        finding = {
            "code": str(drift.get("code") or ""),
            "family": FAMILY_LABELS.get(family, family.lower() or "unknown"),
            "severity": str(drift.get("severity") or "unknown"),
            "ma13_class": str(drift.get("ma13_class") or ""),
            "risk_class": risk_class(drift),
            "affected_workflow": affected_workflow(drift),
            "likely_owner": likely_owner(drift),
            "remediation_class": signoff_policy.remediation_class(drift),
            "requires_human_signoff": signoff_policy.requires_signoff(drift),
            "summary": str(drift.get("drift_summary") or ""),
            "evidence": drift.get("evidence") or {},
        }
        findings.append(finding)

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in findings:
        by_family[str(finding["family"])].append(finding)
    severity_counts = Counter(str(item.get("severity") or "unknown") for item in findings)
    signoff_count = sum(1 for item in findings if item["requires_human_signoff"])
    top_risk = "green"
    if any(item["risk_class"] == "red" for item in findings):
        top_risk = "red"
    elif any(item["risk_class"] == "amber" for item in findings):
        top_risk = "amber"
    elif any(item["risk_class"] == "yellow" for item in findings):
        top_risk = "yellow"

    return {
        "schema_version": "mechanic.obd_report.v1",
        "case_id": case_id,
        "confidence_label": confidence_label,
        "top_risk_class": top_risk,
        "drift_count": len(findings),
        "requires_human_signoff_count": signoff_count,
        "severity_counts": dict(sorted(severity_counts.items())),
        "families": {family: len(items) for family, items in sorted(by_family.items())},
        "findings": findings,
        "artifact_links": dict(artifact_links or {}),
        "pilot_positioning": "AI workflow OBD scanner for AI platform teams",
        "sla": {"scan_start_seconds": 60, "scan_complete_seconds": 300},
    }


def render_obd_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Mechanic OBD Report - `{report.get('case_id')}`",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Confidence | `{report.get('confidence_label')}` |",
        f"| Top risk | `{report.get('top_risk_class')}` |",
        f"| Drift count | {report.get('drift_count')} |",
        f"| Human sign-off required | {report.get('requires_human_signoff_count')} |",
        "",
        "## Findings",
        "",
        "| Code | Risk | Owner | Sign-off | Remediation | Workflow | Summary |",
        "|------|------|-------|----------|-------------|----------|---------|",
    ]
    for finding in report.get("findings") or []:
        summary = str(finding.get("summary") or "").replace("|", "\\|")
        lines.append(
            "| {code} | {risk} | {owner} | {signoff} | {remediation} | `{workflow}` | {summary} |".format(
                code=finding.get("code"),
                risk=finding.get("risk_class"),
                owner=finding.get("likely_owner"),
                signoff="yes" if finding.get("requires_human_signoff") else "no",
                remediation=finding.get("remediation_class"),
                workflow=finding.get("affected_workflow"),
                summary=summary,
            )
        )
    return "\n".join(lines) + "\n"
