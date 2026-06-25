"""Canonical knowledge authority snapshot for AAIS."""

# Mythic: Knowledge Authority Organ
# Engineering: KnowledgeAuthorityEngine
from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul.runtime import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from pathlib import Path
from typing import Any

from src.state_hygiene import normalize_truth_scope, precedence_rank


CANONICAL_DOCTRINE_DOCS = [
    {
        "title": "AAIS Runtime Guide",
        "path": "docs/runtime/AAIS_RUNTIME_GUIDE.md",
        "role": "current runtime handbook",
    },
    {
        "title": "AAIS Doc Protocol",
        "path": "docs/contracts/AAIS_DOC_PROTOCOL.md",
        "role": "document authority order",
    },
    {
        "title": "AAIS Documentation Map",
        "path": "docs/README.md",
        "role": "reading order and document tiers",
    },
    {
        "title": "Jarvis Protocol",
        "path": "docs/contracts/JARVIS_PROTOCOL.md",
        "role": "runtime exchange contract",
    },
    {
        "title": "Jarvis Reasoning Protocol",
        "path": "docs/contracts/JARVIS_REASONING_PROTOCOL.md",
        "role": "bounded reasoning contract",
    },
    {
        "title": "AAIS UL Doctrine",
        "path": "docs/contracts/AAIS_UL_DOCTRINE.md",
        "role": "modular boundary law",
    },
]

OPERATOR_AUTHORITY_SOURCES = (
    "memory",
    "workspace",
    "doctrine",
    "document",
    "live_research",
    "urg_library",
)

AUTHORITY_SOURCE_METADATA = {
    "memory": {
        "label": "Live operator memories",
        "type": "operator",
        "scope": "session",
    },
    "workspace": {
        "label": "Workspace truth",
        "type": "runtime",
        "scope": "global",
    },
    "doctrine": {
        "label": "Canonical docs",
        "type": "file",
        "scope": "global",
    },
    "document": {
        "label": "Ingested documents",
        "type": "file",
        "scope": "global",
    },
    "live_research": {
        "label": "Live research",
        "type": "external",
        "scope": "session",
    },
    "urg_library": {
        "label": "URG library",
        "type": "governed",
        "scope": "global",
    },
}

AUTHORITY_PRESETS = {
    "strict_local": {
        "label": "Strict Local",
        "description": "Prefer workspace and governed local knowledge. Keep live research disabled.",
        "primary_source": "workspace",
        "shadow_sources": ["document"],
        "disabled_sources": ["live_research"],
    },
    "docs_first": {
        "label": "Docs-First",
        "description": "Prefer canonical docs before other supporting sources.",
        "primary_source": "doctrine",
        "shadow_sources": ["live_research"],
        "disabled_sources": [],
    },
    "exploratory": {
        "label": "Exploratory",
        "description": "Allow live research to widen evidence while keeping governance visible.",
        "primary_source": "live_research",
        "shadow_sources": [],
        "disabled_sources": [],
    },
    "urg_anchored": {
        "label": "URG-Anchored",
        "description": "Prefer governed URG proven catalog entries over supporting sources.",
        "primary_source": "urg_library",
        "shadow_sources": ["memory", "document"],
        "disabled_sources": ["live_research"],
    },
}


def _normalize_source_type(value: str | None) -> str | None:
    normalized = " ".join(str(value or "").strip().lower().split()).replace("-", "_")
    if normalized == "memory_override":
        normalized = "memory"
    return normalized if normalized in OPERATOR_AUTHORITY_SOURCES else None


def _normalize_source_list(values: Any) -> list[str]:
    normalized: list[str] = []
    for value in list(values or []):
        source_type = _normalize_source_type(value)
        if source_type and source_type not in normalized:
            normalized.append(source_type)
    return normalized


def default_authority_preferences() -> dict[str, Any]:
    """Return the canonical empty operator authority preference set."""
    return {
        "preset": "default",
        "primary_source": None,
        "shadow_sources": [],
        "disabled_sources": [],
        "truth_scope_lock": None,
    }


def authority_surface_priority(preferences: dict[str, Any] | None) -> str | None:
    """Return the current surfaced source without treating it as an authority override."""
    normalized_preferences = normalize_authority_preferences(preferences)
    return _normalize_source_type(normalized_preferences.get("primary_source"))


