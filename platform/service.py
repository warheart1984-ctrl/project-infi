"""Platform service composition root."""

from __future__ import annotations

from pathlib import Path

from platform.artifacts.index import ArtifactIndex
from platform.jobs.queue import JobQueue
from platform.jobs.registry import JobRegistry
from platform.quotas.limiter import QuotaLimiter
from platform.settings import PlatformSettings
from platform.store import PlatformStore


class PlatformService:
    def __init__(self, settings: PlatformSettings | None = None) -> None:
        self.settings = settings or PlatformSettings.from_env()
        self.settings.runtime_root.mkdir(parents=True, exist_ok=True)
        self.settings.audit_path.parent.mkdir(parents=True, exist_ok=True)
        db_url = self.settings.database_url
        sqlite = "" if db_url else str(self.settings.sqlite_path)
        self.store = PlatformStore(db_path=sqlite, database_url=db_url)
        self.queue = JobQueue(self.settings.redis_url)
        self.jobs = JobRegistry(
            store=self.store,
            queue=self.queue,
            audit_path=self.settings.audit_path,
            quota_limiter=None,
        )
        self.quotas = QuotaLimiter(store=self.store, redis_url=self.settings.redis_url)
        self.jobs.quota_limiter = self.quotas
        self.artifacts = ArtifactIndex(
            store=self.store,
            audit_path=Path(self.settings.audit_path),
        )
