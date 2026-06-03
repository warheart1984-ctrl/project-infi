"""Bilateral federation grants — runtime JSONL store (v1.7+)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from src.ugr.platform.tenant_registry import TenantRegistry, normalize_tenant_id


CAP_ROUTE_STEP = "route_step"
CAP_READ_MARKETPLACE = "read_marketplace"
CAP_GOVERNANCE_COSIGN = "governance_cosign"

VALID_CAPABILITIES = frozenset(
    {CAP_ROUTE_STEP, CAP_READ_MARKETPLACE, CAP_GOVERNANCE_COSIGN}
)

GRANT_STATUS_PENDING = "pending"
GRANT_STATUS_ACCEPTED = "accepted"
GRANT_STATUS_REVOKED = "revoked"


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[3] / ".runtime"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class FederationGrant:
    grant_id: str
    issuer_tenant: str
    grantee_tenant: str
    status: str
    capabilities: tuple[str, ...]
    issued_at: int
    accepted_at: int | None
    expires_at: int | None
    issued_by_operator: str
    accepted_by_operator: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "grant_id": self.grant_id,
            "issuer_tenant": self.issuer_tenant,
            "grantee_tenant": self.grantee_tenant,
            "status": self.status,
            "capabilities": list(self.capabilities),
            "issued_at": self.issued_at,
            "accepted_at": self.accepted_at,
            "expires_at": self.expires_at,
            "issued_by_operator": self.issued_by_operator,
            "accepted_by_operator": self.accepted_by_operator,
        }

    def to_manifold_grant(self) -> dict[str, Any]:
        """Format for tenant manifold federation_grants[] (outbound from issuer)."""
        return {
            "grant_id": self.grant_id,
            "target_tenant": self.grantee_tenant,
            "status": self.status,
            "capabilities": list(self.capabilities),
            "expires_at": self.expires_at,
        }

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities

    def is_active(self, *, now: int | None = None) -> bool:
        if self.status != GRANT_STATUS_ACCEPTED:
            return False
        ts = int(now if now is not None else time.time())
        if self.expires_at is not None and int(self.expires_at) < ts:
            return False
        return True


class FederationGrantStore:
    """Append-only grant log; latest record per grant_id wins."""

    def __init__(self, runtime_dir: str | Path | None = None):
        root = Path(runtime_dir or _default_runtime_dir())
        self.path = root / "urg" / "federation" / "grants.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _append(self, record: dict[str, Any]) -> None:
        line = _stable_json(record)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows

    def _merged_grants(self) -> dict[str, FederationGrant]:
        merged: dict[str, dict[str, Any]] = {}
        for row in self._read_all():
            gid = str(row.get("grant_id") or "").strip()
            if not gid:
                continue
            base = dict(merged.get(gid) or {})
            base.update(row)
            merged[gid] = base
        out: dict[str, FederationGrant] = {}
        for gid, row in merged.items():
            grant = _row_to_grant(row)
            if grant:
                out[gid] = grant
        return out

    def get(self, grant_id: str) -> FederationGrant | None:
        return self._merged_grants().get(str(grant_id or "").strip())

    def issue(
        self,
        *,
        issuer_tenant: str,
        grantee_tenant: str,
        capabilities: list[str],
        operator_id: str,
        expires_at: int | None = None,
        grant_id: str | None = None,
    ) -> FederationGrant:
        issuer = normalize_tenant_id(issuer_tenant)
        grantee = normalize_tenant_id(grantee_tenant)
        if issuer == grantee:
            raise ValueError("issuer and grantee must differ")
        caps = tuple(
            c for c in (str(x).strip() for x in capabilities)
            if c in VALID_CAPABILITIES
        )
        if not caps:
            raise ValueError("at least one valid capability required")
        reg = TenantRegistry()
        if reg.get(issuer) is None or reg.get(grantee) is None:
            raise ValueError("unknown issuer or grantee tenant")
        gid = str(grant_id or "").strip() or f"fed-{uuid.uuid4().hex[:12]}"
        now = int(time.time())
        record = {
            "record_kind": "outbound_issue",
            "grant_id": gid,
            "issuer_tenant": issuer,
            "grantee_tenant": grantee,
            "status": GRANT_STATUS_PENDING,
            "capabilities": list(caps),
            "issued_at": now,
            "accepted_at": None,
            "expires_at": expires_at,
            "issued_by_operator": str(operator_id or "").strip(),
            "accepted_by_operator": None,
        }
        self._append(record)
        grant = _row_to_grant(record)
        assert grant is not None
        return grant

    def accept(
        self,
        grant_id: str,
        *,
        accepting_tenant: str,
        operator_id: str,
    ) -> FederationGrant:
        grant = self.get(grant_id)
        if grant is None:
            raise ValueError(f"unknown grant_id {grant_id}")
        acceptor = normalize_tenant_id(accepting_tenant)
        if acceptor != grant.grantee_tenant:
            raise ValueError("only grantee may accept")
        if grant.status != GRANT_STATUS_PENDING:
            raise ValueError(f"grant status is {grant.status}, not pending")
        now = int(time.time())
        outbound = {
            "record_kind": "outbound_accept",
            "grant_id": grant.grant_id,
            "issuer_tenant": grant.issuer_tenant,
            "grantee_tenant": grant.grantee_tenant,
            "status": GRANT_STATUS_ACCEPTED,
            "capabilities": list(grant.capabilities),
            "issued_at": grant.issued_at,
            "accepted_at": now,
            "expires_at": grant.expires_at,
            "issued_by_operator": grant.issued_by_operator,
            "accepted_by_operator": str(operator_id or "").strip(),
        }
        self._append(outbound)
        inbound = {
            "record_kind": "inbound_grant",
            "grant_id": grant.grant_id,
            "issuer_tenant": grant.issuer_tenant,
            "grantee_tenant": grant.grantee_tenant,
            "status": GRANT_STATUS_ACCEPTED,
            "capabilities": list(grant.capabilities),
            "issued_at": grant.issued_at,
            "accepted_at": now,
            "expires_at": grant.expires_at,
            "issued_by_operator": grant.issued_by_operator,
            "accepted_by_operator": str(operator_id or "").strip(),
        }
        self._append(inbound)
        updated = self.get(grant_id)
        assert updated is not None
        return updated

    def revoke(self, grant_id: str, *, operator_id: str, revoking_tenant: str) -> FederationGrant:
        grant = self.get(grant_id)
        if grant is None:
            raise ValueError(f"unknown grant_id {grant_id}")
        revoker = normalize_tenant_id(revoking_tenant)
        if revoker not in {grant.issuer_tenant, grant.grantee_tenant}:
            raise ValueError("only issuer or grantee may revoke")
        record = grant.to_dict()
        record["record_kind"] = "revoke"
        record["status"] = GRANT_STATUS_REVOKED
        record["revoked_by_operator"] = str(operator_id or "").strip()
        record["revoked_at"] = int(time.time())
        self._append(record)
        updated = self.get(grant_id)
        assert updated is not None
        return updated

    def list_for_tenant(self, tenant_id: str) -> list[FederationGrant]:
        tenant_norm = normalize_tenant_id(tenant_id)
        grants = self._merged_grants()
        result: list[FederationGrant] = []
        for grant in grants.values():
            if grant.issuer_tenant == tenant_norm or grant.grantee_tenant == tenant_norm:
                result.append(grant)
        return sorted(result, key=lambda g: g.grant_id)

    def list_outbound_accepted(self, issuer_tenant: str) -> list[FederationGrant]:
        issuer = normalize_tenant_id(issuer_tenant)
        now = int(time.time())
        return [
            g
            for g in self._merged_grants().values()
            if g.issuer_tenant == issuer and g.is_active(now=now)
        ]

    def verify_step_capability(
        self,
        *,
        home_tenant: str,
        peer_tenant: str,
        grant_id: str,
        capability: str,
    ) -> tuple[FederationGrant | None, str | None]:
        gid = str(grant_id or "").strip()
        if not gid:
            return None, "federation_grant_id required for federated step"
        grant = self.get(gid)
        if grant is None:
            return None, f"unknown federation grant {gid}"
        home = normalize_tenant_id(home_tenant)
        peer = normalize_tenant_id(peer_tenant)
        if grant.issuer_tenant != home:
            return None, "grant issuer must be home tenant"
        if grant.grantee_tenant != peer:
            return None, "grant grantee must match federation_peer_tenant"
        if not grant.is_active():
            return None, f"grant {gid} not accepted or expired"
        if not grant.has_capability(capability):
            return None, f"grant {gid} lacks capability {capability}"
        return grant, None


def merge_federation_grants_for_tenant(
    tenant_spec: Any,
    runtime_dir: str | Path | None = None,
) -> tuple[dict[str, Any], ...]:
    """Union static tenants.json grants with runtime accepted outbound grants."""
    static = [dict(g) for g in (tenant_spec.federation_grants or ())]
    if runtime_dir is None:
        return tuple(static)
    store = FederationGrantStore(runtime_dir)
    for grant in store.list_outbound_accepted(tenant_spec.tenant_id):
        static.append(grant.to_manifold_grant())
    return tuple(static)


def _row_to_grant(row: dict[str, Any]) -> FederationGrant | None:
    gid = str(row.get("grant_id") or "").strip()
    if not gid:
        return None
    caps = tuple(
        str(c) for c in (row.get("capabilities") or []) if str(c) in VALID_CAPABILITIES
    )
    accepted_raw = row.get("accepted_at")
    accepted_at = int(accepted_raw) if accepted_raw is not None else None
    expires_raw = row.get("expires_at")
    expires_at = int(expires_raw) if expires_raw is not None else None
    return FederationGrant(
        grant_id=gid,
        issuer_tenant=normalize_tenant_id(row.get("issuer_tenant")),
        grantee_tenant=normalize_tenant_id(row.get("grantee_tenant")),
        status=str(row.get("status") or GRANT_STATUS_PENDING),
        capabilities=caps,
        issued_at=int(row.get("issued_at") or 0),
        accepted_at=accepted_at,
        expires_at=expires_at,
        issued_by_operator=str(row.get("issued_by_operator") or ""),
        accepted_by_operator=(
            str(row.get("accepted_by_operator") or "") or None
        ),
    )


def compute_federation_digest(
    *,
    home_rows: list[dict[str, Any]],
    peer_rows: list[dict[str, Any]],
    grant_id: str,
    federation_forge: list[dict[str, Any]] | None = None,
) -> str:
    """Stable digest over cross-linked federation ledger rows (v1.8+)."""
    forge_entries = []
    for entry in list(federation_forge or []):
        forge_entries.append(
            {
                "grant_id": entry.get("grant_id"),
                "step_id": entry.get("step_id"),
                "mission_rail": entry.get("mission_rail"),
                "peer_rail": entry.get("peer_rail"),
            }
        )
    payload = {
        "grant_id": str(grant_id or ""),
        "forge": forge_entries,
        "home": [
            {
                "phase": r.get("phase"),
                "mission_id": r.get("mission_id"),
                "step_id": r.get("step_id"),
                "action_id": r.get("action_id"),
                "federation_grant_id": r.get("federation_grant_id"),
            }
            for r in home_rows
            if r.get("phase") in {"federation_step", "federation_governance"}
        ],
        "peer": [
            {
                "phase": r.get("phase"),
                "home_mission_id": r.get("home_mission_id"),
                "step_id": r.get("step_id"),
                "action_id": r.get("action_id"),
                "grant_id": r.get("grant_id") or r.get("federation_grant_id"),
            }
            for r in peer_rows
            if r.get("phase") in {"federation_inbound", "federation_governance_inbound"}
        ],
    }
    return sha256(_stable_json(payload).encode("utf-8")).hexdigest()
