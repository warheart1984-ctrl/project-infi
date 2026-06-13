"""Export governed Nova turns into Jarvis LoRA message examples."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from nova.lawful_llm import LawfulTurn


DEFAULT_SYSTEM_PROMPT = (
    "You are Nova Cortex inside AAIS. Answer through UL over LSG, obey RSL, "
    "respect tenant scope, and preserve Voss receipt accountability."
)


def _sha256_text(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def build_lawful_turn_training_example(
    *,
    prompt: str,
    turn: LawfulTurn,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> dict[str, Any]:
    """Project one admitted Nova turn into conversational JSONL training shape."""

    provider = turn.nova_cortex.get("provider")
    model = turn.nova_cortex.get("model")
    metadata: dict[str, Any] = {
        "source": "nova_lawful_turn",
        "prompt_sha256": _sha256_text(prompt),
        "answer_sha256": _sha256_text(turn.text),
        "rsl": dict(turn.rsl),
        "ul": dict(turn.nova_cortex.get("ul") or {}),
        "lsg": dict(turn.nova_cortex.get("lsg") or {}),
        "api_kernel": dict(turn.api_kernel),
        "voss_runtime": {
            "decision": turn.voss_runtime.get("decision"),
            "runtime": turn.voss_runtime.get("runtime"),
        },
        "receipt": dict(turn.receipt),
    }
    if provider:
        metadata["provider"] = str(provider)
    if model:
        metadata["model"] = str(model)

    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": turn.text},
        ],
        "metadata": metadata,
    }


def append_lawful_turn_example(
    path: Path | str,
    *,
    prompt: str,
    turn: LawfulTurn,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> Path:
    """Append one governed Nova turn to a private training JSONL file."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    example = build_lawful_turn_training_example(
        prompt=prompt,
        turn=turn,
        system_prompt=system_prompt,
    )
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(example, ensure_ascii=True, sort_keys=True) + "\n")
    return output_path
