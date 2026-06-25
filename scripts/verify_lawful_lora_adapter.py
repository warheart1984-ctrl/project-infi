"""Verify governed Lawful LoRA adapter load gate and optional Nova /v1/chat receipt."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.jarvis_lora_training_validator import evaluate_adapter_load_gate

DEFAULT_ADAPTER_DIR = ROOT / "training" / "out" / "jarvis-qwen-lora" / "final"


def _resolve_adapter_dir(raw: str | None) -> Path:
    candidate = (raw or os.getenv("AAIS_TEXT_ADAPTER_PATH") or str(DEFAULT_ADAPTER_DIR)).strip()
    path = Path(candidate)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    return path


def _load_metadata(adapter_dir: Path) -> dict:
    path = adapter_dir / "adapter_metadata.json"
    return json.loads(path.read_text(encoding="utf-8"))


def verify_adapter_gate(adapter_dir: Path, base_model: str) -> tuple[bool, dict]:
    metadata = _load_metadata(adapter_dir)
    allowed, reason, governance = evaluate_adapter_load_gate(metadata, base_model)
    return allowed, {"reason": reason, **governance}


def verify_nova_chat(nova_url: str, prompt: str) -> dict:
    payload = {
        "model": "lawful-nova",
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        nova_url.rstrip("/") + "/v1/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Nova chat failed HTTP {exc.code}: {detail}") from exc

    receipt = body.get("receipt") or body.get("voss_runtime") or {}
    return {
        "status": body.get("status") or body.get("decision"),
        "has_receipt": bool(receipt),
        "receipt_keys": sorted(receipt.keys()) if isinstance(receipt, dict) else [],
        "content_preview": str(body.get("content") or body.get("text") or "")[:160],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Lawful LoRA adapter governance and Nova chat.")
    parser.add_argument("--adapter-dir", default=None)
    parser.add_argument("--base-model", default=os.getenv("AAIS_TEXT_MODEL_NAME", "Qwen/Qwen2.5-1.5B-Instruct"))
    parser.add_argument("--nova-url", default=os.getenv("NOVA_API_URL", "http://127.0.0.1:8080"))
    parser.add_argument("--prompt", default="summarize lawful inference in one sentence")
    parser.add_argument("--skip-chat", action="store_true")
    args = parser.parse_args()

    adapter_dir = _resolve_adapter_dir(args.adapter_dir)
    allowed, governance = verify_adapter_gate(adapter_dir, args.base_model)
    print(json.dumps({"adapter_gate": governance}, indent=2))
    if not allowed:
        return 1

    if args.skip_chat:
        return 0

    chat = verify_nova_chat(args.nova_url, args.prompt)
    print(json.dumps({"nova_chat": chat}, indent=2))
    if not chat.get("has_receipt") and not chat.get("status"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
