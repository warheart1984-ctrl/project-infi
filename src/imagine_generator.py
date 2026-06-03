"""Imagine Generator — governed imagination patterns for Story Forge handoff."""

# Mythic: Imagine Generator Organ
# Engineering: ImagineGeneratorEngine
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PATTERN_VERSION = "imagine_generator.v1"
DEFAULT_IMAGINE_ROOT = Path(".runtime/imagine_generator")
DEFAULT_STORY_FORGE_ROOT = Path(".runtime/story_forge")
FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "tools" / "imagine" / "fixtures"

REQUIRED_TOP = frozenset(
    {
        "imagine_generator_version",
        "pattern_id",
        "pattern_type",
        "prompt_frame",
        "constraints",
        "cisiv_stage",
        "claim_label",
        "created_at_utc",
    }
)

PATTERN_TYPES = frozenset(
    {"scene_seed", "character_beat", "visual_motif", "audio_cue", "world_texture"}
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def imagine_root(root: Path | None = None) -> Path:
    return (root or DEFAULT_IMAGINE_ROOT).expanduser().resolve()


def pattern_dir(pattern_id: str, *, root: Path | None = None) -> Path:
    return imagine_root(root) / pattern_id


def pattern_path(pattern_id: str, *, root: Path | None = None) -> Path:
    return pattern_dir(pattern_id, root=root) / "imagine_generator.v1.json"


def ledger_path(pattern_id: str, *, root: Path | None = None) -> Path:
    return pattern_dir(pattern_id, root=root) / "pattern_ledger.jsonl"


def story_forge_admission_path(pattern_id: str, *, story_forge_root: Path | None = None) -> Path:
    base = (story_forge_root or DEFAULT_STORY_FORGE_ROOT).expanduser().resolve()
    return base / "imagine_admissions" / f"{pattern_id}.json"


def load_fixture(name: str) -> dict[str, Any]:
    path = FIXTURE_ROOT / f"{name}.json"
    if not path.is_file():
        path = FIXTURE_ROOT / name
    if not path.is_file():
        raise FileNotFoundError(f"imagine fixture not found: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_pattern(pattern: dict[str, Any]) -> None:
    if not isinstance(pattern, dict):
        raise ValueError("pattern must be an object")
    missing = sorted(REQUIRED_TOP - set(pattern.keys()))
    if missing:
        raise ValueError(f"pattern missing required fields: {', '.join(missing)}")
    if pattern.get("imagine_generator_version") != PATTERN_VERSION:
        raise ValueError(f"imagine_generator_version must be {PATTERN_VERSION}")
    if pattern.get("pattern_type") not in PATTERN_TYPES:
        raise ValueError("invalid pattern_type")
    if not str(pattern.get("prompt_frame") or "").strip():
        raise ValueError("prompt_frame is required")


def check_constraints(pattern: dict[str, Any]) -> dict[str, Any]:
    frame = str(pattern.get("prompt_frame") or "")
    violations: list[dict[str, str]] = []
    for constraint in pattern.get("constraints") or []:
        kind = str(constraint.get("constraint_kind") or "")
        value = str(constraint.get("value") or "")
        if kind == "forbidden_term" and value:
            if re.search(re.escape(value), frame, re.IGNORECASE):
                violations.append(
                    {
                        "constraint_id": str(constraint.get("constraint_id") or ""),
                        "reason": f"forbidden_term:{value}",
                    }
                )
    passed = not violations
    claim_label = "asserted" if passed else "rejected"
    return {"passed": passed, "violations": violations, "claim_label": claim_label}


def build_pattern(
    *,
    pattern_type: str,
    prompt_frame: str,
    constraints: list[dict[str, Any]] | None = None,
    pattern_id: str | None = None,
    mission_id: str | None = None,
    session_id: str | None = None,
    cisiv_stage: str = "implementation",
) -> dict[str, Any]:
    now = _utc_now_iso()
    pattern = {
        "imagine_generator_version": PATTERN_VERSION,
        "pattern_id": pattern_id or f"pattern-{uuid.uuid4().hex[:12]}",
        "pattern_type": pattern_type,
        "prompt_frame": prompt_frame.strip(),
        "constraints": list(constraints or []),
        "cisiv_stage": cisiv_stage,
        "claim_label": "asserted",
        "created_at_utc": now,
    }
    if mission_id:
        pattern["mission_id"] = mission_id
    if session_id:
        pattern["session_id"] = session_id
    check = check_constraints(pattern)
    pattern["claim_label"] = check["claim_label"]
    validate_pattern(pattern)
    return pattern


def build_pattern_from_fixture(fixture_name: str) -> dict[str, Any]:
    spec = load_fixture(fixture_name)
    return build_pattern(
        pattern_type=str(spec["pattern_type"]),
        prompt_frame=str(spec["prompt_frame"]),
        constraints=spec.get("constraints"),
        pattern_id=spec.get("pattern_id"),
        mission_id=spec.get("mission_id"),
    )


def persist_pattern(pattern: dict[str, Any], *, root: Path | None = None) -> Path:
    validate_pattern(pattern)
    pid = str(pattern["pattern_id"])
    path = pattern_path(pid, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(pattern)
    payload["updated_at_utc"] = _utc_now_iso()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def append_pattern_ledger(pattern_id: str, event: dict[str, Any], *, root: Path | None = None) -> Path:
    path = ledger_path(pattern_id, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = dict(event)
    record.setdefault("recorded_at_utc", _utc_now_iso())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return path


def pattern_content_hash(pattern: dict[str, Any]) -> str:
    raw = json.dumps(pattern, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def admit_to_story_forge(
    pattern: dict[str, Any],
    *,
    story_forge_root: Path | None = None,
) -> dict[str, Any]:
    check = check_constraints(pattern)
    if not check["passed"]:
        return {
            "status": "rejected",
            "reason": "constraint_violation",
            "violations": check["violations"],
        }
    if pattern.get("claim_label") == "rejected":
        return {"status": "rejected", "reason": "claim_label_rejected"}

    pid = str(pattern["pattern_id"])
    admission = {
        "pattern_id": pid,
        "imagine_generator_version": PATTERN_VERSION,
        "pattern_type": pattern.get("pattern_type"),
        "content_hash": pattern_content_hash(pattern),
        "prompt_frame": pattern.get("prompt_frame"),
        "claim_label": "asserted",
        "admitted_at_utc": _utc_now_iso(),
        "downstream_lane": "story_forge",
    }
    path = story_forge_admission_path(pid, story_forge_root=story_forge_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(admission, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_pattern_ledger(
        pid,
        {"event": "story_forge_admitted", "path": str(path)},
        root=imagine_root(),
    )
    return {"status": "admitted", "admission_path": str(path), "admission": admission}


def load_pattern(pattern_id: str, *, root: Path | None = None) -> dict[str, Any]:
    path = pattern_path(pattern_id, root=root)
    if not path.is_file():
        raise FileNotFoundError(f"pattern not found: {pattern_id}")
    pattern = json.loads(path.read_text(encoding="utf-8"))
    validate_pattern(pattern)
    return pattern


__all__ = [
    "PATTERN_VERSION",
    "admit_to_story_forge",
    "append_pattern_ledger",
    "build_pattern",
    "build_pattern_from_fixture",
    "check_constraints",
    "load_pattern",
    "persist_pattern",
    "story_forge_admission_path",
    "validate_pattern",
]
