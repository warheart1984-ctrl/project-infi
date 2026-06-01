"""Multi-region job and artifact routing (v9)."""

from __future__ import annotations

import os
from typing import Any


def resolve_job_region(*, org: dict[str, Any] | None, requested: str = "") -> str:
    org_region = str(org.get("region") if org else "us") or "us"
    residency = str(org.get("data_residency") if org else "") or org_region
    region = (requested or org_region).lower()
    if residency and region != residency:
        raise PermissionError(f"region {region} violates data_residency {residency}")
    return region


def region_queue_key(region: str) -> str:
    return f"platform:jobs:{region}"


def enqueue_job_for_region(*, queue: Any, job_id: str, region: str) -> bool:
    return queue.enqueue(job_id, region=region)


def artifact_storage_prefix(*, region: str, org_id: str, subsystem: str, job_id: str) -> str:
    bucket = os.environ.get("PLATFORM_S3_BUCKET", "platform-artifacts")
    return f"s3://{bucket}/{region}/{org_id}/{subsystem}/{job_id}/"


def worker_region() -> str:
    return os.environ.get("PLATFORM_WORKER_REGION", "us").lower()
