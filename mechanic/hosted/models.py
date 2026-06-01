"""Data contracts for the standalone Mechanic hosted pilot."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from src.datetime_compat import UTC

from mechanic.common import sha256_file

Provider = Literal["github", "gitlab"]
Plan = Literal["pilot", "team", "enterprise"]
SlaTier = Literal["pilot_5m", "standard", "enterprise"]
ScanStatus = Literal[
    "queued",
    "checking_out",
    "scanning",
    "diagnosing",
    "replaying",
    "reporting",
    "complete",
    "failed",
]
ConfidenceLabel = Literal["asserted", "local_proven", "ci_proven", "second_machine_proven", "rejected"]


@dataclass(slots=True)
class Customer:
    customer_id: str
    org: str
    plan: Plan = "pilot"
    allowed_repos: list[str] = field(default_factory=list)
    sla_tier: SlaTier = "pilot_5m"

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SignoffPolicy:
    require_human_for_severities: list[str] = field(default_factory=lambda: ["critical", "high"])
    require_human_for_ma13_classes: list[str] = field(default_factory=lambda: ["II", "III"])
    raw_apply_blocked: bool = True
    apply_review_proposal_only: bool = True

    def requires_signoff(self, drift: dict[str, Any]) -> bool:
        severity = str(drift.get("severity") or "").lower()
        ma13 = str(drift.get("ma13_class") or "").upper()
        return severity in {s.lower() for s in self.require_human_for_severities} and ma13 in {
            c.upper() for c in self.require_human_for_ma13_classes
        }

    def remediation_class(self, drift: dict[str, Any]) -> str:
        if self.requires_signoff(drift):
            ma13 = str(drift.get("ma13_class") or "").upper()
            return "legal_or_security_signoff" if ma13 == "III" else "review_required"
        if str(drift.get("severity") or "").lower() in {"critical", "high", "medium"}:
            return "review_required"
        return "observe"

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RepoInstallation:
    installation_id: str
    customer_id: str
    provider: Provider
    repo_id: str
    default_branch: str = "main"
    permissions: list[str] = field(default_factory=lambda: ["contents:read", "metadata:read"])
    policy_profile: SignoffPolicy = field(default_factory=SignoffPolicy)

    def model_dump(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["policy_profile"] = self.policy_profile.model_dump()
        return payload


@dataclass(slots=True)
class ScanJob:
    scan_id: str
    case_id: str
    customer_id: str
    installation_id: str
    repo_ref: str
    status: ScanStatus = "queued"
    created_at_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    started_at_utc: str = ""
    finished_at_utc: str = ""
    sla_target_seconds: int = 300
    error: str = ""

    def mark(self, status: ScanStatus) -> None:
        self.status = status
        now = datetime.now(UTC).isoformat()
        if status != "queued" and not self.started_at_utc:
            self.started_at_utc = now
        if status in {"complete", "failed"}:
            self.finished_at_utc = now

    @property
    def sla_deadline_utc(self) -> str:
        created = datetime.fromisoformat(self.created_at_utc)
        return (created + timedelta(seconds=self.sla_target_seconds)).isoformat()

    def model_dump(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["sla_deadline_utc"] = self.sla_deadline_utc
        return payload


@dataclass(slots=True)
class EvidenceBundle:
    bundle_version: str
    case_id: str
    scan_id: str
    artifact_dir: str
    confidence_label: ConfidenceLabel
    artifacts: dict[str, dict[str, str]]
    trace_inputs: list[dict[str, str]] = field(default_factory=list)
    repo_ref: str = ""
    customer_repo_mutated: bool = False

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


def build_artifact_manifest(case_dir: Path, *, artifact_names: list[str]) -> dict[str, dict[str, str]]:
    manifest: dict[str, dict[str, str]] = {}
    for name in artifact_names:
        path = case_dir / name
        if path.is_file():
            manifest[name] = {"path": str(path), "sha256": sha256_file(path)}
        else:
            manifest[name] = {"path": str(path), "sha256": "", "missing": "true"}
    return manifest


def trace_input_manifest(paths: list[str | Path]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for item in paths:
        path = Path(item)
        record = {"path": str(path), "sha256": ""}
        if path.is_file():
            record["sha256"] = sha256_file(path)
        result.append(record)
    return result
