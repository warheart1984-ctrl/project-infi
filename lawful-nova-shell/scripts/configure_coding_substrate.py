from __future__ import annotations

import argparse
import json
from pathlib import Path


REGISTRY = {
    "coding_substrate": {
        "id": "coding-substrate-1",
        "backend": "ollama",
        "model": "qwen2.5-coder:3b",
        "tier": 15,
        "role": "codegen + refactor + evidence",
    },
    "qwen_coder_7b": {
        "id": "qwen2.5-coder-7b",
        "backend": "ollama",
        "model": "qwen2.5-coder:7b",
        "tier": 14,
        "role": "larger codegen fallback",
    },
    "deepseek_coder": {
        "id": "deepseek-coder-6.7b",
        "backend": "ollama",
        "model": "deepseek-coder:6.7b",
        "tier": 13,
        "role": "completion + refactor fallback",
    },
    "coding_substrate_full": {
        "id": "coding-substrate-1-full",
        "backend": "ollama",
        "model": "coding-substrate-1:latest",
        "tier": 12,
        "role": "heavy governed codegen fallback",
    },
    "gemma4": {
        "id": "gemma4-local",
        "backend": "ollama",
        "model": "gemma4:latest",
        "tier": 11,
        "role": "general reasoning fallback",
    },
    "analysis_substrate": {
        "id": "analysis-1",
        "backend": "ollama",
        "model": "gemma4:latest",
        "tier": 14,
        "role": "specs + reasoning",
    },
    "qwen_governed": {
        "id": "qwen-governed-1",
        "backend": "ollama",
        "model": "qwen2.5-coder:3b",
        "tier": 15,
        "role": "codegen + refactor + evidence",
    },
}

CODEX_OLLAMA = {"default_model": "qwen2.5-coder:3b"}

SUBSTRATES = {
    "coding_substrate_1": {
        "id": "coding-substrate-1",
        "backend": "ollama",
        "model": "qwen2.5-coder:3b",
        "role": "codegen",
        "tier": 15,
        "node": "nova-node-1",
    },
    "analysis_substrate_1": {
        "id": "analysis-1",
        "backend": "ollama",
        "model": "gemma4:latest",
        "role": "analysis",
        "tier": 14,
        "node": "nova-node-1",
    },
    "qwen_governed_1": {
        "id": "qwen-governed-1",
        "backend": "ollama",
        "model": "qwen2.5-coder:3b",
        "role": "codegen",
        "tier": 15,
        "node": "nova-node-1",
    },
}

CAPABILITIES = {
    "coding-substrate-1": {
        "id": "coding-substrate-1",
        "role": "codegen",
        "capabilities": [
            "generate_code",
            "refactor_code",
            "explain_code",
            "write_tests",
        ],
        "constraints": [
            "no_global_state",
            "no_unbounded_io",
            "no_external_network",
        ],
    },
    "qwen-governed-1": {
        "id": "qwen-governed-1",
        "role": "codegen",
        "capabilities": [
            "generate_code",
            "refactor_code",
            "explain_code",
            "write_tests",
        ],
        "constraints": [
            "no_global_state",
            "no_unbounded_io",
            "no_external_network",
        ],
    },
    "analysis-1": {
        "id": "analysis-1",
        "role": "analysis",
        "capabilities": [
            "summarize_context",
            "explain_code",
            "write_docs",
        ],
        "constraints": [
            "no_global_state",
            "no_unbounded_io",
            "no_external_network",
        ],
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure Nova's stable local coding substrate.")
    parser.add_argument(
        "--registry-out",
        type=Path,
        default=Path.home() / "nova-model-registry.json",
        help="Path for the federation-ready Nova model registry.",
    )
    parser.add_argument(
        "--codex-out",
        type=Path,
        default=Path.home() / ".codex" / "ollama-launch-models.json",
        help="Path for Codex App's Ollama launch model config.",
    )
    parser.add_argument(
        "--substrates-out",
        type=Path,
        default=Path.home() / "nova-substrates.json",
        help="Path for the federation-ready Nova substrate registry.",
    )
    parser.add_argument(
        "--capabilities-out",
        type=Path,
        default=Path.home() / "nova-substrate-capabilities.json",
        help="Path for the Nova substrate capabilities ledger.",
    )
    args = parser.parse_args()

    _write_json(args.registry_out, REGISTRY)
    _write_json(args.codex_out, CODEX_OLLAMA)
    _write_json(args.substrates_out, SUBSTRATES)
    _write_json(args.capabilities_out, CAPABILITIES)
    print(f"Nova model registry: {args.registry_out}")
    print(f"Codex Ollama model config: {args.codex_out}")
    print(f"Nova substrate registry: {args.substrates_out}")
    print(f"Nova substrate capabilities: {args.capabilities_out}")
    print("Coding substrate: coding-substrate-1 (qwen2.5-coder:3b, tier 15)")
    return 0


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
