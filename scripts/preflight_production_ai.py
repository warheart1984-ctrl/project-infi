#!/usr/bin/env python3
"""Preflight: verify production can initialize real AI (remote API or local torch stack)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Production AI preflight")
    parser.add_argument(
        "--preset",
        default=os.getenv("AAIS_PREFLIGHT_PRESET", "").strip() or None,
        choices=sorted(__import__("src.main", fromlist=["RUNTIME_PRESETS"]).RUNTIME_PRESETS.keys()),
        help="Apply runtime preset env before checks (e.g. production)",
    )
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv(_REPO / ".env")

    if args.preset:
        from src.main import apply_runtime_preset

        apply_runtime_preset(args.preset)

    from src import api
    from src.provider_registry import provider_registry

    provider_registry.refresh()
    remote_ids = api._configured_remote_providers()
    providers = provider_registry.list_status()

    torch_ok = False
    torch_err: str | None = None
    try:
        import torch  # noqa: F401

        torch_ok = True
    except ImportError as exc:
        torch_err = str(exc)

    profile = (os.getenv("AAIS_MODEL_PROFILE") or "full").strip().lower()
    explicit_model = (os.getenv("AAIS_TEXT_MODEL_NAME") or "").strip()
    if explicit_model:
        local_model = explicit_model
    elif profile == "lite":
        local_model = "Qwen/Qwen2.5-0.5B-Instruct"
    else:
        local_model = "mistralai/Mistral-7B-Instruct-v0.1"

    report = {
        "preset": args.preset,
        "remote_provider_ids": remote_ids,
        "torch_available": torch_ok,
        "torch_error": torch_err,
        "providers": providers,
        "local_inference_path": "remote_api" if remote_ids else "local_torch",
        "resolved_local_model": None if remote_ids else local_model,
        "model_profile": profile,
        "strict_startup": os.getenv("AAIS_ALLOW_STARTUP_FALLBACK", "1").lower() not in ("1", "true", "yes", "on"),
    }

    if remote_ids:
        print(f"PASS: AI preflight — remote providers: {', '.join(remote_ids)}")
        print(json.dumps(report, indent=2))
        return 0

    if torch_ok:
        print(
            "PASS: AI preflight — local torch stack available "
            f"(model={local_model}, profile={profile})"
        )
        print(json.dumps(report, indent=2))
        return 0

    print("FAIL: Production AI preflight", file=sys.stderr)
    print(
        "  Configure OPENROUTER_API_KEY or ANTHROPIC_API_KEY in .env for API-backed production,",
        file=sys.stderr,
    )
    print('  or install local stack: pip install -e ".[real]"', file=sys.stderr)
    if torch_err:
        print(f"  torch: {torch_err}", file=sys.stderr)
    print(json.dumps(report, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
