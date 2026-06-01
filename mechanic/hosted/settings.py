"""Environment-driven settings for hosted Mechanic deployment."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class HostedSettings:
    artifact_root: str = ".runtime/mechanic-hosted"
    database_url: str = ""
    sqlite_path: str = ""
    artifact_backend: str = "filesystem"
    s3_bucket: str = ""
    s3_prefix: str = "mechanic"
    s3_endpoint_url: str = ""
    s3_region: str = "us-east-1"
    api_key_hash: str = ""
    artifact_signing_secret: str = "mechanic-local-dev"
    github_app_id: str = ""
    github_private_key_pem: str = ""
    github_private_key_path: str = ""
    github_webhook_secret: str = ""
    github_checkout_root: str = ".runtime/mechanic-checkouts"
    redis_url: str = ""
    max_workers: int = 2
    max_repo_bytes: int = 25_000_000
    ci_replay_command: str = ""
    second_machine_replay_command: str = ""
    require_api_key: bool = False

    @classmethod
    def from_env(cls) -> "HostedSettings":
        private_key = os.environ.get("MECHANIC_GITHUB_PRIVATE_KEY_PEM", "")
        private_key_path = os.environ.get("MECHANIC_GITHUB_PRIVATE_KEY_PATH", "")
        if not private_key and private_key_path:
            try:
                with open(private_key_path, "r", encoding="utf-8") as handle:
                    private_key = handle.read()
            except OSError:
                private_key = ""
        api_hash = os.environ.get("MECHANIC_HOSTED_API_KEY_SHA256", "")
        return cls(
            artifact_root=os.environ.get("MECHANIC_ARTIFACT_ROOT", ".runtime/mechanic-hosted"),
            database_url=os.environ.get("MECHANIC_DATABASE_URL", ""),
            sqlite_path=os.environ.get("MECHANIC_HOSTED_DB", ""),
            artifact_backend=os.environ.get("MECHANIC_ARTIFACT_BACKEND", "filesystem"),
            s3_bucket=os.environ.get("MECHANIC_S3_BUCKET", ""),
            s3_prefix=os.environ.get("MECHANIC_S3_PREFIX", "mechanic"),
            s3_endpoint_url=os.environ.get("MECHANIC_S3_ENDPOINT_URL", ""),
            s3_region=os.environ.get("MECHANIC_S3_REGION", "us-east-1"),
            api_key_hash=api_hash,
            artifact_signing_secret=os.environ.get("MECHANIC_ARTIFACT_SIGNING_SECRET", "mechanic-local-dev"),
            github_app_id=os.environ.get("MECHANIC_GITHUB_APP_ID", ""),
            github_private_key_pem=private_key,
            github_private_key_path=private_key_path,
            github_webhook_secret=os.environ.get("MECHANIC_GITHUB_WEBHOOK_SECRET", ""),
            github_checkout_root=os.environ.get("MECHANIC_GITHUB_CHECKOUT_ROOT", ".runtime/mechanic-checkouts"),
            redis_url=os.environ.get("MECHANIC_REDIS_URL", ""),
            max_workers=int(os.environ.get("MECHANIC_MAX_WORKERS", "2")),
            max_repo_bytes=int(os.environ.get("MECHANIC_MAX_REPO_BYTES", "25000000")),
            ci_replay_command=os.environ.get("MECHANIC_CI_REPLAY_COMMAND", ""),
            second_machine_replay_command=os.environ.get("MECHANIC_SECOND_MACHINE_REPLAY_COMMAND", ""),
            require_api_key=os.environ.get("MECHANIC_REQUIRE_API_KEY", "").strip() == "1" or bool(api_hash),
        )

    def validate_for_deploy(self) -> list[str]:
        missing: list[str] = []
        if self.require_api_key and not self.api_key_hash:
            missing.append("MECHANIC_HOSTED_API_KEY_SHA256")
        if not self.artifact_signing_secret or self.artifact_signing_secret == "mechanic-local-dev":
            missing.append("MECHANIC_ARTIFACT_SIGNING_SECRET")
        if self.artifact_backend == "s3" and not self.s3_bucket:
            missing.append("MECHANIC_S3_BUCKET")
        if not (self.database_url or self.sqlite_path):
            missing.append("MECHANIC_DATABASE_URL or MECHANIC_HOSTED_DB")
        if not self.github_webhook_secret:
            missing.append("MECHANIC_GITHUB_WEBHOOK_SECRET")
        return missing
