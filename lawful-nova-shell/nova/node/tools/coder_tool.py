from __future__ import annotations

import difflib
import re
from typing import Any

from nova.node.tools.local_model import generate


def run(task: dict[str, Any]) -> dict[str, Any]:
    instruction = str(task.get("instruction") or "")
    current_code = str(task.get("current_code") or "")
    file_path = str(task.get("file_path") or "unknown")
    context = str(task.get("context") or "")

    prompt = f"""You are a constitutional coding tool (Ring-2).
You MUST obey governance invariants: minimal change, preserve existing style, no security regressions.

File: {file_path}
Instruction: {instruction}

Extra context:
{context}

Current code:
```
{current_code}
```

Return ONLY the complete updated file. No explanations, no markdown fences outside the code."""

    updated_code = _strip_markdown_fences(
        generate(
            prompt,
            model=str(task.get("model") or "qwen2.5-coder:3b"),
            temperature=float(task.get("temperature", 0.15)),
            max_tokens=int(task.get("max_tokens", 4096)),
        )
    )
    diff_lines = difflib.unified_diff(
        current_code.splitlines(),
        updated_code.splitlines(),
        fromfile=f"{file_path} (original)",
        tofile=f"{file_path} (updated)",
        lineterm="",
    )
    diff_text = "\n".join(diff_lines)

    return {
        "updated_code": updated_code,
        "diff": diff_text,
        "file_path": file_path,
        "receipts": ["coder_tool", "governance.patch_generated"],
        "metadata": {
            "hunks": _hunk_count(diff_text),
            "char_delta": len(updated_code) - len(current_code),
        },
    }


def _strip_markdown_fences(value: str) -> str:
    text = str(value or "")
    match = re.search(r"```(?:[A-Za-z0-9_+-]+)?\s*(.*?)```", text, flags=re.DOTALL)
    if not match:
        return text
    return match.group(1).strip()


def _hunk_count(diff_text: str) -> int:
    return sum(1 for line in diff_text.splitlines() if line.startswith("@@"))
