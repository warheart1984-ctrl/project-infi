"""Schema models for the EvolveEngine boundary."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any


VALID_EVALUATION_MODES = {"forge_eval"}
VALID_FORGE_EVAL_MODES = {"io_tests", "llm_rubric", "repo_patch"}
VALID_CANDIDATE_FIELDS = {"program", "patch", "repo"}
VALID_ERROR_CODES = {
    "invalid_request",
    "timeout",
    "evaluation_failure",
    "backend_failure",
    "constraint_exceeded",
    "law_violation",
}


class SchemaValidationError(ValueError):
    """Raised when a payload does not match the public contract."""


def _dump(value: Any, *, exclude_none: bool = False) -> Any:
    if isinstance(value, SchemaMixin):
        return value.model_dump(exclude_none=exclude_none)
    if isinstance(value, list):
        return [_dump(item, exclude_none=exclude_none) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _dump(item, exclude_none=exclude_none)
            for key, item in value.items()
            if not (exclude_none and item is None)
        }
    return value


def _require_dict(payload: Any, name: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise SchemaValidationError(f"{name} must be an object")
    return dict(payload)


def _require_string(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SchemaValidationError(f"{name} is required")
    return text


def _coerce_int(value: Any, name: str, *, minimum: int = 0) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise SchemaValidationError(f"{name} must be an integer") from exc
    if parsed < minimum:
        raise SchemaValidationError(f"{name} must be >= {minimum}")
    return parsed


def _coerce_float(value: Any, name: str, *, minimum: float = 0.0) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise SchemaValidationError(f"{name} must be numeric") from exc
    if parsed < minimum:
        raise SchemaValidationError(f"{name} must be >= {minimum}")
    return parsed


def _validate_mode(value: Any) -> str:
    mode = _require_string(value, "evaluation.mode")
    if mode not in VALID_EVALUATION_MODES:
        raise SchemaValidationError(
            f"evaluation.mode must be one of: {', '.join(sorted(VALID_EVALUATION_MODES))}"
        )
    return mode


def _validate_forge_eval_mode(value: Any) -> str:
    mode = _require_string(value, "evaluation.forge_eval_mode")
    if mode not in VALID_FORGE_EVAL_MODES:
        raise SchemaValidationError(
            "evaluation.forge_eval_mode must be one of: "
            + ", ".join(sorted(VALID_FORGE_EVAL_MODES))
        )
    return mode


def _validate_candidate_field(value: Any) -> str:
    field_name = _require_string(value or "program", "evaluation.candidate_field")
    if field_name not in VALID_CANDIDATE_FIELDS:
        raise SchemaValidationError(
            "evaluation.candidate_field must be one of: "
            + ", ".join(sorted(VALID_CANDIDATE_FIELDS))
        )
    return field_name


class SchemaMixin:
    """Small compatibility mixin that mirrors the Pydantic calls used in this repo."""

    def model_dump(self, *, exclude_none: bool = False) -> dict[str, Any]:
        return {
            item.name: _dump(getattr(self, item.name), exclude_none=exclude_none)
            for item in fields(self)
            if not (exclude_none and getattr(self, item.name) is None)
        }


@dataclass(slots=True)
class EvolutionConfig(SchemaMixin):
    """Local evolution configuration."""

    initial_candidate: str | None = None
    seed_candidates: list[str] = field(default_factory=list)
    strategy: str = "local_search"

    @classmethod
    def model_validate(cls, payload: Any) -> EvolutionConfig:
        data = _require_dict(payload, "config")
        raw_seeds = data.get("seed_candidates") or []
        if not isinstance(raw_seeds, list):
            raise SchemaValidationError("config.seed_candidates must be an array")
        return cls(
            initial_candidate=str(data.get("initial_candidate"))
            if data.get("initial_candidate") is not None
            else None,
            seed_candidates=[str(item) for item in raw_seeds if str(item or "").strip()],
            strategy=str(data.get("strategy") or "local_search"),
        )


@dataclass(slots=True)
class EvaluationConfig(SchemaMixin):
    """Evaluation configuration routed through ForgeEval."""

    mode: str
    forge_eval_mode: str
    payload: dict[str, Any] = field(default_factory=dict)
    candidate_field: str = "program"
    success_threshold: float | None = None
    failure_threshold: float | None = None

    @classmethod
    def model_validate(cls, payload: Any) -> EvaluationConfig:
        data = _require_dict(payload, "evaluation")
        base_payload = data.get("payload") or {}
        if not isinstance(base_payload, dict):
            raise SchemaValidationError("evaluation.payload must be an object")
        return cls(
            mode=_validate_mode(data.get("mode")),
            forge_eval_mode=_validate_forge_eval_mode(data.get("forge_eval_mode")),
            payload=dict(base_payload),
            candidate_field=_validate_candidate_field(data.get("candidate_field") or "program"),
            success_threshold=_coerce_float(
                data.get("success_threshold"),
                "evaluation.success_threshold",
                minimum=0.0,
            ),
            failure_threshold=_coerce_float(
                data.get("failure_threshold"),
                "evaluation.failure_threshold",
                minimum=0.0,
            ),
        )


@dataclass(slots=True)
class EvolutionConstraints(SchemaMixin):
    """Bounded search constraints."""

    population_size: int | None = None
    max_generations: int | None = None
    max_evaluations: int | None = None
    max_wall_time_seconds: float | None = None
    target_score: float | None = None

    @classmethod
    def model_validate(cls, payload: Any) -> EvolutionConstraints:
        data = _require_dict(payload, "constraints")
        return cls(
            population_size=_coerce_int(data.get("population_size"), "constraints.population_size", minimum=1),
            max_generations=_coerce_int(data.get("max_generations"), "constraints.max_generations", minimum=1),
            max_evaluations=_coerce_int(data.get("max_evaluations"), "constraints.max_evaluations", minimum=1),
            max_wall_time_seconds=_coerce_float(
                data.get("max_wall_time_seconds"),
                "constraints.max_wall_time_seconds",
                minimum=0.1,
            ),
            target_score=_coerce_float(data.get("target_score"), "constraints.target_score", minimum=0.0),
        )


@dataclass(slots=True)
class EvolutionRequest(SchemaMixin):
    """Public request contract for `POST /evolve`."""

    job_id: str
    task: str
    config: EvolutionConfig = field(default_factory=EvolutionConfig)
    evaluation: EvaluationConfig = field(
        default_factory=lambda: EvaluationConfig(mode="forge_eval", forge_eval_mode="llm_rubric")
    )
    constraints: EvolutionConstraints = field(default_factory=EvolutionConstraints)
    jarvis_run_id: str | None = None

    @classmethod
    def model_validate(cls, payload: Any) -> EvolutionRequest:
        data = _require_dict(payload, "request")
        return cls(
            job_id=_require_string(data.get("job_id"), "job_id"),
            task=_require_string(data.get("task"), "task"),
            config=EvolutionConfig.model_validate(data.get("config") or {}),
            evaluation=EvaluationConfig.model_validate(data.get("evaluation") or {}),
            constraints=EvolutionConstraints.model_validate(data.get("constraints") or {}),
            jarvis_run_id=str(data.get("jarvis_run_id")).strip()
            if data.get("jarvis_run_id") is not None and str(data.get("jarvis_run_id")).strip()
            else None,
        )


@dataclass(slots=True)
class GenerationSummary(SchemaMixin):
    """Summary of one completed generation."""

    generation_index: int
    best_score: float
    average_score: float
    best_candidate: str
    successful_evaluations: int
    failed_evaluations: int
    hall_of_fame_delta: int = 0
    hall_of_shame_delta: int = 0

    @classmethod
    def model_validate(cls, payload: Any) -> GenerationSummary:
        data = _require_dict(payload, "result.history[]")
        return cls(
            generation_index=int(data.get("generation_index", 0)),
            best_score=float(data.get("best_score", 0.0)),
            average_score=float(data.get("average_score", 0.0)),
            best_candidate=str(data.get("best_candidate") or ""),
            successful_evaluations=int(data.get("successful_evaluations", 0)),
            failed_evaluations=int(data.get("failed_evaluations", 0)),
            hall_of_fame_delta=int(data.get("hall_of_fame_delta", 0)),
            hall_of_shame_delta=int(data.get("hall_of_shame_delta", 0)),
        )


@dataclass(slots=True)
class EvolutionResult(SchemaMixin):
    """Successful evolve result payload."""

    best_score: float
    best_genome: dict[str, Any] = field(default_factory=dict)
    best_program: str | None = None
    generations_run: int = 0
    evaluations: int = 0
    validated_outcomes: int = 0
    history: list[GenerationSummary] = field(default_factory=list)
    hall_of_fame_count: int = 0
    hall_of_shame_count: int = 0

    @classmethod
    def model_validate(cls, payload: Any) -> EvolutionResult:
        data = _require_dict(payload, "result")
        history = data.get("history") or []
        if not isinstance(history, list):
            raise SchemaValidationError("result.history must be an array")
        best_genome = data.get("best_genome") or {}
        if not isinstance(best_genome, dict):
            raise SchemaValidationError("result.best_genome must be an object")
        return cls(
            best_score=float(data.get("best_score", 0.0)),
            best_genome=dict(best_genome),
            best_program=str(data.get("best_program"))
            if data.get("best_program") is not None
            else None,
            generations_run=int(data.get("generations_run", 0)),
            evaluations=int(data.get("evaluations", 0)),
            validated_outcomes=int(data.get("validated_outcomes", 0)),
            history=[GenerationSummary.model_validate(item) for item in history],
            hall_of_fame_count=int(data.get("hall_of_fame_count", 0)),
            hall_of_shame_count=int(data.get("hall_of_shame_count", 0)),
        )


@dataclass(slots=True)
class EvolutionError(SchemaMixin):
    """Machine-readable evolve error."""

    code: str
    message: str

    @classmethod
    def model_validate(cls, payload: Any) -> EvolutionError:
        data = _require_dict(payload, "error")
        code = _require_string(data.get("code"), "error.code")
        if code not in VALID_ERROR_CODES:
            raise SchemaValidationError(
                f"error.code must be one of: {', '.join(sorted(VALID_ERROR_CODES))}"
            )
        return cls(code=code, message=str(data.get("message") or ""))


@dataclass(slots=True)
class EvolutionSuccessResponse(SchemaMixin):
    """Successful evolve response envelope."""

    job_id: str
    task: str
    result: EvolutionResult
    law_enforcement: dict[str, Any] = field(default_factory=dict)
    ul_snapshot: dict[str, Any] = field(default_factory=dict)
    ok: bool = True

    @classmethod
    def model_validate(cls, payload: Any) -> EvolutionSuccessResponse:
        data = _require_dict(payload, "response")
        if data.get("ok") is not True:
            raise SchemaValidationError("response.ok must be true")
        return cls(
            job_id=_require_string(data.get("job_id"), "job_id"),
            task=_require_string(data.get("task"), "task"),
            result=EvolutionResult.model_validate(data.get("result") or {}),
            law_enforcement=_require_dict(data.get("law_enforcement") or {}, "law_enforcement"),
            ul_snapshot=_require_dict(data.get("ul_snapshot") or {}, "ul_snapshot"),
        )


@dataclass(slots=True)
class EvolutionErrorResponse(SchemaMixin):
    """Failed evolve response envelope."""

    job_id: str
    task: str
    error: EvolutionError
    law_enforcement: dict[str, Any] = field(default_factory=dict)
    ul_snapshot: dict[str, Any] = field(default_factory=dict)
    ok: bool = False

    @classmethod
    def model_validate(cls, payload: Any) -> EvolutionErrorResponse:
        data = _require_dict(payload, "response")
        if data.get("ok") is not False:
            raise SchemaValidationError("response.ok must be false")
        return cls(
            job_id=_require_string(data.get("job_id"), "job_id"),
            task=str(data.get("task") or ""),
            error=EvolutionError.model_validate(data.get("error") or {}),
            law_enforcement=_require_dict(data.get("law_enforcement") or {}, "law_enforcement"),
            ul_snapshot=_require_dict(data.get("ul_snapshot") or {}, "ul_snapshot"),
        )


@dataclass(slots=True)
class EvolveHealthResponse(SchemaMixin):
    """Health payload for the evolve service."""

    status: str
    service: str
    storage_root: str
    forge_eval_base_url: str
    forge_eval_reachable: bool = False
    forge_eval_error: str | None = None
    limits: dict[str, Any] = field(default_factory=dict)
    contract_version: str | None = None
    foundation_laws: list[str] = field(default_factory=list)
