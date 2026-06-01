"""Aggregate drift detectors for all platform organs."""

from __future__ import annotations

from typing import Any

from platform.drift.detectors import ai_factory, forgekeeper, lab, mechanic, slingshot


def run_detectors(
    *,
    artifact: dict[str, Any] | None = None,
    job: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for fn in (mechanic.detect, slingshot.detect, lab.detect, ai_factory.detect, forgekeeper.detect):
        findings.extend(fn(artifact=artifact, job=job))
    return findings
