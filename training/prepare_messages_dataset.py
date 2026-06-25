"""Build a conversational fine-tuning dataset for Jarvis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.nova_training_export import NOVA_LAWFUL_EXPORT_ADMISSION_ID

ALLOWED_ROLES = {"system", "user", "assistant"}
SEED_DEFAULT = Path("training/data/jarvis_seed_messages.jsonl")
HF_SUPPLEMENT_DEFAULT = Path("training/data/hf_sft_supplement.jsonl")
HF_SUPPLEMENT_ADMISSION_ID = "jarvis-lora-hf-ultrachat-200k-v1"
NOVA_LAWFUL_CORPUS_NAME = "nova_lawful_turns.jsonl"


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


def _classify_source(path: Path, seed_path: Path) -> str:
    """Map an input file to a governed dataset source kind."""
    resolved = path.resolve()
    if resolved == seed_path.resolve():
        return "seed"
    if resolved == HF_SUPPLEMENT_DEFAULT.resolve():
        return "external"
    return "private"


def build_dataset(seed_path: Path, private_paths: list[Path] | None):
    """Combine the checked-in seed set with private operator examples."""
    examples = []
    source_files: list[dict] = []

    seed_count = 0
    for index, record in enumerate(_read_jsonl(seed_path), start=1):
        examples.append(_normalize_messages(record, f"{seed_path.name}:{index}"))
        seed_count += 1
    source_files.append(
        {
            "path": str(seed_path),
            "source_kind": "seed",
            "example_count": seed_count,
        }
    )

    for private_path in private_paths or []:
        if not private_path.exists():
            continue
        file_count = 0
        for index, record in enumerate(_read_jsonl(private_path), start=1):
            examples.append(_normalize_messages(record, f"{private_path.name}:{index}"))
            file_count += 1
        source_files.append(
            {
                "path": str(private_path),
                "source_kind": _classify_source(private_path, seed_path),
                "example_count": file_count,
            }
        )

    return examples, source_files


def build_dataset_manifest(output_path: Path, source_files: list[dict], example_count: int):
    """Write a governed dataset manifest sidecar for training envelopes."""
    sources = sorted({entry["source_kind"] for entry in source_files})
    admission_ids = []
    if "external" in sources:
        admission_ids.append(HF_SUPPLEMENT_ADMISSION_ID)

    has_nova_lawful = any(
        NOVA_LAWFUL_CORPUS_NAME in str(entry.get("path") or "").replace("\\", "/")
        for entry in source_files
    )
    if has_nova_lawful:
        admission_ids.append(NOVA_LAWFUL_EXPORT_ADMISSION_ID)

    export_manifest_path = None
    export_manifest_sha256 = None
    if has_nova_lawful:
        for entry in source_files:
            candidate = Path(str(entry.get("path") or ""))
            manifest_candidate = candidate.with_name("export_manifest.json")
            if manifest_candidate.is_file():
                export_manifest_path = str(manifest_candidate)
                export_manifest_sha256 = json.loads(manifest_candidate.read_text(encoding="utf-8")).get(
                    "corpus_sha256"
                )
                break

    manifest = {
        "manifest_version": "jarvis_lora_dataset_manifest.v1",
        "output_path": str(output_path),
        "example_count": example_count,
        "sources": sources,
        "admission_ids": sorted(set(admission_ids)),
        "source_files": source_files,
    }
    if export_manifest_path:
        manifest["export_manifest_path"] = export_manifest_path
    if export_manifest_sha256:
        manifest["export_manifest_sha256"] = export_manifest_sha256
    manifest_path = output_path.with_name("dataset_manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def main():
    parser = argparse.ArgumentParser(description="Prepare a Jarvis chat fine-tuning dataset.")
    parser.add_argument(
        "--seed",
        default=str(SEED_DEFAULT),
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

    examples, source_files = build_dataset(
        seed_path,
        [path for path in private_paths if path.exists()],
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example, ensure_ascii=True) + "\n")

    manifest_path = build_dataset_manifest(output_path, source_files, len(examples))

    seed_count = sum(1 for _ in _read_jsonl(seed_path))
    private_count = max(0, len(examples) - seed_count)

    print(f"Wrote {len(examples)} examples to {output_path}")
    print(f"Wrote dataset manifest to {manifest_path}")
    print(f"Seed examples: {seed_count}")
    print(f"Private examples: {private_count}")


if __name__ == "__main__":
    main()
