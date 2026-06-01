"""GitHub App helpers for hosted Mechanic."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import requests

from mechanic.hosted.security import verify_github_webhook_signature


class GitHubAppClient:
    def __init__(self, *, app_id: str, private_key_pem: str, webhook_secret: str, api_base: str = "https://api.github.com") -> None:
        self.app_id = app_id
        self.private_key_pem = private_key_pem
        self.webhook_secret = webhook_secret
        self.api_base = api_base.rstrip("/")

    def verify_webhook(self, *, body: bytes, signature_header: str) -> bool:
        return verify_github_webhook_signature(
            body=body,
            signature_header=signature_header,
            webhook_secret=self.webhook_secret,
        )

    def app_jwt(self) -> str:
        try:
            import jwt  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("PyJWT is required for GitHub App JWT signing") from exc
        now = int(time.time())
        payload = {"iat": now - 60, "exp": now + 540, "iss": self.app_id}
        return jwt.encode(payload, self.private_key_pem, algorithm="RS256")

    def installation_token(self, installation_id: str, *, repositories: list[str] | None = None) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.app_jwt()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        body: dict[str, Any] = {"permissions": {"contents": "read", "metadata": "read"}}
        if repositories:
            body["repositories"] = repositories
        response = requests.post(
            f"{self.api_base}/app/installations/{installation_id}/access_tokens",
            headers=headers,
            json=body,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def checkout_repo(
        self,
        *,
        installation_id: str,
        repo_id: str,
        checkout_root: Path,
        repo_ref: str = "main",
        clone_url: str | None = None,
    ) -> str:
        token_payload = self.installation_token(installation_id, repositories=[repo_id.split("/")[-1]])
        token = str(token_payload.get("token") or "")
        if not token:
            raise ValueError("GitHub installation token response did not include token")
        url = clone_url or f"https://github.com/{repo_id}.git"
        auth_url = url.replace("https://", f"https://x-access-token:{token}@")
        checkout_root.mkdir(parents=True, exist_ok=True)
        target = checkout_root / _safe_repo_id(repo_id) / _safe_repo_id(repo_ref)
        if target.exists():
            shutil.rmtree(target)
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", repo_ref, auth_url, str(target)],
            capture_output=True,
            text=True,
            timeout=300,
            check=True,
        )
        return str(target)

    @staticmethod
    def installation_payload_from_webhook(payload: dict[str, Any]) -> dict[str, Any]:
        installation = payload.get("installation") or {}
        repo = payload.get("repository") or {}
        account = installation.get("account") or payload.get("sender") or {}
        return {
            "installation_id": str(installation.get("id") or ""),
            "customer_id": str((account.get("login") if isinstance(account, dict) else "") or "github-customer"),
            "org": str((account.get("login") if isinstance(account, dict) else "") or "github-org"),
            "repo_id": str(repo.get("full_name") or ""),
            "default_branch": str(repo.get("default_branch") or "main"),
            "permissions": ["contents:read", "metadata:read"],
        }


def _safe_repo_id(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in value)[:120]
