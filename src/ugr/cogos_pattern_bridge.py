"""Wolf CoG → unified pattern ledger write-path bridge (UGR-D4)."""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
import json
import os
from pathlib import Path
from typing import Any

from src.ugr.unified_pattern_ledger import UnifiedPatternLedger, normalize_cogos_pattern_record


def _default_cogos_patterns_dir() -> Path:
    env_path = os.getenv("COGOS_PATTERNS_DIR")
    if env_path:
        return Path(env_path).expanduser()
    return Path("/opt/cogos/memory/patterns")


class CogosPatternBridge:
    """Ingest cogos pattern rows into the unified v0.5 ledger."""

    BRIDGE_VERSION = "1.0"

    def __init__(
        self,
        *,
        ledger: UnifiedPatternLedger | Any | None = None,
        runtime_root: str | Path | None = None,
        cogos_patterns_dir: str | Path | None = None,
    ):
        root = Path(runtime_root or os.getenv("AAIS_RUNTIME_DIR") or Path(__file__).resolve().parents[2] / ".runtime")
        self.runtime_root = root
        self.cogos_patterns_dir = Path(cogos_patterns_dir or _default_cogos_patterns_dir())
        self._ledger = ledger
        self._seen_pattern_ids: set[str] | None = None

    @property
    def ledger(self) -> UnifiedPatternLedger | Any:
        if self._ledger is not None:
            return self._ledger
        return UnifiedPatternLedger(runtime_root=self.runtime_root)

    def _load_seen_pattern_ids(self) -> set[str]:
        if self._seen_pattern_ids is not None:
            return self._seen_pattern_ids
        seen: set[str] = set()
        events_path = self._events_path_for_ledger()
        if events_path.exists():
            with events_path.open(encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    if str(row.get("origin") or "") == "cogos":
                        pattern_id = str(row.get("pattern_id") or "")
                        if pattern_id:
                            seen.add(pattern_id)
        self._seen_pattern_ids = seen
        return seen

    def _events_path_for_ledger(self) -> Path:
        ledger = self.ledger
        if hasattr(ledger, "events_path"):
            return Path(ledger.events_path)
        if hasattr(ledger, "unified_dir"):
            return Path(ledger.unified_dir) / "pattern_events.jsonl"
        if hasattr(ledger, "_ledger") and hasattr(ledger._ledger, "unified_dir"):
            return Path(ledger._ledger.unified_dir) / "pattern_events.jsonl"
        return self.runtime_root / "collective-pattern-ledger" / "unified" / "pattern_events.jsonl"

    def ingest_record(self, cogos_row: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_cogos_pattern_record(cogos_row)
        pattern_id = str(normalized.get("pattern_id") or "")
        seen = self._load_seen_pattern_ids()
        if pattern_id and pattern_id in seen:
            return _wrap_ul_payload({"status": "duplicate", "record": normalized, "written": False})

        if hasattr(self.ledger, "append_pattern_event"):
            record = self.ledger.append_pattern_event(dict(cogos_row), mirror_legacy=False)
        else:
            underlying = getattr(self.ledger, "_ledger", self.ledger)
            record = underlying.append_pattern_event(dict(cogos_row), mirror_legacy=False)

        if pattern_id:
            seen.add(pattern_id)
        return _wrap_ul_payload({"status": "ok", "record": record, "written": True})

    def sync_events_jsonl(self, *, path: Path | None = None, max_rows: int | None = None) -> dict[str, Any]:
        source = path or (self.cogos_patterns_dir / "events.jsonl")
        if not source.exists():
            return _wrap_ul_payload({
                "status": "missing_source",
                "source": str(source),
                "ingested": 0,
                "duplicates": 0,
                "errors": 0,
            })
        ingested = 0
        duplicates = 0
        errors = 0
        rows: list[dict[str, Any]] = []
        with source.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        if max_rows is not None and max_rows > 0:
            rows = rows[-max_rows:]
        for row in rows:
            try:
                result = self.ingest_record(row)
                if result.get("written"):
                    ingested += 1
                elif result.get("status") == "duplicate":
                    duplicates += 1
            except Exception:
                errors += 1
        return _wrap_ul_payload({
            "status": "ok",
            "source": str(source),
            "ingested": ingested,
            "duplicates": duplicates,
            "errors": errors,
            "bridge_version": self.BRIDGE_VERSION,
        })

    def sync_fixture_rows(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        ingested = 0
        duplicates = 0
        for row in rows:
            result = self.ingest_record(row)
            if result.get("written"):
                ingested += 1
            elif result.get("status") == "duplicate":
                duplicates += 1
        return _wrap_ul_payload({
            "status": "ok",
            "ingested": ingested,
            "duplicates": duplicates,
            "bridge_version": self.BRIDGE_VERSION,
        })
