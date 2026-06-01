"""Platform service configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PlatformSettings:
    api_host: str = "127.0.0.1"
    api_port: int = 8090
    database_url: str = ""
    sqlite_path: Path = Path(".runtime/platform/platform.sqlite3")
    redis_url: str = ""
    audit_path: Path = Path(".runtime/platform/audit/platform_audit.jsonl")
    runtime_root: Path = Path(".runtime/platform")
    master_api_key: str = ""
    master_api_key_hash: str = ""
    require_api_key: bool = True
    rate_limit_per_minute: int = 120
    max_request_bytes: int = 1_048_576
    worker_poll_seconds: float = 1.0
    s3_endpoint: str = ""
    s3_bucket: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""

    @classmethod
    def from_env(cls) -> PlatformSettings:
        sqlite = Path(os.environ.get("PLATFORM_SQLITE_PATH", ".runtime/platform/platform.sqlite3"))
        master = os.environ.get("PLATFORM_MASTER_API_KEY", "")
        master_hash = os.environ.get("PLATFORM_MASTER_API_KEY_SHA256", "")
        if master and not master_hash:
            import hashlib

            master_hash = hashlib.sha256(master.encode("utf-8")).hexdigest()
        return cls(
            api_host=os.environ.get("PLATFORM_API_HOST", "127.0.0.1"),
            api_port=int(os.environ.get("PLATFORM_API_PORT", "8090")),
            database_url=os.environ.get("PLATFORM_DATABASE_URL", ""),
            sqlite_path=sqlite,
            redis_url=os.environ.get("PLATFORM_REDIS_URL", ""),
            audit_path=Path(os.environ.get("PLATFORM_AUDIT_PATH", ".runtime/platform/audit/platform_audit.jsonl")),
            runtime_root=Path(os.environ.get("PLATFORM_RUNTIME_ROOT", ".runtime/platform")),
            master_api_key=master,
            master_api_key_hash=master_hash,
            require_api_key=os.environ.get("PLATFORM_REQUIRE_API_KEY", "1") != "0",
            rate_limit_per_minute=int(os.environ.get("PLATFORM_RATE_LIMIT_PER_MINUTE", "120")),
            max_request_bytes=int(os.environ.get("PLATFORM_MAX_REQUEST_BYTES", "1048576")),
            worker_poll_seconds=float(os.environ.get("PLATFORM_WORKER_POLL_SECONDS", "1.0")),
            s3_endpoint=os.environ.get("PLATFORM_S3_ENDPOINT", ""),
            s3_bucket=os.environ.get("PLATFORM_S3_BUCKET", ""),
            s3_access_key=os.environ.get("PLATFORM_S3_ACCESS_KEY", ""),
            s3_secret_key=os.environ.get("PLATFORM_S3_SECRET_KEY", ""),
        )