def normalize_authority_preferences(value: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize one operator authority preference payload into canonical shape."""
    preferences = dict(default_authority_preferences())
    raw = dict(value or {})
    preferences["preset"] = str(raw.get("preset") or "default").strip().lower() or "default"
    preferences["primary_source"] = _normalize_source_type(raw.get("primary_source"))
    preferences["shadow_sources"] = _normalize_source_list(raw.get("shadow_sources"))
    preferences["disabled_sources"] = _normalize_source_list(raw.get("disabled_sources"))

    truth_scope_lock = raw.get("truth_scope_lock")
    if isinstance(truth_scope_lock, dict):
        scope = normalize_truth_scope(truth_scope_lock.get("scope"), default="live")
        remaining_turns = max(0, min(int(truth_scope_lock.get("remaining_turns") or 0), 12))
        if remaining_turns > 0:
            preferences["truth_scope_lock"] = {
                "scope": scope,
                "remaining_turns": remaining_turns,
                "created_at": truth_scope_lock.get("created_at"),
            }

    if preferences["primary_source"] in preferences["disabled_sources"]:
        preferences["disabled_sources"] = [
            source_type
            for source_type in preferences["disabled_sources"]
            if source_type != preferences["primary_source"]
        ]
    if preferences["primary_source"] in preferences["shadow_sources"]:
        preferences["shadow_sources"] = [
            source_type
            for source_type in preferences["shadow_sources"]
            if source_type != preferences["primary_source"]
        ]
    preferences["shadow_sources"] = [
        source_type
        for source_type in preferences["shadow_sources"]
        if source_type not in preferences["disabled_sources"]
    ]
    return preferences


def default_knowledge_conflict_decisions() -> dict[str, Any]:
    """Return the canonical empty conflict decision store."""
    return {
        "deferred_conflicts": [],
    }


def normalize_knowledge_conflict_decisions(value: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize session-scoped knowledge conflict decisions."""
    raw = dict(value or {})
    deferred = [
        str(conflict_id).strip()
        for conflict_id in list(raw.get("deferred_conflicts") or [])
        if str(conflict_id).strip()
    ]
    seen: list[str] = []
    for conflict_id in deferred:
        if conflict_id not in seen:
            seen.append(conflict_id)
    return {
        "deferred_conflicts": seen,
    }


def authority_status_for(source_type: str, preferences: dict[str, Any] | None) -> str:
    """Return the canonical status for one authority source."""
    normalized_preferences = normalize_authority_preferences(preferences)
    normalized_source = _normalize_source_type(source_type)
    if not normalized_source:
        return "active"
    if normalized_source in normalized_preferences["disabled_sources"]:
        return "disabled"
    if normalized_source in normalized_preferences["shadow_sources"]:
        return "shadow"
    return "active"


class KnowledgeAuthority:
    """Build one governed knowledge snapshot across AAIS sources."""

    def __init__(self, repo_root: str | Path | None = None):
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[1]

    def _absolute_doc_path(self, relative_path: str) -> Path:
        return (self.repo_root / relative_path).resolve()

    def _authority_sort_key(self, entry: dict[str, Any], preferences: dict[str, Any]) -> tuple[int, str]:
        source_type = _normalize_source_type(entry.get("source_type"))
        adjusted_rank = int(entry.get("precedence_rank") or 0)
        status = authority_status_for(source_type or "", preferences)
        if status == "shadow":
            adjusted_rank += 12
        if status == "disabled":
            adjusted_rank += 40
        return adjusted_rank, str(entry.get("label") or "")

    def _build_authority_order(self, preferences: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        normalized_preferences = normalize_authority_preferences(preferences)
        surfaced_source = authority_surface_priority(normalized_preferences)
        entries = [
            ("memory_override", "canonical", "Override memories"),
            ("memory", "canonical", "Live operator memories"),
            ("governance_state", "canonical", "Governance and continuity state"),
            ("workspace", "canonical", "Workspace profile and project truth"),
            ("workspace", "derived", "Workspace intel and repo evidence"),
            ("document", "reference", "Ingested document knowledge"),
            ("live_research", "derived", "Fresh live research"),
            ("urg_library", "canonical", "Governed URG library entries"),
            ("doctrine", "reference", "Doctrine and canonical docs"),
            ("review", "derived", "Review proposals and run history"),
            ("run", "derived", "Execution history"),
            ("governance_event", "historical", "Governance audit history"),
        ]
        ordered = [
            {
                "source_type": source_type,
                "truth_status": truth_status,
                "label": label,
                "precedence_rank": precedence_rank(source_type, truth_status),
                "status": authority_status_for(source_type, normalized_preferences),
                "surface_priority": _normalize_source_type(source_type) == surfaced_source,
            }
            for source_type, truth_status, label in entries
        ]
        ordered.sort(key=lambda entry: self._authority_sort_key(entry, normalized_preferences))
        return ordered

    def _build_doctrine_entries(self, query: str | None, limit: int) -> list[dict[str, Any]]:
        query_text = " ".join(str(query or "").lower().split())
        docs = []

        def _append_matches(require_query: bool) -> None:
            for item in CANONICAL_DOCTRINE_DOCS:
                if len(docs) >= limit:
                    break
                haystack = f"{item['title']} {item['role']} {item['path']}".lower()
                if require_query and query_text and query_text not in haystack:
                    continue
                docs.append(
                    {
                        "title": item["title"],
                        "path": str(self._absolute_doc_path(item["path"])),
                        "role": item["role"],
                        "source_type": "doctrine",
                        "truth_status": "reference",
                        "precedence_rank": precedence_rank("doctrine", "reference"),
                    }
                )

        _append_matches(require_query=True)
        if docs:
            return docs

        _append_matches(require_query=False)
        return docs[:limit]

    def _build_active_authorities(
        self,
        *,
        summary: dict[str, Any],
        workspace_profile: dict[str, Any],
        workspace_projects: list[dict[str, Any]],
        document_entries: list[dict[str, Any]],
        research_entries: list[dict[str, Any]],
        urg_library_entries: list[dict[str, Any]],
        doctrine_entries: list[dict[str, Any]],
        preferences: dict[str, Any],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        surfaced_source = authority_surface_priority(preferences)
        versions = {
            "memory": f"{summary.get('memory_count', 0)} record(s)",
            "workspace": clip_value(workspace_profile.get("root") or workspace_profile.get("label") or "workspace"),
            "doctrine": f"{len(doctrine_entries)} doc(s)",
            "document": f"{len(document_entries)} source(s)",
            "live_research": f"{len(research_entries)} source(s)",
            "urg_library": f"{len(urg_library_entries)} entry(ies)",
        }

        for source_type in OPERATOR_AUTHORITY_SOURCES:
            metadata = AUTHORITY_SOURCE_METADATA[source_type]
            base_status = authority_status_for(source_type, preferences)
            if source_type == "document" and not document_entries and base_status == "active":
                base_status = "shadow"
            if source_type == "live_research" and not research_entries and base_status == "active":
                base_status = "shadow"
            if source_type == "urg_library" and not urg_library_entries and base_status == "active":
                base_status = "shadow"
            rows.append(
                {
                    "source_type": source_type,
                    "name": metadata["label"],
                    "type": metadata["type"],
                    "scope": metadata["scope"],
                    "version": versions[source_type],
                    "status": base_status,
                    "surface_priority": source_type == surfaced_source,
                }
            )
        return rows

    def _build_conflict_inbox(
        self,
        *,
        memory_conflicts: list[dict[str, Any]],
        preferences: dict[str, Any],
        conflict_decisions: dict[str, Any],
        research_entries: list[dict[str, Any]],
        limit: int,
    ) -> list[dict[str, Any]]:
        deferred_conflicts = set(normalize_knowledge_conflict_decisions(conflict_decisions).get("deferred_conflicts") or [])
        inbox: list[dict[str, Any]] = []

        for conflict in list(memory_conflicts or [])[: max(1, min(int(limit or 6), 20))]:
            memory_ids = [str(memory_id) for memory_id in list(conflict.get("memory_ids") or []) if str(memory_id).strip()]
            conflict_id = f"memory_conflict:{':'.join(sorted(memory_ids))}"
            inbox.append(
                {
                    "id": conflict_id,
                    "kind": "memory_conflict",
                    "status": "deferred" if conflict_id in deferred_conflicts else "active",
                    "severity": "warning",
                    "title": f"Conflicting {conflict.get('category') or 'memory'} memory",
                    "summary": conflict.get("reason") or "Two live memories overlap but disagree.",
                    "memory_ids": memory_ids,
                    "target_memory_id": memory_ids[0] if memory_ids else None,
                    "archive_candidate_id": memory_ids[-1] if len(memory_ids) > 1 else None,
                    "source_type": "memory",
                    "truth_status": "canonical",
                    "shared_terms": list(conflict.get("shared_terms") or []),
                    "left_excerpt": conflict.get("left_excerpt"),
                    "right_excerpt": conflict.get("right_excerpt"),
                    "actions": {
                        "focus_memory": bool(memory_ids),
                        "archive_candidate": len(memory_ids) > 1,
                        "defer": True,
                    },
                }
            )

        if research_entries and authority_status_for("live_research", preferences) == "disabled":
            conflict_id = "authority_conflict:live_research_disabled"
            inbox.append(
                {
                    "id": conflict_id,
                    "kind": "authority_conflict",
                    "status": "deferred" if conflict_id in deferred_conflicts else "active",
                    "severity": "warning",
                    "title": "Live research is present while the source is disabled",
                    "summary": "The session captured live research, but the current authority preferences disable live research as truth input.",
                    "memory_ids": [],
                    "target_memory_id": None,
                    "archive_candidate_id": None,
                    "source_type": "live_research",
                    "truth_status": "derived",
                    "shared_terms": [],
                    "actions": {
                        "focus_memory": False,
                        "archive_candidate": False,
                        "defer": True,
                    },
                }
            )
        return inbox[: max(1, min(int(limit or 6), 20))]

    def build_snapshot(
        self,
        *,
        memory_store,
        workspace_profile: dict[str, Any],
        workspace_projects: list[dict[str, Any]],
        document_store,
        live_research: dict[str, Any] | None,
        urg_library: dict[str, Any] | None = None,
        authority_preferences: dict[str, Any] | None = None,
        conflict_decisions: dict[str, Any] | None = None,
        query: str | None = None,
        limit: int = 6,
    ) -> dict[str, Any]:
        normalized_preferences = normalize_authority_preferences(authority_preferences)
        normalized_conflict_decisions = normalize_knowledge_conflict_decisions(conflict_decisions)
        memory_limit = max(1, min(int(limit or 6), 20))
        memories = memory_store.list_memories(
            query=query,
            limit=memory_limit,
            active=True,
            sort="priority",
            truth_scope="live",
        )
        memory_entries = [
            {
                "id": memory.get("id"),
                "content": memory.get("content"),
                "category": memory.get("category"),
                "why": memory.get("why"),
                "state_class": memory.get("state_class"),
                "truth_status": memory.get("truth_status"),
                "source_type": "memory_override" if memory.get("override") else "memory",
                "precedence_rank": precedence_rank(
                    "memory_override" if memory.get("override") else "memory",
                    str(memory.get("truth_status") or "canonical"),
                ),
            }
            for memory in memories
        ]

        document_entries = []
        try:
            listed_documents = list(document_store.list_documents() or [])
        except Exception:
            listed_documents = []
        for document in listed_documents[:memory_limit]:
            metadata = dict(document.get("metadata") or {})
            document_entries.append(
                {
                    "doc_id": document.get("doc_id"),
                    "chunk_count": document.get("chunk_count"),
                    "source": metadata.get("source") or document.get("doc_id"),
                    "type": metadata.get("type") or "document",
                    "source_type": "document",
                    "truth_status": "reference",
                    "precedence_rank": precedence_rank("document", "reference"),
                }
            )

        research_entries = []
        research_payload = dict(live_research or {})
        urg_library_payload = dict(urg_library or {})
        urg_library_entries = []
        for entry in list(urg_library_payload.get("entries") or [])[:memory_limit]:
            urg_library_entries.append(
                {
                    "contribution_id": entry.get("contribution_id"),
                    "title": entry.get("title"),
                    "summary": entry.get("summary"),
                    "epistemic_state": entry.get("epistemic_state"),
                    "source_type": "urg_library",
                    "truth_status": "canonical" if entry.get("epistemic_state") == "proven" else "derived",
                    "precedence_rank": precedence_rank(
                        "urg_library",
                        "canonical" if entry.get("epistemic_state") == "proven" else "derived",
                    ),
                }
            )
        for source in list(research_payload.get("sources") or [])[:memory_limit]:
            research_entries.append(
                {
                    "title": source.get("title"),
                    "url": source.get("url"),
                    "snippet": source.get("snippet"),
                    "source_type": "live_research",
                    "truth_status": "derived",
                    "precedence_rank": precedence_rank("live_research", "derived"),
                }
            )

        project_entries = [
            {
                "name": project.get("name"),
                "path": project.get("path"),
                "language": project.get("language"),
                "source_type": "workspace",
                "truth_status": "derived",
                "precedence_rank": precedence_rank("workspace", "derived"),
            }
            for project in list(workspace_projects or [])[:memory_limit]
        ]

        doctrine_entries = self._build_doctrine_entries(query=query, limit=memory_limit)
        memory_conflicts = memory_store.detect_conflicts(limit=memory_limit)

        summary = {
            "memory_count": len(memory_entries),
            "document_count": len(document_entries),
            "live_research_count": len(research_entries),
            "urg_library_count": len(urg_library_entries),
            "workspace_project_count": len(project_entries),
            "doctrine_count": len(doctrine_entries),
        }
        active_authorities = self._build_active_authorities(
            summary=summary,
            workspace_profile=workspace_profile,
            workspace_projects=workspace_projects,
            document_entries=document_entries,
            research_entries=research_entries,
            urg_library_entries=urg_library_entries,
            doctrine_entries=doctrine_entries,
            preferences=normalized_preferences,
        )
        conflict_inbox = self._build_conflict_inbox(
            memory_conflicts=memory_conflicts,
            preferences=normalized_preferences,
            conflict_decisions=normalized_conflict_decisions,
            research_entries=research_entries,
            limit=memory_limit,
        )
        authority_order = self._build_authority_order(normalized_preferences)
        surfaced_source = authority_surface_priority(normalized_preferences)
        surfaced_metadata = AUTHORITY_SOURCE_METADATA.get(surfaced_source or "")
        summary.update(
            {
                "mode": (
                    "external-allowed"
                    if research_entries and authority_status_for("live_research", normalized_preferences) != "disabled"
                    else "hybrid"
                    if document_entries or doctrine_entries
                    else "local-only"
                ),
                "source_priority": [entry["label"] for entry in authority_order[:5]],
                "surface_priority": (
                    surfaced_metadata.get("label")
                    if isinstance(surfaced_metadata, dict)
                    else None
                ),
                "active_conflict_count": len([item for item in conflict_inbox if item.get("status") == "active"]),
                "deferred_conflict_count": len([item for item in conflict_inbox if item.get("status") == "deferred"]),
            }
        )
        current_contract = (
            "Prefer workspace truth and governed local knowledge. Live research remains disabled."
            if normalized_preferences.get("preset") == "strict_local"
            else "Canonical docs outrank supporting sources; live research stays advisory."
            if normalized_preferences.get("preset") == "docs_first"
            else "Live research may widen evidence, but canonical operator truth still wins."
            if normalized_preferences.get("preset") == "exploratory"
            else "Do not invent APIs; prefer governed memory, workspace truth, and canonical docs over model prior."
        )

        return _wrap_ul_payload({
            "authority_order": authority_order,
            "active_authorities": active_authorities,
            "preferences": normalized_preferences,
            "presets": [
                {
                    "id": preset_id,
                    "label": preset["label"],
                    "description": preset["description"],
                }
                for preset_id, preset in AUTHORITY_PRESETS.items()
            ],
            "summary": summary,
            "current_contract": current_contract,
            "conflict_policy": {
                "winner_rule": "Higher precedence rank wins. If ranks tie, canonical beats derived, and live operator truth beats reference context.",
                "projection_rule": "Workbench and API surfaces render the same shared precedence snapshot instead of re-interpreting knowledge locally. Surface priority only changes operator visibility, not authority replacement.",
            },
            "surface_priority": {
                "source_type": surfaced_source,
                "label": surfaced_metadata.get("label") if isinstance(surfaced_metadata, dict) else None,
                "non_authoritative": True,
                "affects": "operator_visibility",
            },
            "sovereignty_guard": {
                "surface_priority_non_authoritative": True,
                "authority_replacement_allowed": False,
                "routing_authority": "turn_contract",
                "voice_authority": "turn_contract",
            },
            "conflict_inbox": conflict_inbox,
            "conflict_decisions": normalized_conflict_decisions,
            "memory": memory_entries,
            "documents": document_entries,
            "live_research": {
                "query": research_payload.get("query"),
                "summary": research_payload.get("summary"),
                "sources": research_entries,
            },
            "urg_library": {
                "query": urg_library_payload.get("query"),
                "summary": urg_library_payload.get("summary"),
                "entries": urg_library_entries,
            },
            "workspace": {
                "profile": dict(workspace_profile or {}),
                "projects": project_entries,
            },
            "doctrine": doctrine_entries,
        })


def clip_value(value: Any, limit: int = 72) -> str:
    """Return one short operator-facing summary string."""
    cleaned = " ".join(str(value or "").split()).strip()
    if not cleaned:
        return "n/a"
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3].rstrip()}..."
