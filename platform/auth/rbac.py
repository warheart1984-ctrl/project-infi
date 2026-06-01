"""RBAC and scope checks for platform routes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform.common import OrgRole, normalize_org_role, scopes_for_roles

ACTION_SCOPES: dict[str, str] = {
    "org.create": "org:admin",
    "org.read": "jobs:read",
    "org.list": "jobs:read",
    "api_key.create": "api_key:create",
    "principal.read": "jobs:read",
    "principal.manage": "org:admin",
    "job.create": "jobs:submit",
    "job.read": "jobs:read",
    "job.cancel": "jobs:cancel",
    "artifact.register": "artifacts:register",
    "artifact.read": "artifacts:read",
    "audit.read": "audit:read",
    "invite.create": "invite:create",
    "invite.accept": "jobs:read",
    "usage.read": "org:billing",
    "billing.export": "org:billing",
    "org.billing": "org:billing",
    "org.admin": "org:admin",
}


@dataclass(slots=True)
class Principal:
    principal_id: str
    org_id: str
    roles: list[OrgRole | str]
    scopes: list[str] = field(default_factory=list)
    api_key_id: str = ""
    principal_kind: str = "service_account"
    display_name: str = ""

    def is_platform_admin(self) -> bool:
        return "platform_admin" in self.roles or "*" in self.scopes

    def has_scope(self, scope: str) -> bool:
        if self.is_platform_admin() or "*" in self.scopes:
            return True
        return scope in self.scopes

    def model_dump(self) -> dict[str, Any]:
        return {
            "identity_version": "platform.platform_identity.v1",
            "org_id": self.org_id,
            "principal_id": self.principal_id,
            "principal_kind": self.principal_kind,
            "display_name": self.display_name,
            "roles": [normalize_org_role(str(r)) for r in self.roles],
            "scopes": list(self.scopes),
            "api_key_id": self.api_key_id,
        }


def authorize_scope(*, principal: Principal, scope: str, target_org_id: str | None = None) -> bool:
    if not principal.has_scope(scope):
        return False
    if principal.is_platform_admin():
        return True
    if target_org_id and principal.org_id != target_org_id:
        return False
    return True


def authorize(*, principal: Principal, action: str, target_org_id: str | None = None) -> bool:
    scope = ACTION_SCOPES.get(action)
    if not scope:
        return False
    return authorize_scope(principal=principal, scope=scope, target_org_id=target_org_id)


def principal_from_resolution(resolved: dict[str, Any]) -> Principal:
    roles = [normalize_org_role(str(r)) for r in (resolved.get("roles") or ["read_only"])]
    scopes = list(resolved.get("scopes") or scopes_for_roles(roles))
    return Principal(
        principal_id=str(resolved["principal_id"]),
        org_id=str(resolved["org_id"]),
        roles=roles,
        scopes=scopes,
        api_key_id=str(resolved.get("api_key_id") or ""),
        display_name=str(resolved.get("display_name") or ""),
        principal_kind=str(resolved.get("principal_kind") or "service_account"),
    )
