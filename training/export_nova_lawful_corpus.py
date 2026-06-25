"""Export admitted LawfulTurn receipts into a governed Nova training corpus."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nova.governance import seams
from nova.lawful_llm import LawfulLLM
from training.nova_training_export import (
    DEFAULT_CORPUS_PATH,
    append_lawful_turn_example,
    write_export_manifest,
)

DEFAULT_PROMPTS: list[dict] = [
    {
        "prompt": "explain gravity",
        "capability": "reason",
        "memory_facts": [("gravity", "is", "an attractive interaction between masses")],
    },
    {"prompt": "summarize invariants", "capability": "summarize"},
    {"prompt": "what is RSL in one sentence", "capability": "reason"},
    {"prompt": "describe tenant scope for lawful inference", "capability": "summarize"},
]


def _load_prompts(path: Path | None) -> list[dict]:
    if path is None:
        return list(DEFAULT_PROMPTS)
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            cleaned = line.strip()
            if not cleaned:
                continue
            record = json.loads(cleaned)
            if "prompt" not in record or "capability" not in record:
                raise ValueError(f"{path}:{line_number} requires prompt and capability")
            records.append(record)
    return records


def export_corpus(
    *,
    output_path: Path,
    tenant_id: str,
    operator_session_id: str,
    signing_secret: str,
    prompts: list[dict],
    reset_ledger: bool,
) -> int:
    if reset_ledger and output_path.exists():
        output_path.unlink()

    if output_path.exists():
        output_path.unlink()

    seams.reset_seams_for_tests()
    llm = LawfulLLM(
        operator_session_id=operator_session_id,
        signing_secret=signing_secret,
    )

    exported = 0
    for item in prompts:
        turn = llm.ask(
            str(item["prompt"]),
            tenant_id=tenant_id,
            capability=str(item["capability"]),
            memory_facts=item.get("memory_facts") or (),
        )
        if str(turn.rsl.get("status") or "").upper() != "SATISFIED":
            raise RuntimeError(f"turn not admitted for prompt={item['prompt']!r}")
        append_lawful_turn_example(
            output_path,
            prompt=str(item["prompt"]),
            turn=turn,
        )
        exported += 1

    write_export_manifest(output_path, example_count=exported)
    return exported


def main() -> int:
    parser = argparse.ArgumentParser(description="Export admitted Nova LawfulTurns to JSONL.")
    parser.add_argument("--output", default=str(DEFAULT_CORPUS_PATH), help="Corpus JSONL output path.")
    parser.add_argument("--prompts", default="", help="Optional JSONL prompt spec file.")
    parser.add_argument("--tenant-id", default="tenant-alpha")
    parser.add_argument("--operator-session-id", default="nova-lawful-export")
    parser.add_argument(
        "--signing-secret",
        default=os.getenv("NOVA_LAWFUL_EXPORT_SIGNING_SECRET", "nova-lawful-export-secret"),
    )
    parser.add_argument("--reset-ledger", action="store_true", help="Reset governance seams before export.")
    args = parser.parse_args()

    prompts_path = Path(args.prompts) if args.prompts else None
    prompts = _load_prompts(prompts_path)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = export_corpus(
        output_path=output_path,
        tenant_id=args.tenant_id,
        operator_session_id=args.operator_session_id,
        signing_secret=args.signing_secret,
        prompts=prompts,
        reset_ledger=args.reset_ledger,
    )
    print(f"Exported {count} admitted lawful turns to {output_path}")
    print(f"Wrote export manifest to {output_path.with_name('export_manifest.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
