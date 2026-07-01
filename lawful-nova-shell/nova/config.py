from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def load_nova_config() -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "provider": os.getenv("NOVA_PROVIDER", "local").strip().lower() or "local",
        "local_model": os.getenv("NOVA_LOCAL_MODEL", "nova-local"),
        "ollama_url": os.getenv(
            "NOVA_OLLAMA_URL",
            os.getenv("NOVA_OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        ),
        "ollama_model": os.getenv("NOVA_OLLAMA_MODEL", "qwen2.5-coder:3b"),
        "external_url": os.getenv("NOVA_EXTERNAL_URL"),
        "external_api_key": os.getenv("NOVA_EXTERNAL_API_KEY"),
        "external_model": os.getenv("NOVA_EXTERNAL_MODEL"),
        "timeout": float(os.getenv("NOVA_PROVIDER_TIMEOUT", os.getenv("NOVA_OLLAMA_TIMEOUT", "120"))),
    }
    path = Path(os.getenv("NOVA_CONFIG", "nova-config.json"))
    if path.exists():
        try:
            cfg.update(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg
