from __future__ import annotations
from app.llm import chat
from app.memory import retrieve_memory, store_memory
from app.agentic import run_tool_loop
from app.db import log_event

def create_plan(goal: str) -> list[str]:
    prompt = f'''
Create a short practical numbered plan to achieve this goal.
Keep it efficient and avoid unnecessary steps.

Goal:
{goal}

Return only the steps, one per line, like:
1. ...
2. ...
3. ...
'''.strip()

    raw = chat([{"role": "user", "content": prompt}], temperature=0.2, fast=True)
    steps = []
    for line in raw.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned[0].isdigit():
            parts = cleaned.split(".", 1)
            cleaned = parts[1].strip() if len(parts) > 1 else cleaned
        steps.append(cleaned)
    return steps[:5] if steps else [goal]

def critique_step(step: str, result: str) -> str:
    prompt = f'''
Review this step result briefly.

Step:
{step}

Result:
{result}

Respond in 1 short sentence with whether it looks good or what is missing.
'''.strip()
    return chat([{"role": "user", "content": prompt}], temperature=0.2, fast=True)

def finalize(goal: str, steps_with_results: list[dict]) -> str:
    summary_lines = []
    for item in steps_with_results:
        summary_lines.append(f"Step: {item['step']}\nResult: {item['result']}\nCritique: {item['critique']}")
    joined = "\n\n".join(summary_lines)
    prompt = f'''
Write a final helpful response for this goal.
Be concise and practical.

Goal:
{goal}

Work completed:
{joined}
'''.strip()
    return chat([{"role": "user", "content": prompt}], temperature=0.3)

def run_goal_workflow(goal: str, session_id: str = "default", progress_callback=None) -> tuple[list[str], list[dict], str]:
    def emit(event_type: str, payload: dict):
        if progress_callback:
            progress_callback(event_type, payload)

    log_event("agent_goal_start", {"session_id": session_id, "goal": goal})
    emit("goal_started", {"goal": goal})

    memories = retrieve_memory(goal, session_id=session_id, n_results=3)
    memory_text = "\n".join(memories) if memories else "none"

    plan = create_plan(f"{goal}\n\nRelevant memory:\n{memory_text}")
    emit("plan_created", {"plan": plan})

    recent_history = []
    step_results = []

    for index, step in enumerate(plan, start=1):
        emit("step_started", {"index": index, "step": step})
        response, used_tool, tool_result, _, _ = run_tool_loop(step, recent_history, session_id=session_id)
        critique = critique_step(step, response)

        result_text = response if not used_tool else f"{response}\n\n[tool={used_tool}]\n{tool_result}"
        step_results.append({"step": step, "result": result_text, "critique": critique})
        emit("step_finished", {"index": index, "step": step, "result": result_text, "critique": critique})

        recent_history.append({"role": "user", "content": step})
        recent_history.append({"role": "assistant", "content": response})
        if len(recent_history) > 8:
            recent_history = recent_history[-8:]

    final_response = finalize(goal, step_results)
    store_memory(f"Goal: {goal}\nFinal response: {final_response}", session_id=session_id)
    emit("goal_finished", {"final_response": final_response})

    log_event("agent_goal_done", {"session_id": session_id, "goal": goal, "final_response": final_response[:1000]})
    return plan, step_results, final_response
