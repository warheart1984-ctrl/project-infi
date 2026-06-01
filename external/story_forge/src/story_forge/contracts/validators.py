from __future__ import annotations

from dataclasses import MISSING, fields, is_dataclass
from types import NoneType
from typing import Any, get_args, get_origin, get_type_hints

from story_forge.contracts.cinematic import CinematicPlan
from story_forge.contracts.directional import DirectionalContext
from story_forge.contracts.engine_handoff import EngineHandoffInput
from story_forge.contracts.errors import (
    ERROR_ENGINE_INTAKE_REJECTED,
    ERROR_INVALID_STAGE_INPUT,
    raise_pipeline_error,
)
from story_forge.contracts.pipeline import TARGET_MOVIE
from story_forge.contracts.presentation import PresentedOutput
from story_forge.contracts.staging import StagedPlan
from story_forge.contracts.translation import SceneGrammar


def build_contract(payload: dict[str, Any], model_type: type[Any], *, stage: str) -> Any:
    if not isinstance(payload, dict):
        raise_pipeline_error(
            error_type=ERROR_INVALID_STAGE_INPUT,
            message=f"{model_type.__name__} input must be an object.",
            failed_stage=stage,
        )
    return _build_model(payload, model_type, stage=stage, path=model_type.__name__)


def ensure_contract_instance(value: Any, model_type: type[Any], *, stage: str) -> Any:
    if not is_dataclass(model_type):
        raise TypeError(f"{model_type!r} is not a dataclass type.")
    if not isinstance(value, model_type):
        raise_pipeline_error(
            error_type=ERROR_INVALID_STAGE_INPUT,
            message=f"{model_type.__name__} output must be a {model_type.__name__} instance.",
            failed_stage=stage,
        )
    _validate_value(value, model_type, stage=stage, path=model_type.__name__)
    return value


def validate_engine_handoff_contract(handoff: EngineHandoffInput) -> EngineHandoffInput:
    if not isinstance(handoff, EngineHandoffInput):
        raise_pipeline_error(
            error_type=ERROR_INVALID_STAGE_INPUT,
            message="Engine handoff input must be an EngineHandoffInput instance.",
            failed_stage="engine_handoff",
        )
    required = (
        ("scene_grammar", handoff.scene_grammar, SceneGrammar),
        ("staged_plan", handoff.staged_plan, StagedPlan),
        ("directional_context", handoff.directional_context, DirectionalContext),
        ("presented_output", handoff.presented_output, PresentedOutput),
    )
    for name, value, expected_type in required:
        if value is None or not isinstance(value, expected_type) or not getattr(value, "valid", False):
            raise_pipeline_error(
                error_type=ERROR_ENGINE_INTAKE_REJECTED,
                message=f"Engine handoff requires {name}.valid == true.",
                failed_stage="engine_handoff",
                details={"field": name},
            )
    if not getattr(handoff.staged_plan, "implemented", False):
        raise_pipeline_error(
            error_type=ERROR_ENGINE_INTAKE_REJECTED,
            message="Engine handoff rejects an unimplemented staged_plan scaffold.",
            failed_stage="engine_handoff",
            details={"field": "staged_plan", "reason": "implemented_false"},
        )
    if not getattr(handoff.presented_output, "implemented", False):
        raise_pipeline_error(
            error_type=ERROR_ENGINE_INTAKE_REJECTED,
            message="Engine handoff rejects an unimplemented presented_output scaffold.",
            failed_stage="engine_handoff",
            details={"field": "presented_output", "reason": "implemented_false"},
        )
    if handoff.directional_context.target == TARGET_MOVIE and handoff.cinematic_plan is None:
        raise_pipeline_error(
            error_type=ERROR_ENGINE_INTAKE_REJECTED,
            message="Engine handoff requires a cinematic_plan for target='movie'.",
            failed_stage="engine_handoff",
            details={"field": "cinematic_plan", "reason": "missing_for_movie"},
        )
    if handoff.cinematic_plan is not None and (
        not isinstance(handoff.cinematic_plan, CinematicPlan)
        or not handoff.cinematic_plan.valid
    ):
        raise_pipeline_error(
            error_type=ERROR_ENGINE_INTAKE_REJECTED,
            message="Engine handoff rejects an invalid cinematic_plan.",
            failed_stage="engine_handoff",
            details={"field": "cinematic_plan"},
        )
    if handoff.cinematic_plan is not None and not getattr(handoff.cinematic_plan, "implemented", False):
        raise_pipeline_error(
            error_type=ERROR_ENGINE_INTAKE_REJECTED,
            message="Engine handoff rejects an unimplemented cinematic_plan scaffold.",
            failed_stage="engine_handoff",
            details={"field": "cinematic_plan", "reason": "implemented_false"},
        )
    if handoff.scene_grammar.total_scenes != len(handoff.staged_plan.staged_units):
        raise_pipeline_error(
            error_type=ERROR_ENGINE_INTAKE_REJECTED,
            message="Engine handoff requires staging to preserve the translated scene count.",
            failed_stage="engine_handoff",
            details={"field": "staged_plan", "reason": "scene_count_mismatch"},
        )
    staged_scene_ids = [unit.scene_id for unit in handoff.staged_plan.staged_units]
    presented_scene_ids = [unit.scene_id for unit in handoff.presented_output.staged_units]
    if staged_scene_ids != presented_scene_ids:
        raise_pipeline_error(
            error_type=ERROR_ENGINE_INTAKE_REJECTED,
            message="Engine handoff requires presented_output.staged_units to match staged_plan order.",
            failed_stage="engine_handoff",
            details={"field": "presented_output", "reason": "staged_unit_mismatch"},
        )
    return handoff


