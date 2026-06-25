from app.celery_app import celery
from app.runtime_services import agent_fault_journal, run_ledger
from app.workflow import run_goal_workflow
from app.db import update_job, log_event, add_job_event
from app.workflow_runtime import execute_queued_workflow_run

@celery.task(name="app.tasks.run_agent_job")
def run_agent_job(job_id: str, goal: str, session_id: str):
    def emit(event_type: str, payload: dict):
        add_job_event(job_id, event_type, payload)

    sid = str(session_id or "agent-default").strip() or "agent-default"
    run = run_ledger.ensure_run(
        sid,
        title=str(goal or "Agent job")[:120],
        kind="agent_job",
        meta={"surface": "agent_job", "job_id": job_id, "cisiv_stage": "implementation"},
    )
    run_id = str(run.get("id") or "")

    try:
        update_job(job_id, "running")
        emit("running", {"goal": goal, "run_id": run_id})
        log_event("job_start", {"job_id": job_id, "session_id": session_id, "goal": goal, "run_id": run_id})

        plan, steps, final_response = run_goal_workflow(
            goal,
            session_id=session_id,
            progress_callback=emit,
        )
        result = {
            "plan": plan,
            "steps": steps,
            "final_response": final_response,
            "session_id": session_id,
            "run_id": run_id,
        }

        run_ledger.append_step(
            run_id,
            {
                "kind": "agent_job",
                "title": "Agent job completed",
                "summary": str(final_response or "")[:500],
                "status": "completed",
                "cisiv_stage": "implementation",
                "meta": {"job_id": job_id, "step_count": len(steps)},
            },
        )
        run_ledger.close_run(run_id, status="completed", summary=str(final_response or "")[:500])

        update_job(job_id, "completed", result=result)
        emit("completed", {"final_response": final_response, "run_id": run_id})
        log_event("job_done", {"job_id": job_id, "run_id": run_id})
        return result
    except Exception as exc:
        agent_fault_journal.record_agent_failure(
            run_id=run_id,
            goal=goal,
            error=str(exc),
            session_id=session_id,
            fault_code="AGENT_JOB_FAILED",
        )
        run_ledger.append_step(
            run_id,
            {
                "kind": "agent_job",
                "title": "Agent job failed",
                "summary": str(exc)[:500],
                "status": "failed",
                "cisiv_stage": "verification",
                "meta": {"job_id": job_id, "fault_code": "AGENT_JOB_FAILED"},
            },
        )
        run_ledger.close_run(run_id, status="failed", summary=str(exc)[:500])
        update_job(job_id, "failed", error=str(exc))
        emit("failed", {"error": str(exc), "run_id": run_id})
        log_event("job_failed", {"job_id": job_id, "error": str(exc), "run_id": run_id})
        raise


@celery.task(name="app.tasks.run_workflow_job")
def run_workflow_job(workflow_run_id: str, workflow_id: str, trigger_data: dict | None = None, resume: bool = False):
    try:
        execute_queued_workflow_run(
            workflow_run_id=workflow_run_id,
            workflow_id=workflow_id,
            trigger_data=trigger_data,
            resume=resume,
        )
        return {"workflow_run_id": workflow_run_id, "status": "processed"}
    except Exception as exc:
        log_event("workflow_run_failed", {"workflow_run_id": workflow_run_id, "error": str(exc)})
        raise
