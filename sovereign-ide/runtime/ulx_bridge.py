from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ULX_ROOT = Path("E:/")
if str(ULX_ROOT) not in sys.path:
    sys.path.insert(0, str(ULX_ROOT))

from ulx import compile_source_to_ulxb, run_source
from ulx_integration import SevenLayerArchitecture


DEFAULT_ULX_SOURCE = """@constitution {
    @article sovereignty {
        always: true;
        never: false;
    }
}

module constitutional_governance [sovereign] {
    fn validate_constitution() -> bool {
        return true;
    }
}
"""


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class ULXBridge:
    def __init__(self, source: str | None = None):
        self.source = source or DEFAULT_ULX_SOURCE
        self.architecture = SevenLayerArchitecture()
        self._last_compile: dict[str, Any] | None = None
        self._last_run: dict[str, Any] | None = None
        self._last_trace: dict[str, Any] | None = None

    def manifest(self) -> dict[str, Any]:
        source = self._normalized_source()
        source_hash = _sha256(source)
        return {
            "surface": "ulx",
            "title": "ULX Workbench",
            "source_hash": source_hash,
            "source_length": len(source),
            "commands": ["compile", "run", "trace"],
            "compile": self._last_compile or {},
            "run": self._last_run or {},
            "trace": self._last_trace or {},
            "traceability_links": len(getattr(self.architecture.traceability_registry, "links", {})),
            "architecture": {
                "components": sorted(self.architecture.components.keys()),
                "audit_entries": len(getattr(self.architecture.audit_ledger, "entries", [])),
            },
        }

    def compile(self, source: str | None = None) -> dict[str, Any]:
        source_text = self._normalized_source(source)
        source_hash = _sha256(source_text)
        with TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "ulx_sample.ulxb"
            compiled = compile_source_to_ulxb(source_text, str(out_path))
        result = {
            "surface": "ulx",
            "command": "compile",
            "accepted": True,
            "source_hash": source_hash,
            "source_preview": source_text[:120].strip(),
            "bytecode": compiled,
            "bytecode_summary": {
                "functions": sorted((compiled.get("functions") or {}).keys()),
                "has_constitution": bool(compiled.get("constitution")),
            },
        }
        self._last_compile = result
        return result

    def run(self, source: str | None = None) -> dict[str, Any]:
        source_text = self._normalized_source(source)
        source_hash = _sha256(source_text)
        interpreter, result = run_source(source_text, "constitutional_governance::validate_constitution")
        output = {
            "surface": "ulx",
            "command": "run",
            "accepted": True,
            "source_hash": source_hash,
            "result": result,
            "interpreter": interpreter.__class__.__name__ if interpreter is not None else "unknown",
        }
        self._last_run = output
        return output

    def trace(self, source: str | None = None) -> dict[str, Any]:
        source_text = self._normalized_source(source)
        source_hash = _sha256(source_text)
        trace_id = f"ulx-{source_hash[:12]}"
        compile_trace_id = f"{trace_id}-compile"
        run_trace_id = f"{trace_id}-run"

        self.architecture.load_constitution(source_text)
        self.architecture.create_traceability_link(
            compile_trace_id,
            "ulx.source",
            "ulx.compile",
            "compile",
            {"source_hash": source_hash},
        )
        self.architecture.create_traceability_link(
            run_trace_id,
            "ulx.compile",
            "ulx.run",
            "execution",
            {"source_hash": source_hash},
        )

        trace = {
            "surface": "ulx",
            "command": "trace",
            "accepted": True,
            "traceId": trace_id,
            "source_hash": source_hash,
            "links": {
                "forward": self.architecture.traceability_registry.resolve_forward("ulx.source"),
                "backward": self.architecture.traceability_registry.resolve_backward("ulx.run"),
            },
            "audit": {
                "chain_valid": self.architecture.verify_audit_chain(),
                "summary": self.architecture.get_compliance_status(),
            },
            "bundle": self._bundle_summary(),
        }
        self._last_trace = trace
        return trace

    def _bundle_summary(self) -> dict[str, Any]:
        bundle = self.architecture.compliance_dashboard.get_conformance_summary()
        return {
            "components": bundle.get("total_components", 0),
            "standards": sorted(bundle.get("by_standard", {}).keys()),
            "open_findings": len(bundle.get("open_findings", [])),
        }

    def _normalized_source(self, source: str | None = None) -> str:
        candidate = self.source if source is None else source
        return str(candidate).strip()
