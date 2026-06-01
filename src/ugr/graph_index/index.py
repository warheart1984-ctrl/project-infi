"""In-memory graph index over unified pattern ledger claims."""

from __future__ import annotations

from collections import defaultdict
import re
from typing import Any

from src.ugr.platform.tenant_registry import normalize_tenant_id


_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_./-]{3,}")


def claim_haystack(row: dict[str, Any]) -> str:
    return " ".join(
        [str(row.get("subject") or ""), str(row.get("predicate") or ""), str(row.get("object") or "")]
    ).lower()


def normalize_terms(terms: list[str]) -> list[str]:
    return [" ".join(str(term).split()).strip().lower() for term in terms if str(term).strip()]


def claim_matches_terms(row: dict[str, Any], terms: list[str]) -> bool:
    haystack = claim_haystack(row)
    return any(term in haystack for term in terms)


def _subject_key(row: dict[str, Any]) -> str:
    return " ".join(str(row.get("subject") or "").split()).strip().lower()


def _predicate_key(row: dict[str, Any]) -> str:
    return " ".join(str(row.get("predicate") or "").split()).strip().lower()


def _index_terms(row: dict[str, Any]) -> set[str]:
    terms: set[str] = set()
    for token in _TOKEN_PATTERN.findall(claim_haystack(row)):
        terms.add(token.lower())
    subject = _subject_key(row)
    predicate = _predicate_key(row)
    if subject:
        terms.add(subject)
    if predicate:
        terms.add(predicate)
    return terms


class GraphClaimIndex:
    """Adjacency index for claim queries — JSONL remains canonical source of truth."""

    INDEX_VERSION = "1.0"

    def __init__(self) -> None:
        self._claims: dict[str, dict[str, Any]] = {}
        self._insertion_order: list[str] = []
        self._by_tenant: dict[str, set[str]] = defaultdict(set)
        self._by_subject: dict[str, set[str]] = defaultdict(set)
        self._by_predicate: dict[str, set[str]] = defaultdict(set)
        self._by_term: dict[str, set[str]] = defaultdict(set)
        self._subject_predicate_edges: dict[tuple[str, str], set[str]] = defaultdict(set)

    @property
    def claim_count(self) -> int:
        return len(self._claims)

    def clear(self) -> None:
        self._claims.clear()
        self._insertion_order.clear()
        self._by_tenant.clear()
        self._by_subject.clear()
        self._by_predicate.clear()
        self._by_term.clear()
        self._subject_predicate_edges.clear()

    def upsert_claim(self, row: dict[str, Any]) -> None:
        claim_id = str(row.get("claim_id") or "").strip()
        if not claim_id:
            return
        if claim_id not in self._claims:
            self._insertion_order.append(claim_id)
        self._claims[claim_id] = dict(row)
        tenant_scope = normalize_tenant_id(row.get("tenant_scope") or "global")
        subject = _subject_key(row)
        predicate = _predicate_key(row)
        self._by_tenant[tenant_scope].add(claim_id)
        if subject:
            self._by_subject[subject].add(claim_id)
        if predicate:
            self._by_predicate[predicate].add(claim_id)
        if subject and predicate:
            self._subject_predicate_edges[(subject, predicate)].add(claim_id)
        for term in _index_terms(row):
            self._by_term[term].add(claim_id)

    def rebuild(self, claims: list[dict[str, Any]]) -> None:
        self.clear()
        for row in claims:
            self.upsert_claim(row)

    def _tenant_allowed(self, row: dict[str, Any], query_tenant: str) -> bool:
        if query_tenant == "global":
            return True
        row_tenant = normalize_tenant_id(row.get("tenant_scope") or "global")
        return row_tenant in {query_tenant, "global"}

    def _candidate_ids(self, terms: list[str]) -> set[str]:
        candidate: set[str] = set()
        for term in terms:
            candidate.update(self._by_term.get(term, set()))
            for key, values in self._by_subject.items():
                if term in key:
                    candidate.update(values)
            for key, values in self._by_predicate.items():
                if term in key:
                    candidate.update(values)
        return candidate

    def read_claims(self, *, tenant_scope: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        normalized = normalize_tenant_id(tenant_scope or "global")
        rows: list[dict[str, Any]] = []
        for claim_id in self._insertion_order:
            row = self._claims.get(claim_id)
            if not row:
                continue
            if tenant_scope and normalize_tenant_id(row.get("tenant_scope") or "global") != normalized:
                if normalized != "global":
                    continue
            rows.append(dict(row))
        return rows[-limit:]

    def query_by_subject(self, subject: str, *, tenant_scope: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        needle = " ".join(str(subject or "").split()).strip().lower()
        if not needle:
            return []
        query_tenant = normalize_tenant_id(tenant_scope or "global")
        matches: list[dict[str, Any]] = []
        for claim_id in self._insertion_order:
            row = self._claims.get(claim_id)
            if not row:
                continue
            if not self._tenant_allowed(row, query_tenant):
                continue
            if needle in str(row.get("subject") or "").lower():
                matches.append(dict(row))
        return matches[-limit:]

    def query_related(
        self,
        terms: list[str],
        *,
        tenant_scope: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        normalized_terms = normalize_terms(terms)
        if not normalized_terms:
            return []
        query_tenant = normalize_tenant_id(tenant_scope or "global")
        candidate_ids = self._candidate_ids(normalized_terms)
        search_ids = (
            list(self._insertion_order)
            if not candidate_ids
            else [claim_id for claim_id in self._insertion_order if claim_id in candidate_ids]
        )
        matches: list[dict[str, Any]] = []
        for claim_id in search_ids:
            row = self._claims.get(claim_id)
            if not row:
                continue
            if not self._tenant_allowed(row, query_tenant):
                continue
            if claim_matches_terms(row, normalized_terms):
                matches.append(dict(row))
        return matches[-limit:]

    def related_by_subject_predicate(
        self,
        subject: str,
        predicate: str,
        *,
        tenant_scope: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        subject_key = " ".join(str(subject or "").split()).strip().lower()
        predicate_key = " ".join(str(predicate or "").split()).strip().lower()
        query_tenant = normalize_tenant_id(tenant_scope or "global")
        claim_ids = self._subject_predicate_edges.get((subject_key, predicate_key), set())
        matches: list[dict[str, Any]] = []
        for claim_id in self._insertion_order:
            if claim_id not in claim_ids:
                continue
            row = self._claims.get(claim_id)
            if not row:
                continue
            if not self._tenant_allowed(row, query_tenant):
                continue
            matches.append(dict(row))
        return matches[-limit:]

    def stats(self) -> dict[str, Any]:
        return {
            "index_version": self.INDEX_VERSION,
            "claim_count": self.claim_count,
            "tenant_buckets": len(self._by_tenant),
            "subject_buckets": len(self._by_subject),
            "predicate_buckets": len(self._by_predicate),
            "term_buckets": len(self._by_term),
            "subject_predicate_edges": len(self._subject_predicate_edges),
        }
