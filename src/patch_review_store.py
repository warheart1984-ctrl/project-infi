# Mythic: Patch Review Store
# Engineering: PatchReviewStoreEngine
from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
import json
from pathlib import Path
import threading
from typing import Any

from src.state_hygiene import (
    filter_operator_records,
    normalize_truth_scope,
    project_record,
)


PATCH_REVIEW_FILENAME = "patch-reviews.json"


def _wrap_review(review: dict[str, Any]) -> dict[str, Any]:
    from src.aais_ul.runtime import wrap_runtime_snapshot

    return wrap_runtime_snapshot(dict(review))


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


class PatchReviewStore:
    """Durable review records for proposal-first PatchForge plans."""

    def __init__(self, runtime_dir: str | Path | None = None):
        self.runtime_dir = Path(runtime_dir) if runtime_dir else None
        self._lock = threading.Lock()

    def configure_runtime_dir(self, runtime_dir: str | Path | None) -> None:
        self.runtime_dir = Path(runtime_dir) if runtime_dir else None

    def _resolve_path(self) -> Path:
        root = (
            self.runtime_dir.expanduser().resolve()
            if self.runtime_dir is not None
            else Path(__file__).resolve().parents[1] / ".runtime"
        )
        root.mkdir(parents=True, exist_ok=True)
        return root / PATCH_REVIEW_FILENAME

    def _load_payload(self) -> dict[str, Any]:
        path = self._resolve_path()
        if not path.exists():
            return {"reviews": []}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"reviews": []}
        if not isinstance(payload, dict):
            return {"reviews": []}
        reviews = payload.get("reviews")
        if not isinstance(reviews, list):
            reviews = []
        return {"reviews": [self._normalize_review(review) for review in reviews if isinstance(review, dict)]}

    def _save_payload(self, payload: dict[str, Any]) -> None:
        self._resolve_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _normalize_review(self, review: dict[str, Any]) -> dict[str, Any]:
        history = review.get("history")
        if not isinstance(history, list):
            history = []
        target_decisions = review.get("target_decisions")
        if not isinstance(target_decisions, dict):
            target_decisions = {}
        current_decision = review.get("current_decision")
        if not isinstance(current_decision, dict):
            current_decision = {
                "state": str(review.get("status") or "proposed"),
                "note": "",
                "target_kind": "plan",
                "target_index": None,
                "updated_at": str(review.get("updated_at") or review.get("created_at") or ""),
            }
        patch_plan = review.get("patch_plan")
        if not isinstance(patch_plan, dict):
            patch_plan = {}
        created_at = str(review.get("created_at") or _utc_now())
        updated_at = str(review.get("updated_at") or created_at)
        status = str(review.get("status") or current_decision.get("state") or "proposed")
        normalized = {
            "id": str(review.get("id") or patch_plan.get("plan_id") or ""),
            "session_id": str(review.get("session_id") or ""),
            "goal": str(review.get("goal") or patch_plan.get("goal") or "").strip(),
            "status": status,
            "created_at": created_at,
            "updated_at": updated_at,
            "state_class": str(review.get("state_class") or patch_plan.get("state_class") or "").strip() or None,
            "truth_status": str(review.get("truth_status") or patch_plan.get("truth_status") or "").strip() or None,
            "retention_status": str(review.get("retention_status") or "").strip() or None,
            "patch_plan": patch_plan,
            "current_decision": {
                "state": str(current_decision.get("state") or status or "proposed"),
                "note": str(current_decision.get("note") or "").strip(),
                "target_kind": str(current_decision.get("target_kind") or "plan"),
                "target_index": current_decision.get("target_index"),
                "updated_at": str(current_decision.get("updated_at") or updated_at),
            },
            "target_decisions": {
                str(key): {
                    "state": str((value or {}).get("state") or "proposed"),
                    "note": str((value or {}).get("note") or "").strip(),
                    "target_kind": str((value or {}).get("target_kind") or "plan"),
                    "target_index": (value or {}).get("target_index"),
                    "updated_at": str((value or {}).get("updated_at") or updated_at),
                }
                for key, value in target_decisions.items()
                if isinstance(value, dict)
            },
            "history": [dict(item) for item in history if isinstance(item, dict)],
            "decision_counts": self._build_decision_counts(
                current_decision=current_decision,
                target_decisions=target_decisions,
            ),
            "apply_gate": self._build_apply_gate(
                current_decision=current_decision,
                target_decisions=target_decisions,
                patch_plan=patch_plan,
            ),
        }
        projected = project_record(normalized, kind="review", source_type="review")
        projected.pop("_state_hygiene_kind", None)
        return projected

    def _build_decision_counts(
        self,
        *,
        current_decision: dict[str, Any] | None,
        target_decisions: dict[str, Any] | None,
    ) -> dict[str, int]:
        counts = {"proposed": 0, "accepted": 0, "rejected": 0, "needs_revision": 0}
        state = str((current_decision or {}).get("state") or "proposed").strip().lower()
        if state in counts:
            counts[state] += 1
        for decision in (target_decisions or {}).values():
            decision_state = str((decision or {}).get("state") or "").strip().lower()
            if decision_state in counts:
                counts[decision_state] += 1
        return counts

    def _build_apply_gate(
        self,
        *,
        current_decision: dict[str, Any] | None,
        target_decisions: dict[str, Any] | None,
        patch_plan: dict[str, Any] | None,
    ) -> dict[str, Any]:
        blockers: list[str] = []
        decision_state = str((current_decision or {}).get("state") or "proposed").strip().lower()
        if decision_state != "accepted":
            blockers.append("Review approval must be accepted before Jarvis can apply this patch.")
        for key, decision in (target_decisions or {}).items():
            target_state = str((decision or {}).get("state") or "").strip().lower()
            if target_state in {"rejected", "needs_revision"}:
                blockers.append(f"{key} is still marked {target_state.replace('_', ' ')}.")
        if not list((patch_plan or {}).get("target_files") or []):
            blockers.append("Patch review does not contain any target files.")
        return {
            "ready": len(blockers) == 0,
            "decision_state": decision_state,
            "blockers": blockers,
        }

    def _build_review_targets(self, patch_plan: dict[str, Any]) -> dict[str, Any]:
        hunks = [dict(hunk) for hunk in list((patch_plan or {}).get("hunks") or []) if isinstance(hunk, dict)]
        return {
            "target_files": list((patch_plan or {}).get("target_files") or []),
            "hunks": [
                {
                    "index": hunk.get("index"),
                    "file_path": hunk.get("file_path"),
                    "header": hunk.get("header"),
                    "line_count": int(hunk.get("line_count") or 0),
                }
                for hunk in hunks
            ],
            "line_action_count": sum(int(hunk.get("line_count") or 0) for hunk in hunks),
        }

    def _find_review_index(self, payload: dict[str, Any], review_id: str) -> int | None:
        for index, review in enumerate(payload.get("reviews", [])):
            if str(review.get("id") or "") == str(review_id):
                return index
        return None

    def create_review(
        self,
        *,
        session_id: str | None,
        patch_plan: dict[str, Any],
    ) -> dict[str, Any]:
        plan_id = str((patch_plan or {}).get("plan_id") or "").strip()
        if not plan_id:
            raise ValueError("Patch review requires a patch plan with plan_id.")
        now = _utc_now()
        record = {
            "id": plan_id,
            "session_id": str(session_id or "").strip(),
            "goal": str((patch_plan or {}).get("goal") or "").strip(),
            "status": "proposed",
            "created_at": now,
            "updated_at": now,
            "state_class": str((patch_plan or {}).get("state_class") or "").strip() or None,
            "truth_status": str((patch_plan or {}).get("truth_status") or "").strip() or None,
            "retention_status": None,
            "patch_plan": dict(patch_plan or {}),
            "current_decision": {
                "state": "proposed",
                "note": "",
                "target_kind": "plan",
                "target_index": None,
                "updated_at": now,
            },
            "target_decisions": {},
            "history": [
                {
                    "state": "proposed",
                    "note": "",
                    "target_kind": "plan",
                    "target_index": None,
                    "created_at": now,
                }
            ],
        }
        with self._lock:
            payload = self._load_payload()
            index = self._find_review_index(payload, plan_id)
            if index is not None:
                existing = self._normalize_review(payload["reviews"][index])
                existing["patch_plan"] = dict(patch_plan or {})
                existing["goal"] = record["goal"]
                existing["updated_at"] = now
                payload["reviews"][index] = existing
                self._save_payload(payload)
                return _wrap_review(dict(existing))
            payload["reviews"].append(record)
            self._save_payload(payload)
        return _wrap_review(dict(self._normalize_review(record)))

    def list_reviews(
        self,
        *,
        session_id: str | None = None,
        limit: int = 20,
        truth_scope: str = "live",
    ) -> list[dict[str, Any]]:
        capped_limit = min(max(1, int(limit or 20)), 100)
        with self._lock:
            payload = self._load_payload()
        reviews = payload.get("reviews", [])
        if session_id:
            reviews = [review for review in reviews if review.get("session_id") == session_id]
        ordered = sorted(
            reviews,
            key=lambda item: (str(item.get("updated_at") or ""), str(item.get("id") or "")),
            reverse=True,
        )
        projected = [
            {
                "id": review["id"],
                "session_id": review["session_id"],
                "goal": review["goal"],
                "status": review["status"],
                "created_at": review["created_at"],
                "updated_at": review["updated_at"],
                "state_class": review.get("state_class"),
                "truth_status": review.get("truth_status"),
                "retention_status": review.get("retention_status"),
                "state_hygiene": dict(review.get("state_hygiene") or {}),
                "current_decision": dict(review.get("current_decision") or {}),
                "decision_counts": dict(review.get("decision_counts") or {}),
                "apply_gate": dict(review.get("apply_gate") or {}),
                "target_files": list((review.get("patch_plan") or {}).get("target_files") or []),
                "hunk_count": int((review.get("patch_plan") or {}).get("hunk_count") or 0),
            }
            for review in ordered
        ]
        if normalize_truth_scope(truth_scope) != "all":
            projected = filter_operator_records(projected, truth_scope=truth_scope)
        return projected[:capped_limit]

    def get_review(self, review_id: str) -> dict[str, Any] | None:
        with self._lock:
            payload = self._load_payload()
        index = self._find_review_index(payload, review_id)
        if index is None:
            return None
        review = self._normalize_review(payload["reviews"][index])
        review["review_targets"] = self._build_review_targets(review.get("patch_plan") or {})
        return _wrap_review(dict(review))

    def record_decision(
        self,
        review_id: str,
        *,
        decision: str,
        note: str | None = None,
        target_kind: str = "plan",
        target_index: int | None = None,
    ) -> dict[str, Any] | None:
        normalized_decision = str(decision or "").strip().lower()
        if normalized_decision not in {"accepted", "rejected", "needs_revision"}:
            raise ValueError("decision must be accepted, rejected, or needs_revision.")
        normalized_target_kind = str(target_kind or "plan").strip().lower()
        if normalized_target_kind not in {"plan", "hunk", "line"}:
            raise ValueError("target_kind must be plan, hunk, or line.")
        if normalized_target_kind != "plan" and target_index is None:
            raise ValueError("target_index is required for hunk or line decisions.")
        now = _utc_now()
        with self._lock:
            payload = self._load_payload()
            index = self._find_review_index(payload, review_id)
            if index is None:
                return None
            record = self._normalize_review(payload["reviews"][index])
            event = {
                "state": normalized_decision,
                "note": str(note or "").strip(),
                "target_kind": normalized_target_kind,
                "target_index": target_index,
                "created_at": now,
            }
            record["updated_at"] = now
            if normalized_target_kind == "plan":
                record["status"] = normalized_decision
                record["current_decision"] = {
                    "state": normalized_decision,
                    "note": event["note"],
                    "target_kind": event["target_kind"],
                    "target_index": target_index,
                    "updated_at": now,
                }
            else:
                key = f"{normalized_target_kind}:{target_index}"
                record.setdefault("target_decisions", {})[key] = {
                    "state": normalized_decision,
                    "note": event["note"],
                    "target_kind": normalized_target_kind,
                    "target_index": target_index,
                    "updated_at": now,
                }
            record.setdefault("history", []).append(event)
            record["decision_counts"] = self._build_decision_counts(
                current_decision=record.get("current_decision"),
                target_decisions=record.get("target_decisions"),
            )
            payload["reviews"][index] = record
            self._save_payload(payload)
            review = self._normalize_review(record)
            review["review_targets"] = self._build_review_targets(review.get("patch_plan") or {})
            return _wrap_review(dict(review))

    def compact_reviews(self) -> dict[str, Any]:
        """Archive non-live reviews so proposal artifacts stop looking current."""
        archived_reviews = 0
        now = _utc_now()
        with self._lock:
            payload = self._load_payload()
            for review in payload.get("reviews", []):
                projected = self._normalize_review(review)
                if projected.get("state_class") == "live":
                    continue
                if str(projected.get("retention_status") or "") == "archived":
                    continue
                review["retention_status"] = "archived"
                review["updated_at"] = now
                review.setdefault("history", []).append(
                    {
                        "state": "archived",
                        "note": "Archived by state hygiene compaction.",
                        "target_kind": "plan",
                        "target_index": None,
                        "created_at": now,
                    }
                )
                archived_reviews += 1
            if archived_reviews:
                self._save_payload(payload)
        return {"archived_reviews": archived_reviews}
