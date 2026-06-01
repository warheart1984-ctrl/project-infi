"""Hosted control plane for the Mechanic pilot API."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from mechanic.hosted.artifacts import FilesystemArtifactStore, S3ArtifactStore, artifact_store_from_settings
from mechanic.hosted.github_app import GitHubAppClient
from mechanic.hosted.models import Customer, RepoInstallation, ScanJob, SignoffPolicy
from mechanic.hosted.queue import HostedScanQueue
from mechanic.hosted.security import append_audit_event
from mechanic.hosted.settings import HostedSettings
from mechanic.hosted.store import HostedMechanicStore
from mechanic.hosted.trace_import import import_trace_file
from mechanic.hosted.worker import run_hosted_scan


class HostedMechanicService:
    """Persistent pilot service matching the planned v1 API surface."""

    def __init__(
        self,
        *,
        artifact_root: str | Path,
        db_path: str | Path | None = None,
        database_url: str = "",
        artifact_signing_secret: str = "mechanic-local-dev",
        max_workers: int = 2,
        settings: HostedSettings | None = None,
    ) -> None:
        self.settings = settings or HostedSettings.from_env()
        self.artifact_root = Path(artifact_root).expanduser().resolve()
        self.store = HostedMechanicStore(
            db_path=db_path or self.settings.sqlite_path or (self.artifact_root / "mechanic_hosted.sqlite3"),
            database_url=database_url or self.settings.database_url,
        )
        self.artifacts = artifact_store_from_settings(self.settings)
        if isinstance(self.artifacts, FilesystemArtifactStore):
            self.artifacts = FilesystemArtifactStore(root=self.artifact_root, signing_secret=artifact_signing_secret)
        self.queue = HostedScanQueue(max_workers=max_workers or self.settings.max_workers)
        self.audit_log = self.artifact_root / "audit" / "hosted_audit.jsonl"
        self.github = GitHubAppClient(
            app_id=self.settings.github_app_id,
            private_key_pem=self.settings.github_private_key_pem,
            webhook_secret=self.settings.github_webhook_secret,
        )

    def github_installation_callback(self, payload: dict[str, Any]) -> dict[str, Any]:
        org = str(payload.get("org") or payload.get("account") or "pilot-org")
        customer_id = str(payload.get("customer_id") or f"cust-{uuid4().hex[:10]}")
        repo_id = str(payload.get("repo_id") or payload.get("repository") or "")
        if not repo_id:
            raise ValueError("repo_id is required")
        customer = self.store.get_customer(customer_id) or Customer(customer_id=customer_id, org=org, allowed_repos=[repo_id])
        if repo_id not in customer.allowed_repos:
            customer.allowed_repos.append(repo_id)
        self.store.save_customer(customer)
        installation = RepoInstallation(
            installation_id=str(payload.get("installation_id") or f"inst-{uuid4().hex[:10]}"),
            customer_id=customer_id,
            provider="github",
            repo_id=repo_id,
            default_branch=str(payload.get("default_branch") or "main"),
            permissions=list(payload.get("permissions") or ["contents:read", "metadata:read"]),
        )
        self.store.save_installation(installation)
        append_audit_event(
            self.audit_log,
            event_type="github_installation_callback",
            actor=customer_id,
            payload={"installation_id": installation.installation_id, "repo_id": repo_id},
        )
        return {"customer": customer.model_dump(), "installation": installation.model_dump()}

    def checkout_github_repo(
        self,
        *,
        installation_id: str,
        repo_id: str,
        repo_ref: str = "main",
        clone_url: str | None = None,
    ) -> str:
        return self.github.checkout_repo(
            installation_id=installation_id,
            repo_id=repo_id,
            checkout_root=Path(self.settings.github_checkout_root),
            repo_ref=repo_ref,
            clone_url=clone_url,
        )

    def create_scan(self, payload: dict[str, Any]) -> dict[str, Any]:
        wait = bool(payload.get("wait", True))
        installation_id = str(payload.get("installation_id") or "")
        installation = self.store.get_installation(installation_id)
        if installation is None:
            raise ValueError("unknown installation_id")
        repo_path = str(payload.get("repo_path") or "")
        if not repo_path and payload.get("checkout") is True:
            repo_path = self.checkout_github_repo(
                installation_id=installation_id,
                repo_id=installation.repo_id,
                repo_ref=str(payload.get("repo_ref") or installation.default_branch),
                clone_url=payload.get("clone_url"),
            )
        if not repo_path:
            raise ValueError("repo_path is required for pilot worker checkout")
        scan_id = str(payload.get("scan_id") or f"scan-{uuid4().hex[:12]}")
        case_id = str(payload.get("case_id") or scan_id)
        job = ScanJob(
            scan_id=scan_id,
            case_id=case_id,
            customer_id=installation.customer_id,
            installation_id=installation_id,
            repo_ref=str(payload.get("repo_ref") or installation.default_branch),
        )
        self.store.save_scan_job(job)
        append_audit_event(
            self.audit_log,
            event_type="scan_queued",
            actor=installation.customer_id,
            payload={"scan_id": scan_id, "repo_ref": job.repo_ref},
        )

        def run_job() -> dict[str, Any]:
            job.mark("checking_out")
            self.store.save_scan_job(job)
            job.mark("scanning")
            self.store.save_scan_job(job)
            case_dir = self.artifacts.case_dir(installation.customer_id, scan_id, case_id)
            bundle = run_hosted_scan(
                case_id=case_id,
                scan_id=scan_id,
                repo_path=repo_path,
                artifact_dir=case_dir.parent,
                repo_ref=job.repo_ref,
                trace_paths=list(payload.get("trace_paths") or []),
                policy=installation.policy_profile,
                proof_tier=str(payload.get("proof_tier") or "local"),
                max_repo_bytes=int(payload.get("max_repo_bytes") or self.settings.max_repo_bytes),
            )
            remote_paths = self.artifacts.publish_case_dir(Path(bundle.artifact_dir))
            bundle_payload = bundle.model_dump()
            bundle_path = Path(bundle.artifact_dir) / "evidence_bundle.v1.json"
            if bundle_path.is_file():
                bundle_payload = json.loads(bundle_path.read_text(encoding="utf-8"))
            signed = {
                name: self.artifacts.sign_artifact_path(remote_paths.get(meta["path"], meta["path"]))
                for name, meta in (bundle_payload.get("artifacts") or {}).items()
                if meta.get("path") and not meta.get("missing")
            }
            bundle_payload["signed_artifact_links"] = signed
            bundle_path.write_text(json.dumps(bundle_payload, sort_keys=True, indent=2), encoding="utf-8")
            self.store.save_evidence_bundle(scan_id, installation.customer_id, bundle_payload)
            job.mark("complete")
            self.store.save_scan_job(job)
            append_audit_event(
                self.audit_log,
                event_type="scan_complete",
                actor=installation.customer_id,
                payload={"scan_id": scan_id, "confidence_label": bundle_payload.get("confidence_label")},
            )
            return {"job": job.model_dump(), "evidence_bundle": bundle.model_dump()}

        future = self.queue.submit(scan_id, run_job)
        if not wait:
            return {"job": job.model_dump(), "queued": True}
        try:
            result = future.result(timeout=float(payload.get("timeout_seconds") or 300))
            return result
        except Exception as exc:
            job.error = str(exc)
            job.mark("failed")
            self.store.save_scan_job(job)
            append_audit_event(
                self.audit_log,
                event_type="scan_failed",
                actor=installation.customer_id,
                payload={"scan_id": scan_id, "error": str(exc)},
            )
            raise

    def get_scan(self, scan_id: str) -> dict[str, Any]:
        job = self._job(scan_id)
        return job.model_dump()

    def get_scan_report(self, scan_id: str) -> dict[str, Any]:
        bundle = self.get_scan_artifacts(scan_id)
        path = Path(str(bundle.get("artifact_dir"))) / "mechanic_obd_report.v1.json"
        if not path.is_file():
            raise ValueError("report not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def get_scan_artifacts(self, scan_id: str) -> dict[str, Any]:
        bundle = self.store.get_evidence_bundle(scan_id)
        if bundle is None:
            raise ValueError("evidence bundle not found")
        return bundle

    def import_trace(self, payload: dict[str, Any]) -> dict[str, Any]:
        source = str(payload.get("source") or "generic")
        if source not in {"generic", "langsmith", "n8n", "make", "cursor"}:
            raise ValueError("unsupported trace source")
        input_path = str(payload.get("input_path") or "")
        if not input_path:
            raise ValueError("input_path is required")
        output_path = payload.get("output_path") or (self.artifact_root / "trace_imports" / f"{uuid4().hex}.ndjson")
        return import_trace_file(source=source, input_path=input_path, output_path=output_path)  # type: ignore[arg-type]

    def replay_scan(self, scan_id: str, *, proof_tier: str = "ci") -> dict[str, Any]:
        from mechanic.hosted.worker import replay_scan

        job = self._job(scan_id)
        bundle = self.get_scan_artifacts(scan_id)
        artifact_dir = Path(str(bundle.get("artifact_dir")))
        repo_path = ""
        genome_path = artifact_dir / "process_genome.v1.json"
        if genome_path.is_file():
            genome = json.loads(genome_path.read_text(encoding="utf-8"))
            repo_path = str(genome.get("repo_path") or "")
        if not repo_path:
            raise ValueError("repo_path missing from genome artifact")
        job.mark("replaying")
        self.store.save_scan_job(job)
        result = replay_scan(case_id=job.case_id, repo_path=repo_path, original_case_dir=artifact_dir, tier=proof_tier)
        (artifact_dir / "replay_result.v1.json").write_text(json.dumps(result, sort_keys=True, indent=2), encoding="utf-8")
        job.mark("complete")
        self.store.save_scan_job(job)
        append_audit_event(
            self.audit_log,
            event_type="scan_replay",
            actor=job.customer_id,
            payload={"scan_id": scan_id, "proof_tier": proof_tier, "matched": result.get("matched")},
        )
        return result

    def routes(self) -> dict[str, str]:
        return {
            "POST /v1/installations/github/callback": "github_installation_callback",
            "POST /v1/scans": "create_scan",
            "GET /v1/scans/{scan_id}": "get_scan",
            "GET /v1/scans/{scan_id}/report": "get_scan_report",
            "GET /v1/scans/{scan_id}/artifacts": "get_scan_artifacts",
            "POST /v1/traces/import": "import_trace",
            "POST /v1/scans/{scan_id}/replay": "replay_scan",
        }

    def _job(self, scan_id: str) -> ScanJob:
        job = self.store.get_scan_job(scan_id)
        if job is None:
            raise ValueError("unknown scan_id")
        return job
