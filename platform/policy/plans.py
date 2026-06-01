"""Default plan templates."""

from __future__ import annotations

from typing import Any

PLAN_TEMPLATES: dict[str, dict[str, Any]] = {
    "free": {
        "plan_id": "free",
        "max_concurrent_jobs": 2,
        "max_daily_cost": 5.0,
        "jobs_per_day": 20,
        "artifacts_per_day": 100,
        "allowed_subsystems": ["mechanic", "lab", "ai_factory", "forgekeeper"],
        "allowed_job_types": ["scan", "session", "build", "plan"],
        "slingshot_enabled": False,
    },
    "pro": {
        "plan_id": "pro",
        "max_concurrent_jobs": 10,
        "max_daily_cost": 100.0,
        "jobs_per_day": 500,
        "artifacts_per_day": 5000,
        "allowed_subsystems": ["mechanic", "slingshot", "lab", "ai_factory", "forgekeeper"],
        "allowed_job_types": ["scan", "preload", "launch", "session", "build", "plan"],
        "slingshot_enabled": True,
    },
    "enterprise": {
        "plan_id": "enterprise",
        "max_concurrent_jobs": 50,
        "max_daily_cost": 10000.0,
        "jobs_per_day": 100000,
        "artifacts_per_day": 1000000,
        "allowed_subsystems": ["mechanic", "slingshot", "lab", "ai_factory", "forgekeeper"],
        "allowed_job_types": ["scan", "preload", "launch", "session", "build", "plan", "generic"],
        "slingshot_enabled": True,
    },
}
