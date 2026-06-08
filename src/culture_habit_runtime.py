"""Culture habit runtime — pattern mining and governed adoption (Stage 5 / Release 36)."""

# Mythic: Culture Habit Runtime
# Engineering: CultureHabitRuntimeEngine
from __future__ import annotations

import json
import os
import threading
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.culture_habit_registry import HABIT_VERSION, adopted_habits, save_adopted_habit
from src.workflow_family_registry import list_handoff_edges

PATTERN_VERSION = "habit_pattern.v1"
MIN_OCCURRENCE_DEFAULT = 3


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def _min_occurrence() -> int:
    raw = os.getenv("AAIS_CULTURE_HABIT_MIN_OCCURRENCE", str(MIN_OCCURRENCE_DEFAULT))
    try:
        return max(1, int(raw))
    except ValueError:
        return MIN_OCCURRENCE_DEFAULT


class CultureHabitRuntime:
    def __init__(self, *, runtime_dir: Path | None = None, repo_root: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._repo_root = repo_root or Path(__file__).resolve().parents[1]
        self._candidates_dir = self._runtime_dir / "culture_habit_candidates"
        self._preferences_path = self._runtime_dir / "jarvis_memory_board_preferences.v1.json"
        self._lock = threading.Lock()

    def mine_habit_patterns(
        self,
        *,
        session_id: str | None = None,
        window_days: int = 30,
    ) -> dict[str, Any]:
        """HCC-0 observe-only mining from ledger + mesh runs."""
        since = (datetime.now(timezone.utc) - timedelta(days=max(1, window_days))).replace(microsecond=0)
        since_iso = since.isoformat().replace("+00:00", "Z")
        counters: Counter[str] = Counter()
        meta: dict[str, dict[str, Any]] = {}

        scopes = [str(session_id)] if session_id else ["global"]
        try:
            from src.operator_decision_ledger import operator_decision_ledger_store

            for scope in scopes:
                for row in operator_decision_ledger_store.list_events(scope, since=since_iso, limit=500):
                    key, pattern = self._pattern_from_ledger_row(row)
                    if key:
                        counters[key] += 1
                        meta[key] = pattern
        except Exception:
            pass

        mesh_dir = self._runtime_dir / "organ_mesh_runs"
        if mesh_dir.is_dir():
            for path in mesh_dir.glob("*.json"):
                try:
                    run = json.loads(path.read_text(encoding="utf-8"))
                    recorded = str(run.get("completed_at") or run.get("started_at") or "")
                    if recorded and recorded < since_iso:
                        continue
                    key, pattern = self._pattern_from_mesh_run(run)
                    if key:
                        counters[key] += 1
                        meta[key] = pattern
                except (json.JSONDecodeError, OSError):
                    continue

        min_occ = _min_occurrence()
        candidates: list[dict[str, Any]] = []
        for key, count in counters.most_common():
            if count < min_occ:
                continue
            base = dict(meta.get(key) or {})
            candidate = self._build_candidate(base, occurrence_count=count)
            candidates.append(candidate)
            self._persist_candidate(candidate)

        return {
            "outcome": "observed",
            "hcc_class": "HCC-0",
            "candidate_count": len(candidates),
            "candidates": candidates,
            "window_days": window_days,
            "min_occurrence": min_occ,
            "claim_label": "asserted",
        }

    def _pattern_from_ledger_row(self, row: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
        kind = str(row.get("decision_kind") or "")
        if kind == "organ_handoff":
            handoff = dict(row.get("handoff") or {})
            src = str(handoff.get("source_family_id") or "")
            tgt = str(handoff.get("target_family_id") or "")
            chains = [
                str(handoff.get("source_chain_id") or ""),
                str(handoff.get("chain_id") or ""),
            ]
            chains = [c for c in chains if c]
            key = f"mesh_path:{src}:{tgt}:{':'.join(chains)}"
            return key, {
                "pattern_kind": "mesh_path",
                "source_family_id": src,
                "target_family_id": tgt,
                "chain_ids": chains,
                "last_seen_at": row.get("recorded_at"),
            }
        if kind == "organ_mesh_run":
            mesh = dict(row.get("mesh_run") or {})
            plan = dict(mesh.get("plan") or {})
            edge = dict(plan.get("edge") or {})
            if edge:
                src = str(edge.get("source_family_id") or "")
                tgt = str(edge.get("target_family_id") or "")
                chains = [
                    str(edge.get("source_chain_id") or ""),
                    str(edge.get("chain_id") or ""),
                ]
                chains = [c for c in chains if c]
                key = f"mesh_path:{src}:{tgt}:{':'.join(chains)}"
                return key, {
                    "pattern_kind": "mesh_path",
                    "source_family_id": src,
                    "target_family_id": tgt,
                    "chain_ids": chains,
                    "last_seen_at": row.get("recorded_at"),
                }
        if kind == "autonomic_routine":
            routine_id = str(row.get("routine_id") or "")
            if routine_id:
                key = f"routine:{routine_id}"
                return key, {
                    "pattern_kind": "routine",
                    "chain_ids": [routine_id],
                    "last_seen_at": row.get("recorded_at"),
                }
        if kind == "plug_execution":
            ctx = dict(row.get("event_context") or {})
            plug_id = str(ctx.get("plug_id") or "")
            if plug_id:
                key = f"chain:{plug_id}"
                return key, {
                    "pattern_kind": "chain",
                    "chain_ids": [plug_id],
                    "last_seen_at": row.get("recorded_at"),
                }
        return None, {}

    def _pattern_from_mesh_run(self, run: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
        plan = dict(run.get("plan") or {})
        edge = dict(plan.get("edge") or {})
        if not edge:
            return None, {}
        src = str(edge.get("source_family_id") or "")
        tgt = str(edge.get("target_family_id") or "")
        chains = [str(edge.get("source_chain_id") or ""), str(edge.get("chain_id") or "")]
        chains = [c for c in chains if c]
        key = f"mesh_path:{src}:{tgt}:{':'.join(chains)}"
        return key, {
            "pattern_kind": "mesh_path",
            "source_family_id": src,
            "target_family_id": tgt,
            "chain_ids": chains,
            "last_seen_at": run.get("completed_at") or run.get("started_at"),
        }

    def _build_candidate(self, base: dict[str, Any], *, occurrence_count: int) -> dict[str, Any]:
        pattern_key = self._pattern_key(base)
        return {
            "pattern_version": PATTERN_VERSION,
            "pattern_key": pattern_key,
            "candidate_id": f"cand_{uuid4().hex[:12]}",
            "pattern_kind": base.get("pattern_kind") or "chain",
            "source_family_id": base.get("source_family_id"),
            "target_family_id": base.get("target_family_id"),
            "chain_ids": list(base.get("chain_ids") or []),
            "occurrence_count": occurrence_count,
            "last_seen_at": base.get("last_seen_at") or _utc_now_iso(),
            "hcc_class": "HCC-1",
            "claim_label": "asserted",
            "operator_promoted": False,
        }

    def _pattern_key(self, pattern: dict[str, Any]) -> str:
        kind = str(pattern.get("pattern_kind") or "chain")
        if kind == "mesh_path":
            src = str(pattern.get("source_family_id") or "")
            tgt = str(pattern.get("target_family_id") or "")
            chains = ":".join(list(pattern.get("chain_ids") or []))
            return f"mesh_path:{src}:{tgt}:{chains}"
        if kind == "routine":
            return f"routine:{(pattern.get('chain_ids') or [''])[0]}"
        chains = ":".join(list(pattern.get("chain_ids") or []))
        return f"chain:{chains or 'unknown'}"

    def _persist_candidate(self, candidate: dict[str, Any]) -> None:
        cid = str(candidate.get("candidate_id") or f"cand_{uuid4().hex[:12]}")
        candidate["candidate_id"] = cid
        with self._lock:
            self._candidates_dir.mkdir(parents=True, exist_ok=True)
            path = self._candidates_dir / f"{cid}.json"
            path.write_text(json.dumps(candidate, sort_keys=True) + "\n", encoding="utf-8")

    def list_candidates(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self._candidates_dir.is_dir():
            return []
        rows: list[dict[str, Any]] = []
        for path in sorted(self._candidates_dir.glob("*.json"), reverse=True)[:limit]:
            try:
                rows.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return rows

    def rank_habit_candidates(self, text: str = "") -> list[dict[str, Any]]:
        candidates = self.list_candidates(limit=100)
        if not candidates:
            mined = self.mine_habit_patterns()
            candidates = list(mined.get("candidates") or [])
        lowered = str(text or "").lower()

        def score(item: dict[str, Any]) -> float:
            base = float(item.get("occurrence_count") or 0)
            if not lowered:
                return base
            bonus = 0.0
            for field in ("source_family_id", "target_family_id"):
                val = str(item.get(field) or "").replace("_", " ")
                if val and val in lowered:
                    bonus += 2.0
            for chain_id in list(item.get("chain_ids") or []):
                if str(chain_id).replace("_", " ") in lowered:
                    bonus += 1.5
            return base + bonus

        ranked = sorted(candidates, key=score, reverse=True)
        return ranked[:8]

    def adopt_habit(
        self,
        candidate: dict[str, Any],
        *,
        operator_approved: bool = False,
        session_id: str = "global",
    ) -> dict[str, Any]:
        if not operator_approved:
            return {"outcome": "blocked", "reason": "operator_approved required", "status": 403}
        if not candidate:
            return {"outcome": "blocked", "reason": "empty_candidate"}

        habit_id = f"habit_{uuid4().hex[:12]}"
        habit = {
            "habit_version": HABIT_VERSION,
            "habit_id": habit_id,
            "pattern_kind": str(candidate.get("pattern_kind") or "chain"),
            "source_family_id": candidate.get("source_family_id"),
            "target_family_id": candidate.get("target_family_id"),
            "chain_ids": list(candidate.get("chain_ids") or []),
            "occurrence_count": int(candidate.get("occurrence_count") or 0),
            "last_seen_at": candidate.get("last_seen_at") or _utc_now_iso(),
            "claim_label": "asserted",
            "operator_promoted": True,
            "hcc_class": "HCC-2",
            "candidate_id": candidate.get("candidate_id"),
        }
        save_adopted_habit(habit, repo_root=self._repo_root)
        self._write_preference_slot(habit)
        self._emit_habit_adoption_ledger(session_id, habit)
        return {"outcome": "adopted", "habit": habit, "hcc_class": "HCC-2"}

    def _write_preference_slot(self, habit: dict[str, Any]) -> None:
        """Persist adopted habit into preference slot overlay (slot_06)."""
        with self._lock:
            payload: dict[str, Any] = {}
            if self._preferences_path.is_file():
                try:
                    payload = json.loads(self._preferences_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    payload = {}
            habits = list(payload.get("adopted_habits") or [])
            habits = [h for h in habits if str(h.get("habit_id")) != str(habit.get("habit_id"))]
            habits.append(habit)
            payload = {
                "preference_overlay_version": "jarvis_memory_board_preferences.v1",
                "slot_id": "slot_06",
                "module_id": "capability_routing_preferences_v2",
                "adopted_habits": habits,
                "updated_at": _utc_now_iso(),
            }
            self._preferences_path.parent.mkdir(parents=True, exist_ok=True)
            self._preferences_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    def adopted_mesh_habits(self) -> list[dict[str, Any]]:
        return [
            h
            for h in adopted_habits(repo_root=self._repo_root)
            if str(h.get("pattern_kind") or "") == "mesh_path" and h.get("operator_promoted")
        ]

    def mesh_habit_boost(self, edge: dict[str, Any]) -> float:
        boost = 0.0
        src = str(edge.get("source_family_id") or "")
        tgt = str(edge.get("target_family_id") or "")
        chains = [
            str(edge.get("source_chain_id") or ""),
            str(edge.get("chain_id") or ""),
        ]
        for habit in self.adopted_mesh_habits():
            if str(habit.get("source_family_id") or "") != src:
                continue
            if str(habit.get("target_family_id") or "") != tgt:
                continue
            habit_chains = list(habit.get("chain_ids") or [])
            if habit_chains and chains and habit_chains == [c for c in chains if c]:
                boost += float(habit.get("occurrence_count") or 1) * 2.0
            else:
                boost += 1.0
        return boost

    def culture_posture(self) -> dict[str, Any]:
        candidates = self.list_candidates(limit=200)
        adopted = adopted_habits(repo_root=self._repo_root)
        stale = [
            c
            for c in candidates
            if str(c.get("last_seen_at") or "") < (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        ]
        return {
            "candidate_habits": len(candidates),
            "adopted_habits": len(adopted),
            "stale_candidates": len(stale),
            "mesh_habits": len(self.adopted_mesh_habits()),
            "claim_label": "asserted",
        }

    def culture_snapshot(self) -> dict[str, Any]:
        return {
            "culture_version": "operator_culture.v1",
            "posture": self.culture_posture(),
            "adopted_habits": adopted_habits(repo_root=self._repo_root),
            "recent_candidates": self.list_candidates(limit=20),
            "handoff_edge_count": len(list_handoff_edges()),
            "claim_label": "asserted",
        }

    def _emit_habit_adoption_ledger(self, session_id: str, habit: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_habit_adoption_event

            append_habit_adoption_event(session_id, habit=habit)
        except Exception:
            pass

    def _emit_habit_candidate_ledger(self, session_id: str, candidate: dict[str, Any]) -> None:
        try:
            from src.operator_decision_ledger import append_habit_candidate_event

            append_habit_candidate_event(session_id, candidate=candidate)
        except Exception:
            pass


culture_habit_runtime = CultureHabitRuntime()
