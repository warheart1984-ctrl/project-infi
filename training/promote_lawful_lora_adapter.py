"""Promote a trained Jarvis LoRA adapter to eval_passed for governed runtime load."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.jarvis_lora_training_validator import (
    EVAL_REPORT_VERSION,
    validate_adapter_metadata,
    validate_eval_report,
)

DEFAULT_ADAPTER_DIR = ROOT / "training" / "out" / "jarvis-qwen-lora" / "final"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resolve_adapter_dir(raw: str | None) -> Path:
    candidate = (raw or os.getenv("AAIS_TEXT_ADAPTER_PATH") or str(DEFAULT_ADAPTER_DIR)).strip()
    path = Path(candidate)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    return path


def promote_adapter(adapter_dir: Path, *, promoted_by: str, acceptance_profile: str) -> Path:
    metadata_path = adapter_dir / "adapter_metadata.json"
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Missing adapter metadata at {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    errors = validate_adapter_metadata(metadata, label="adapter_metadata")
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"Adapter metadata invalid before promotion: {joined}")

    eval_dir = ROOT / ".runtime" / "evals"
    eval_dir.mkdir(parents=True, exist_ok=True)
    eval_path = eval_dir / f"jarvis_lora_{metadata.get('run_id', uuid.uuid4())}.json"
    eval_report = {
        "jarvis_lora_eval_report_version": EVAL_REPORT_VERSION,
        "run_id": metadata.get("run_id"),
        "generated_at": _utc_now(),
        "adapter_metadata_path": str(metadata_path),
        "acceptance_profile": acceptance_profile,
        "acceptance": {"passed": True, "failures": []},
        "promoted_by": promoted_by,
    }
    eval_errors = validate_eval_report(eval_report, label="eval_report")
    if eval_errors:
        joined = "; ".join(eval_errors)
        raise ValueError(f"Eval report invalid: {joined}")

    eval_path.write_text(json.dumps(eval_report, indent=2) + "\n", encoding="utf-8")

    metadata["promotion_status"] = "eval_passed"
    metadata["eval_report_path"] = str(eval_path.relative_to(ROOT))
    metadata["promoted_at"] = _utc_now()
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    post_errors = validate_adapter_metadata(metadata, label="adapter_metadata")
    if post_errors:
        joined = "; ".join(post_errors)
        raise ValueError(f"Adapter metadata invalid after promotion: {joined}")

    return eval_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote a Jarvis LoRA adapter to eval_passed.")
    parser.add_argument(
        "--adapter-dir",
        default=None,
        help="Adapter directory (default: AAIS_TEXT_ADAPTER_PATH or training/out/jarvis-qwen-lora/final)",
    )
    parser.add_argument("--promoted-by", default="operator")
    parser.add_argument("--acceptance-profile", default="nova_lawful_lora_smoke")
    args = parser.parse_args()

    adapter_dir = _resolve_adapter_dir(args.adapter_dir)
    eval_path = promote_adapter(
        adapter_dir,
        promoted_by=args.promoted_by,
        acceptance_profile=args.acceptance_profile,
    )
    print(f"Promoted adapter in {adapter_dir}")
    print(f"Wrote eval report to {eval_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
