"""Pattern ledger store for UGR — delegates to unified v0.5 ledger."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any
import os

from src.ugr.unified_pattern_ledger import UnifiedPatternLedger, UNIFIED_LEDGER_VERSION, _stable_json


UGR_LEDGER_ID = "aais.ugr.pattern_ledger"
UGR_LEDGER_VERSION = UNIFIED_LEDGER_VERSION

CLASSIFICATIONS = frozenset(
    {
        "success",
        "failure",
        "near_miss",
        "recovered_failure",
        "unresolved",
        "pending_review",
    }
)
CLAIM_STATUSES = frozenset({"proposed", "accepted", "rejected", "contested"})


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[2] / ".runtime"


@dataclass(frozen=True)
class PatternClaim:
    claim_id: str
    subject: str
    predicate: str
    object: str
    confidence: float
    source_lane: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    tenant_scope: str = "global"
    status: str = "proposed"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


def _platform_enabled() -> bool:
    return os.getenv("UGR_PLATFORM_ENABLED", "").strip().lower() in {"1", "true", "yes"}


def _causal_graph_enabled() -> bool:
    from src.ugr.causal_graph.store import causal_graph_enabled

    return causal_graph_enabled()


def _graph_enabled() -> bool:
    from src.ugr.graph_index.store import graph_index_enabled

    return graph_index_enabled() or _causal_graph_enabled()


class PatternLedgerStore:
    """UGR-facing ledger API backed by the unified pattern ledger."""

    def __init__(self, runtime_dir: str | Path | None = None):
        self._runtime_root = Path(runtime_dir or _default_runtime_dir())
        self._platform = _platform_enabled()
        if self._platform:
            from src.ugr.platform.sharded_ledger import ShardedPatternLedger

            self._ledger = ShardedPatternLedger(runtime_root=self._runtime_root)
        else:
            self._ledger = UnifiedPatternLedger(runtime_root=self._runtime_root)
        self._graph = None
        if _causal_graph_enabled():
            from src.ugr.causal_graph.store import CausalGraphStore

            self._graph = CausalGraphStore(runtime_root=self._runtime_root, ledger=self._ledger)
        elif _graph_enabled():
            from src.ugr.graph_index.store import GraphIndexStore

            self._graph = GraphIndexStore(runtime_root=self._runtime_root, ledger=self._ledger)

    @property
    def claims_path(self) -> Path:
        if self._platform:
            shard_root = self._ledger.router.shard_root("shard-global")
            return shard_root / "unified" / "claims.jsonl"
        return self._ledger._path_for("claim")

    @property
    def events_path(self) -> Path:
        if self._platform:
            shard_root = self._ledger.router.shard_root("shard-global")
            return shard_root / "unified" / "pattern_events.jsonl"
        return self._ledger.unified_dir / "pattern_events.jsonl"

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        self._runtime_root = Path(runtime_dir)
        self._ledger.configure_runtime_root(self._runtime_root)
        if self._graph is not None:
            if hasattr(self._graph, "configure_runtime_root"):
                self._graph.configure_runtime_root(self._runtime_root)
            else:
                self._graph.runtime_root = self._runtime_root
            self._graph.ledger = self._ledger
            self._graph.rebuild()

    def make_claim_id(self, subject: str, predicate: str, object_value: str, source_lane: str) -> str:
        digest = sha256(
            _stable_json(
                {
                    "subject": subject,
                    "predicate": predicate,
                    "object": object_value,
                    "source_lane": source_lane,
                }
            ).encode("utf-8")
        ).hexdigest()[:16]
        return f"claim-{digest}"

    def append_claim(self, claim: PatternClaim | dict[str, Any]) -> dict[str, Any]:
        payload = claim.to_dict() if isinstance(claim, PatternClaim) else dict(claim or {})
        record = self._ledger.append_claim(payload, origin="ugr")
        if self._graph is not None:
            self._graph.on_append(record)
        return record

    def append_evidence(
        self,
        *,
        source_type: str,
        source_uri: str,
        classification: str,
        summary: str,
        tenant_scope: str = "global",
        parsed_claims: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return self._ledger.append_evidence(
            source_type=source_type,
            source_uri=source_uri,
            classification=classification,
            summary=summary,
            tenant_scope=tenant_scope,
            parsed_claims=parsed_claims,
            origin="ugr",
        )

    def read_claims(self, *, tenant_scope: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        if self._platform:
            return self._ledger.read_claims(tenant_scope=tenant_scope, limit=limit)
        if tenant_scope:
            return self._ledger.read_claims(tenant_scope=tenant_scope, limit=limit)
        return self._ledger.read_claims(limit=limit)

    def query_by_subject(self, subject: str, *, tenant_scope: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        if self._graph is not None:
            return self._graph.query_by_subject(subject, tenant_scope=tenant_scope, limit=limit)
        needle = " ".join(str(subject or "").split()).strip().lower()
        if not needle:
            return []
        matches = [
            row
            for row in self.read_claims(limit=max(limit * 4, 40))
            if needle in str(row.get("subject") or "").lower()
        ]
        return matches[-limit:]

    def query_related(self, terms: list[str], *, tenant_scope: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        if self._graph is not None:
            return self._graph.query_related(terms, tenant_scope=tenant_scope, limit=limit)
        if tenant_scope is not None or self._platform:
            return self._ledger.query_related(terms, tenant_scope=tenant_scope, limit=limit)
        return self._ledger.query_related(terms, limit=limit)

    def graph_index_stats(self) -> dict[str, Any] | None:
        if self._graph is None:
            return None
        return self._graph.stats()

    def rebuild_graph_index(self) -> dict[str, Any] | None:
        if self._graph is None:
            return None
        return self._graph.rebuild()

    def query_provenance(self, claim_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        if self._graph is not None and hasattr(self._graph, "query_provenance"):
            return self._graph.query_provenance(claim_id, limit=limit)
        return []

    def query_causal(
        self,
        claim_id: str,
        *,
        depth: int | None = None,
        tenant_scope: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        if self._graph is not None and hasattr(self._graph, "query_causal"):
            return self._graph.query_causal(
                claim_id,
                depth=depth,
                tenant_scope=tenant_scope,
                limit=limit,
            )
        return {"claim_id": claim_id, "edges": [], "nodes": []}

    def region_health(self) -> dict[str, Any] | None:
        if self._graph is not None and hasattr(self._graph, "region_health"):
            return self._graph.region_health()
        return None

    def append_pattern_event(self, entry: dict[str, Any], *, mirror_legacy: bool = True) -> dict[str, Any]:
        if hasattr(self._ledger, "append_pattern_event"):
            return self._ledger.append_pattern_event(entry, mirror_legacy=mirror_legacy)
        raise AttributeError("underlying ledger does not support pattern events")

    def sync_cogos_patterns(
        self,
        *,
        rows: list[dict[str, Any]] | None = None,
        source_path: str | Path | None = None,
    ) -> dict[str, Any]:
        from src.ugr.cogos_pattern_bridge import CogosPatternBridge

        bridge = CogosPatternBridge(ledger=self, runtime_root=self._runtime_root)
        if rows is not None:
            return bridge.sync_fixture_rows(rows)
        return bridge.sync_events_jsonl(path=Path(source_path) if source_path else None)
