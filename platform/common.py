"""Shared platform utilities."""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any, Literal

ClaimLabel = Literal["asserted", "proven", "rejected"]
ProofStatus = Literal["asserted", "proven", "disputed"]
Subsystem = Literal[
    "mechanic",
    "forgekeeper",
    "slingshot",
    "lab",
    "ai_factory",
    "drift_detector",
    "workflow_engine",
]
OidcProvider = Literal["google", "microsoft", "github", "local"]
BillingStatus = Literal["active", "past_due", "suspended"]

PROOF_REQUIRED_KINDS: frozenset[str] = frozenset(
    {
        "ai_factory.build",
        "slingshot.preload",
        "slingshot.launch",
        "factory_build",
    }
)
OrgRole = Literal["owner", "admin", "operator", "read_only", "auditor", "platform_admin"]
LegacyRole = Literal["platform_admin", "org_admin", "operator", "viewer"]
PlatformRole = OrgRole | LegacyRole
JobStatus = Literal["queued", "running", "complete", "failed", "cancelled", "blocked_proof"]
JobPriority = Literal["low", "normal", "high"]
SlaClass = Literal["interactive", "batch", "proof"]
ArtifactVisibility = Literal["org", "private", "shared"]
RetentionClass = Literal["short", "standard", "long"]
PlanId = Literal["free", "pro", "enterprise"]

JOB_VERSION = "platform.platform_job.v1"
REF_VERSION = "platform.platform_artifact_ref.v1"
IDENTITY_VERSION = "platform.platform_identity.v1"
BINDING_VERSION = "platform.platform_role_binding.v1"

DEFAULT_SCOPES_BY_ROLE: dict[str, list[str]] = {
    "platform_admin": ["*", "proof:attest"],
    "owner": [
        "org:admin",
        "org:billing",
        "jobs:submit",
        "jobs:read",
        "jobs:cancel",
        "artifacts:read",
        "artifacts:register",
        "audit:read",
        "api_key:create",
        "invite:create",
    ],
    "admin": [
        "org:admin",
        "jobs:submit",
        "jobs:read",
        "jobs:cancel",
        "artifacts:read",
        "artifacts:register",
        "audit:read",
        "api_key:create",
        "invite:create",
    ],
    "operator": ["jobs:submit", "jobs:read", "artifacts:read", "artifacts:register"],
    "read_only": ["jobs:read", "artifacts:read", "audit:read"],
    "auditor": ["jobs:read", "artifacts:read", "audit:read", "org:billing"],
    "org_admin": [
        "org:admin",
        "jobs:submit",
        "jobs:read",
        "artifacts:read",
        "artifacts:register",
        "audit:read",
        "api_key:create",
    ],
    "viewer": ["jobs:read", "artifacts:read", "audit:read"],
}


def normalize_org_role(role: str) -> OrgRole:
    mapping = {
        "org_admin": "admin",
        "viewer": "read_only",
    }
    normalized = mapping.get(role, role)
    if normalized in ("owner", "admin", "operator", "read_only", "auditor", "platform_admin"):
        return normalized  # type: ignore[return-value]
    return "read_only"


def scopes_for_roles(roles: list[str], extra_scopes: list[str] | None = None) -> list[str]:
    scopes: set[str] = set(extra_scopes or [])
    for role in roles:
        for scope in DEFAULT_SCOPES_BY_ROLE.get(normalize_org_role(role), []):
            scopes.add(scope)
    return sorted(scopes)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
