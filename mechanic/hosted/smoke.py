"""Hosted Mechanic smoke gate using only local stubs."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from mechanic.hosted.stubs import create_stubbed_service


def run_stubbed_smoke(*, repo_path: str | Path, artifact_root: str | Path | None = None) -> dict[str, Any]:
    root_ctx = tempfile.TemporaryDirectory() if artifact_root is None else None
    root = Path(artifact_root or root_ctx.name).resolve()  # type: ignore[union-attr]
    try:
        service = create_stubbed_service(
            artifact_root=root / "artifacts",
            db_path=root / "hosted.sqlite3",
            source_repo=repo_path,
        )
        service.github_installation_callback(
            {
                "customer_id": "stub-customer",
                "org": "stub-org",
                "repo_id": "stub-org/mechanic-fixture",
                "installation_id": "stub-installation",
            }
        )
        result = service.create_scan(
            {
                "installation_id": "stub-installation",
                "scan_id": "stub-scan",
                "case_id": "stub-case",
                "repo_ref": "main",
                "checkout": True,
                "wait": True,
            }
        )
        report = service.get_scan_report("stub-scan")
        artifacts = service.get_scan_artifacts("stub-scan")
        return {
            "ok": True,
            "job_status": result["job"]["status"],
            "confidence_label": artifacts.get("confidence_label"),
            "top_risk_class": report.get("top_risk_class"),
            "signed_artifacts": sorted((artifacts.get("signed_artifact_links") or {}).keys()),
            "artifact_dir": artifacts.get("artifact_dir"),
        }
    finally:
        if root_ctx is not None:
            root_ctx.cleanup()


def main() -> int:
    repo = Path(__file__).resolve().parents[1] / "fixtures" / "sample-customer-repo"
    result = run_stubbed_smoke(repo_path=repo)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
