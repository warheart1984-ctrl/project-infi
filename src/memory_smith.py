# Mythic: Memory Smith Organ
# Engineering: MemorySmithEngine
from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul.runtime import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from datetime import datetime
from src.datetime_compat import UTC
import json
from pathlib import Path
import threading
from typing import Any
from uuid import uuid4


MEMORY_CURATION_FILENAME = "memory-curation.json"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


class MemorySmith:
    """Curate durable versus stale state so old noise does not hijack new turns."""

    def __init__(self, runtime_dir: str | Path | None = None):
        self.runtime_dir = Path(runtime_dir) if runtime_dir else None
        self._lock = threading.Lock()
        self._promote_callback = None
        self._expire_callback = None

    def configure_runtime_dir(self, runtime_dir: str | Path | None) -> None:
        self.runtime_dir = Path(runtime_dir) if runtime_dir else None

    def configure_governance_callbacks(self, *, promote=None, expire=None) -> None:
        """Attach board-governed promotion and expiry handlers from the runtime."""
        self._promote_callback = promote
        self._expire_callback = expire

    def _resolve_path(self) -> Path:
        root = (
            self.runtime_dir.expanduser().resolve()
            if self.runtime_dir is not None
            else Path(__file__).resolve().parents[1] / ".runtime"
        )
        root.mkdir(parents=True, exist_ok=True)
        return root / MEMORY_CURATION_FILENAME

    def _load_payload(self) -> dict[str, Any]:
        path = self._resolve_path()
        if not path.exists():
            return {"reviews": [], "durable": [], "expired": [], "project_summary": {}}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"reviews": [], "durable": [], "expired": [], "project_summary": {}}
        if not isinstance(payload, dict):
            return {"reviews": [], "durable": [], "expired": [], "project_summary": {}}
        payload.setdefault("reviews", [])
        payload.setdefault("durable", [])
        payload.setdefault("expired", [])
        payload.setdefault("project_summary", {})
        return payload

    def _save_payload(self, payload: dict[str, Any]) -> None:
        self._resolve_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def promote_memory(self, memory: dict[str, Any]) -> dict[str, Any]:
        durable = {
            "id": memory.get("id") or f"mem_{uuid4().hex}",
            "text": str(memory.get("text") or "").strip(),
            "source": str(memory.get("source") or "memory_smith"),
            "created_at": str(memory.get("created_at") or _utc_now()),
        }
        if callable(self._promote_callback):
            promoted = self._promote_callback(durable)
            if isinstance(promoted, dict):
                durable["memory_id"] = str(promoted.get("id") or "").strip() or None
                durable["governance"] = dict(promoted.get("governance") or {})
        with self._lock:
            payload = self._load_payload()
            payload["durable"].append(durable)
            self._save_payload(payload)
        return durable

    def expire_stale_items(self, context: dict[str, Any]) -> list[str]:
        expired_messages: list[str] = []
        latest_test_status = str((context.get("project_summary") or {}).get("latest_test_status") or "").lower()
        if latest_test_status == "passed":
            expired_messages.append("Expired stale blocker state after a passing verification run.")
        return expired_messages

    def build_project_summary(self, context: dict[str, Any]) -> dict[str, Any]:
        project_summary = dict(context.get("project_summary") or {})
        latest_test_status = str(project_summary.get("latest_test_status") or "").strip().lower()
        if not latest_test_status:
            test_outcomes = context.get("test_outcomes") or []
            if isinstance(test_outcomes, list) and test_outcomes:
                latest_test_status = str((test_outcomes[-1] or {}).get("status") or "").strip().lower()
                if latest_test_status:
                    project_summary["latest_test_status"] = latest_test_status
        project_summary.setdefault("summary", "MemorySmith has no durable project summary yet.")
        if latest_test_status == "passed":
            project_summary["summary"] = "Latest known verification state is green."
        elif latest_test_status == "failed":
            project_summary["summary"] = "Latest known verification state still has failures."
        return _wrap_ul_payload(project_summary)

    def _normalize_review_targets(self, context: dict[str, Any]) -> tuple[list[str], list[str]]:
        """Return explicit expiry targets supplied by the caller, when present."""
        target_ids: list[str] = []
        target_texts: list[str] = []
        for field in ("expire_memory_ids", "stale_blocker_memory_ids", "target_memory_ids"):
            for item in list(context.get(field) or []):
                cleaned = str(item or "").strip()
                if cleaned and cleaned not in target_ids:
                    target_ids.append(cleaned)
        for field in ("expire_memory_texts", "stale_blocker_memory_texts", "target_memory_texts"):
            for item in list(context.get(field) or []):
                cleaned = " ".join(str(item or "").split()).strip()
                if cleaned and cleaned not in target_texts:
                    target_texts.append(cleaned)
        return target_ids, target_texts

    def review_memory_candidates(self, context: dict[str, Any]) -> dict[str, Any]:
        manual_notes = list(context.get("manual_notes") or [])
        test_outcomes = list(context.get("test_outcomes") or [])
        durable: list[dict[str, Any]] = []
        session_only: list[dict[str, Any]] = []
        expired: list[dict[str, Any]] = []
        target_ids, target_texts = self._normalize_review_targets(context)

        for note in manual_notes:
            text = " ".join(str(note or "").split()).strip()
            if not text:
                continue
            bucket = durable if any(token in text.lower() for token in ("always", "default", "project", "canonical")) else session_only
            bucket.append({"text": text, "source": "manual_note"})

        latest_test_status = ""
        if test_outcomes:
            latest_test_status = str((test_outcomes[-1] or {}).get("status") or "").strip().lower()
        if latest_test_status == "passed":
            expiry_item = {
                "reason": "stale_blocker",
                "message": "Latest tests passed, so stale blocker state should not dominate future turns.",
            }
            if target_ids:
                expiry_item["target_ids"] = list(target_ids)
            if target_texts:
                expiry_item["target_texts"] = list(target_texts)
            expired.append(expiry_item)
        elif latest_test_status == "failed":
            session_only.append(
                {
                    "text": "Recent verification still reports a failing state; keep it session-local until reconfirmed.",
                    "source": "test_outcome",
                }
            )

        project_summary = self.build_project_summary(
            {
                **context,
                "test_outcomes": test_outcomes,
                "project_summary": {
                    **dict(context.get("project_summary") or {}),
                    **({"latest_test_status": latest_test_status} if latest_test_status else {}),
                },
            }
        )
        review = {
            "review_id": f"memory_review_{uuid4().hex}",
            "reviewed_at": _utc_now(),
            "durable": durable,
            "session_only": session_only,
            "expired": expired,
            "project_summary": project_summary,
            "summary": (
                f"MemorySmith kept {len(durable)} durable item(s), "
                f"{len(session_only)} session-only item(s), and expired {len(expired)} stale item(s)."
            ),
        }
        promoted = []
        if callable(self._promote_callback):
            for item in durable:
                promoted_payload = self._promote_callback(
                    {
                        "text": item.get("text"),
                        "source": item.get("source") or "memory_smith_review",
                        "created_at": review["reviewed_at"],
                    }
                )
                if isinstance(promoted_payload, dict):
                    promoted.append(
                        {
                            "memory_id": str(promoted_payload.get("id") or "").strip() or None,
                            "category": str(promoted_payload.get("category") or "").strip() or None,
                            "governance": dict(promoted_payload.get("governance") or {}),
                        }
                    )
        expired_actions = []
        if callable(self._expire_callback):
            for item in expired:
                expired_payload = self._expire_callback(item)
                if isinstance(expired_payload, dict):
                    expired_actions.append(expired_payload)
        review["promoted"] = promoted
        review["expired_actions"] = expired_actions
        with self._lock:
            payload = self._load_payload()
            payload["reviews"].append(review)
            payload["project_summary"] = project_summary
            payload["expired"].extend(expired)
            payload["durable"].extend(durable)
            self._save_payload(payload)
        return _wrap_ul_payload(review)

    def observe_lifecycle(self, session_id: str, lifecycle: dict[str, Any]) -> dict[str, Any] | None:
        action_id = str(lifecycle.get("action_id") or "").strip().lower()
        stage = str(lifecycle.get("stage") or "").strip().lower()
        if action_id != "run_pytest" or stage not in {"executed", "failed"}:
            return None
        status = "passed" if stage == "executed" and str(lifecycle.get("result_status") or "").lower() != "failed" else "failed"
        review_context = {
            "session_id": session_id,
            "test_outcomes": [{"status": status, "source": "action_lifecycle"}],
            "project_summary": {"latest_test_status": status},
        }
        target_ids, target_texts = self._normalize_review_targets(lifecycle)
        if target_ids:
            review_context["expire_memory_ids"] = target_ids
        if target_texts:
            review_context["expire_memory_texts"] = target_texts
        return self.review_memory_candidates(review_context)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            payload = self._load_payload()
        return _wrap_ul_payload({
            "review_count": len(payload.get("reviews") or []),
            "durable_count": len(payload.get("durable") or []),
            "expired_count": len(payload.get("expired") or []),
            "project_summary": dict(payload.get("project_summary") or {}),
        })
