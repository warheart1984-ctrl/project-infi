from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ERROR_TRANSLATION_NOT_IMPLEMENTED = "TranslationNotImplemented"
ERROR_INVALID_TARGET = "InvalidTarget"
ERROR_TARGET_NOT_SUPPORTED = "TargetNotSupported"
ERROR_TARGET_MISMATCH = "TargetMismatch"
ERROR_ENGINE_INTAKE_REJECTED = "EngineIntakeRejected"
ERROR_INVALID_STAGE_INPUT = "InvalidStageInput"


@dataclass(slots=True)
class PipelineError:
    ok: bool = False
    error_type: str = ERROR_INVALID_STAGE_INPUT
    message: str = ""
    failed_stage: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "error_type": self.error_type,
            "message": self.message,
            "failed_stage": self.failed_stage,
            "details": dict(self.details),
        }


class PipelineContractError(Exception):
    def __init__(self, error: PipelineError) -> None:
        super().__init__(error.message)
        self.error = error


def make_error(
    *,
    error_type: str,
    message: str,
    failed_stage: str,
    details: dict[str, Any] | None = None,
) -> PipelineError:
    return PipelineError(
        error_type=error_type,
        message=message,
        failed_stage=failed_stage,
        details=dict(details or {}),
    )


def raise_pipeline_error(
    *,
    error_type: str,
    message: str,
    failed_stage: str,
    details: dict[str, Any] | None = None,
) -> None:
    raise PipelineContractError(
        make_error(
            error_type=error_type,
            message=message,
            failed_stage=failed_stage,
            details=details,
        )
    )
