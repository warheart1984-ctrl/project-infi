"""Jarvis Creative Core Runtime - shared bounded wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from src.datetime_compat import UTC
import json
import os
from pathlib import Path
import threading
import uuid
from typing import Any, Literal


RuntimeMode = Literal["real", "dry_run"]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _clip_text(value: Any, limit: int = 320) -> str:
    text = " ".join(str(value or "").split()).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _sanitize_payload(payload: Any, *, max_items: int = 12):
    """Keep runtime payloads compact and JSON-safe."""
    if payload is None:
        return None
    if isinstance(payload, dict):
        result = {}
        for index, (key, value) in enumerate(payload.items()):
            if index >= max_items:
                break
            result[str(key)] = _sanitize_payload(value, max_items=max_items)
        return result
    if isinstance(payload, list):
        return [_sanitize_payload(item, max_items=max_items) for item in payload[:max_items]]
    if isinstance(payload, tuple):
        return [_sanitize_payload(item, max_items=max_items) for item in payload[:max_items]]
    if isinstance(payload, (str, int, float, bool)) or payload is None:
        if isinstance(payload, str):
            return _clip_text(payload, limit=1000)
        return payload
    return _clip_text(repr(payload), limit=1000)


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def _normalize_mode(mode: str | None) -> RuntimeMode:
    normalized = str(mode or "real").strip().lower().replace("-", "_")
    return "dry_run" if normalized == "dry_run" else "real"


@dataclass(frozen=True)
class RuntimeEvent:
    event_id: str
    timestamp: datetime
    runtime_version: str
    event_type: str
    payload: dict[str, Any]
    trace_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        reserved = {
            "id",
            "event_id",
            "timestamp",
            "runtime_version",
            "core",
            "event_type",
            "trace_id",
        }
        payload = _sanitize_payload(self.payload or {})
        data = {
            "id": self.event_id,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "runtime_version": self.runtime_version,
            "core": self.runtime_version,
            "event_type": self.event_type,
            "trace_id": self.trace_id,
        }
        for key, value in (payload or {}).items():
            if key in reserved:
                continue
            data[key] = value
        return data


class CreativeCoreRuntime:
    """Single bounded runtime surface for creative-core execution."""

    def __init__(
        self,
        core_id: str,
        engine,
        runtime_dir: str | Path | None = None,
        *,
        mode: RuntimeMode = "real",
    ) -> None:
        self.core_id = str(core_id or "core").strip().lower()
        self.version = self.core_id
        self.engine = engine
        self.mode = _normalize_mode(mode)
        self.trace_id = str(uuid.uuid4())
        self._lock = threading.Lock()
        self.configure_runtime_dir(runtime_dir or _default_runtime_dir())

    def configure_runtime_dir(self, runtime_dir: str | Path | None) -> None:
        root = Path(runtime_dir or _default_runtime_dir()).expanduser()
        runtime_name = f"{self.core_id}-runtime"
        if root.name.lower() == runtime_name:
            runtime_root = root
            engine_root = root.parent
        else:
            runtime_root = root / runtime_name
            engine_root = root
        if hasattr(self.engine, "configure_runtime_dir"):
            self.engine.configure_runtime_dir(engine_root)
        self.runtime_dir = runtime_root
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.runtime_dir / "state.json"
        self.events_path = self.runtime_dir / "events.jsonl"
        with self._lock:
            self._state = self._load_state()
            self._state.setdefault("trace_id", self.trace_id)
            self._state["mode"] = self.mode
            self._state["version"] = self.version
            self._state["runtime_version"] = self.version
            self._persist_state()

    def reset(self) -> None:
        """Reset in-memory and on-disk runtime state for isolated tests."""
        self.trace_id = str(uuid.uuid4())
        with self._lock:
            self._state = self._default_state()
            self._persist_state()
            self.events_path.write_text("", encoding="utf-8")

    def run(self, input_text: str, **kwargs):
        """Run the wrapped engine and record one inspectable runtime trail."""
        self._mark_running(input_text=input_text, **kwargs)
        request = {
            "input_text": input_text,
            "context": kwargs.get("context", ""),
            "location": kwargs.get("location", ""),
            "characters": kwargs.get("characters"),
            "trace_id": kwargs.get("trace_id") or str(uuid.uuid4()),
            "task_type": kwargs.get("task_type") or f"{self.core_id}_creative_pass",
            "sensitivity_level": kwargs.get("sensitivity_level"),
            "model": kwargs.get("model"),
        }
        for key, value in kwargs.items():
            if key not in request:
                request[key] = value
        try:
            result = self.execute_model_call(request)
        except Exception as exc:
            self.record_failure(
                input_text=input_text,
                error=str(exc),
                trace_id=request["trace_id"],
                context=kwargs.get("context"),
                location=kwargs.get("location"),
                characters=kwargs.get("characters"),
            )
            raise

        event = self.record_success(result)
        enriched = dict(result)
        enriched["runtime"] = {
            "event": event,
            "snapshot": self.snapshot(limit=5),
        }
        return enriched

    def execute_model_call(self, request: dict[str, Any]) -> dict[str, Any]:
        """Bounded model interaction with centralized observability."""
        trace_id = str(request.get("trace_id") or self.trace_id or uuid.uuid4())
        self.log_event(
            "model_call_started",
            {
                "task_type": request.get("task_type") or f"{self.core_id}_creative_pass",
                "sensitivity_level": request.get("sensitivity_level"),
                "model": request.get("model"),
            },
            trace_id=trace_id,
        )
        try:
            response = self._perform_model_call(request)
        except Exception as exc:
            self.log_event(
                "model_call_failed",
                {
                    "task_type": request.get("task_type") or f"{self.core_id}_creative_pass",
                    "model": request.get("model"),
                    "status": "failed",
                    "error": _clip_text(str(exc), limit=240),
                },
                trace_id=trace_id,
            )
            raise

        usage = response.get("usage") if isinstance(response, dict) else {}
        self.log_event(
            "model_call_completed",
            {
                "model": request.get("model") or response.get("model"),
                "provider": response.get("provider"),
                "tokens_used": (usage or {}).get("total_tokens"),
                "status": "success",
            },
            trace_id=trace_id,
        )
        result = dict(response)
        result.setdefault("runtime_version", self.version)
        result.setdefault("core", self.core_id)
        result["trace_id"] = trace_id
        return result

    def _perform_model_call(self, request: dict[str, Any]) -> dict[str, Any]:
        """Default bounded call bridge to the wrapped engine."""
        input_text = " ".join(str(request.get("input_text") or request.get("input") or "").split()).strip()
        if not input_text:
            raise ValueError(f"{self.core_id.upper()} runtime needs a non-empty input prompt.")
        reserved = {
            "input_text",
            "input",
            "trace_id",
            "task_type",
            "sensitivity_level",
            "model",
        }
        engine_kwargs = {
            key: value
            for key, value in request.items()
            if key not in reserved and value is not None
        }
        return self.engine.run(input_text, **engine_kwargs)

    def log_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        trace_id: str | None = None,
        event_id: str | None = None,
    ) -> dict[str, Any]:
        """Centralized immutable event logging for observability."""
        event = RuntimeEvent(
            event_id=str(event_id or f"{self.core_id}_event_{uuid.uuid4().hex[:12]}"),
            timestamp=_utc_now(),
            runtime_version=self.version,
            event_type=str(event_type or "unknown").strip() or "unknown",
            payload=dict(payload or {}),
            trace_id=trace_id or self.trace_id,
        )
        event_dict = event.to_dict()
        with self._lock:
            self._state["event_count"] = int(self._state.get("event_count") or 0) + 1
            self._state["last_updated"] = event_dict["timestamp"]
            self._state["trace_id"] = event_dict.get("trace_id") or self.trace_id
            self._persist_state()
            self._append_event_locked(event_dict)
        return event_dict

    def get_runtime_state(self) -> dict[str, Any]:
        """Return the API and Workbench snapshot without recent events."""
        with self._lock:
            payload = dict(self._state)
        payload["core"] = self.core_id
        payload["version"] = self.version
        payload["runtime_version"] = self.version
        payload["mode"] = self.mode
        return payload

    def snapshot(self, *, limit: int = 10) -> dict[str, Any]:
        payload = self.get_runtime_state()
        payload["recent_events"] = self.list_events(limit=limit)
        payload["event_count"] = len(payload["recent_events"]) if payload.get("event_count") is None else payload["event_count"]
        from src.aais_ul.runtime import wrap_runtime_snapshot

        return wrap_runtime_snapshot(payload)

    def get_events(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.list_events(limit=limit)

    def list_events(self, *, limit: int = 20) -> list[dict[str, Any]]:
        normalized_limit = max(1, min(int(limit or 20), 100))
        if not self.events_path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in self.events_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events[-normalized_limit:]

    def update_state(self, key: str, value: Any) -> None:
        """Safe audited state mutation."""
        with self._lock:
            self._state[key] = _sanitize_payload(value)
            self._state["last_updated"] = _utc_now_iso()
            self._persist_state()
        self.log_event("state_updated", {"key": key, "value": _clip_text(value, limit=240)})

    def record_success(self, result: dict[str, Any]) -> dict[str, Any]:
        output = str(result.get("output") or result.get("summary") or "").strip()
        scene = result.get("scene") if isinstance(result.get("scene"), dict) else {}
        event_payload = {
            "status": str(result.get("status") or "completed"),
            "summary": _clip_text(output or result.get("input") or f"{self.core_id} run completed."),
            "provider": str(result.get("provider") or ""),
            "model": str(result.get("model") or ""),
            "pipeline": [str(item).strip() for item in (result.get("pipeline") or []) if str(item).strip()],
            "location": str(result.get("location") or scene.get("location") or ""),
            "characters": [str(name).strip() for name in (result.get("characters") or []) if str(name).strip()],
            "quality_score": result.get("quality_report", {}).get("quality_score")
            if isinstance(result.get("quality_report"), dict)
            else None,
        }
        timestamp = _utc_now_iso()
        event_id = f"{self.core_id}_run_{uuid.uuid4().hex[:12]}"
        with self._lock:
            self._state.update(
                {
                    "core": self.core_id,
                    "version": self.version,
                    "runtime_version": self.version,
                    "mode": self.mode,
                    "status": "ready",
                    "last_run_id": event_id,
                    "last_run_at": timestamp,
                    "last_input": _clip_text(result.get("input")),
                    "last_summary": event_payload["summary"],
                    "last_provider": event_payload["provider"],
                    "last_model": event_payload["model"],
                    "last_pipeline": list(event_payload["pipeline"]),
                    "last_location": event_payload["location"],
                    "last_characters": list(event_payload["characters"]),
                    "last_quality_score": event_payload["quality_score"],
                    "last_memory_path": str(result.get("memory_path") or ""),
                    "scene_count": int(self._state.get("scene_count") or 0) + 1,
                    "run_count": int(self._state.get("run_count") or 0) + 1,
                    "failure_count": int(self._state.get("failure_count") or 0),
                    "last_updated": timestamp,
                    "trace_id": str(result.get("trace_id") or self.trace_id),
                }
            )
            self._persist_state()
        event = self.log_event(
            "completed",
            {"id": event_id, **event_payload},
            trace_id=str(result.get("trace_id") or self.trace_id),
            event_id=event_id,
        )
        return event

    def record_failure(
        self,
        *,
        input_text: str,
        error: str,
        trace_id: str | None = None,
        context: str | None = None,
        location: str | None = None,
        characters: list[str] | None = None,
    ) -> dict[str, Any]:
        event_id = f"{self.core_id}_run_{uuid.uuid4().hex[:12]}"
        summary = _clip_text(error or f"{self.core_id} runtime failed.")
        timestamp = _utc_now_iso()
        event_payload = {
            "id": event_id,
            "status": "failed",
            "summary": summary,
            "provider": "",
            "model": "",
            "pipeline": [],
            "location": str(location or ""),
            "characters": [str(name).strip() for name in (characters or []) if str(name).strip()],
            "quality_score": None,
            "context": _clip_text(context or "", limit=240),
        }
        with self._lock:
            self._state.update(
                {
                    "core": self.core_id,
                    "version": self.version,
                    "runtime_version": self.version,
                    "mode": self.mode,
                    "status": "degraded",
                    "last_run_id": event_id,
                    "last_run_at": timestamp,
                    "last_input": _clip_text(input_text),
                    "last_summary": summary,
                    "last_provider": "",
                    "last_model": "",
                    "last_pipeline": [],
                    "last_location": event_payload["location"],
                    "last_characters": list(event_payload["characters"]),
                    "last_quality_score": None,
                    "run_count": int(self._state.get("run_count") or 0),
                    "failure_count": int(self._state.get("failure_count") or 0) + 1,
                    "last_updated": timestamp,
                    "trace_id": str(trace_id or self.trace_id),
                }
            )
            self._persist_state()
        return self.log_event(
            "failed",
            event_payload,
            trace_id=str(trace_id or self.trace_id),
            event_id=event_id,
        )

    def _mark_running(self, input_text: str, **kwargs) -> None:
        with self._lock:
            self._state.update(
                {
                    "core": self.core_id,
                    "version": self.version,
                    "runtime_version": self.version,
                    "mode": self.mode,
                    "status": "running",
                    "last_input": _clip_text(input_text),
                    "last_location": str(kwargs.get("location") or ""),
                    "last_characters": [
                        str(name).strip()
                        for name in (kwargs.get("characters") or [])
                        if str(name).strip()
                    ],
                    "last_updated": _utc_now_iso(),
                }
            )
            self._persist_state()

    def _default_state(self) -> dict[str, Any]:
        return {
            "core": self.core_id,
            "version": self.version,
            "runtime_version": self.version,
            "mode": self.mode,
            "status": "idle",
            "last_run_id": None,
            "last_run_at": None,
            "last_input": "",
            "last_summary": "",
            "last_provider": "",
            "last_model": "",
            "last_pipeline": [],
            "last_location": "",
            "last_characters": [],
            "last_quality_score": None,
            "last_memory_path": "",
            "scene_count": 0,
            "run_count": 0,
            "failure_count": 0,
            "event_count": 0,
            "trace_id": self.trace_id,
            "last_updated": _utc_now_iso(),
        }

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return self._default_state()
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return self._default_state()
        if not isinstance(payload, dict):
            return self._default_state()
        state = self._default_state()
        state.update(payload)
        state["mode"] = _normalize_mode(state.get("mode"))
        state["version"] = self.version
        state["runtime_version"] = self.version
        state.setdefault("trace_id", self.trace_id)
        return state

    def _persist_state(self) -> None:
        self.state_path.write_text(
            json.dumps(_sanitize_payload(self._state), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _append_event_locked(self, event: dict[str, Any]) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_sanitize_payload(event), ensure_ascii=False) + "\n")

    def __repr__(self) -> str:
        return (
            f"<CreativeCoreRuntime v={self.version} mode={self.mode} "
            f"events={self.get_runtime_state().get('event_count', 0)}>"
        )


def create_runtime(
    version: str,
    mode: RuntimeMode = "real",
    runtime_dir: str | Path | None = None,
) -> CreativeCoreRuntime:
    """Factory helper for version-specific runtime wrappers."""
    normalized = str(version or "").strip().lower()
    if normalized == "v9":
        try:
            from .v9_runtime import V9Runtime
        except ImportError:  # pragma: no cover - fallback for direct module execution
            from src.v9_runtime import V9Runtime

        return V9Runtime(mode=mode, runtime_dir=runtime_dir)
    if normalized == "v10":
        try:
            from .v10_runtime import V10Runtime
        except ImportError:  # pragma: no cover - fallback for direct module execution
            from src.v10_runtime import V10Runtime

        return V10Runtime(mode=mode, runtime_dir=runtime_dir)
    raise ValueError(f"Unknown runtime version: {version}")
