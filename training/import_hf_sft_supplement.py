"""Import a small Hugging Face SFT supplement for Jarvis LoRA training.

Uses HuggingFaceH4/ultrachat_200k train_sft rows (messages schema) and prepends
the Jarvis system prompt so prepare_messages_dataset.py can merge them.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasets import load_dataset


DEFAULT_DATASET = "HuggingFaceH4/ultrachat_200k"
DEFAULT_SPLIT = "train_sft"
DEFAULT_SYSTEM_PROMPT = (
    "You are Jarvis, a private local AI partner for one person only."
)


def _to_jarvis_record(messages: list[dict], system_prompt: str) -> dict:
    """Convert Hub messages into Jarvis conversational JSONL format."""
    cleaned = []
    for message in messages:
        role = str(message.get("role", "")).strip().lower()
        content = str(message.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        cleaned.append({"role": role, "content": content})

    if not any(message["role"] == "user" for message in cleaned):
        raise ValueError("row is missing a user turn")
    if not any(message["role"] == "assistant" for message in cleaned):
        raise ValueError("row is missing an assistant turn")

    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            *cleaned,
        ]
    }


def import_supplement(
    dataset_name: str,
    split: str,
    limit: int,
    system_prompt: str,
    start_index: int = 0,
):
    """Load and normalize a bounded slice of Hub SFT examples."""
    rows = load_dataset(dataset_name, split=split, streaming=True)
    examples = []

    for index, row in enumerate(rows):
        if index < start_index:
            continue
        if len(examples) >= limit:
            break

        messages = row.get("messages")
        if not isinstance(messages, list):
            continue

        try:
            examples.append(_to_jarvis_record(messages, system_prompt))
        except ValueError:
            continue

    return examples


def main():
    parser = argparse.ArgumentParser(
        description="Import a small HF SFT supplement for Jarvis training."
    )
    parser.add_argument(
        "--dataset",
        default=DEFAULT_DATASET,
        help="Hub dataset repo id.",
    )
    parser.add_argument(
        "--split",
        default=DEFAULT_SPLIT,
        help="Dataset split to stream from.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of normalized examples to write.",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Skip this many streamed rows before collecting examples.",
    )
    parser.add_argument(
        "--system-prompt",
        default=DEFAULT_SYSTEM_PROMPT,
        help="System prompt prepended to every imported conversation.",
    )
    parser.add_argument(
        "--output",
        default="training/data/hf_sft_supplement.jsonl",
        help="Where to write Jarvis-compatible JSONL rows.",
    )
    args = parser.parse_args()

    examples = import_supplement(
        dataset_name=args.dataset,
        split=args.split,
        limit=args.limit,
        system_prompt=args.system_prompt,
        start_index=args.start_index,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example, ensure_ascii=True) + "\n")

    print(f"Wrote {len(examples)} examples to {output_path}")
    print(f"Source: {args.dataset} ({args.split})")


if __name__ == "__main__":
    main()
