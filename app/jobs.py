from __future__ import annotations

import threading

from app.db import add_job_event, create_job, update_job
from app.workflow import run_goal_workflow


class JobRunner:
    def create_and_start(self, goal: str, session_id: str) -> str:
        job_id = create_job(goal, session_id)

        def worker() -> None:
            update_job(job_id, "running")

            def progress(event_type: str, payload: dict) -> None:
                add_job_event(job_id, event_type, payload)

            try:
                plan, steps, final_response = run_goal_workflow(goal, session_id=session_id, progress_callback=progress)
                update_job(job_id, "completed", {"plan": plan, "steps": steps, "final_response": final_response})
                add_job_event(job_id, "completed", {"final_response": final_response})
            except Exception as exc:
                update_job(job_id, "failed", error=str(exc))
                add_job_event(job_id, "failed", {"error": str(exc)})

        threading.Thread(target=worker, daemon=True).start()
        return job_id

    def get(self, job_id: str):
        from app.db import get_job

        return get_job(job_id)


runner = JobRunner()
