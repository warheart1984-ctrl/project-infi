"""Deterministic stubs for hosted Mechanic external dependencies."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from mechanic.hosted.artifacts import FilesystemArtifactStore
from mechanic.hosted.control_plane import HostedMechanicService


class StubGitHubAppClient:
    """GitHub App stand-in for local smoke tests and demos."""

    def __init__(self, *, source_repo: str | Path | None = None) -> None:
        self.source_repo = Path(source_repo).expanduser().resolve() if source_repo else None

    def verify_webhook(self, *, body: bytes, signature_header: str) -> bool:
        return True

    def installation_token(self, installation_id: str, *, repositories: list[str] | None = None) -> dict[str, Any]:
        return {
            "token": f"stub-token-{installation_id}",
            "permissions": {"contents": "read", "metadata": "read"},
            "repositories": list(repositories or []),
        }

    def checkout_repo(
        self,
        *,
        installation_id: str,
        repo_id: str,
        checkout_root: Path,
        repo_ref: str = "main",
        clone_url: str | None = None,
    ) -> str:
        source = Path(clone_url).expanduser().resolve() if clone_url else self.source_repo
        if source is None or not source.is_dir():
            raise ValueError("stub GitHub checkout requires a local source repo")
        checkout_root.mkdir(parents=True, exist_ok=True)
        target = checkout_root / _safe(repo_id) / _safe(repo_ref)
        if target.exists():
            shutil.rmtree(target)
        ignore = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache")
        shutil.copytree(source, target, ignore=ignore)
        return str(target)


class StubArtifactStore(FilesystemArtifactStore):
    """Object-store stand-in that keeps files local and emits stable stub URLs."""

    def publish_case_dir(self, case_dir: Path) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for path in sorted(case_dir.rglob("*")):
            if path.is_file():
                rel = str(path.relative_to(case_dir)).replace("\\", "/")
                mapping[str(path)] = f"stub-s3://mechanic-artifacts/{case_dir.name}/{rel}"
        return mapping

    def sign_artifact_path(self, path: str | Path) -> str:
        return f"signed-{path}"

    def verify_signed_path(self, signed: str) -> bool:
        return signed.startswith("signed-")


def create_stubbed_service(
    *,
    artifact_root: str | Path,
    db_path: str | Path,
    source_repo: str | Path,
) -> HostedMechanicService:
    service = HostedMechanicService(artifact_root=artifact_root, db_path=db_path)
    service.github = StubGitHubAppClient(source_repo=source_repo)  # type: ignore[assignment]
    service.artifacts = StubArtifactStore(root=artifact_root, signing_secret="stub-signing-secret")
    return service


def _safe(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in value)[:120]
