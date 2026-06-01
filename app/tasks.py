from app.celery_app import celery
from app.workflow import run_goal_workflow
from app.db import update_job, log_event, add_job_event
from app.workflow_runtime import execute_queued_workflow_run

@celery.task(name="app.tasks.run_agent_job")
def run_agent_job(job_id: str, goal: str, session_id: str):
    def emit(event_type: str, payload: dict):
        add_job_event(job_id, event_type, payload)

    try:
        update_job(job_id, "running")
        emit("running", {"goal": goal})
        log_event("job_start", {"job_id": job_id, "session_id": session_id, "goal": goal})

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
        }

        update_job(job_id, "completed", result=result)
        emit("completed", {"final_response": final_response})
        log_event("job_done", {"job_id": job_id})
        return result
    except Exception as exc:
        update_job(job_id, "failed", error=str(exc))
        emit("failed", {"error": str(exc)})
        log_event("job_failed", {"job_id": job_id, "error": str(exc)})
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
