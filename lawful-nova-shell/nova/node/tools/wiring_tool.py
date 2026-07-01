from __future__ import annotations

from typing import Any

from nova.node.tools.local_model import generate


def run(task: dict[str, Any]) -> dict[str, Any]:
    goal = str(task.get("goal") or "")
    components = [str(component) for component in task.get("components", [])]
    context = str(task.get("context") or "")

    prompt = f"""
You are a constitutional wiring agent.
Generate glue code to achieve the goal.

Goal:
{goal}

Components:
{", ".join(components)}

Context:
{context}

Return ONLY the glue code. No explanations.
"""

    glue_code = generate(prompt, model=str(task.get("model") or "qwen2.5-coder:3b"), temperature=0.1)
    return {
        "glue_code": glue_code,
        "goal": goal,
        "components": components,
        "receipts": ["wiring_tool"],
    }
