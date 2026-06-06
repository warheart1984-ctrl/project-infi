"""Core EvolveEngine runtime."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests

from evolve_engine.backends.local_evolving_ai import (
    EvolutionEvaluationError,
    EvolutionTimeoutError,
    LocalEvolutionBackend,
    ResolvedConstraints,
)
from evolve_engine.schemas import (
    EvolveHealthResponse,
    EvolutionError,
    EvolutionErrorResponse,
    EvolutionRequest,
    EvolutionResult,
    EvolutionSuccessResponse,
    SchemaValidationError,
)
from evolve_engine.trace_store import EvolveTraceStore
from evolve_engine.universal_language import CONTRACT_VERSION, finalize_contract_error, finalize_contract_success
from src.evolve.law_bridge import enforce_laws


class ForgeEvalUnavailableError(RuntimeError):
    """Raised when ForgeEval cannot be reached or returns an invalid contract."""


class ForgeEvalCaller:
    """Small HTTP evaluator transport used by EvolveEngine."""

    def __init__(
        self,
        base_url: str,
        *,
        session: requests.sessions.Session | Any | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.base_url = str(base_url).rstrip("/")
        self.session = session or requests.Session()
        self.timeout_seconds = float(timeout_seconds)

    def evaluate_candidate(
        self,
        *,
        job_id: str,
        generation_index: int,
        individual_index: int,
        request: EvolutionRequest,
        candidate: str,
    ) -> dict[str, Any]:
        payload = dict(request.evaluation.payload or {})
        payload[request.evaluation.candidate_field] = candidate
        eval_task_id = f"{job_id}-g{generation_index}-i{individual_index}"
        headers = {
            "X-Evolve-Job-ID": job_id,
            "X-Evolve-Generation": str(generation_index),
            "X-Evolve-Individual": str(individual_index),
        }
        if request.jarvis_run_id:
            headers["X-Jarvis-Run-ID"] = request.jarvis_run_id
        try:
            response = self.session.post(
                f"{self.base_url}/evaluate",
                json={
                    "task_id": eval_task_id,
                    "mode": request.evaluation.forge_eval_mode,
                    "payload": payload,
                },
                headers=headers,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise ForgeEvalUnavailableError(f"ForgeEval unavailable: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ForgeEvalUnavailableError("ForgeEval returned invalid JSON.") from exc

        if not isinstance(data, dict) or "ok" not in data:
            raise ForgeEvalUnavailableError("ForgeEval returned an invalid response contract.")
        return data


class EvolveEngineService:
    """End-to-end evolution service with bounded search and durable traces."""

    def __init__(
        self,
        storage_root: str | Path | None = None,
        *,
        forge_eval_base_url: str | None = None,
        evaluator: ForgeEvalCaller | Any | None = None,
    ) -> None:
        self.storage_root = Path(
            storage_root
            or os.getenv("EVOLVE_STORAGE")
            or (Path.cwd() / ".runtime" / "evolve_engine")
        ).expanduser().resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.forge_eval_base_url = str(
            forge_eval_base_url or os.getenv("FORGE_EVAL_BASE_URL") or "http://127.0.0.1:6061"
        ).rstrip("/")
        self.max_generations = max(1, int(os.getenv("EVOLVE_MAX_GENERATIONS", "6")))
        self.max_population = max(1, int(os.getenv("EVOLVE_MAX_POPULATION", "6")))
        self.max_evaluations = max(1, int(os.getenv("EVOLVE_MAX_EVALUATIONS", "30")))
        self.max_wall_time_seconds = max(1.0, float(os.getenv("EVOLVE_MAX_WALL_TIME_SECONDS", "60")))
        self.max_retained_jobs = max(1, int(os.getenv("EVOLVE_MAX_RETAINED_JOBS", "50")))
        self.max_retained_hall_entries = max(1, int(os.getenv("EVOLVE_MAX_RETAINED_HALL_ENTRIES", "200")))
        self.max_retained_evaluations = max(1, int(os.getenv("EVOLVE_MAX_RETAINED_EVALUATIONS", "5000")))
        self.trace_store = EvolveTraceStore(self.storage_root)
        self.evaluator = evaluator or ForgeEvalCaller(
            self.forge_eval_base_url,
            timeout_seconds=float(os.getenv("EVOLVE_FORGE_EVAL_TIMEOUT_SECONDS", "30")),
        )
        self.backend = LocalEvolutionBackend(self.evaluator)

    def health(self) -> EvolveHealthResponse:
        forge_eval_reachable = False
        forge_eval_error = None
        try:
            # Lightweight probe to the evaluator (used for evolution jobs).
            # Timeout short so health stays fast.
            resp = self.evaluator.session.get(
                f"{self.forge_eval_base_url}/health",
                timeout=2.0,
            )
            forge_eval_reachable = resp.status_code < 500
        except Exception as exc:
            forge_eval_error = str(exc)[:200]

        status = "ready" if forge_eval_reachable else "degraded"
        if not forge_eval_reachable:
            # Still report as runnable for MVP, but clearly note the missing dependency.
            status = "degraded"

        return EvolveHealthResponse(
            status=status,
            service="evolve_engine",
            storage_root=str(self.storage_root),
            forge_eval_base_url=self.forge_eval_base_url,
            forge_eval_reachable=forge_eval_reachable,
            forge_eval_error=forge_eval_error,
            contract_version=CONTRACT_VERSION,
            foundation_laws=[
                "law_1_admission_control",
                "law_2_execution_governance",
                "law_3_observability",
                "law_4_violation_handling",
                "law_5_consistent_execution",
                "law_6_adaptation_constraint",
            ],
            limits={
                "max_generations": self.max_generations,
                "max_population": self.max_population,
                "max_evaluations": self.max_evaluations,
                "max_wall_time_seconds": self.max_wall_time_seconds,
                "max_retained_jobs": self.max_retained_jobs,
                "max_retained_hall_entries": self.max_retained_hall_entries,
                "max_retained_evaluations": self.max_retained_evaluations,
            },
        )

    def evolve(
        self,
        request_payload: dict[str, Any] | EvolutionRequest,
    ) -> tuple[EvolutionSuccessResponse | EvolutionErrorResponse, int]:
        raw_payload = (
            dict(request_payload or {})
            if isinstance(request_payload, dict)
            else request_payload.model_dump(exclude_none=True)
        )
        job_id = str(raw_payload.get("job_id") or "").strip() or "unknown_job"
        task = str(raw_payload.get("task") or "").strip()
        law_enforcement: dict[str, Any] = {}
        ul_snapshot: dict[str, Any] = {}

        try:
            payload = (
                request_payload
                if isinstance(request_payload, EvolutionRequest)
                else EvolutionRequest.model_validate(request_payload)
            )
        except SchemaValidationError as exc:
            return (
                EvolutionErrorResponse(
                    job_id=job_id,
                    task=task,
                    error=EvolutionError(code="invalid_request", message=str(exc)),
                ),
                400,
            )

        constraints = self._resolve_constraints(payload)
        law_state = enforce_laws(
            None,
            "evolve_request",
            {
                "request": payload,
                "constraints": constraints,
            },
        )
        law_enforcement = dict(law_state.get("law_enforcement") or {})
        ul_snapshot = dict(law_state.get("ul_snapshot") or {})
        self.trace_store.begin_job(
            job_id=payload.job_id,
            jarvis_run_id=payload.jarvis_run_id,
            task=payload.task,
            request_payload={
                **payload.model_dump(exclude_none=True),
                "applied_constraints": {
                    "population_size": constraints.population_size,
                    "max_generations": constraints.max_generations,
                    "max_evaluations": constraints.max_evaluations,
                    "max_wall_time_seconds": constraints.max_wall_time_seconds,
                    "target_score": constraints.target_score,
                },
                "law_enforcement": law_enforcement,
                "ul_snapshot": ul_snapshot,
            },
        )
        self.trace_store.record_decision(
            job_id=payload.job_id,
            phase="admission_control",
            payload=law_enforcement.get("origin_integrity") or {},
        )
        self.trace_store.record_decision(
            job_id=payload.job_id,
            phase="execution_governance",
            payload=law_enforcement.get("execution_governance") or {},
        )
        if not law_state.get("allowed", False):
            violation = dict(law_state.get("violation") or {})
            if violation:
                self.trace_store.record_violation(
                    job_id=payload.job_id,
                    law_id=str(violation.get("law_id") or "law_2_execution_governance"),
                    severity=str(violation.get("severity") or "high"),
                    code=str(violation.get("code") or "law_violation"),
                    component_id=str(violation.get("component_id") or payload.job_id),
                    execution_id=str(violation.get("execution_id") or payload.job_id),
                    containment_state=str(violation.get("containment_state") or "contained"),
                    payload=violation,
                )
            self.trace_store.fail_job(job_id=payload.job_id, status="law_blocked")
            self.prune_retention()
            return self._error(
                payload,
                "law_violation",
                str((violation or {}).get("message") or "Foundation law enforcement blocked the evolve request."),
                status_code=400,
                law_enforcement=finalize_contract_error(
                    law_enforcement,
                    error_code="law_violation",
                    message=str((violation or {}).get("message") or "Foundation law enforcement blocked the evolve request."),
                    law_id=str((violation or {}).get("law_id") or "law_2_execution_governance"),
                ),
                ul_snapshot=ul_snapshot,
            )

        try:
            result_payload = self.backend.run(
                payload,
                constraints=constraints,
                trace_store=self.trace_store,
                law_enforcement=law_enforcement,
            )
        except EvolutionTimeoutError as exc:
            finalized = finalize_contract_error(
                law_enforcement,
                error_code="timeout",
                message=str(exc),
                law_id="law_4_violation_handling",
                severity="medium",
            )
            self.trace_store.record_violation(
                job_id=payload.job_id,
                law_id="law_4_violation_handling",
                severity="medium",
                code="timeout",
                component_id=payload.job_id,
                execution_id=payload.job_id,
                containment_state="contained",
                payload={"message": str(exc)},
            )
            self.trace_store.fail_job(job_id=payload.job_id, status="timeout")
            self.prune_retention()
            return self._error(
                payload,
                "timeout",
                str(exc),
                status_code=504,
                law_enforcement=finalized,
                ul_snapshot=ul_snapshot,
            )
        except EvolutionEvaluationError as exc:
            finalized = finalize_contract_error(
                law_enforcement,
                error_code="evaluation_failure",
                message=str(exc),
                law_id="law_6_adaptation_constraint",
            )
            self.trace_store.record_violation(
                job_id=payload.job_id,
                law_id="law_6_adaptation_constraint",
                severity="high",
                code="evaluation_failure",
                component_id=payload.job_id,
                execution_id=payload.job_id,
                containment_state="contained",
                payload={"message": str(exc)},
            )
            self.trace_store.fail_job(job_id=payload.job_id, status="evaluation_failure")
            self.prune_retention()
            return self._error(
                payload,
                "evaluation_failure",
                str(exc),
                status_code=502,
                law_enforcement=finalized,
                ul_snapshot=ul_snapshot,
            )
        except ForgeEvalUnavailableError as exc:
            finalized = finalize_contract_error(
                law_enforcement,
                error_code="backend_failure",
                message=str(exc),
                law_id="law_4_violation_handling",
            )
            self.trace_store.record_violation(
                job_id=payload.job_id,
                law_id="law_4_violation_handling",
                severity="high",
                code="backend_failure",
                component_id=payload.job_id,
                execution_id=payload.job_id,
                containment_state="contained",
                payload={"message": str(exc)},
            )
            self.trace_store.fail_job(job_id=payload.job_id, status="backend_failure")
            self.prune_retention()
            return self._error(
                payload,
                "backend_failure",
                str(exc),
                status_code=503,
                law_enforcement=finalized,
                ul_snapshot=ul_snapshot,
            )
        except Exception as exc:
            finalized = finalize_contract_error(
                law_enforcement,
                error_code="backend_failure",
                message=str(exc),
                law_id="law_4_violation_handling",
            )
            self.trace_store.record_violation(
                job_id=payload.job_id,
                law_id="law_4_violation_handling",
                severity="high",
                code="backend_failure",
                component_id=payload.job_id,
                execution_id=payload.job_id,
                containment_state="contained",
                payload={"message": str(exc)},
            )
            self.trace_store.fail_job(job_id=payload.job_id, status="backend_failure")
            self.prune_retention()
            return self._error(
                payload,
                "backend_failure",
                str(exc),
                status_code=500,
                law_enforcement=finalized,
                ul_snapshot=ul_snapshot,
            )

        result = EvolutionResult.model_validate(result_payload)
        finalized = finalize_contract_success(
            law_enforcement,
            best_score=result.best_score,
            generations_run=result.generations_run,
            evaluations=result.evaluations,
            validated_outcomes=result.validated_outcomes,
        )
        self.trace_store.record_decision(
            job_id=payload.job_id,
            phase="completion",
            payload={
                "best_score": result.best_score,
                "generations_run": result.generations_run,
                "evaluations": result.evaluations,
                "validated_outcomes": result.validated_outcomes,
            },
        )
        self.trace_store.complete_job(
            job_id=payload.job_id,
            status="completed",
            best_score=result.best_score,
            best_candidate=str(result.best_genome.get("candidate") or ""),
            best_program=result.best_program,
            generations_run=result.generations_run,
            evaluations=result.evaluations,
            hall_of_fame_count=result.hall_of_fame_count,
            hall_of_shame_count=result.hall_of_shame_count,
        )
        self.prune_retention()
        return (
            EvolutionSuccessResponse(
                job_id=payload.job_id,
                task=payload.task,
                result=result,
                law_enforcement=finalized,
                ul_snapshot=ul_snapshot,
            ),
            200,
        )

    def get_job_trace(self, job_id: str) -> dict[str, Any] | None:
        return self.trace_store.read_job(job_id)

    def get_job_evaluations(self, job_id: str, *, limit: int = 200) -> dict[str, Any]:
        return {
            "job_id": job_id,
            "evaluations": self.trace_store.read_job_evaluations(job_id, limit=limit),
        }

    def get_run_trace(self, jarvis_run_id: str) -> dict[str, Any]:
        return self.trace_store.read_run(jarvis_run_id)

    def list_hall_of_fame(self, *, limit: int = 20) -> dict[str, Any]:
        return {
            "entries": self.trace_store.list_hall_of_fame(limit=limit),
        }

    def list_hall_of_shame(self, *, limit: int = 20) -> dict[str, Any]:
        return {
            "entries": self.trace_store.list_hall_of_shame(limit=limit),
        }

    def prune_retention(
        self,
        *,
        max_jobs: int | None = None,
        max_hall_entries: int | None = None,
        max_evaluations: int | None = None,
    ) -> dict[str, Any]:
        return self.trace_store.prune_retention(
            max_jobs=max_jobs or self.max_retained_jobs,
            max_hall_entries=max_hall_entries or self.max_retained_hall_entries,
            max_evaluations=max_evaluations or self.max_retained_evaluations,
        )

    def _resolve_constraints(self, request: EvolutionRequest) -> ResolvedConstraints:
        return ResolvedConstraints(
            population_size=min(request.constraints.population_size or self.max_population, self.max_population),
            max_generations=min(request.constraints.max_generations or self.max_generations, self.max_generations),
            max_evaluations=min(request.constraints.max_evaluations or self.max_evaluations, self.max_evaluations),
            max_wall_time_seconds=min(
                request.constraints.max_wall_time_seconds or self.max_wall_time_seconds,
                self.max_wall_time_seconds,
            ),
            target_score=request.constraints.target_score,
        )

    def _error(
        self,
        request: EvolutionRequest,
        code: str,
        message: str,
        *,
        status_code: int,
        law_enforcement: dict[str, Any] | None = None,
        ul_snapshot: dict[str, Any] | None = None,
    ) -> tuple[EvolutionErrorResponse, int]:
        return (
            EvolutionErrorResponse(
                job_id=request.job_id,
                task=request.task,
                error=EvolutionError(code=code, message=message),
                law_enforcement=dict(law_enforcement or {}),
                ul_snapshot=dict(ul_snapshot or {}),
            ),
            status_code,
        )
