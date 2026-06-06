"""Brain session CRUD and operator decisions."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.brain_deliberation_runtime import deliberate
from src.brain_proposal_validator import build_brain_proposal

VALID_DECISIONS = frozenset({"accept", "reject", "defer"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


class BrainSessionStore:
    def __init__(self, *, runtime_dir: Path | None = None):
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._dir = self._runtime_dir / "brain_sessions"
        self._lock = threading.Lock()

    def _path(self, session_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
        return self._dir / f"{safe}.json"

    def list_sessions(self) -> list[dict[str, Any]]:
        if not self._dir.is_dir():
            return []
        sessions: list[dict[str, Any]] = []
        for path in sorted(self._dir.glob("*.json")):
            try:
                sessions.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return sessions

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        path = self._path(session_id)
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _write(self, session: dict[str, Any]) -> dict[str, Any]:
        session["updated_at"] = _utc_now_iso()
        path = self._path(str(session["session_id"]))
        with self._lock:
            self._dir.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(session, sort_keys=True) + "\n", encoding="utf-8")
        return session

    def create_session(self, text: str, *, include_deliberation: bool = False) -> dict[str, Any]:
        session_id = f"sess-{uuid4()}"
        proposal = build_brain_proposal(text, emitter="brain_session_store")
        session = {
            "brain_session_version": "brain_session.v1",
            "session_id": session_id,
            "created_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
            "status": "open",
            "operator_decision": "pending",
            "operator_text": text[:500],
            "proposals": [proposal],
            "deliberations": [],
            "active_deliberation_id": None,
        }
        if include_deliberation:
            deliberation = deliberate(text, session_id=session_id)
            session["deliberations"] = [deliberation]
            session["active_deliberation_id"] = deliberation.get("deliberation_id")
        return self._write(session)

    def append_proposal(self, session_id: str, text: str) -> dict[str, Any] | None:
        session = self.get_session(session_id)
        if not session:
            return None
        session.setdefault("proposals", []).append(build_brain_proposal(text, emitter="brain_session_store"))
        return self._write(session)

    def decide(self, session_id: str, decision: str) -> dict[str, Any] | None:
        if decision not in VALID_DECISIONS:
            return None
        session = self.get_session(session_id)
        if not session:
            return None
        mapping = {"accept": "accepted", "reject": "rejected", "defer": "deferred"}
        session["operator_decision"] = mapping[decision]
        if decision in {"reject", "defer"}:
            session["status"] = "closed"
        return self._write(session)

    def append_deliberation(self, session_id: str, text: str) -> dict[str, Any] | None:
        session = self.get_session(session_id)
        if not session:
            return None
        deliberation = deliberate(text, session_id=session_id)
        session.setdefault("deliberations", []).append(deliberation)
        session["active_deliberation_id"] = deliberation.get("deliberation_id")
        return self._write(session)


brain_session_store = BrainSessionStore()
