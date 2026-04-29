from __future__ import annotations

import base64
import binascii
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib import request
from urllib.parse import urlparse

from PIL import Image, UnidentifiedImageError

JsonDict = dict[str, Any]


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def encode_data_uri(raw_bytes: bytes, mime_type: str = "image/png") -> str:
    encoded = base64.b64encode(raw_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def decode_data_uri(value: str) -> tuple[str, bytes]:
    header, encoded = value.split(",", 1)
    if ";base64" not in header:
        raise SemanticValidationError("Image source data URI must be base64 encoded.")
    mime_type = header[5:].split(";", 1)[0] or "image/png"
    try:
        return mime_type, base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise SemanticValidationError("Image source data URI did not contain valid base64.") from exc


def normalize_image_bytes(
    raw_bytes: bytes,
    *,
    source_label: str,
) -> tuple[bytes, str]:
    try:
        with Image.open(BytesIO(raw_bytes)) as image:
            converted = image.convert("RGBA")
            buffer = BytesIO()
            converted.save(buffer, format="PNG")
    except UnidentifiedImageError as exc:
        raise SemanticValidationError(f"{source_label} must be a renderable image.") from exc
    except OSError as exc:
        raise BoundaryExecutionError(f"{source_label} could not be normalized.") from exc
    return buffer.getvalue(), "image/png"


def normalize_image_reference(
    value: str,
    *,
    source_label: str,
) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise SemanticValidationError("Image response did not contain valid image values.")

    if raw.startswith("data:image/"):
        _, decoded = decode_data_uri(raw)
        normalized, mime_type = normalize_image_bytes(decoded, source_label=source_label)
        return encode_data_uri(normalized, mime_type)

    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"}:
        try:
            with request.urlopen(raw, timeout=30.0) as response:
                downloaded = response.read()
        except OSError as exc:
            raise BoundaryExecutionError(f"{source_label} could not be downloaded.") from exc
        normalized, mime_type = normalize_image_bytes(downloaded, source_label=source_label)
        return encode_data_uri(normalized, mime_type)

    path = Path(raw)
    if path.exists():
        if not path.is_file():
            raise InputValidationError(f"Image path is not a file: {path}")
        try:
            file_bytes = path.read_bytes()
        except OSError as exc:
            raise BoundaryExecutionError(f"{source_label} could not be read.") from exc
        normalized, mime_type = normalize_image_bytes(file_bytes, source_label=source_label)
        return encode_data_uri(normalized, mime_type)

    raise SemanticValidationError("Image response did not contain valid image values.")


class CapabilityModuleError(Exception):
    error_type = "CapabilityError"


class InputValidationError(CapabilityModuleError):
    error_type = "InputError"


class SemanticValidationError(CapabilityModuleError):
    error_type = "SemanticError"


class APIExecutionError(CapabilityModuleError):
    error_type = "APIError"


class BoundaryExecutionError(CapabilityModuleError):
    error_type = "BoundaryError"


class AAISCapabilityModule(ABC):
    module_name = "capability"

    def __init__(
        self,
        *,
        provider_name: str,
        logger: logging.Logger | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.logger = logger or logging.getLogger(f"{__name__}.{self.module_name}.{provider_name}")

    def execute(self, action: str, payload: dict[str, Any]) -> JsonDict:
        result: JsonDict | None = None
        try:
            if not isinstance(payload, dict):
                raise InputValidationError("Adapter payload must be a dictionary.")
            data, model = self._perform_action(action, payload)
            if not isinstance(data, dict):
                raise SemanticValidationError("Capability action did not return a dictionary payload.")
            result = self._ok(
                action,
                data=data,
                provider=self.provider_name,
                model=model,
                timestamp=_utc_timestamp(),
            )
        except Exception as exc:  # noqa: BLE001 - sealed provider boundary
            result = self._guarded_error(action, exc)
        finally:
            self._log_execution(action, result)
        return result

    @abstractmethod
    def _perform_action(self, action: str, payload: dict[str, Any]) -> tuple[JsonDict, str]:
        raise NotImplementedError

    def _ok(self, action: str, *, data: JsonDict, **meta: Any) -> JsonDict:
        return {
            "ok": True,
            "module": self.module_name,
            "action": action,
            "data": data,
            "meta": meta,
        }

    def _err(self, action: str, error_type: str, message: str, **details: Any) -> JsonDict:
        return {
            "ok": False,
            "module": self.module_name,
            "action": action,
            "error_type": error_type,
            "message": message,
            "details": details,
        }

    def _guarded_error(self, action: str, exc: Exception) -> JsonDict:
        if isinstance(exc, (InputValidationError, SemanticValidationError)):
            return self._err(
                action,
                exc.error_type,
                str(exc),
                provider=self.provider_name,
                exception=str(exc),
            )
        if isinstance(exc, APIExecutionError):
            return self._err(
                action,
                exc.error_type,
                self._action_failure_message(action),
                provider=self.provider_name,
                exception=str(exc),
            )
        if isinstance(exc, CapabilityModuleError):
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
        return f"{self.module_name.title()} action failed"

    def _log_execution(self, action: str, result: JsonDict | None) -> None:
        if result is None:
            self.logger.error(
                "%s execution ended without result provider=%s action=%s",
                self.module_name,
                self.provider_name,
                action,
            )
            return
        if result.get("ok"):
            self.logger.info(
                "%s execution ok provider=%s action=%s timestamp=%s",
                self.module_name,
                self.provider_name,
                action,
                result.get("meta", {}).get("timestamp", "unknown"),
            )
            return
        self.logger.warning(
            "%s execution failed provider=%s action=%s error_type=%s message=%s exception=%s",
            self.module_name,
            self.provider_name,
            action,
            result.get("error_type", "UnknownError"),
            result.get("message", ""),
            result.get("details", {}).get("exception", ""),
        )


class AAISImageModule(AAISCapabilityModule):
    module_name = "image"

    def _action_failure_message(self, action: str) -> str:
        mapping = {
            "generate": "Image generation failed",
            "analyze": "Image analysis failed",
            "edit": "Image edit failed",
        }
        return mapping.get(action, "Image action failed")
