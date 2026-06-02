"""Dispatch platform jobs to subsystem adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from platform.adapters.ai_factory import run_ai_factory_build
from platform.adapters.forgekeeper import run_forgekeeper_plan
from platform.adapters.lab import (
    run_lab_experiments_list,
    run_lab_project_init,
    run_lab_project_status,
    run_lab_session,
    run_lab_session_close,
    run_lab_session_start,
    run_lab_tool_invoke,
)
from platform.adapters.mechanic import run_mechanic_scan
from platform.adapters.slingshot import run_slingshot_preload
from platform.artifacts.index import ArtifactIndex
from platform.artifacts.scanner import ingest_hash_manifest
from platform.auth.rbac import Principal
from platform.jobs.registry import JobRegistry
from platform.drift.detectors.base import run_detectors
from platform.synthetic_mind import register_synthetic_mind_for_org, ref_from_ai_factory_result
from platform.drift.scheduler import maybe_enqueue_investigation
from platform.jobs.schema import mark_job_started, update_job_status
from platform.workflow.engine import advance_workflow, run_workflow


def dispatch_job(
    *,
    registry: JobRegistry,
    artifact_index: ArtifactIndex,
    principal: Principal,
    job: dict[str, Any],
) -> dict[str, Any]:
    params = dict((job.get("metadata") or {}).get("params") or {})
    subsystem = str(job.get("subsystem"))
    kind = str(job.get("kind"))
    job = mark_job_started(update_job_status(job, status="running"))
    registry.save_job(job)

    try:
        if subsystem == "mechanic" and kind == "mechanic.scan":
            case_id = str(params.get("case_id") or job.get("subsystem_job_id"))
            result = run_mechanic_scan(
                case_id=case_id,
                repo_path=str(params.get("repo_path") or "mechanic/fixtures/sample-customer-repo"),
                trace_path=str(params.get("trace_path") or ""),
            )
            job = update_job_status(
                job,
                status="complete",
                subsystem_job_id=case_id,
                metadata={"result": result},
                links=[{"link_type": "mechanic_case", "target_id": case_id}],
            )
            artifact_index.register_directory(
                principal=principal,
                subsystem="mechanic",
                directory=Path(result["artifact_dir"]),
                job_id=str(job["job_id"]),
                correlation_id=str(job["correlation_id"]),
            )

        elif subsystem == "slingshot" and kind == "slingshot.preload":
            case_id = str(params.get("case_id") or job.get("subsystem_job_id"))
            lineage: list[str] = []
            result = run_slingshot_preload(
                case_id=case_id,
                repo_path=str(params.get("repo_path") or "mechanic/fixtures/sample-customer-repo-v2"),
                trace_path=str(params.get("trace_path") or ""),
            )
            job = update_job_status(
                job,
                status="complete",
                subsystem_job_id=case_id,
                metadata={"result": result, "mechanic_embedded": True},
                links=[
                    {"link_type": "slingshot_frame", "target_id": case_id},
                    {"link_type": "mechanic_case", "target_id": case_id},
                ],
            )
            artifact_index.register_directory(
                principal=principal,
                subsystem="slingshot",
                directory=Path(result["artifact_dir"]),
                job_id=str(job["job_id"]),
                correlation_id=str(job["correlation_id"]),
                lineage_parent_refs=lineage,
            )
            artifact_index.register_directory(
                principal=principal,
                subsystem="mechanic",
                directory=Path(result["mechanic_case_dir"]),
                job_id=str(job["job_id"]),
                correlation_id=str(job["correlation_id"]),
            )

        elif subsystem == "lab" and kind == "lab.session":
            project_id = str(params.get("project_id") or "nova-ai-factory")
            result = run_lab_session(project_id=project_id)
            job = update_job_status(
                job,
                status="complete",
                subsystem_job_id=str(result["session_id"]),
                metadata={"result": result},
                links=[{"link_type": "lab_session", "target_id": result["session_id"]}],
            )
            artifact_index.register_directory(
                principal=principal,
                subsystem="lab",
                directory=Path(result["artifact_dir"]),
                job_id=str(job["job_id"]),
                correlation_id=str(job["correlation_id"]),
            )

        elif subsystem == "lab" and kind == "lab.session.start":
            project_id = str(params.get("project_id") or "nova-ai-factory")
            result = run_lab_session_start(project_id=project_id, agent=str(params.get("agent") or "platform-agent"))
            job = update_job_status(
                job,
                status="running",
                subsystem_job_id=str(result["session_id"]),
                metadata={"result": result},
                links=[{"link_type": "lab_session", "target_id": result["session_id"]}],
            )

        elif subsystem == "lab" and kind == "lab.tool.invoke":
            project_id = str(params.get("project_id") or "nova-ai-factory")
            session_id = str(params.get("session_id") or "")
            result = run_lab_tool_invoke(
                project_id=project_id,
                session_id=session_id,
                tool=str(params.get("tool") or "read_file"),
                args=dict(params.get("args") or {}),
            )
            job = update_job_status(job, status="complete", metadata={"result": result})

        elif subsystem == "lab" and kind == "lab.session.close":
            project_id = str(params.get("project_id") or "nova-ai-factory")
            session_id = str(params.get("session_id") or "")
            result = run_lab_session_close(project_id=project_id, session_id=session_id)
            job = update_job_status(job, status="complete", metadata={"result": result})

        elif subsystem == "lab" and kind == "lab.project.init":
            result = run_lab_project_init(params)
            job = update_job_status(
                job,
                status="complete",
                subsystem_job_id=str(result.get("project_id") or ""),
                metadata={"result": result},
            )

        elif subsystem == "lab" and kind == "lab.project.status":
            project_id = str(params.get("project_id") or "nova-ai-factory")
            result = run_lab_project_status(project_id)
            job = update_job_status(job, status="complete", metadata={"result": result})

        elif subsystem == "lab" and kind == "lab.experiments.list":
            project_id = str(params.get("project_id") or "nova-ai-factory")
            result = run_lab_experiments_list(project_id)
            job = update_job_status(job, status="complete", metadata={"result": result})

        elif subsystem == "ai_factory" and kind == "ai_factory.build":
            spec_path = str(params.get("spec_path") or "factory/specs/nova-default.yaml")
            result = run_ai_factory_build(spec_path=spec_path, skip_pytest=bool(params.get("skip_pytest", True)))
            mind_ref = ref_from_ai_factory_result(
                org_id=str(job["org_id"]),
                result=result,
                job_id=str(job["job_id"]),
            )
            register_synthetic_mind_for_org(
                store=registry.store,
                org_id=str(job["org_id"]),
                ref=mind_ref,
            )
            job = update_job_status(
                job,
                status="complete",
                subsystem_job_id=result["build_id"],
                metadata={"result": result, "synthetic_mind_ref": mind_ref},
                links=[{"link_type": "factory_build", "target_id": result["build_id"]}],
            )
            ingest_hash_manifest(
                index=artifact_index,
                principal=principal,
                subsystem="ai_factory",
                job_id=str(job["job_id"]),
                correlation_id=str(job["correlation_id"]),
                manifest=result.get("hash_manifest") or [],
                base_dir=Path(result["output_dir"]),
            )
            artifact_index.register(
                principal=principal,
                payload=artifact_index.build_ref(
                    org_id=principal.org_id,
                    subsystem="ai_factory",
                    logical_path=f"synthetic_mind/{mind_ref['build_id']}/ref.json",
                    storage_uri=mind_ref.get("storage_uri") or f"synthetic-mind://{mind_ref['build_id']}",
                    sha256=mind_ref["bundle_hash"],
                    job_id=str(job["job_id"]),
                    correlation_id=str(job["correlation_id"]),
                    artifact_type="synthetic_mind_ref",
                    metadata={"synthetic_mind_ref": mind_ref},
                ),
            )

        elif subsystem == "forgekeeper" and kind == "forgekeeper.plan":
            plan_id = str(params.get("plan_id") or job.get("subsystem_job_id") or "platform-plan")
            result = run_forgekeeper_plan(plan_id=plan_id, scope=str(params.get("scope") or "."))
            job = update_job_status(
                job,
                status="complete",
                subsystem_job_id=plan_id,
                metadata={"result": result},
                links=[{"link_type": "forgekeeper_plan", "target_id": plan_id}],
            )
            artifact_index.register_directory(
                principal=principal,
                subsystem="forgekeeper",
                directory=Path(result["artifact_dir"]),
                job_id=str(job["job_id"]),
                correlation_id=str(job["correlation_id"]),
            )

        elif subsystem == "drift_detector" and kind == "drift_check":
            findings = list(params.get("findings") or [])
            job = update_job_status(job, status="complete", metadata={"findings": findings, "result": "checked"})
            for f in findings:
                vc = str(f.get("violation_class") or "")
                if vc in {"II", "III", "class_ii", "class_iii"}:
                    maybe_enqueue_investigation(
                        store=registry.store,
                        org_id=str(job["org_id"]),
                        drift_job=job,
                        violation_class=vc,
                        enqueue=lambda jid, region="us": registry.queue.enqueue(jid, region=region),
                    )

        elif subsystem == "drift_detector" and kind == "drift_investigation":
            job = update_job_status(
                job,
                status="complete",
                metadata={"violation_class": params.get("violation_class"), "result": "investigated"},
            )

        elif subsystem == "workflow_engine" and kind == "workflow_run":
            job = run_workflow(store=registry.store, job=job)

        else:
            job = update_job_status(job, status="failed", metadata={"error": f"unsupported:{subsystem}/{kind}"})

    except Exception as exc:
        job = update_job_status(job, status="failed", metadata={"error": str(exc)})

    registry.save_job(job)
    if job.get("status") == "complete":
        advance_workflow(
            store=registry.store,
            completed_job=job,
            enqueue=lambda jid, region="us": registry.queue.enqueue(jid, region=region),
        )
        _post_complete_hooks(registry=registry, job=job)
    return job


def _post_complete_hooks(*, registry: JobRegistry, job: dict[str, Any]) -> None:
    from platform.drift.scheduler import maybe_enqueue_drift
    from platform.proof.runner import auto_enqueue_proof_if_required

    findings = run_detectors(job=job)
    maybe_enqueue_drift(
        store=registry.store,
        org_id=str(job["org_id"]),
        source_job_id=str(job["job_id"]),
        findings=findings,
        enqueue=lambda jid, region="us": registry.queue.enqueue(jid, region=region),
    )
    auto_enqueue_proof_if_required(store=registry.store, job=job, enqueue=registry.queue.enqueue)
