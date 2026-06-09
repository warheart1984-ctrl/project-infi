"""Monotonic truth store for proven-false claims."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.rls.reasoning_graph import claim_fingerprint

_REGISTRY_FILENAME = "rls_falsity_registry.jsonl"


def _default_registry_path() -> Path:
    try:
        from src.temporal_replay.paths import default_runtime_dir

        base = default_runtime_dir()
    except Exception:
        base = Path(
            os.environ.get("AAIS_RUNTIME_DIR")
            or os.environ.get("PROJECT_INFI_RUNTIME", ".runtime")
        )
    return Path(base) / _REGISTRY_FILENAME


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FalsityRegistry:
    """Append-only store of proven-false claim fingerprints."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _default_registry_path()

    @property
    def path(self) -> Path:
        return self._path

    def _ensure_parent(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def list_falsified(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self._path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

    def is_falsified(self, text: str) -> dict[str, Any] | None:
        fp = claim_fingerprint(text)
        return self.is_falsified_fingerprint(fp)

    def is_falsified_fingerprint(self, fingerprint: str) -> dict[str, Any] | None:
        fp = str(fingerprint or "").strip()
        if not fp:
            return None
        for record in reversed(self.list_falsified()):
            if record.get("claim_fingerprint") == fp and record.get("status") == "falsified":
                return record
        return None

    def record_falsified(
        self,
        *,
        text: str,
        reason: str,
        graph_id: str | None = None,
        invariant_id: str | None = None,
        rejection_source: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_parent()
        entry = {
            "claim_fingerprint": claim_fingerprint(text),
            "claim_text": str(text or "")[:500],
            "status": "falsified",
            "reason": reason,
            "graph_id": graph_id,
            "invariant_id": invariant_id,
            "recorded_at": _utc_now_iso(),
            "epistemic_state": "rejected",
            "rejection_source": str(rejection_source or "falsity_registry").strip() or "falsity_registry",
        }
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def record_falsified_fingerprint(
        self,
        *,
        fingerprint: str,
        reason: str,
        sync_mode: str = "fingerprint_only",
        rejection_source: str | None = None,
    ) -> dict[str, Any]:
        """Record a proven-false claim by fingerprint when full text is unavailable."""
        fp = str(fingerprint or "").strip()
        if not fp:
            raise ValueError("fingerprint required")
        if self.is_falsified_fingerprint(fp):
            return self.is_falsified_fingerprint(fp)  # type: ignore[return-value]
        self._ensure_parent()
        entry = {
            "claim_fingerprint": fp,
            "claim_text": "",
            "status": "falsified",
            "reason": reason,
            "sync_mode": sync_mode,
            "recorded_at": _utc_now_iso(),
            "epistemic_state": "rejected",
            "rejection_source": str(rejection_source or "falsity_registry").strip() or "falsity_registry",
        }
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def has_valid_override_for_fingerprint(
        self,
        fingerprint: str,
        evidence_refs: list[str] | None = None,
    ) -> bool:
        fp = str(fingerprint or "").strip()
        if not fp:
            return False
        refs = {str(r).strip() for r in (evidence_refs or []) if str(r).strip()}
        for record in reversed(self.list_falsified()):
            if record.get("claim_fingerprint") != fp:
                continue
            if record.get("status") != "operator_override":
                continue
            override_refs = {str(r).strip() for r in (record.get("new_evidence_refs") or [])}
            if not refs or override_refs & refs:
                return True
        return False

    def is_resurrection_blocked(
        self,
        fingerprint: str,
        *,
        evidence_refs: list[str] | None = None,
    ) -> bool:
        """True when a falsified fingerprint cannot re-enter without a valid override."""
        fp = str(fingerprint or "").strip()
        if not fp or not self.is_falsified_fingerprint(fp):
            return False
        return not self.has_valid_override_for_fingerprint(fp, evidence_refs)

    def record_override(
        self,
        *,
        text: str,
        operator_id: str,
        new_evidence_refs: list[str],
        reason: str,
    ) -> dict[str, Any]:
        self._ensure_parent()
        entry = {
            "claim_fingerprint": claim_fingerprint(text),
            "claim_text": str(text or "")[:500],
            "status": "operator_override",
            "operator_id": operator_id,
            "new_evidence_refs": list(new_evidence_refs),
            "reason": reason,
            "recorded_at": _utc_now_iso(),
        }
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def has_valid_override(self, text: str, evidence_refs: list[str]) -> bool:
        fp = claim_fingerprint(text)
        refs = {str(r).strip() for r in evidence_refs if str(r).strip()}
        for record in reversed(self.list_falsified()):
            if record.get("claim_fingerprint") != fp:
                continue
            if record.get("status") != "operator_override":
                continue
            override_refs = {str(r).strip() for r in (record.get("new_evidence_refs") or [])}
            if override_refs & refs:
                return True
        return False


def check_monotonic_falsity(
    graph: dict[str, Any],
    registry: FalsityRegistry | None = None,
) -> list[dict[str, Any]]:
    """Reject only when the terminal conclusion reasserts a proven-false claim."""
    reg = registry or FalsityRegistry()
    violations: list[dict[str, Any]] = []
    conclusion_id = str(graph.get("conclusion_id") or "")
    if not conclusion_id:
        return violations

    nodes = {str(n.get("id")): n for n in graph.get("nodes") or []}
    conclusion = nodes.get(conclusion_id, {})
    ctext = str(conclusion.get("text") or "")
    if not ctext or not reg.is_falsified(ctext):
        return violations

    refs = list(conclusion.get("evidence_refs") or [])
    if reg.has_valid_override(ctext, refs):
        return violations

    violations.append(
        {
            "code": "monotonic_falsity_violation",
            "severity": "error",
            "node_ids": [conclusion_id],
            "detail": "Terminal conclusion reasserts proven-false claim without operator override",
        }
    )
    return violations
