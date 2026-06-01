"""Lab safety protocol — path jail, deny-list, confirmations."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Any

from lab.spec import InstrumentSpec, LabProjectSpec

NETWORK_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


class GovernanceDenied(RuntimeError):
    """Raised when an action violates lab policy."""

    def __init__(self, reason: str, *, violation_class: str = "III") -> None:
        super().__init__(reason)
        self.reason = reason
        self.violation_class = violation_class


def resolve_workspace_path(workspace: Path, relative: str) -> Path:
    rel = relative.replace("\\", "/").lstrip("/")
    if ".." in Path(rel).parts:
        raise GovernanceDenied("path escape via .. is forbidden")
    target = (workspace / rel).resolve()
    workspace_resolved = workspace.resolve()
    try:
        target.relative_to(workspace_resolved)
    except ValueError as exc:
        raise GovernanceDenied(f"path outside workspace: {relative}") from exc
    return target


def path_matches_glob(relative: str, pattern: str) -> bool:
    rel = relative.replace("\\", "/")
    pat = pattern.replace("\\", "/")
    return fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat.lstrip("/"))


def is_read_only(spec: LabProjectSpec, relative: str) -> bool:
    for pattern in spec.prohibitions.read_only_paths:
        if path_matches_glob(relative, pattern):
            return True
    return False


def is_high_impact(spec: LabProjectSpec, relative: str) -> bool:
    for pattern in spec.prohibitions.high_impact_patterns:
        if path_matches_glob(relative, pattern):
            return True
    return False


def requires_confirmation(
    spec: LabProjectSpec,
    instrument: InstrumentSpec | None,
    relative: str,
) -> bool:
    if is_high_impact(spec, relative):
        return True
    if instrument:
        for pattern in instrument.requires_confirmation_paths:
            if path_matches_glob(relative, pattern):
                return True
    return False


def check_command_allowed(spec: LabProjectSpec, argv: list[str]) -> None:
    joined = " ".join(argv).lower()
    for forbidden in spec.prohibitions.forbidden_commands:
        if forbidden.lower() in joined:
            raise GovernanceDenied(f"forbidden command fragment: {forbidden}")


def check_instrument_allowed(
    spec: LabProjectSpec,
    instrument: InstrumentSpec,
    *,
    spine_profile: dict[str, Any] | None = None,
) -> None:
    if instrument.requires_network and not spec.prohibitions.network_allowed:
        raise GovernanceDenied("instrument requires network but policy denies network")
    if instrument.command:
        check_command_allowed(spec, instrument.command)
    if spine_profile:
        enabled = set(
            spine_profile.get("stages", {})
            .get("cortex_execute", {})
            .get("enabled_instruments", [])
        )
        if enabled and instrument.name not in enabled:
            raise GovernanceDenied(f"instrument not enabled in spine: {instrument.name}")


def check_write_allowed(
    spec: LabProjectSpec,
    relative: str,
    *,
    confirmations: set[str],
    instrument: InstrumentSpec | None = None,
) -> None:
    if is_read_only(spec, relative):
        raise GovernanceDenied(f"read-only path: {relative}")
    if requires_confirmation(spec, instrument, relative):
        token = relative.replace("\\", "/")
        if token not in confirmations:
            raise GovernanceDenied(
                f"high-impact write requires confirmation for: {relative}",
                violation_class="II",
            )


def sanitized_subprocess_env(spec: LabProjectSpec) -> dict[str, str]:
    env = dict(os.environ)
    if not spec.prohibitions.network_allowed:
        for key in NETWORK_ENV_KEYS:
            env.pop(key, None)
    return env


def validate_allowed_paths(
    instrument: InstrumentSpec,
    workspace: Path,
    paths: list[str],
) -> None:
    if not instrument.allowed_paths:
        return
    for rel in paths:
        rel_norm = rel.replace("\\", "/")
        if not any(
            rel_norm.startswith(p.rstrip("/") + "/")
            or rel_norm == p.rstrip("/")
            or path_matches_glob(rel_norm, p)
            for p in instrument.allowed_paths
        ):
            raise GovernanceDenied(
                f"path {rel} not under instrument allowed_paths: {instrument.allowed_paths}"
            )
        resolve_workspace_path(workspace, rel)
