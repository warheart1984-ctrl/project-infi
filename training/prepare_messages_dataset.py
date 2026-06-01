"""Build a conversational fine-tuning dataset for Jarvis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ALLOWED_ROLES = {"system", "user", "assistant"}


def _read_jsonl(path: Path):
    """Yield non-empty JSONL records from disk."""
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            cleaned = line.strip()
            if not cleaned:
                continue
            try:
                yield json.loads(cleaned)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number} is not valid JSON") from exc


def _normalize_messages(record, source_name: str):
    """Normalize one record into the TRL conversational format."""
    if "messages" in record:
        messages = record["messages"]
    elif "prompt" in record and "completion" in record:
        messages = [
            {"role": "user", "content": record["prompt"]},
            {"role": "assistant", "content": record["completion"]},
        ]
    else:
        raise ValueError(
            f"{source_name} must contain either 'messages' or prompt/completion fields"
        )

    normalized = []
    for index, message in enumerate(messages, start=1):
        if not isinstance(message, dict):
            raise ValueError(f"{source_name} message {index} must be an object")

        role = str(message.get("role", "")).strip().lower()
        content = str(message.get("content", "")).strip()
        if role not in ALLOWED_ROLES:
            raise ValueError(f"{source_name} message {index} has unsupported role '{role}'")
        if not content:
            raise ValueError(f"{source_name} message {index} has empty content")

        normalized.append({"role": role, "content": content})

    has_user = any(message["role"] == "user" for message in normalized)
    has_assistant = any(message["role"] == "assistant" for message in normalized)
    if not has_user or not has_assistant:
        raise ValueError(f"{source_name} must contain at least one user and one assistant turn")

    return {"messages": normalized}


def _iter_private_paths(raw_values):
    """Yield normalized private dataset paths from repeated or comma-separated CLI values."""
    for raw_value in raw_values or []:
        for piece in str(raw_value).split(","):
            cleaned = piece.strip()
            if cleaned:
                yield Path(cleaned)


def build_dataset(seed_path: Path, private_paths: list[Path] | None):
    """Combine the checked-in seed set with private operator examples."""
    examples = []

    for index, record in enumerate(_read_jsonl(seed_path), start=1):
        examples.append(_normalize_messages(record, f"{seed_path.name}:{index}"))

    for private_path in private_paths or []:
        if not private_path.exists():
            continue
        for index, record in enumerate(_read_jsonl(private_path), start=1):
            examples.append(_normalize_messages(record, f"{private_path.name}:{index}"))

    return examples


def main():
    parser = argparse.ArgumentParser(description="Prepare a Jarvis chat fine-tuning dataset.")
    parser.add_argument(
        "--seed",
        default="training/data/jarvis_seed_messages.jsonl",
        help="Checked-in seed dataset in conversational JSONL format.",
    )
    parser.add_argument(
        "--private",
        action="append",
        default=["training/data/private_messages.jsonl"],
        help="Optional private example files. Repeat the flag or pass comma-separated paths.",
    )
    parser.add_argument(
        "--output",
        default="training/out/jarvis_train_messages.jsonl",
        help="Where to write the normalized dataset.",
    )
    args = parser.parse_args()

    seed_path = Path(args.seed)
    private_paths = [path for path in _iter_private_paths(args.private)]
    output_path = Path(args.output)

    examples = build_dataset(
        seed_path,
        [path for path in private_paths if path.exists()],
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example, ensure_ascii=True) + "\n")

    seed_count = sum(1 for _ in _read_jsonl(seed_path))
    private_count = max(0, len(examples) - seed_count)

    print(f"Wrote {len(examples)} examples to {output_path}")
    print(f"Seed examples: {seed_count}")
    print(f"Private examples: {private_count}")


if __name__ == "__main__":
    main()
