"""Sentinel adapters for trace ingestion."""

from scorpion.sentinel.audit_log import AuditExportSentinel
from scorpion.sentinel.fixture import FixtureSentinel
from scorpion.sentinel.kernel_stub import KernelSentinelStub
from scorpion.sentinel.registry import get_sentinel, list_sentinels

__all__ = [
    "AuditExportSentinel",
    "FixtureSentinel",
    "KernelSentinelStub",
    "get_sentinel",
    "list_sentinels",
]
