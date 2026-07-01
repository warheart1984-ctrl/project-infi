from __future__ import annotations

import json
from typing import Any

from nova.node.tools.local_model import generate


def run(task: dict[str, Any]) -> dict[str, Any]:
    patch = str(task.get("patch") or "")
    code_before = str(task.get("code_before") or "")
    code_after = str(task.get("code_after") or "")
    instruction = str(task.get("instruction") or "")
    file_path = str(task.get("file_path") or "")

    prompt = f"""You are a constitutional analysis tool (Ring-2).
Analyze the following change:

Instruction: {instruction}

Code before:
```
{code_before}
```

Code after:
```
{code_after}
```

Patch:
```diff
{patch}
```

Return a structured explanation as JSON:
{{
  "summary": "...",
  "risks": ["..."],
  "testing_recommendations": ["..."],
  "why_this_approach": "...",
  "potential_breakage": "..."
}}"""
    analysis = generate(
        prompt,
        model=str(task.get("model") or "qwen2.5-coder:3b"),
        temperature=float(task.get("temperature", 0.2)),
        max_tokens=int(task.get("max_tokens", 2048)),
    )

    try:
        parsed: dict[str, Any] = json.loads(_strip_json_fences(analysis))
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed = {"raw_analysis": analysis}

    return {
        "analysis": parsed,
        "receipts": ["explain_tool", "governance.patch_explained"],
        "metadata": {"analyzed_file": file_path or task.get("file_path")},
    }


def _strip_json_fences(value: str) -> str:
    text = str(value or "").strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()
