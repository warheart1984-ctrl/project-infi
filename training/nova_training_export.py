"""Export governed Nova turns into Jarvis LoRA message examples."""

from __future__ import annotations

from hashlib import sha256
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nova.lawful_llm import LawfulTurn

NOVA_LAWFUL_EXPORT_ADMISSION_ID = "nova-lawful-turns-export-v1"
EXPORT_MANIFEST_VERSION = "nova_lawful_export_manifest.v1"
DEFAULT_CORPUS_PATH = Path("training/data/nova_lawful_turns.jsonl")


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


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def build_export_manifest(
    corpus_path: Path | str,
    *,
    example_count: int,
    admission_id: str = NOVA_LAWFUL_EXPORT_ADMISSION_ID,
) -> dict[str, Any]:
    """Build a governed export manifest for a Nova lawful-turn corpus."""
    resolved = Path(corpus_path)
    return {
        "export_manifest_version": EXPORT_MANIFEST_VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "corpus_path": str(resolved),
        "corpus_sha256": _sha256_file(resolved) if resolved.is_file() else None,
        "example_count": example_count,
        "admission_id": admission_id,
        "source": "nova_lawful_turn",
    }


def write_export_manifest(
    corpus_path: Path | str,
    *,
    example_count: int,
    manifest_path: Path | str | None = None,
) -> Path:
    """Write export_manifest.json beside the corpus (default: training/data/)."""
    resolved_corpus = Path(corpus_path)
    output_manifest = Path(manifest_path) if manifest_path else resolved_corpus.with_name("export_manifest.json")
    payload = build_export_manifest(resolved_corpus, example_count=example_count)
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_manifest
