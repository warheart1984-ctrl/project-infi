"""Jarvis continuity profiles.

Continuity belongs to Jarvis, not the underlying provider. This store keeps
the operator-facing voice, formatting, and stable project/tool hints outside
the model layer so they survive routing and provider changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
import json
import os
from pathlib import Path
import threading
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


def _trim_unique(values: list[str], *, limit: int) -> list[str]:
    unique: list[str] = []
    for value in values:
        cleaned = " ".join(str(value or "").split()).strip()
        if not cleaned or cleaned in unique:
            continue
        unique.append(cleaned)
        if len(unique) >= limit:
            break
    return unique


@dataclass
class ContinuityProfile:
    tenant_id: str = "local"
    user_id: str = "operator"
    tone: str = "concise"
    formatting_preferences: dict[str, bool] = field(
        default_factory=lambda: {"markdown": True, "code_blocks": True}
    )
    refusal_style: str = "Calm, direct, and specific about the real limit."
    explanation_style: str = "Explain the answer plainly without collapsing into generic assistant language."
    known_projects: list[str] = field(default_factory=list)
    preferred_tools: list[str] = field(default_factory=list)
    self_description: str = (
        "You are Jarvis, the operator-facing sovereign core for a private local AAIS system. "
        "You remain Jarvis across provider swaps, fallback, routing changes, and guardrail interventions."
    )
    continuity_rules: list[str] = field(
        default_factory=lambda: [
            "Answer as Jarvis in one consistent voice.",
            "Do not refer to the user as Jarvis.",
            "Do not collapse into generic assistant disclaimers.",
            "Preserve operator-facing continuity before display.",
        ]
    )
    updated_at: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "tone": self.tone,
            "formatting_preferences": dict(self.formatting_preferences),
            "refusal_style": self.refusal_style,
            "explanation_style": self.explanation_style,
            "known_projects": list(self.known_projects),
            "preferred_tools": list(self.preferred_tools),
            "self_description": self.self_description,
            "continuity_rules": list(self.continuity_rules),
            "updated_at": self.updated_at,
        }


class ContinuityProfileStore:
    """Persist one local-first continuity profile per operator."""

    def __init__(self, runtime_dir: str | Path | None = None):
        self.runtime_dir = Path(runtime_dir or _default_runtime_dir()) / "continuity"
        self._lock = threading.Lock()
        self._profiles: dict[str, dict[str, Any]] = {}
        self._load()

    @property
    def _profiles_path(self) -> Path:
        return self.runtime_dir / "profiles.json"

    def configure_runtime_dir(self, runtime_dir: str | Path) -> None:
        with self._lock:
            self.runtime_dir = Path(runtime_dir) / "continuity"
            self._profiles = {}
            self._load()

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._profiles = {}
            self._persist_locked()
        return self.get_profile().to_dict()

    def get_profile(self, tenant_id: str = "local", user_id: str = "operator") -> ContinuityProfile:
        key = self._profile_key(tenant_id, user_id)
        with self._lock:
            payload = dict(self._profiles.get(key) or {})
            if not payload:
                profile = ContinuityProfile(tenant_id=tenant_id, user_id=user_id)
                self._profiles[key] = profile.to_dict()
                self._persist_locked()
                return profile
            return ContinuityProfile(**payload)

    def update_profile(
        self,
        *,
        tenant_id: str = "local",
        user_id: str = "operator",
        tone: str | None = None,
        formatting_preferences: dict[str, bool] | None = None,
        refusal_style: str | None = None,
        explanation_style: str | None = None,
        known_projects: list[str] | None = None,
        preferred_tools: list[str] | None = None,
        self_description: str | None = None,
        continuity_rules: list[str] | None = None,
    ) -> dict[str, Any]:
        profile = self.get_profile(tenant_id=tenant_id, user_id=user_id)
        if tone is not None:
            profile.tone = str(tone).strip() or profile.tone
        if formatting_preferences is not None:
            profile.formatting_preferences = {
                "markdown": bool(formatting_preferences.get("markdown", True)),
                "code_blocks": bool(formatting_preferences.get("code_blocks", True)),
            }
        if refusal_style is not None:
            profile.refusal_style = str(refusal_style).strip() or profile.refusal_style
        if explanation_style is not None:
            profile.explanation_style = str(explanation_style).strip() or profile.explanation_style
        if known_projects is not None:
            profile.known_projects = _trim_unique(list(known_projects), limit=8)
        if preferred_tools is not None:
            profile.preferred_tools = _trim_unique(list(preferred_tools), limit=8)
        if self_description is not None:
            profile.self_description = str(self_description).strip() or profile.self_description
        if continuity_rules is not None:
            profile.continuity_rules = _trim_unique(list(continuity_rules), limit=8)
        profile.updated_at = _utc_now_iso()
        with self._lock:
            self._profiles[self._profile_key(tenant_id, user_id)] = profile.to_dict()
            self._persist_locked()
        return profile.to_dict()

    def refresh_from_session(
        self,
        session,
        *,
        tenant_id: str = "local",
        user_id: str = "operator",
    ) -> dict[str, Any]:
        profile = self.get_profile(tenant_id=tenant_id, user_id=user_id)
        projects = list(profile.known_projects)
        tools = list(profile.preferred_tools)

        projects = _trim_unique(
            list(session.memory_summary.active_projects) + projects,
            limit=8,
        )
        workspace_context = session.metadata.get("workspace_context") or {}
        for result in workspace_context.get("results", [])[:4]:
            relative_path = str(result.get("relative_path") or "").strip()
            if relative_path:
                projects = _trim_unique([relative_path] + projects, limit=8)
        action_lifecycle = session.metadata.get("action_lifecycle") or {}
        action = action_lifecycle.get("action") or session.metadata.get("pending_action") or {}
        if action.get("label"):
            tools = _trim_unique([action["label"]] + tools, limit=8)
        if session.metadata.get("browser_verification"):
            tools = _trim_unique(["browser_verify"] + tools, limit=8)

        return self.update_profile(
            tenant_id=tenant_id,
            user_id=user_id,
            known_projects=projects,
            preferred_tools=tools,
        )

    def build_prompt_block(self, profile: ContinuityProfile) -> str:
        tool_summary = ", ".join(profile.preferred_tools[:4]) or "none yet"
        project_summary = ", ".join(profile.known_projects[:4]) or "none yet"
        rules = "\n".join(f"- {rule}" for rule in profile.continuity_rules)
        return (
            "Jarvis Continuity Profile\n"
            f"Self description: {profile.self_description}\n"
            f"Tone: {profile.tone}\n"
            f"Formatting: markdown={str(profile.formatting_preferences.get('markdown', True)).lower()}, "
            f"code_blocks={str(profile.formatting_preferences.get('code_blocks', True)).lower()}\n"
            f"Refusal style: {profile.refusal_style}\n"
            f"Explanation style: {profile.explanation_style}\n"
            f"Known projects: {project_summary}\n"
            f"Preferred tools: {tool_summary}\n"
            "Continuity rules:\n"
            f"{rules}"
        )

    def _profile_key(self, tenant_id: str, user_id: str) -> str:
        return f"{tenant_id}:{user_id}"

    def _load(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        if not self._profiles_path.exists():
            self._profiles = {}
            return
        try:
            self._profiles = json.loads(self._profiles_path.read_text(encoding="utf-8"))
        except Exception:
            self._profiles = {}

    def _persist_locked(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._profiles_path.write_text(json.dumps(self._profiles, indent=2), encoding="utf-8")


continuity_profile_store = ContinuityProfileStore()
