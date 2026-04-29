from __future__ import annotations

import logging
from abc import ABC
from datetime import datetime, timezone
from typing import Any, Callable

JsonDict = dict[str, Any]


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class EngineModuleError(Exception):
    error_type = "EngineError"


class InputValidationError(EngineModuleError):
    error_type = "InputError"


class SemanticValidationError(EngineModuleError):
    error_type = "SemanticError"


class BoundaryExecutionError(EngineModuleError):
    error_type = "BoundaryError"


class AAISEngineModule(ABC):
    def __init__(
        self,
        *,
        provider_name: str,
        logger: logging.Logger | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.logger = logger or logging.getLogger(f"{__name__}.{provider_name}.engine")

    def _ok(self, action: str, data: JsonDict | None = None, **meta: Any) -> JsonDict:
        return {
            "ok": True,
            "module": "engine",
            "action": action,
            "data": data or {},
            "meta": meta,
        }

    def _err(self, action: str, error_type: str, message: str, **details: Any) -> JsonDict:
        return {
            "ok": False,
            "module": "engine",
            "action": action,
            "error_type": error_type,
            "message": message,
            "details": details,
        }

    def _execute(
        self,
        action: str,
        fn: Callable[[], JsonDict],
    ) -> JsonDict:
        result: JsonDict | None = None
        try:
            data = fn()
            if not isinstance(data, dict):
                raise SemanticValidationError("Engine action did not return a dictionary payload.")
            result = self._ok(
                action,
                data=data,
                provider=self.provider_name,
                timestamp=_utc_timestamp(),
            )
        except Exception as exc:  # noqa: BLE001 - boundary adapter must seal failures
            result = self._guarded_error(action, exc)
        finally:
            self._log_execution(action, result)
        return result

    def _guarded_error(self, action: str, exc: Exception) -> JsonDict:
        if isinstance(exc, (InputValidationError, SemanticValidationError)):
            return self._err(
                action,
                exc.error_type,
                str(exc),
                provider=self.provider_name,
                exception=str(exc),
            )
        if isinstance(exc, EngineModuleError):
            return self._err(
                action,
                exc.error_type,
                self._action_failure_message(action),
                provider=self.provider_name,
                exception=str(exc),
            )
        return self._err(
            action,
            BoundaryExecutionError.error_type,
            self._action_failure_message(action),
            provider=self.provider_name,
            exception=str(exc),
        )

    def _action_failure_message(self, action: str) -> str:
        mapping = {
            "scene_build": "Scene build failed",
            "runtime_bind": "Runtime bind failed",
            "runtime_step": "Runtime step failed",
            "capture": "Capture failed",
        }
        return mapping.get(action, "Engine action failed")

    def _log_execution(self, action: str, result: JsonDict | None) -> None:
        if result is None:
            self.logger.error(
                "engine execution ended without result provider=%s action=%s",
                self.provider_name,
                action,
            )
            return
        if result.get("ok"):
            self.logger.info(
                "engine execution ok provider=%s action=%s timestamp=%s",
                self.provider_name,
                action,
                result.get("meta", {}).get("timestamp", "unknown"),
            )
            return
        self.logger.warning(
            "engine execution failed provider=%s action=%s error_type=%s message=%s exception=%s",
            self.provider_name,
            action,
            result.get("error_type", "UnknownError"),
            result.get("message", ""),
            result.get("details", {}).get("exception", ""),
        )
