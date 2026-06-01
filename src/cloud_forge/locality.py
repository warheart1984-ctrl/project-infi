"""Cloud locality: domain slices, queue priority, session prewarm (Phase 4)."""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from datetime import datetime, timezone
import json
import os
import threading
from pathlib import Path
from typing import Any

from src.cloud_forge.templates import DOMAIN_FORGE_VOSS_OS, get_domain_template
from src.cloud_forge.types import ClusterState, GovernanceWeight, LawEnvelope, PerformanceProfile


SLICES_PATH = (
    Path(__file__).resolve().parents[2] / "configs" / "cloud-forge" / "domain-slices.json"
)
PREWARM_ROOT = Path(__file__).resolve().parents[2] / ".runtime" / "cloud_forge" / "prewarm"

PRIORITY_CLASSES = (
    "cloud-forge-critical",
    "cloud-forge-high",
    "cloud-forge-normal",
    "cloud-forge-low",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_slices_registry() -> dict[str, Any]:
    path = Path(os.getenv("CLOUD_FORGE_SLICES_PATH", str(SLICES_PATH)))
    if not path.is_file():
        return _wrap_ul_payload({"slices": []})
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_domain_slice(domain: str | None) -> dict[str, Any]:
    """Map task domain to co-location slice (exact match, else fallback `*`)."""
    registry = _load_slices_registry()
    slices = list(registry.get("slices") or [])
    domain_norm = str(domain or "").strip()
    exact = next((s for s in slices if s.get("domain") == domain_norm), None)
    if exact:
        return dict(exact)
    fallback = next((s for s in slices if s.get("domain") == "*"), None)
    if fallback:
        return dict(fallback)
    return _wrap_ul_payload({
        "slice_id": "unmapped",
        "domain": domain_norm or "unknown",
        "namespace": "cloud-forge-default",
        "region": "us-central1",
        "components": ["llm-gateway"],
    })


def map_governance_to_priority(
    actor: GovernanceWeight,
    tenant: PerformanceProfile,
    cluster: ClusterState | None = None,
) -> dict[str, Any]:
    """
    Map wL / wT / wI + performance biases + cluster load → queue priority class.

    Aligns with Phase 4: weight → priority class (K8s PriorityClass name).
    """
    cluster = cluster or ClusterState()
    load_penalty = {"low": 0, "medium": 40, "high": 120}.get(
        str(cluster.load or "low").strip().lower(),
        0,
    )
    score = int(
        actor.wL * tenant.latency_bias
        + actor.effective_wT * tenant.throughput_bias * 0.6
        + actor.effective_wI * tenant.intelligence_bias * 0.4
        - load_penalty
    )
    score = max(0, min(1000, score))

    if score >= 200:
        priority_class = "cloud-forge-critical"
    elif score >= 120:
        priority_class = "cloud-forge-high"
    elif score >= 60:
        priority_class = "cloud-forge-normal"
    else:
        priority_class = "cloud-forge-low"

    return _wrap_ul_payload({
        "priority_score": score,
        "priority_class": priority_class,
        "k8s_priority_class": priority_class,
        "load_penalty": load_penalty,
        "claim_status": "asserted",
    })


def enrich_cluster_for_domain(
    domain: str | None,
    cluster: ClusterState | dict[str, Any] | None,
) -> ClusterState:
    """Merge domain slice metadata into advisory cluster state."""
    slice_info = resolve_domain_slice(domain)
    base = (
        cluster
        if isinstance(cluster, ClusterState)
        else ClusterState.from_dict(cluster)
    )
    hot = list(base.hot_domains)
    domain_norm = str(domain or "").strip()
    if domain_norm and domain_norm not in hot:
        hot.append(domain_norm)
    return ClusterState(
        load=base.load,
        hot_domains=hot,
        model_availability=dict(base.model_availability),
    )


def build_law_bundle(law: LawEnvelope, domain: str | None) -> dict[str, Any]:
    """Pre-warmable law bundle: envelope + domain doc paths."""
    template = get_domain_template(domain)
    prefetch = list((template or {}).get("prefetch_docs") or [])
    return _wrap_ul_payload({
        "law_id": law.law_id,
        "law_version": law.law_version,
        "forbid_express": law.forbid_express,
        "forbid_cache_above": law.forbid_cache_above,
        "prefetch_docs": prefetch,
        "resolved_at": _utc_now_iso(),
    })


def build_strategy_profile(tenant: PerformanceProfile, actor: GovernanceWeight) -> dict[str, Any]:
    return _wrap_ul_payload({
        "latency_bias": tenant.latency_bias,
        "throughput_bias": tenant.throughput_bias,
        "intelligence_bias": tenant.intelligence_bias,
        "wL_express_threshold": tenant.wL_express_threshold,
        "wL_express_floor": tenant.wL_express_floor,
        "actor_wL": actor.wL,
        "actor_wT": actor.effective_wT,
        "actor_wI": actor.effective_wI,
        "resolved_at": _utc_now_iso(),
    })


class SessionPrewarmStore:
    """Per-tenant session cache for law bundle + strategy profile."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or PREWARM_ROOT)
        self._lock = threading.Lock()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, tenant_id: str, session_id: str) -> Path:
        safe_tenant = "".join(c if c.isalnum() or c in "._-" else "_" for c in tenant_id)
        safe_session = "".join(c if c.isalnum() or c in "._-" else "_" for c in session_id)
        return self.root / safe_tenant / f"{safe_session}.json"

    def get(self, tenant_id: str, session_id: str) -> dict[str, Any] | None:
        path = self._path(tenant_id, session_id)
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def set(self, tenant_id: str, session_id: str, record: dict[str, Any]) -> dict[str, Any]:
        path = self._path(tenant_id, session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {**record, "stored_at": _utc_now_iso()}
        with self._lock:
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    def resolve_or_create(
        self,
        tenant_id: str,
        session_id: str,
        law: LawEnvelope,
        tenant: PerformanceProfile,
        actor: GovernanceWeight,
        domain: str | None,
        *,
        ttl_minutes: int = 30,
    ) -> dict[str, Any]:
        existing = self.get(tenant_id, session_id)
        if existing and existing.get("law_version") == law.law_version:
            existing["cache_hit"] = True
            return existing

        record = {
            "tenant_id": tenant_id,
            "session_id": session_id,
            "domain": domain,
            "law_id": law.law_id,
            "law_version": law.law_version,
            "ttl_minutes": ttl_minutes,
            "law_bundle": build_law_bundle(law, domain),
            "strategy_profile": build_strategy_profile(tenant, actor),
            "slice": resolve_domain_slice(domain),
            "cache_hit": False,
        }
        return self.set(tenant_id, session_id, record)


_default_prewarm: SessionPrewarmStore | None = None


def get_default_prewarm_store() -> SessionPrewarmStore:
    global _default_prewarm
    if _default_prewarm is None:
        configured = os.getenv("CLOUD_FORGE_PREWARM_ROOT")
        _default_prewarm = SessionPrewarmStore(configured or PREWARM_ROOT)
    return _default_prewarm


def build_cloud_placement(
    *,
    actor: GovernanceWeight,
    tenant: PerformanceProfile,
    domain: str | None,
    cluster: ClusterState | None = None,
    session_prewarm: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full Phase 4 placement block for pipeline / readout attachment."""
    slice_info = resolve_domain_slice(domain)
    priority = map_governance_to_priority(actor, tenant, cluster)
    return _wrap_ul_payload({
        "slice_id": slice_info.get("slice_id"),
        "namespace": slice_info.get("namespace"),
        "region": slice_info.get("region"),
        "domain": domain,
        "components": list(slice_info.get("components") or []),
        "priority": priority,
        "session_prewarm": {
            "active": session_prewarm is not None,
            "cache_hit": bool((session_prewarm or {}).get("cache_hit")),
            "law_version": (session_prewarm or {}).get("law_version"),
        },
        "forge_voss_os_slice": domain == DOMAIN_FORGE_VOSS_OS,
        "claim_status": "asserted",
    })


def apply_priority_parallelism_boost(
    parallelism: int,
    priority: dict[str, Any],
) -> int:
    """Optional throughput boost for high priority classes."""
    cls = str(priority.get("priority_class") or "")
    if cls == "cloud-forge-critical":
        return min(16, parallelism + 4)
    if cls == "cloud-forge-high":
        return min(16, parallelism + 2)
    return parallelism
