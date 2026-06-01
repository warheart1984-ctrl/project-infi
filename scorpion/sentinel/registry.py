"""Sentinel adapter registry (fixture, audit export, kernel stub)."""

from __future__ import annotations

from scorpion.sentinel.audit_log import AuditExportSentinel
from scorpion.sentinel.base import SentinelAdapter
from scorpion.sentinel.fixture import FixtureSentinel
from scorpion.sentinel.kernel_stub import KernelSentinelStub

_ADAPTERS: dict[str, type] = {
    "fixture": FixtureSentinel,
    "audit": AuditExportSentinel,
    "kernel": KernelSentinelStub,
}


def get_sentinel(name: str) -> SentinelAdapter:
    key = (name or "fixture").strip().lower()
    factory = _ADAPTERS.get(key)
    if factory is None:
        allowed = ", ".join(sorted(_ADAPTERS))
        raise ValueError(f"unknown sentinel {name!r}; allowed: {allowed}")
    return factory()


def list_sentinels() -> list[str]:
    return sorted(_ADAPTERS)
