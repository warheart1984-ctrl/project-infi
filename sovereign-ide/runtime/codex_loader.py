from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


class CodexLoader:
    def __init__(self, base: str | Path | None = None):
        source = base if base is not None else os.environ.get("LEDGER_PATH", "sovereign")
        self.base = self._resolve_base(Path(source))
        self.constitution: Dict[str, Any] = {}
        self.specs: Dict[str, Any] = {}
        self.conformance: Dict[str, Any] = {}

    def load_all(self):
        self.constitution = {}
        self.specs = {}
        self.conformance = {}
        if self.base.is_file():
            payload = self._load_json(self.base)
            self.constitution = self._coerce_mapping(payload.get("constitution", payload))
            self.specs = self._coerce_nested_mapping(payload.get("specs", {}))
            self.conformance = self._coerce_nested_mapping(payload.get("conformance", {}))
        else:
            self.constitution = self._load("constitution_hardware.json")
            self.specs["goa_cpu"] = self._load("spec_goa_cpu.json")
            self.conformance["goa_cpu"] = self._load("conf_goa_cpu.json")
            self.specs["prime_architect"] = self._load("prime_architect.json")
        return {
            "constitution": self.constitution,
            "specs": self.specs,
            "conformance": self.conformance,
        }

    def _resolve_base(self, source: Path) -> Path:
        if source.is_absolute():
            return source
        return (Path(__file__).resolve().parents[1] / source).resolve()

    def _load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

    def _coerce_mapping(self, payload: Any) -> Dict[str, Any]:
        return dict(payload) if isinstance(payload, dict) else {}

    def _coerce_nested_mapping(self, payload: Any) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        return {str(key): value for key, value in payload.items()}

    def _load(self, name):
        path = self.base / name
        if not path.exists():
            return {}
        return self._load_json(path)
