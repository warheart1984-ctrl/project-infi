"""SQLite-backed trace store for EvolveEngine."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import sqlite3
from typing import Any


class EvolveTraceStore:
    """Persist job traces, generation summaries, and mutation halls."""

    def __init__(self, storage_root: str | Path) -> None:
        self.storage_root = Path(storage_root).expanduser().resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_root / "evolve_traces.sqlite3"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS evolve_jobs (
                    job_id TEXT PRIMARY KEY,
                    jarvis_run_id TEXT,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_json TEXT,
                    best_score REAL,
                    best_candidate TEXT,
                    best_program TEXT,
                    generations_run INTEGER DEFAULT 0,
                    evaluations INTEGER DEFAULT 0,
                    hall_of_fame_count INTEGER DEFAULT 0,
                    hall_of_shame_count INTEGER DEFAULT 0,
                    started_at TEXT NOT NULL,
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS evolve_generations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    generation_index INTEGER NOT NULL,
                    summary_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS evolve_individuals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    generation_index INTEGER NOT NULL,
                    individual_index INTEGER NOT NULL,
                    eval_task_id TEXT,
                    candidate TEXT NOT NULL,
                    score REAL,
                    ok INTEGER NOT NULL,
                    details_json TEXT,
                    error_json TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS evolve_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS evolve_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    law_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    code TEXT NOT NULL,
                    component_id TEXT,
                    execution_id TEXT,
                    containment_state TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS hall_of_fame (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    generation_index INTEGER NOT NULL,
                    individual_index INTEGER NOT NULL,
                    eval_task_id TEXT,
                    score REAL,
                    candidate TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS hall_of_shame (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    generation_index INTEGER NOT NULL,
                    individual_index INTEGER NOT NULL,
                    eval_task_id TEXT,
                    score REAL,
                    candidate TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def begin_job(self, *, job_id: str, jarvis_run_id: str | None, task: str, request_payload: dict[str, Any]) -> None:
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO evolve_jobs (
                    job_id, jarvis_run_id, task, status, request_json, started_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    jarvis_run_id,
                    task,
                    "running",
                    json.dumps(request_payload, ensure_ascii=False),
                    now,
                ),
            )

    def record_individual(
        self,
        *,
        job_id: str,
        generation_index: int,
        individual_index: int,
        eval_task_id: str,
        candidate: str,
        score: float | None,
        ok: bool,
        details: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evolve_individuals (
                    job_id, generation_index, individual_index, eval_task_id, candidate, score, ok,
                    details_json, error_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    generation_index,
                    individual_index,
                    eval_task_id,
                    candidate,
                    score,
                    1 if ok else 0,
                    json.dumps(details or {}, ensure_ascii=False),
                    json.dumps(error or {}, ensure_ascii=False),
                    now,
                ),
                )

    def record_generation(self, *, job_id: str, generation_index: int, summary: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evolve_generations (job_id, generation_index, summary_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    job_id,
                    generation_index,
                    json.dumps(summary, ensure_ascii=False),
                    datetime.now(UTC).isoformat(),
                ),
            )

    def record_decision(self, *, job_id: str, phase: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evolve_decisions (job_id, phase, payload_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    job_id,
                    phase,
                    json.dumps(payload, ensure_ascii=False),
                    datetime.now(UTC).isoformat(),
                ),
            )

    def record_violation(
        self,
        *,
        job_id: str,
        law_id: str,
        severity: str,
        code: str,
        component_id: str | None,
        execution_id: str | None,
        containment_state: str,
        payload: dict[str, Any],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evolve_violations (
                    job_id,
                    law_id,
                    severity,
                    code,
                    component_id,
                    execution_id,
                    containment_state,
                    payload_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    law_id,
                    severity,
                    code,
                    component_id,
                    execution_id,
                    containment_state,
                    json.dumps(payload, ensure_ascii=False),
                    datetime.now(UTC).isoformat(),
                ),
            )

    def record_hall_of_fame(
        self,
        *,
        job_id: str,
        generation_index: int,
        individual_index: int,
        eval_task_id: str,
        score: float,
        candidate: str,
        reason: str,
    ) -> None:
        self._record_hall_entry(
            table="hall_of_fame",
            job_id=job_id,
            generation_index=generation_index,
            individual_index=individual_index,
            eval_task_id=eval_task_id,
            score=score,
            candidate=candidate,
            reason=reason,
        )

    def record_hall_of_shame(
        self,
        *,
        job_id: str,
        generation_index: int,
        individual_index: int,
        eval_task_id: str,
        score: float | None,
        candidate: str,
        reason: str,
    ) -> None:
        self._record_hall_entry(
            table="hall_of_shame",
            job_id=job_id,
            generation_index=generation_index,
            individual_index=individual_index,
            eval_task_id=eval_task_id,
            score=float(score) if score is not None else None,
            candidate=candidate,
            reason=reason,
        )

    def _record_hall_entry(
        self,
        *,
        table: str,
        job_id: str,
        generation_index: int,
        individual_index: int,
        eval_task_id: str,
        score: float | None,
        candidate: str,
        reason: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                f"""
                INSERT INTO {table} (
                    job_id, generation_index, individual_index, eval_task_id, score, candidate, reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    generation_index,
                    individual_index,
                    eval_task_id,
                    score,
                    candidate,
                    reason,
                    datetime.now(UTC).isoformat(),
                ),
            )

    def complete_job(
        self,
        *,
        job_id: str,
        status: str,
        best_score: float | None = None,
        best_candidate: str | None = None,
        best_program: str | None = None,
        generations_run: int = 0,
        evaluations: int = 0,
        hall_of_fame_count: int = 0,
        hall_of_shame_count: int = 0,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE evolve_jobs
                SET status = ?, best_score = ?, best_candidate = ?, best_program = ?,
                    generations_run = ?, evaluations = ?, hall_of_fame_count = ?, hall_of_shame_count = ?,
                    completed_at = ?
                WHERE job_id = ?
                """,
                (
                    status,
                    best_score,
                    best_candidate,
                    best_program,
                    generations_run,
                    evaluations,
                    hall_of_fame_count,
                    hall_of_shame_count,
                    datetime.now(UTC).isoformat(),
                    job_id,
                ),
            )

    def fail_job(self, *, job_id: str, status: str) -> None:
        self.complete_job(job_id=job_id, status=status)

    def read_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            job_row = conn.execute(
                "SELECT * FROM evolve_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            if job_row is None:
                return None
            history_rows = conn.execute(
                """
                SELECT summary_json FROM evolve_generations
                WHERE job_id = ?
                ORDER BY generation_index ASC
                """,
                (job_id,),
            ).fetchall()
        job = dict(job_row)
        request_payload = json.loads(job.pop("request_json") or "{}")
        history = [json.loads(row["summary_json"] or "{}") for row in history_rows]
        decisions = self.read_job_decisions(job_id)
        violations = self.read_job_violations(job_id)
        hall_of_fame = self.list_hall_of_fame(limit=20, job_id=job_id)
        hall_of_shame = self.list_hall_of_shame(limit=20, job_id=job_id)
        return {
            "job": {
                **job,
                "request": request_payload,
            },
            "history": history,
            "decisions": decisions,
            "violations": violations,
            "hall_of_fame": hall_of_fame,
            "hall_of_shame": hall_of_shame,
        }

    def read_job_evaluations(self, job_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM evolve_individuals
                WHERE job_id = ?
                ORDER BY generation_index ASC, individual_index ASC
                LIMIT ?
                """,
                (job_id, max(1, int(limit))),
            ).fetchall()
        return [self._row_to_evaluation(row) for row in rows]

    def read_run(self, jarvis_run_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT job_id, task, status, best_score, generations_run, evaluations, hall_of_fame_count,
                       hall_of_shame_count, started_at, completed_at
                FROM evolve_jobs
                WHERE jarvis_run_id = ?
                ORDER BY started_at DESC
                """,
                (jarvis_run_id,),
            ).fetchall()
        return {
            "jarvis_run_id": jarvis_run_id,
            "jobs": [dict(row) for row in rows],
        }

    def list_hall_of_fame(self, *, limit: int = 20, job_id: str | None = None) -> list[dict[str, Any]]:
        return self._list_hall("hall_of_fame", limit=limit, job_id=job_id)

    def list_hall_of_shame(self, *, limit: int = 20, job_id: str | None = None) -> list[dict[str, Any]]:
        return self._list_hall("hall_of_shame", limit=limit, job_id=job_id)

    def read_job_decisions(self, job_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT phase, payload_json, created_at
                FROM evolve_decisions
                WHERE job_id = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (job_id, max(1, int(limit))),
            ).fetchall()
        decisions: list[dict[str, Any]] = []
        for row in rows:
            decisions.append(
                {
                    "phase": row["phase"],
                    "payload": json.loads(row["payload_json"] or "{}"),
                    "created_at": row["created_at"],
                }
            )
        return decisions

    def read_job_violations(self, job_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT law_id, severity, code, component_id, execution_id, containment_state, payload_json, created_at
                FROM evolve_violations
                WHERE job_id = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (job_id, max(1, int(limit))),
            ).fetchall()
        violations: list[dict[str, Any]] = []
        for row in rows:
            violations.append(
                {
                    "law_id": row["law_id"],
                    "severity": row["severity"],
                    "code": row["code"],
                    "component_id": row["component_id"],
                    "execution_id": row["execution_id"],
                    "containment_state": row["containment_state"],
                    "payload": json.loads(row["payload_json"] or "{}"),
                    "created_at": row["created_at"],
                }
            )
        return violations

    def prune_retention(
        self,
        *,
        max_jobs: int | None = None,
        max_hall_entries: int | None = None,
        max_evaluations: int | None = None,
    ) -> dict[str, int]:
        removed_jobs = 0
        removed_hall_of_fame = 0
        removed_hall_of_shame = 0
        removed_evaluations = 0
        with self._connect() as conn:
            if max_jobs is not None and max_jobs > 0:
                rows = conn.execute(
                    """
                    SELECT job_id FROM evolve_jobs
                    ORDER BY COALESCE(completed_at, started_at) DESC
                    LIMIT -1 OFFSET ?
                    """,
                    (int(max_jobs),),
                ).fetchall()
                stale_job_ids = [str(row["job_id"]) for row in rows]
                if stale_job_ids:
                    placeholders = ",".join("?" for _ in stale_job_ids)
                    for table_name in (
                        "evolve_generations",
                        "evolve_individuals",
                        "evolve_decisions",
                        "evolve_violations",
                        "hall_of_fame",
                        "hall_of_shame",
                        "evolve_jobs",
                    ):
                        conn.execute(
                            f"DELETE FROM {table_name} WHERE job_id IN ({placeholders})",
                            tuple(stale_job_ids),
                        )
                    removed_jobs = len(stale_job_ids)

            if max_evaluations is not None and max_evaluations > 0:
                removed_evaluations = self._prune_table_by_id(
                    conn,
                    table_name="evolve_individuals",
                    max_rows=int(max_evaluations),
                )

            if max_hall_entries is not None and max_hall_entries > 0:
                removed_hall_of_fame = self._prune_table_by_id(
                    conn,
                    table_name="hall_of_fame",
                    max_rows=int(max_hall_entries),
                )
                removed_hall_of_shame = self._prune_table_by_id(
                    conn,
                    table_name="hall_of_shame",
                    max_rows=int(max_hall_entries),
                )

        return {
            "removed_jobs": removed_jobs,
            "removed_hall_of_fame": removed_hall_of_fame,
            "removed_hall_of_shame": removed_hall_of_shame,
            "removed_evaluations": removed_evaluations,
        }

    def _list_hall(self, table: str, *, limit: int, job_id: str | None = None) -> list[dict[str, Any]]:
        where = ""
        params: list[Any] = []
        if job_id:
            where = "WHERE job_id = ?"
            params.append(job_id)
        params.append(max(1, int(limit)))
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT job_id, generation_index, individual_index, eval_task_id, score, candidate, reason, created_at
                FROM {table}
                {where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [dict(row) for row in rows]

    def _prune_table_by_id(self, conn: sqlite3.Connection, *, table_name: str, max_rows: int) -> int:
        rows = conn.execute(
            f"SELECT id FROM {table_name} ORDER BY created_at DESC, id DESC LIMIT -1 OFFSET ?",
            (max_rows,),
        ).fetchall()
        stale_ids = [int(row["id"]) for row in rows]
        if not stale_ids:
            return 0
        placeholders = ",".join("?" for _ in stale_ids)
        conn.execute(
            f"DELETE FROM {table_name} WHERE id IN ({placeholders})",
            tuple(stale_ids),
        )
        return len(stale_ids)

    def _row_to_evaluation(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "job_id": row["job_id"],
            "generation_index": row["generation_index"],
            "individual_index": row["individual_index"],
            "eval_task_id": row["eval_task_id"],
            "candidate": row["candidate"],
            "score": row["score"],
            "ok": bool(row["ok"]),
            "details": json.loads(row["details_json"] or "{}"),
            "error": json.loads(row["error_json"] or "{}"),
            "created_at": row["created_at"],
        }