def _build_model(payload: dict[str, Any], model_type: type[Any], *, stage: str, path: str) -> Any:
    expected_fields = {field_info.name: field_info for field_info in fields(model_type)}
    type_hints = get_type_hints(model_type)
    extra_fields = sorted(set(payload.keys()) - set(expected_fields.keys()))
    if extra_fields:
        raise_pipeline_error(
            error_type=ERROR_INVALID_STAGE_INPUT,
            message=f"{path} received extra fields: {', '.join(extra_fields)}.",
            failed_stage=stage,
            details={"path": path, "extra_fields": extra_fields},
        )

    values: dict[str, Any] = {}
    missing_fields: list[str] = []
    for field_info in fields(model_type):
        if field_info.name in payload:
            values[field_info.name] = _coerce_value(
                payload[field_info.name],
                type_hints.get(field_info.name, field_info.type),
                stage=stage,
                path=f"{path}.{field_info.name}",
            )
            continue
        if field_info.default is not MISSING:
            values[field_info.name] = field_info.default
            continue
        if field_info.default_factory is not MISSING:  # type: ignore[comparison-overlap]
            values[field_info.name] = field_info.default_factory()
            continue
        missing_fields.append(field_info.name)

    if missing_fields:
        raise_pipeline_error(
            error_type=ERROR_INVALID_STAGE_INPUT,
            message=f"{path} is missing required fields: {', '.join(missing_fields)}.",
            failed_stage=stage,
            details={"path": path, "missing_fields": missing_fields},
        )
    return model_type(**values)


def _coerce_value(value: Any, expected_type: Any, *, stage: str, path: str) -> Any:
    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if expected_type is Any:
        return value
    if origin is list:
        if not isinstance(value, list):
            _raise_type_error(path, "list", value, stage)
        item_type = args[0] if args else Any
        return [
            _coerce_value(item, item_type, stage=stage, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if origin is dict:
        if not isinstance(value, dict):
            _raise_type_error(path, "dict", value, stage)
        key_type = args[0] if len(args) > 0 else Any
        value_type = args[1] if len(args) > 1 else Any
        coerced: dict[Any, Any] = {}
        for key, item in value.items():
            coerced_key = _coerce_value(key, key_type, stage=stage, path=f"{path}.<key>")
            coerced[coerced_key] = _coerce_value(
                item,
                value_type,
                stage=stage,
                path=f"{path}[{coerced_key!r}]",
            )
        return coerced
    if origin is not None and NoneType in args:
        non_none_args = [arg for arg in args if arg is not NoneType]
        if value is None:
            return None
        if len(non_none_args) != 1:
            return value
        return _coerce_value(value, non_none_args[0], stage=stage, path=path)
    if is_dataclass(expected_type):
        if isinstance(value, expected_type):
            _validate_value(value, expected_type, stage=stage, path=path)
            return value
        if not isinstance(value, dict):
            _raise_type_error(path, expected_type.__name__, value, stage)
        return _build_model(value, expected_type, stage=stage, path=path)
    if expected_type is str:
        if not isinstance(value, str):
            _raise_type_error(path, "str", value, stage)
        return value
    if expected_type is int:
        if not isinstance(value, int) or isinstance(value, bool):
            _raise_type_error(path, "int", value, stage)
        return value
    if expected_type is bool:
        if not isinstance(value, bool):
            _raise_type_error(path, "bool", value, stage)
        return value
    return value


def _validate_value(value: Any, expected_type: Any, *, stage: str, path: str) -> None:
    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if expected_type is Any:
        return
    if origin is list:
        if not isinstance(value, list):
            _raise_type_error(path, "list", value, stage)
        item_type = args[0] if args else Any
        for index, item in enumerate(value):
            _validate_value(item, item_type, stage=stage, path=f"{path}[{index}]")
        return
    if origin is dict:
        if not isinstance(value, dict):
            _raise_type_error(path, "dict", value, stage)
        key_type = args[0] if len(args) > 0 else Any
        value_type = args[1] if len(args) > 1 else Any
        for key, item in value.items():
            _validate_value(key, key_type, stage=stage, path=f"{path}.<key>")
            _validate_value(item, value_type, stage=stage, path=f"{path}[{key!r}]")
        return
    if origin is not None and NoneType in args:
        non_none_args = [arg for arg in args if arg is not NoneType]
        if value is None:
            return
        if len(non_none_args) == 1:
            _validate_value(value, non_none_args[0], stage=stage, path=path)
        return
    if is_dataclass(expected_type):
        if not isinstance(value, expected_type):
            _raise_type_error(path, expected_type.__name__, value, stage)
        type_hints = get_type_hints(expected_type)
        for field_info in fields(expected_type):
            _validate_value(
                getattr(value, field_info.name),
                type_hints.get(field_info.name, field_info.type),
                stage=stage,
                path=f"{path}.{field_info.name}",
            )
        return
    if expected_type is str and not isinstance(value, str):
        _raise_type_error(path, "str", value, stage)
    if expected_type is int and (not isinstance(value, int) or isinstance(value, bool)):
        _raise_type_error(path, "int", value, stage)
    if expected_type is bool and not isinstance(value, bool):
        _raise_type_error(path, "bool", value, stage)


def _raise_type_error(path: str, expected: str, value: Any, stage: str) -> None:
    raise_pipeline_error(
        error_type=ERROR_INVALID_STAGE_INPUT,
        message=f"{path} must be {expected}, got {type(value).__name__}.",
        failed_stage=stage,
        details={"path": path, "expected": expected, "actual": type(value).__name__},
    )
