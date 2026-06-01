from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from src.jarvis_types import ProviderDecision


CODE_PATH_RE = re.compile(
    r"(?:^|[\s'\"`])(src/|tests/|frontend/|.+\.(?:py|js|jsx|ts|tsx|css|json|toml|yml|yaml))(?:$|[\s'\"`])",
    re.IGNORECASE,
)
CODE_TERMS = {
    "api.py",
    "pytest",
    "traceback",
    "pending_action",
    "action_lifecycle",
    "executed_at",
    "src/",
    "tests/",
    "debug",
    "fix",
    "route",
    "repo",
    "workspace",
    "patch",
    "build",
    "verify",
}
CREATIVE_TERMS = {"scene", "chapter", "dialogue", "story", "continue this scene", "v10", "v9"}
MYSTIC_TERMS = {"mystic", "reading", "oracle", "omen", "divination"}


class ProviderMind:
    """Choose the high-level Jarvis engine path while keeping one visible mind."""

    def choose_path(self, request: dict[str, Any]) -> dict[str, Any]:
        message = " ".join(str(request.get("message") or "").split()).strip()
        lowered = message.lower()
        response_mode = str(request.get("response_mode") or "fast").strip().lower()
        mode_scope = str(request.get("mode_scope") or "").strip().lower()
        workspace_context = request.get("workspace_context") or {}
        preferred_provider = str(request.get("preferred_provider") or "local").strip().lower()
        if preferred_provider in {"automatic", "best", "best_provider", "best_available", "auto_best"}:
            preferred_provider = "auto"

        workspace_hits = len((workspace_context.get("results") or []))
        focus_files = [
            result.get("relative_path")
            for result in workspace_context.get("results", [])
            if result.get("relative_path")
        ]

        if response_mode in {"tiny", "small", "super", "governed_full"}:
            if response_mode == "small":
                label = "Small Nova"
                hidden_reason = "small_nova_lane"
            elif response_mode in {"super", "governed_full"}:
                label = "Super Nova"
                hidden_reason = "super_nova_lane"
            else:
                label = "Tiny Nova"
                hidden_reason = "tiny_nova_lane"
            decision = ProviderDecision(
                decision_id=f"pm_{uuid4().hex}",
                engine_path="jarvis_chat",
                fallback_path="local",
                confidence=0.98,
                summary=f"ProviderMind kept the turn on the {label} companion path.",
                hidden_reason=hidden_reason,
                route_kind="primary",
            )
            return decision.to_dict()

        if any(term in lowered for term in MYSTIC_TERMS):
            decision = ProviderDecision(
                decision_id=f"pm_{uuid4().hex}",
                engine_path="mystic",
                fallback_path="jarvis_chat",
                confidence=0.96,
                summary="ProviderMind chose the Mystic path for a symbolic or reflective request.",
                hidden_reason="mystic_terms",
                route_kind="specialized",
            )
            return decision.to_dict()

        if any(term in lowered for term in CREATIVE_TERMS):
            primary = "v10_core" if "v10" in lowered or "scene" in lowered or "chapter" in lowered else "v9_core"
            fallback = "v9_core" if primary == "v10_core" else "jarvis_chat"
            decision = ProviderDecision(
                decision_id=f"pm_{uuid4().hex}",
                engine_path=primary,
                fallback_path=fallback,
                confidence=0.88,
                summary="ProviderMind chose the creative scene path.",
                hidden_reason="creative_terms",
                route_kind="specialized",
            )
            return decision.to_dict()

        code_signal_count = sum(term in lowered for term in CODE_TERMS)
        if CODE_PATH_RE.search(lowered):
            code_signal_count += 2
        if any(str(path or "").startswith(("AAIS-main/src/", "AAIS-main/tests/", "src/", "tests/")) for path in focus_files):
            code_signal_count += 2
        if workspace_hits:
            code_signal_count += 1

        if code_signal_count >= 3:
            engine_path = (
                "workbench_debug"
                if response_mode == "debug" or mode_scope == "debugging"
                else ("workbench_builder" if response_mode == "builder" else "workbench_coding")
            )
            decision = ProviderDecision(
                decision_id=f"pm_{uuid4().hex}",
                engine_path=engine_path,
                fallback_path="jarvis_chat",
                confidence=min(0.99, 0.62 + (0.05 * code_signal_count)),
                summary="ProviderMind chose the workbench-aware coding path.",
                hidden_reason=f"code_signals:{code_signal_count}",
                route_kind="primary",
            )
            return decision.to_dict()

        fallback_provider = preferred_provider if preferred_provider not in {"", "local", "auto"} else "local"
        decision = ProviderDecision(
            decision_id=f"pm_{uuid4().hex}",
            engine_path="jarvis_chat",
            fallback_path=fallback_provider,
            confidence=0.72,
            summary="ProviderMind kept the turn on the main Jarvis chat path.",
            hidden_reason="default_chat",
            route_kind="primary",
        )
        return decision.to_dict()
