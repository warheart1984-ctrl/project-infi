"""Local bounded evolution backend for EvolveEngine."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Protocol

from evolve_engine.schemas import EvolutionRequest
from src.evolve.law_bridge import enforce_laws


class EvolutionTimeoutError(RuntimeError):
    """Raised when no work can complete inside the wall-clock budget."""


class EvolutionEvaluationError(RuntimeError):
    """Raised when the evaluator cannot score any candidate successfully."""


class EvaluatorProtocol(Protocol):
    """Evaluator transport used to score candidate mutations."""

    def evaluate_candidate(
        self,
        *,
        job_id: str,
        generation_index: int,
        individual_index: int,
        request: EvolutionRequest,
        candidate: str,
    ) -> dict[str, Any]:
        """Return the normalized evaluator response."""


@dataclass(slots=True)
class ResolvedConstraints:
    """Concrete constraints after server-side clamping."""

    population_size: int
    max_generations: int
    max_evaluations: int
    max_wall_time_seconds: float
    target_score: float | None


class LocalEvolutionBackend:
    """Bounded local-search loop that mutates candidate text and scores it externally."""

    def __init__(self, evaluator: EvaluatorProtocol) -> None:
        self.evaluator = evaluator

    def run(
        self,
        request: EvolutionRequest,
        *,
        constraints: ResolvedConstraints,
        trace_store,
        law_enforcement: dict[str, Any],
    ) -> dict[str, Any]:
        start = time.monotonic()
        population = self._build_initial_population(request, constraints.population_size)
        history: list[dict[str, Any]] = []
        best_candidate: str | None = None
        best_score: float | None = None
        evaluations = 0
        hall_of_fame_count = 0
        hall_of_shame_count = 0
        successful_evaluations = 0

        for generation_index in range(constraints.max_generations):
            if time.monotonic() - start >= constraints.max_wall_time_seconds and not history:
                raise EvolutionTimeoutError("Evolution timed out before a full generation could complete.")
            if evaluations >= constraints.max_evaluations:
                break

            scored: list[dict[str, Any]] = []
            for individual_index, candidate in enumerate(population):
                if evaluations >= constraints.max_evaluations:
                    break
                if time.monotonic() - start >= constraints.max_wall_time_seconds and not scored:
                    raise EvolutionTimeoutError("Evolution timed out before scoring the next candidate.")
                if time.monotonic() - start >= constraints.max_wall_time_seconds:
                    break

                evaluation = self.evaluator.evaluate_candidate(
                    job_id=request.job_id,
                    generation_index=generation_index,
                    individual_index=individual_index,
                    request=request,
                    candidate=candidate,
                )
                payload = dict(evaluation or {})
                ok = payload.get("ok") is True
                result_body = dict(payload.get("result") or {})
                error_body = dict(payload.get("error") or {})
                score = float(result_body.get("score", 0.0)) if ok else 0.0
                eval_task_id = str(
                    payload.get("task_id") or f"{request.job_id}-g{generation_index}-i{individual_index}"
                )

                trace_store.record_individual(
                    job_id=request.job_id,
                    generation_index=generation_index,
                    individual_index=individual_index,
                    eval_task_id=eval_task_id,
                    candidate=candidate,
                    score=score,
                    ok=ok,
                    details=dict(result_body.get("details") or {}),
                    error=error_body if not ok else None,
                )

                fame_reason = self._hall_of_fame_reason(
                    score=score,
                    best_score=best_score,
                    success_threshold=request.evaluation.success_threshold,
                )
                if fame_reason:
                    trace_store.record_hall_of_fame(
                        job_id=request.job_id,
                        generation_index=generation_index,
                        individual_index=individual_index,
                        eval_task_id=eval_task_id,
                        score=score,
                        candidate=candidate,
                        reason=fame_reason,
                    )
                    hall_of_fame_count += 1

                shame_reason = self._hall_of_shame_reason(
                    ok=ok,
                    score=score,
                    error=error_body,
                    failure_threshold=request.evaluation.failure_threshold,
                )
                if shame_reason:
                    trace_store.record_hall_of_shame(
                        job_id=request.job_id,
                        generation_index=generation_index,
                        individual_index=individual_index,
                        eval_task_id=eval_task_id,
                        score=score,
                        candidate=candidate,
                        reason=shame_reason,
                    )
                    hall_of_shame_count += 1

                if ok:
                    successful_evaluations += 1
                    if best_score is None or score > best_score:
                        best_score = score
                        best_candidate = candidate

                scored.append(
                    {
                        "candidate": candidate,
                        "score": score,
                        "ok": ok,
                        "details": dict(result_body.get("details") or {}),
                        "error": error_body,
                    }
                )
                evaluations += 1

            if not scored:
                break

            ranked = sorted(scored, key=lambda item: (item["score"], item["candidate"]), reverse=True)
            top = ranked[0]
            generation_successes = sum(1 for item in ranked if item["ok"])
            generation_failures = len(ranked) - generation_successes
            generation_summary = {
                "generation_index": generation_index,
                "best_score": float(top["score"]),
                "average_score": round(sum(item["score"] for item in ranked) / len(ranked), 6),
                "best_candidate": top["candidate"],
                "successful_evaluations": generation_successes,
                "failed_evaluations": generation_failures,
                "hall_of_fame_delta": sum(
                    1
                    for item in ranked
                    if self._hall_of_fame_reason(
                        score=item["score"],
                        best_score=best_score,
                        success_threshold=request.evaluation.success_threshold,
                    )
                ),
                "hall_of_shame_delta": sum(
                    1
                    for item in ranked
                    if self._hall_of_shame_reason(
                        ok=item["ok"],
                        score=item["score"],
                        error=item["error"],
                        failure_threshold=request.evaluation.failure_threshold,
                    )
                ),
            }
            trace_store.record_generation(
                job_id=request.job_id,
                generation_index=generation_index,
                summary=generation_summary,
            )
            history.append(generation_summary)

            if constraints.target_score is not None and best_score is not None and best_score >= constraints.target_score:
                break
            if generation_index + 1 >= constraints.max_generations:
                break
            if evaluations >= constraints.max_evaluations:
                break
            if time.monotonic() - start >= constraints.max_wall_time_seconds:
                break

            parent_selection = enforce_laws(
                ranked,
                "adaptation_parent_pool",
                {
                    "law_enforcement": law_enforcement,
                },
            )
            trace_store.record_decision(
                job_id=request.job_id,
                phase="adaptation_parent_pool",
                payload=dict(parent_selection.get("decision") or {}),
            )
            if not parent_selection.get("allowed", False):
                violation = dict(parent_selection.get("violation") or {})
                trace_store.record_violation(
                    job_id=request.job_id,
                    law_id=str(violation.get("law_id") or "law_6_adaptation_constraint"),
                    severity=str(violation.get("severity") or "high"),
                    code=str(violation.get("code") or "law_violation"),
                    component_id=str(violation.get("component_id") or request.job_id),
                    execution_id=str(violation.get("execution_id") or request.job_id),
                    containment_state=str(violation.get("containment_state") or "contained"),
                    payload=violation,
                )
                raise EvolutionEvaluationError(
                    str(
                        violation.get("message")
                        or "Adaptation halted because no validated outcomes were available for the next generation."
                    )
                )

            population = self._breed_next_generation(
                ranked=list(parent_selection.get("parents") or []),
                target_size=constraints.population_size,
                task=request.task,
                generation_index=generation_index + 1,
            )

        if successful_evaluations <= 0 or best_candidate is None or best_score is None:
            raise EvolutionEvaluationError("Every mutation failed evaluation; no best candidate could be selected.")

        return {
            "best_score": float(best_score),
            "best_genome": {
                "candidate": best_candidate,
                "candidate_field": request.evaluation.candidate_field,
                "strategy": request.config.strategy,
            },
            "best_program": best_candidate,
            "generations_run": len(history),
            "evaluations": evaluations,
            "validated_outcomes": successful_evaluations,
            "history": history,
            "hall_of_fame_count": hall_of_fame_count,
            "hall_of_shame_count": hall_of_shame_count,
        }

    def _build_initial_population(self, request: EvolutionRequest, target_size: int) -> list[str]:
        seeds: list[str] = []
        if request.config.initial_candidate:
            seeds.append(request.config.initial_candidate)
        seeds.extend(request.config.seed_candidates)
        candidate_field = request.evaluation.candidate_field
        payload_candidate = request.evaluation.payload.get(candidate_field)
        if isinstance(payload_candidate, str) and payload_candidate.strip():
            seeds.append(payload_candidate)
        seeds.append(request.task)

        population: list[str] = []
        for seed in seeds:
            normalized = str(seed or "").strip()
            if normalized and normalized not in population:
                population.append(normalized)
            if len(population) >= target_size:
                break

        if not population:
            population.append(request.task)

        while len(population) < target_size:
            source = population[len(population) % len(population)]
            population.append(
                self._mutate_candidate(
                    source,
                    request.task,
                    generation_index=0,
                    variant_index=len(population),
                )
            )

        return population[:target_size]

    def _breed_next_generation(
        self,
        *,
        ranked: list[dict[str, Any]],
        target_size: int,
        task: str,
        generation_index: int,
    ) -> list[str]:
        elite_count = max(1, min(len(ranked), max(1, target_size // 2)))
        elites = ranked[:elite_count]
        next_population = [str(item["candidate"]) for item in elites]

        variant_index = 0
        while len(next_population) < target_size:
            primary = elites[variant_index % len(elites)]["candidate"]
            secondary = elites[(variant_index + 1) % len(elites)]["candidate"]
            child = self._crossover(primary, secondary, task, variant_index)
            child = self._mutate_candidate(
                child,
                task,
                generation_index=generation_index,
                variant_index=variant_index,
            )
            if child in next_population:
                child = f"{child}\nMutation note {generation_index}.{variant_index}: keep aligning with {task[:72]}"
            next_population.append(child)
            variant_index += 1

        return next_population[:target_size]

    def _mutate_candidate(self, candidate: str, task: str, *, generation_index: int, variant_index: int) -> str:
        base = str(candidate or "").strip() or str(task or "").strip()
        focus = str(task or "").strip()
        mode = (generation_index + variant_index) % 4
        if mode == 0:
            return f"{base}\n\nObjective: {focus}"
        if mode == 1:
            return f"{focus}\n\n{base}"
        if mode == 2:
            return f"{base}\n\nConstraint reminder: stay bounded, score cleanly, and preserve useful structure."
        return f"{base}\n\nMutation {generation_index}.{variant_index}: tighten toward {focus[:90]}."

    def _crossover(self, primary: str, secondary: str, task: str, variant_index: int) -> str:
        primary_lines = [line for line in str(primary or "").splitlines() if line.strip()]
        secondary_lines = [line for line in str(secondary or "").splitlines() if line.strip()]
        head = primary_lines[: max(1, len(primary_lines) // 2)]
        tail = secondary_lines[max(0, len(secondary_lines) // 2) :]
        merged = "\n".join(head + tail).strip()
        if merged:
            return merged
        return f"{primary}\n{secondary}\nBlend {variant_index}: {task[:72]}"

    def _hall_of_fame_reason(
        self,
        *,
        score: float,
        best_score: float | None,
        success_threshold: float | None,
    ) -> str | None:
        threshold = 0.85 if success_threshold is None else float(success_threshold)
        if score >= threshold:
            return "score_met_success_threshold"
        if best_score is None or score > best_score:
            return "new_run_leader"
        return None

    def _hall_of_shame_reason(
        self,
        *,
        ok: bool,
        score: float,
        error: dict[str, Any],
        failure_threshold: float | None,
    ) -> str | None:
        threshold = 0.2 if failure_threshold is None else float(failure_threshold)
        if not ok:
            return str(error.get("code") or "evaluation_error")
        if score <= threshold:
            return "score_below_failure_threshold"
        return None
