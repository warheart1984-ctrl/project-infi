"""Threaded scan queue for hosted Mechanic."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable


class HostedScanQueue:
    def __init__(self, *, max_workers: int = 2) -> None:
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="mechanic-hosted")
        self.futures: dict[str, Future[dict]] = {}

    def submit(self, scan_id: str, fn: Callable[[], dict]) -> Future[dict]:
        future = self.executor.submit(fn)
        self.futures[scan_id] = future
        return future

    def result(self, scan_id: str, timeout: float | None = None) -> dict:
        future = self.futures[scan_id]
        return future.result(timeout=timeout)
